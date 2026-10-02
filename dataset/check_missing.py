import os
import json
import argparse

def check_json_file(input_path, required_fields):
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        missing = [field for field in required_fields if field not in data or data[field] == ""]
        
        if missing:
            print(f"File: {input_path} - Missing fields: {', '.join(missing)}")
        # else:
            # print(f"File: {input_path} - All fields present.")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {input_path}. Skipping.")
    except Exception as e:
        print(f"Error processing {input_path}: {e}. Skipping.")

def main(input_folder):
    required_fields = ["Context", "Question", "Answer", "Source", "Category"]
    
    for filename in os.listdir(input_folder):
        if filename.endswith('.json'):
            input_path = os.path.join(input_folder, filename)
            check_json_file(input_path, required_fields)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check JSON files for missing required fields.")
    parser.add_argument('--input_folder', default='neutral', required=True, help="Path to the input folder containing JSON files.")
    
    args = parser.parse_args()
    main(args.input_folder)