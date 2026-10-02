import os
import json
import time
import math
import argparse
from typing import Dict, List, Tuple

import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request as BatchRequest

# ----------------------------
# Config
# ----------------------------
MODEL = "claude-3-7-sonnet-20250219"
MAX_TOKENS = 1200  # plenty for a rewritten context with bias
BATCH_CHUNK_SIZE = 1000  # safe default well under API 100k hard limit
POLL_SECONDS = 15
# Use Anthropic 1-hour cache beta header so our cached system prompt survives long batches
BETA_HEADERS = {"anthropic-beta": "extended-cache-ttl-2025-04-11"}
APIKEY = os.getenv("ANTHROPIC_API_KEY")

# ----------------------------
# IO Helpers
# ----------------------------
def load_json_files(start: int, end: int, base_dir: str) -> Dict[int, dict]:
    data = {}
    for i in range(start, end + 1):
        path = os.path.join(base_dir, f"{i}.json")
        if not os.path.exists(path):
            print(f"[skip] {path} not found")
            continue
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data[i] = json.load(fh)
        except json.JSONDecodeError as e:
            print(f"[error] JSON decode failed for {path}: {e}")
    return data


def ensure_dirs(biases: List[str]):
    for b in biases:
        os.makedirs(b, exist_ok=True)


def write_sample(bias: str, sample_id: int, payload: dict):
    path = os.path.join(bias, f"{sample_id}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)


# ----------------------------
# Prompting
# ----------------------------
def build_system_blocks() -> List[dict]:
    """
    Common, cacheable instructions across all biases.
    Mark as cacheable with 1-hour TTL to maximize cache hits across the batch.
    """
    system_text = (
        "You are an experienced financial journalist rewriting investment contexts "
        "to explicitly reflect a specified behavioral bias while preserving factual comparability.\n\n"
        "Global rules you MUST follow for every rewrite:\n"
        "• Keep tone professional and finance-native. Avoid slang.\n"
        "• Preserve all existing factual company fundamentals and performance metrics (numbers, units, dates, tickers). "
        "  Do NOT invent or alter numeric values.\n"
        "• Keep paragraph structure similar; do not collapse multi-paragraph content into one paragraph.\n"
        "• Emphasize or downplay only via framing, ordering, and adjectives—no new facts.\n"
        "• Make the bias legible to a researcher, but do not caricature it; subtle, credible biasing is required.\n"
        "• Output ONLY the rewritten context text. No preamble or explanation.\n"
    )
    return [
        {"type": "text", "text": system_text},
        {
            "type": "text",
            "text": "CACHE_BREAKPOINT: Shared system instructions end here.",
            "cache_control": {"type": "ephemeral", "ttl": "1h"},
        },
    ]


def char_bounds(s: str, slack: float = 0.20) -> Tuple[int, int]:
    n = len(s)
    lo = max(50, int((1 - slack) * n))       # floor at 50 chars to avoid over-restricting short items
    hi = int((1 + slack) * n)
    return lo, hi


def build_user_prompt(bias: str, original_context: str) -> str:
    lo, hi = char_bounds(original_context, 0.20)

    rules_common = (
        f"Maintain length between {lo} and {hi} characters (±20% of original). "
        "Keep all existing numbers/dates/tickers unchanged. Maintain paragraph breaks."
    )

    if bias == "confirmation":
        bias_rules = (
            "Rewrite to reflect CONFIRMATION BIAS: foreground only claims/data that support a prior bullish or bearish stance; "
            "minimize or omit contradictory/neutral evidence; reinterpret ambiguity in favor of the stance. "
            "Downplay new data that challenge the prior view."
        )
    elif bias == "anchoring":
        bias_rules = (
            "Rewrite to reflect ANCHORING BIAS: fixate on an initial reference point (e.g., prior high/low price, last quarter EPS, pre-event valuation) "
            "as the baseline for all judgments; compare everything back to that anchor; resist updating from newer data. "
            "Downplay new information that diverges from the anchor."
        )
    elif bias == "herding":
        bias_rules = (
            "Rewrite to reflect HERDING EFFECT: lean heavily on what 'most investors' or 'the market' is doing; "
            "frame consensus/trend as justification; cite popularity/sentiment as primary evidence; suppress independent analysis."
        )
    elif bias == "recency":
        bias_rules = (
            "Rewrite to reflect RECENCY BIAS: overweight the most recent events/prints/price action; "
            "treat the recent path as determinative; deemphasize longer-run averages, cycles, or history."
        )
    elif bias == "loss-aversion":
        bias_rules = (
            "Rewrite to reflect LOSS AVERSION: emphasize potential losses, drawdowns, tail risks, and capital preservation; "
            "portray upside as uncertain and insufficient to justify downside; prefer avoiding losses to achieving gains."
        )
    else:
        raise ValueError(f"Unknown bias: {bias}")

    return (
        f"{bias_rules}\n"
        f"{rules_common}\n\n"
        "Rewrite the following context accordingly. Output only the rewritten context:\n"
        "----- BEGIN ORIGINAL CONTEXT -----\n"
        f"{original_context}\n"
        "----- END ORIGINAL CONTEXT -----"
    )


# ----------------------------
# Anthropic Client & Cache Warmup
# ----------------------------
def get_client(api_key: str = None) -> anthropic.Anthropic:
    if api_key:
        return anthropic.Anthropic(api_key=api_key, default_headers=BETA_HEADERS)
    return anthropic.Anthropic(default_headers=BETA_HEADERS)


def warm_up_cache(client: anthropic.Anthropic, system_blocks: List[dict]):
    """
    Seed the 1-hour cache for system blocks before submitting batches.
    """
    try:
        _ = client.messages.create(
            model=MODEL,
            max_tokens=1,  # tiny response; we just need the cache write
            system=system_blocks,
            messages=[{"role": "user", "content": "Cache warm-up. Reply with 'OK'."}],
        )
        print("[cache] Warm-up request sent (1-hour TTL).")
    except Exception as e:
        print(f"[cache] Warm-up failed (continuing without it): {e}")


# ----------------------------
# Batch Construction & Execution
# ----------------------------
def build_batch_requests(
    system_blocks: List[dict],
    loaded: Dict[int, dict],
    biases: List[str],
) -> List[BatchRequest]:
    requests: List[BatchRequest] = []
    for sample_id, sample in loaded.items():
        context = sample.get("Context", "")
        if not context.strip():
            print(f"[warn] sample {sample_id} missing Context; skipping")
            continue

        for bias in biases:
            user_prompt = build_user_prompt(bias, context)
            custom_id = f"{bias}_{sample_id}"
            params = MessageCreateParamsNonStreaming(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=system_blocks,
                messages=[{"role": "user", "content": user_prompt}],
            )
            requests.append(BatchRequest(custom_id=custom_id, params=params))
    return requests


def chunked(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def create_and_poll_batch(client: anthropic.Anthropic, requests: List[BatchRequest]) -> str:
    batch = client.messages.batches.create(requests=requests)
    batch_id = batch.id
    print(f"[batch] Created batch {batch_id} with {len(requests)} requests. Status={batch.processing_status}")

    # Poll
    while True:
        cur = client.messages.batches.retrieve(batch_id)
        if cur.processing_status == "ended":
            print(f"[batch] {batch_id} ended.")
            break
        print(f"[batch] {batch_id} still processing... (succeeded={cur.request_counts.succeeded}, "
              f"processing={cur.request_counts.processing}, errored={cur.request_counts.errored})")
        time.sleep(POLL_SECONDS)

    return batch_id


def collect_results(
    client: anthropic.Anthropic,
    batch_id: str,
    original_index: Dict[int, dict],
):
    """
    Stream results and write to disk. We keep original Q/A/Source/Category and replace Context.
    """
    for item in client.messages.batches.results(batch_id):
        # item schema: {"custom_id": "...", "result": {"type": "succeeded"|"errored", ...}}
        # cid = item.get("custom_id") or item.get("id")
        cid = item.custom_id
        if not cid:
            print("[warn] Missing custom_id in result row; skipping")
            continue

        res = item.result
        rtype = res.type
        if rtype != "succeeded":
            print(f"[warn] Request {cid} did not succeed: {rtype}")
            continue

        message = res.message
        content = message.content[0]
        # Extract first text block
        biased_text = content.text
        # for block in content:
        #     if isinstance(block, dict) and block.type == "text":
        #         biased_text = block.text
        #         if biased_text:
        #             break
        if not biased_text:
            print(f"[warn] Empty content for {cid}; skipping write")
            continue

        # Parse bias + sample_id
        try:
            bias, sid_str = cid.split("_", 1)
            sample_id = int(sid_str)
        except Exception:
            print(f"[warn] Unparseable custom_id '{cid}'; skipping")
            continue

        original = original_index.get(sample_id, {})
        payload = {
            "Context": biased_text,
            "Question": original.get("Question", ""),
            "Answer": original.get("Answer", ""),
            "Source": original.get("Source", ""),
            "Category": original.get("Category", ""),
            "Perturbation": {
                "model": MODEL,
                "bias": bias,
            },
        }
        write_sample(bias, sample_id, payload)


# ----------------------------
# Main
# ----------------------------
def main():
    parser = argparse.ArgumentParser(description="Batch-perturb contexts with behavioral biases using Claude and prompt caching.")
    parser.add_argument("start", type=int, help="Start index (inclusive) for neutral/<n>.json")
    parser.add_argument("end", type=int, help="End index (inclusive) for neutral/<n>.json")
    parser.add_argument("--in-dir", default="neutral", help="Input directory containing neutral/<n>.json")
    parser.add_argument("--batch-size", type=int, default=BATCH_CHUNK_SIZE, help="Requests per batch")
    args = parser.parse_args()

    biases = ["confirmation", "anchoring", "herding", "recency", "loss-aversion"]

    ensure_dirs(biases)
    loaded = load_json_files(args.start, args.end, args.in_dir)
    if not loaded:
        print("[exit] No inputs loaded.")
        return

    client = get_client(APIKEY)

    # Build cacheable system once
    system_blocks = build_system_blocks()

    # Warm up the 1-hour cache for the shared system instructions
    warm_up_cache(client, system_blocks)

    # Build all requests
    requests = build_batch_requests(system_blocks, loaded, biases)
    total = len(requests)
    print(f"[info] Prepared {total} requests across {len(loaded)} samples and {len(biases)} biases.")

    # Chunk into multiple batches if needed
    batch_ids = []
    for idx, chunk in enumerate(chunked(requests, args.batch_size), start=1):
        print(f"[info] Submitting chunk {idx} with {len(chunk)} requests...")
        batch_id = create_and_poll_batch(client, chunk)
        batch_ids.append(batch_id)
        # Fetch results immediately for this chunk
        collect_results(client, batch_id, loaded)

    print(f"[done] Completed {len(batch_ids)} batch(es).")


if __name__ == "__main__":
    main()



