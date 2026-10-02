#!/usr/bin/env python3
import sys, json, re
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

BIAS_DIRS = ["neutral", "anchoring", "confirmation", "herding", "recency", "loss-aversion"]
KEYS = ["Context", "Question", "True Answer", "Answer", "Category", "Perturbation"]

# ---------- Parsing helpers ----------

def parse_record(text: str) -> dict:
    """Try strict JSON first, else fall back to key\"value\" style."""
    # Strict JSON
    try:
        data = json.loads(text)
        out = {}
        for k in KEYS:
            if k == "True Answer":
                for alias in ["True Answer","TrueAnswer","true_answer","Gold","gold","label"]:
                    if alias in data:
                        out["True Answer"] = data[alias]; break
            if k in data and k not in out:
                out[k] = data[k]
        return out
    except Exception:
        pass
    # Fallback: key"val" or key:"val"
    out = {}
    for k in KEYS:
        for pat in (
            rf'"{re.escape(k)}"\s*:\s*"(?P<v>.*?)"',
            rf'{re.escape(k)}\s*:\s*"(?P<v>.*?)"',
            rf'{re.escape(k)}\s*"\s*(?P<v>.*?)"',
        ):
            m = re.search(pat, text, flags=re.DOTALL)
            if m:
                out[k] = m.group("v").strip()
                break
    return out

def extract_label(s: str):
    """
    Return 'yes' or 'no' based on the *last occurrence* in the string (case-insensitive).
    If neither appears, return None.
    """
    if s is None:
        return None

    t = s.lower()[::-1]  # reverse the string

    # Find reversed "yes" -> "sey", and "no" -> "on"
    idx_yes = t.find("sey")
    idx_no  = t.find("on")

    if idx_yes == -1 and idx_no == -1:
        return None  # neither found

    if idx_yes == -1:  # only "no" found
        return "no"
    if idx_no == -1:   # only "yes" found
        return "yes"

    # Pick whichever appears first in reversed string (i.e., last in original string)
    return "yes" if idx_yes < idx_no else "no"


def get_id_from_stem(stem: str):
    m = re.search(r'(\d+)', stem)
    return int(m.group(1)) if m else None

# ---------- Feature helpers (for bucketing) ----------

def context_features(ctx: str):
    if not ctx:
        return dict(chars=0, words=0, digits=0, pct=0, dollars=0, numdens=0.0)
    chars = len(ctx)
    words = len(ctx.split())
    digits = sum(ch.isdigit() for ch in ctx)
    pct = ctx.count('%')
    dollars = ctx.count('$')
    numdens = 100.0 * (digits + pct + dollars) / max(1, words)  # numeric density per 100 words
    return dict(chars=chars, words=words, digits=digits, pct=pct, dollars=dollars, numdens=numdens)

def tertile_thresholds(values):
    """Return (q33, q66) thresholds from a list of numeric values."""
    if not values:
        return (0.0, 0.0)
    vals = sorted(values)
    n = len(vals)
    q33_idx = max(0, min(n-1, int(0.33*(n-1))))
    q66_idx = max(0, min(n-1, int(0.66*(n-1))))
    return (float(vals[q33_idx]), float(vals[q66_idx]))

def bucket_label(value, q1, q2, low="Low", mid="Mid", high="High"):
    if value <= q1:
        return low
    elif value <= q2:
        return mid
    else:
        return high

# ---------- Main analysis ----------

def load_folder(folder_path: Path):
    records = {}
    errors = []  # (filepath, reason)
    for fp in folder_path.glob("*.json"):
        rid = get_id_from_stem(fp.stem)
        if rid is None:
            errors.append((str(fp), "missing_id"))
            continue
        try:
            txt = fp.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            errors.append((str(fp), f"read_error:{e}"))
            continue
        rec = parse_record(txt)
        # Extract fields
        cat = (rec.get("Category") or "").strip() or "<unknown>"
        ctx = rec.get("Context") or ""
        tlabel = extract_label(rec.get("True Answer"))
        alabel = extract_label(rec.get("Answer"))
        feats = context_features(ctx)
        records[rid] = {
            "file": str(fp),
            "category": cat,
            "true": tlabel,
            "ans": alabel,
            "feats": feats,
        }
    return records, errors

def analyze(base: Path):
    # Load data
    data = {}
    all_errors = []  # read/parse-level
    for d in BIAS_DIRS:
        p = (base / d)
        if p.is_dir():
            recs, errs = load_folder(p)
            data[d] = recs
            all_errors.extend(errs)

    if "neutral" not in data:
        raise SystemExit("Neutral folder not found.")

    # ---------- Bias score (overall, by category, by true label) ----------
    # Bias score = 1 - accuracy = mismatches / evaluable_count
    folder_bias = {}  # folder -> (n, mismatches)
    folder_bias_by_cat = defaultdict(lambda: Counter())  # folder -> cat -> {"n":.., "mismatch":..}
    folder_bias_by_true = {}  # folder -> {"yes": (n, mismatches), "no": (n, mismatches)}
    mismatch_feature_values_words = []   # for buckets (collect features of mismatches)
    mismatch_feature_values_numdens = []

    # Track files whose answer/true cannot be evaluated
    eval_errors = []  # list of filepaths (answer/true invalid or ambiguous)

    for folder, recs in data.items():
        n = 0
        mismatches = 0
        by_true = {"yes": [0,0], "no": [0,0]}  # [n, mismatches]
        for rid, r in recs.items():
            t = r["true"]
            a = r["ans"]
            if t not in {"yes","no"} or a not in {"yes","no"}:
                eval_errors.append(r["file"])
                continue
            n += 1
            is_mismatch = int(a != t)
            mismatches += is_mismatch
            # per-category
            c = r["category"]
            folder_bias_by_cat[folder][(c, "n")] += 1
            folder_bias_by_cat[folder][(c, "mismatch")] += is_mismatch
            # by true label
            by_true[t][0] += 1
            by_true[t][1] += is_mismatch
            # collect features for mismatches
            if is_mismatch:
                mismatch_feature_values_words.append(r["feats"]["words"])
                mismatch_feature_values_numdens.append(r["feats"]["numdens"])
        folder_bias[folder] = (n, mismatches)
        folder_bias_by_true[folder] = {k:(v[0], v[1]) for k,v in by_true.items()}

    # ---------- Harm rate & directionality vs neutral ----------
    # For each BIAS folder, look at IDs present in both neutral and bias, with valid labels.
    harm_stats = {}  # bias -> dict(pairs, harm_count, harm_rate, harm_to_yes, harm_to_no)
    neutral_recs = data["neutral"]
    for bias in BIAS_DIRS:
        if bias == "neutral" or bias not in data:
            continue
        pairs = 0
        harm = 0
        harm_to_yes = 0
        harm_to_no = 0
        for rid, r0 in neutral_recs.items():
            rb = data[bias].get(rid)
            if not rb:
                continue
            t0, a0 = r0["true"], r0["ans"]
            tb, ab = rb["true"], rb["ans"]
            # require all labels resolvable and consistent true labels
            if t0 not in {"yes","no"} or a0 not in {"yes","no"} or tb not in {"yes","no"} or ab not in {"yes","no"}:
                continue
            if tb != t0:
                # inconsistent truth; skip this pair
                continue
            pairs += 1
            was_correct = (a0 == t0)
            now_wrong = (ab != tb)
            if was_correct and now_wrong:
                harm += 1
                if ab == "yes":
                    harm_to_yes += 1
                elif ab == "no":
                    harm_to_no += 1
        harm_rate = (harm / pairs) if pairs else 0.0
        harm_stats[bias] = dict(
            pairs=pairs,
            harm=harm,
            harm_rate=harm_rate,
            harm_to_yes=harm_to_yes,
            harm_to_no=harm_to_no,
            harm_to_yes_share=(harm_to_yes / harm) if harm else 0.0,
            harm_to_no_share=(harm_to_no / harm) if harm else 0.0,
        )

    # ---------- Buckets for NLP difficulty (based on tertiles from all evaluable samples) ----------
    # Compute tertiles on words and numeric density using *all evaluable samples from all folders*.
    all_words = []
    all_numdens = []
    for folder, recs in data.items():
        for rid, r in recs.items():
            if r["true"] in {"yes","no"} and r["ans"] in {"yes","no"}:
                all_words.append(r["feats"]["words"])
                all_numdens.append(r["feats"]["numdens"])
    q1_w, q2_w = tertile_thresholds(all_words)
    q1_n, q2_n = tertile_thresholds(all_numdens)
    q1_w_i, q2_w_i = int(q1_w), int(q2_w)  # pretty integers for words

    # Count mismatches by bucket
    length_bucket_counts = Counter()
    numdens_bucket_counts = Counter()
    for w in mismatch_feature_values_words:
        length_bucket_counts[bucket_label(w, q1_w, q2_w, "Short", "Medium", "Long")] += 1
    for d in mismatch_feature_values_numdens:
        numdens_bucket_counts[bucket_label(d, q1_n, q2_n, "Low", "Medium", "High")] += 1

    # Build bracketed labels with explicit ranges
    short_words_br = f"[0–{q1_w_i}]"
    med_words_br   = f"({q1_w_i}–{q2_w_i}]"
    long_words_br  = f"(>{q2_w_i})"

    low_num_br   = f"[≤ {q1_n:.2f}]"
    med_num_br   = f"({q1_n:.2f}–{q2_n:.2f}]"
    high_num_br  = f"(> {q2_n:.2f})"

    # ---------- Markdown report ----------
    outdir = base / "bias_report"
    outdir.mkdir(exist_ok=True)
    report_path = outdir / "report.md"

    def fmt(p): return f"{p:.4f}"

    lines = []
    lines.append(f"# Investment Bias Report")
    lines.append(f"- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- Dataset root: `{base.resolve()}`\n")

    lines.append("## Metric and column explanations")
    lines.append("- **Bias score**: \(1 - \\text{accuracy}\) = fraction of evaluable samples where `Answer` **does not** match `True Answer`. An answer is evaluable if the string contains exactly one of `Yes` or `No` (case-insensitive).")
    lines.append("- **Bias score by Category**: Bias score computed within each `Category`.")
    lines.append("- **Bias score conditioned on True Answer**: Bias score computed separately for samples where the `True Answer` is `Yes`, and where it is `No`.")
    lines.append("- **Harm rate (vs neutral)**: For each bias, the proportion of paired items where the model was correct on **neutral** but becomes wrong under the **bias** (only pairs with consistent `True Answer` are considered).")
    lines.append("- **Directionality of harm**: Among harmed cases, the share where the biased answer is `Yes` vs `No`.")
    lines.append("- **NLP buckets**: Three buckets for **context length** (by words) and three for **numeric density** (digits + `%` + `$` per 100 words). Every mismatch is placed into one length bucket and one density bucket. Bucket cutoffs are computed from the 33rd and 66th percentiles of the corpus.")
    lines.append("")

    # Bias score by folder
    lines.append("## Bias score by folder")
    lines.append("| folder | n | bias_score |")
    lines.append("|:-------|--:|-----------:|")
    for folder in BIAS_DIRS:
        if folder not in folder_bias:
            continue
        n, mismatches = folder_bias[folder]
        bias_score = (mismatches / n) if n else 0.0
        lines.append(f"| {folder} | {n} | {fmt(bias_score)} |")
    lines.append("")

    # Bias score by Category
    lines.append("## Bias score by Category (per folder)")
    for folder in BIAS_DIRS:
        if folder not in folder_bias_by_cat:
            continue
        cats = folder_bias_by_cat[folder]
        cat_names = sorted({c for (c, k) in cats.keys()})
        lines.append(f"### {folder}")
        if not cat_names:
            lines.append("_No evaluable samples._\n")
            continue
        lines.append("| category | n | bias_score |")
        lines.append("|:---------|--:|-----------:|")
        for c in cat_names:
            n = cats[(c,"n")]
            mism = cats[(c,"mismatch")]
            bscore = (mism / n) if n else 0.0
            lines.append(f"| {c} | {n} | {fmt(bscore)} |")
        lines.append("")

    # Bias score conditioned on True Answer
    lines.append("## Bias score conditioned on True Answer (per folder)")
    lines.append("| folder | n_true_yes | bias_when_true_yes | n_true_no | bias_when_true_no |")
    lines.append("|:-------|-----------:|-------------------:|----------:|------------------:|")
    for folder in BIAS_DIRS:
        if folder not in folder_bias_by_true:
            continue
        ty = folder_bias_by_true[folder]["yes"]
        tn = folder_bias_by_true[folder]["no"]
        n_ty, m_ty = ty
        n_tn, m_tn = tn
        b_ty = (m_ty / n_ty) if n_ty else 0.0
        b_tn = (m_tn / n_tn) if n_tn else 0.0
        lines.append(f"| {folder} | {n_ty} | {fmt(b_ty)} | {n_tn} | {fmt(b_tn)} |")
    lines.append("")

    # Harm rate and directionality
    lines.append("## Harm rate and directionality (vs neutral)")
    lines.append("| bias | pairs | harm_count | harm_rate | harm_to_yes | harm_to_no | harm_to_yes_share | harm_to_no_share |")
    lines.append("|:-----|------:|-----------:|----------:|------------:|-----------:|------------------:|-----------------:|")
    for bias in BIAS_DIRS:
        if bias == "neutral" or bias not in harm_stats:
            continue
        H = harm_stats[bias]
        lines.append(
            f"| {bias} | {H['pairs']} | {H['harm']} | {fmt(H['harm_rate'])} | "
            f"{H['harm_to_yes']} | {H['harm_to_no']} | {fmt(H['harm_to_yes_share'])} | {fmt(H['harm_to_no_share'])} |"
        )
    lines.append("")

    # NLP buckets (for mismatches)
    lines.append("## NLP difficulty buckets (mismatches only)")
    lines.append(f"- **Context length buckets (words)**: Short {short_words_br}, Medium {med_words_br}, Long {long_words_br}")
    lines.append(f"- **Numeric density buckets** (per 100 words): Low {low_num_br}, Medium {med_num_br}, High {high_num_br}\n")

    lines.append("### Context length (words) — mismatch counts")
    lines.append("| bucket | count |")
    lines.append("|:-------|------:|")
    lines.append(f"| Short {short_words_br} | {length_bucket_counts['Short']} |")
    lines.append(f"| Medium {med_words_br} | {length_bucket_counts['Medium']} |")
    lines.append(f"| Long {long_words_br} | {length_bucket_counts['Long']} |")
    lines.append("")

    lines.append("### Numeric density (per 100 words) — mismatch counts")
    lines.append("| bucket | count |")
    lines.append("|:-------|------:|")
    lines.append(f"| Low {low_num_br} | {numdens_bucket_counts['Low']} |")
    lines.append(f"| Medium {med_num_br} | {numdens_bucket_counts['Medium']} |")
    lines.append(f"| High {high_num_br} | {numdens_bucket_counts['High']} |")
    lines.append("")

    # Errors
    lines.append("## Files with non-evaluable answers or read/parse issues")
    if not eval_errors and not all_errors:
        lines.append("_None detected._")
    else:
        if eval_errors:
            lines.append("### Evaluable-answer errors (ambiguous/missing Yes/No)")
            for fp in sorted(set(eval_errors)):
                lines.append(f"- {fp}")
        if all_errors:
            lines.append("\n### Read/parse errors")
            for fp, reason in all_errors:
                lines.append(f"- {fp}  —  {reason}")
    lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Done. Report written to: {report_path}")

if __name__ == "__main__":
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    analyze(base)
