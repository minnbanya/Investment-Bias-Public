import json
import os

# Step 1: Load your data from a JSON file
with open("llm_samples.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Step 2: Create output directory if it doesn't exist
output_dir = "data"
os.makedirs(output_dir, exist_ok=True)

# Step 3: Write each item in the JSON array to its own file
for idx, item in enumerate(data, start=801):
    file_path = os.path.join(output_dir, f"{idx}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(item, f, indent=4, ensure_ascii=False)
    if idx == 400:
        break

print(f"✅ {len(data)} files written to '{output_dir}/' directory.")
