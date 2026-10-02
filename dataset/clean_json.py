import os
import json
import argparse

def clean_json_file(input_path, output_path):
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Keep only the specified keys if they exist
        cleaned_data = {
            key: data.get(key) for key in ["Context", "Question", "Answer", "Source", "Category"]
        }
        
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, indent=4)
        
        print(f"Cleaned and saved: {output_path}")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {input_path}. Skipping.")
    except Exception as e:
        print(f"Error processing {input_path}: {e}. Skipping.")

def main(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    for filename in os.listdir(input_folder):
        if filename.endswith('.json'):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)
            clean_json_file(input_path, output_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean JSON files by keeping only specific keys.")
    parser.add_argument('--input_folder', required=True, help="Path to the input folder containing JSON files.")
    parser.add_argument('--output_folder', default='cleaned_output', help="Path to the output folder (default: 'cleaned_output').")
    
    args = parser.parse_args()
    main(args.input_folder, args.output_folder)