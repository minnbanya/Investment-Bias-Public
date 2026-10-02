# pack_hf_dataset.py
import os, json, gzip

BIAS_FOLDERS = ["neutral","anchoring","herding","recency","loss-aversion","confirmation"]

def norm_key(k: str) -> str:
    # Simple key normalizer to snake_case-ish
    return k.strip().lower().replace(" ", "_")

def write_jsonl_gz(path, rows):
    with gzip.open(path, "wt", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def load_folder(folder):
    rows = []
    for fname in sorted(os.listdir(folder)):
        if not fname.endswith(".json"): 
            continue
        sid = os.path.splitext(fname)[0]
        with open(os.path.join(folder, fname), encoding="utf-8") as fh:
            d = json.load(fh)
        # normalize keys
        dd = {norm_key(k): v for k, v in d.items()}
        context = dd.get("Context") or dd.get("Context".lower()) or d.get("Context","")
        question = dd.get("Question","") or dd.get("Question".lower()) or d.get("Question","")
        answer = dd.get("Answer","") or dd.get("Answer".lower()) or d.get("Answer","")
        source = dd.get("Source","") or dd.get("Source".lower()) or d.get("Source","")
        category = dd.get("Category","") or dd.get("Category".lower()) or d.get("Category","")

        rows.append({
            "id": f"{folder}_{sid}",
            "parent_id": sid if folder != "neutral" else sid,  # same id space
            "bias": "none" if folder == "neutral" else folder,
            "Context": context,
            "Question": question,
            "Answer": answer,
            "Source": source,
            "Category": category,
        })
    return rows

if __name__ == "__main__":
    all_rows = []
    for folder in BIAS_FOLDERS:
        rows = load_folder(folder)
        out_file = f"{folder}.jsonl.gz"
        write_jsonl_gz(out_file, rows)
        print(f"Wrote {out_file} with {len(rows)} rows")
        all_rows.extend(rows)

    # Optional unified file
    write_jsonl_gz("all.jsonl.gz", all_rows)
    print(f"Wrote all.jsonl.gz with {len(all_rows)} rows")
