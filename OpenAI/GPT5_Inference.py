import os
import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

from openai import OpenAI

DATASET_ROOT = Path("../dataset")
OUTPUT_ROOT = Path(".")  # where you currently write folder/{i}.json
FOLDERS = ["neutral", "confirmation", "herding", "anchoring", "loss-aversion", "recency"]

def load_json_files(folder: str, start: int, end: int) -> Dict[int, dict]:
    json_data = {}
    for i in range(start, end + 1):
        filename = DATASET_ROOT / folder / f"{i}.json"
        if filename.exists():
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    json_data[i] = json.load(f)
            except json.JSONDecodeError as e:
                print(f"[WARN] Error decoding JSON in {filename}: {e}")
        else:
            print(f"[INFO] File {filename} not found, skipping.")
    return json_data

def to_yes_no(s: str) -> str:
    # Extract a clean Yes/No to match your “evaluable” rule
    m_yes = re.search(r"\byes\b", s, re.I)
    m_no  = re.search(r"\bno\b",  s, re.I)
    if m_yes and not m_no: return "Yes"
    if m_no and not m_yes: return "No"
    # fallback: take the first occurrence if both appear
    if m_yes and m_no:
        return "Yes" if m_yes.start() < m_no.start() else "No"
    # last resort: truncate/normalize
    return "Yes" if s.strip().lower().startswith("y") else "No" if s.strip().lower().startswith("n") else s.strip()

def build_tasks(start: int, end: int, model: str) -> Tuple[List[dict], List[Tuple[str, int]]]:
    """
    Returns:
      tasks: list of batch JSONL dicts
      index: list of (folder, i) pairs for info
    """
    tasks = []
    index: List[Tuple[str, int]] = []
    for folder in FOLDERS:
        items = load_json_files(folder, start, end)
        for i, data in items.items():
            context = data["Context"]
            question = data["Question"]
            # The instruction mirrors your prompt and keeps the chat semantics
            messages = [
                {"role": "system", "content": "You are a helpful financial QA assistant. Read the Context and Question. Answer strictly with 'Yes' or 'No'."},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion:\n{question}\n\nAnswer with Yes or No only."},
            ]
            task = {
                "custom_id": f"{folder}|{i}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": model,
                    "temperature": 1,
                    "reasoning_effort": "low",
                    "max_completion_tokens": 1000,  # tiny—keeps answers short and cheap
                    "messages": messages,
                },
            }
            tasks.append(task)
            index.append((folder, i))
    return tasks, index

def write_jsonl(tasks: List[dict], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for obj in tasks:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def submit_batch(client: OpenAI, jsonl_path: Path) -> str:
    batch_file = client.files.create(file=open(jsonl_path, "rb"), purpose="batch")
    batch = client.batches.create(
        input_file_id=batch_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={"job": "investment-bias-eval"},
    )
    print(f"[SUBMITTED] batch_id={batch.id}")
    return batch.id

def ensure_output_dirs():
    for folder in FOLDERS:
        (OUTPUT_ROOT / folder).mkdir(parents=True, exist_ok=True)

def _file_text(resp):
    try:
        t = getattr(resp, "text", None)
        if t is not None:
            return t
    except Exception:
        pass
    c = getattr(resp, "content", None)
    return c.decode("utf-8", errors="replace") if c is not None else ""

def _safe_write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def _append_jsonl(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def extract_answer_from_body(body: dict) -> str:
    """
    Try multiple schemas in order:
      1) /v1/chat/completions → body['choices'][0]['message']['content']
      2) Responses API consolidated text → body['output_text']
      3) Responses API structured → concatenate text from body['output'][*].content[*].text
    Returns "" if nothing found.
    """
    # 1) Chat Completions
    try:
        choices = body.get("choices") or []
        if choices:
            msg = choices[0].get("message") or {}
            content = msg.get("content")
            if isinstance(content, str) and content.strip():
                return content
    except Exception:
        pass

    # 2) Responses API: output_text
    txt = body.get("output_text")
    if isinstance(txt, str) and txt.strip():
        return txt

    # 3) Responses API: output array with content blocks
    out = body.get("output")
    if isinstance(out, list):
        pieces = []
        for block in out:
            # Common shapes: {"content":[{"type":"output_text","text": "..."}], ...}
            content = block.get("content")
            if isinstance(content, list):
                for seg in content:
                    if isinstance(seg, dict):
                        t = seg.get("text")
                        if isinstance(t, str) and t:
                            pieces.append(t)
            elif isinstance(content, str) and content:
                pieces.append(content)
        if pieces:
            return "".join(pieces)

    return ""  # give up gracefully


def _counts(batch):
    rc = getattr(batch, "request_counts", None)
    if rc is None:
        return 0, 0, 0
    # Newer SDKs: pydantic model with attributes
    total = getattr(rc, "total", None)
    completed = getattr(rc, "completed", None)
    failed = getattr(rc, "failed", None)
    if total is not None or completed is not None or failed is not None:
        return int(total or 0), int(completed or 0), int(failed or 0)
    # Older SDKs: dict-like
    if isinstance(rc, dict):
        return int(rc.get("total", 0)), int(rc.get("completed", 0)), int(rc.get("failed", 0))
    # Last resort
    return 0, 0, 0

def _dump_error_file(client, error_file_id: str, out_path: str = "batch_errors.jsonl"):
    try:
        err_resp = client.files.content(error_file_id)
        err_text = _file_text(err_resp)
        Path(out_path).write_text(err_text, encoding="utf-8")
        print(f"[ERRORS] Wrote {out_path}")
        lines = err_text.splitlines()
        for i, line in enumerate(lines[:5], 1):
            print(f"  {i:02d}: {line}")
        if not lines:
            print("[ERRORS] (file is empty)")
    except Exception as e:
        print(f"[WARN] Could not download error file: {e}")

def collect_and_write(client: OpenAI, batch_id: str, model_used: str):
    batch = client.batches.retrieve(batch_id)

    print(f"[STATUS] {batch.status}")
    total, completed, failed = _counts(batch)
    print(f"[COUNTS] total={total} completed={completed} failed={failed}")

    # Dump error file if failures exist (or if all failed)
    if failed and getattr(batch, "error_file_id", None):
        _dump_error_file(client, batch.error_file_id, "batch_errors.jsonl")

    output_file_id = getattr(batch, "output_file_id", None)

    # If there are no successful requests or no output file, stop after dumping errors
    if completed == 0 or not output_file_id:
        if completed == 0:
            print("[INFO] No successful requests; skipping outputs.")
        else:
            print("[INFO] output_file_id missing; skipping outputs.")
        return

    # Download successful results
    try:
        result_resp = client.files.content(output_file_id)
        result_text = _file_text(result_resp)
    except Exception as e:
        print(f"[ERROR] Could not download output file: {e}")
        return
    
    # 1) Dump the raw file for debugging
    raw_dir = Path("raw_outputs")
    raw_path = raw_dir / f"{batch_id}.jsonl"
    _safe_write_text(raw_path, result_text)
    print(f"[RAW] Saved raw batch output to {raw_path}")
    
    ensure_output_dirs()
    
    # Prepare a parse-failure log
    fail_log = raw_dir / f"parse_failures_{batch_id}.jsonl"
    
    for line in result_text.splitlines():
        if not line.strip():
            continue
    
        try:
            obj = json.loads(line)
        except Exception as e:
            _append_jsonl(fail_log, {"reason": "json_load_error", "line": line[:2000]})
            continue
    
        cid = obj.get("custom_id", "")
        body = (obj.get("response") or {}).get("body") or {}
    
        # Extract text robustly
        text = ""
        try:
            text = extract_answer_from_body(body).strip()
        except Exception as e:
            _append_jsonl(fail_log, {"reason": "extract_exception", "custom_id": cid, "body_head": str(body)[:2000]})
            continue
    
        if not text:
            _append_jsonl(fail_log, {"reason": "empty_text", "custom_id": cid, "body_head": str(body)[:2000]})
            continue
    
        # custom_id format: "{folder}|{i}"
        try:
            folder, key_s = cid.split("|", 1)
            key = int(key_s)
        except Exception:
            _append_jsonl(fail_log, {"reason": "bad_custom_id", "custom_id": cid})
            continue
    
        src_path = DATASET_ROOT / folder / f"{key}.json"
        if not src_path.exists():
            _append_jsonl(fail_log, {"reason": "missing_source", "custom_id": cid, "src_path": str(src_path)})
            continue
    
        with open(src_path, "r", encoding="utf-8") as f:
            src = json.load(f)
    
        normalized = to_yes_no(text)
    
        new_data = {
            "Context": src["Context"],
            "Question": src["Question"],
            "True Answer": src["Answer"],
            "Answer": normalized,
            "Category": src["Category"],
            "Perturbation": model_used,
        }
    
        out_path = OUTPUT_ROOT / folder / f"{key}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(new_data, f, indent=4, ensure_ascii=False)
    
    print("[DONE] Results written to per-folder JSONs.")
    print(f"[DEBUG] If any lines failed to parse, see {fail_log}")




def main():
    parser = argparse.ArgumentParser(description="Batch evaluation with OpenAI Batch API.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_submit = sub.add_parser("submit", help="Create JSONL and start a batch")
    p_submit.add_argument("start", type=int)
    p_submit.add_argument("end", type=int)
    p_submit.add_argument("--model", default="gpt-5-nano")

    p_collect = sub.add_parser("collect", help="Download results for a completed batch and write outputs")
    p_collect.add_argument("batch_id")
    p_collect.add_argument("--model", default="gpt-5-nano")

    args = parser.parse_args()

    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    if args.cmd == "submit":
        tasks, _ = build_tasks(args.start, args.end, args.model)
        jsonl_path = Path(f"batch_tasks_{args.start}_{args.end}.jsonl")
        write_jsonl(tasks, jsonl_path)
        submit_batch(client, jsonl_path)

    elif args.cmd == "collect":
        collect_and_write(client, args.batch_id, args.model)

if __name__ == "__main__":
    main()



