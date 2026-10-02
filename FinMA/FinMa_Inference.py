from huggingface_hub import login

login(token=os.getenv("HUGGINGFACE_TOKEN"))


# Load model directly
from transformers import AutoTokenizer, AutoModelForCausalLM
import re

tokenizer = AutoTokenizer.from_pretrained("TheFinAI/finma-7b-full", use_fast=False)
model = AutoModelForCausalLM.from_pretrained("TheFinAI/finma-7b-full")

import time
import os
import json
import argparse

def load_json_files(folder, start, end):
    json_data = {}
    
    for i in range(start, end + 1):
        filename = f"../dataset/{folder}/{i}.json"
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as file:
                    json_data[i] = json.load(file)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON in {filename}: {e}")
        else:
            print(f"File {filename} not found, skipping.")
    
    return json_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load JSON files within a specified range.")
    parser.add_argument("start", type=int, help="Starting integer for JSON filenames.")
    parser.add_argument("end", type=int, help="Ending integer for JSON filenames.")
    
    args = parser.parse_args()
    folders = [
            "neutral",
            "confirmation",
            "herding",
            "anchoring",
            "loss-aversion",
            "recency"
        ]

    for folder in folders:
        loaded_jsons = load_json_files(folder, args.start, args.end)
        
        for key, data in loaded_jsons.items():
            context = data["Context"]
            question = data["Question"]
            label = data["Answer"]
            category = data["Category"]
            
            # Final prompt combining the instruction, context, and question
            final_prompt = f"Instruction: You are given a short excerpt of text that provides financial or investment-related information. Based only on this information, answer the following question with either 'Yes' or 'No'. Do not add explanations, reasoning, or extra text. Your entire output must be exactly 'Yes' or 'No'.Context: [{context}] Question: [{question}] Response: ["
            
            # Tokenizing and generating the input as before
            inputs = tokenizer(final_prompt, return_tensors='pt')
            inputs = {key: value.to(model.device) for key, value in inputs.items()}
            
            # Perform inference
            # Perform inference by accessing the underlying model
            # Generating the output
            res = model.generate(
                **inputs, max_length=4096, do_sample=True,
                eos_token_id=tokenizer.eos_token_id,
                use_cache=True
            )
            
            output = tokenizer.decode(res[0], skip_special_tokens=True)
            # This extracts everything after 'Response: [' and removes trailing bracket if present
            match = re.search(r"Response:\s*\[(.*)", output, re.DOTALL)
            if match:
                answer = match.group(1).strip()
            else:
                answer = output.strip()

            new_data = {
                "Context": context,
                "Question": question,
                "True Answer": label,
                "Answer": answer,
                "Category": category,
            }

            os.makedirs(folder, exist_ok=True)


            with open(f"{folder}/{key}.json", "w", encoding="utf-8") as f:
                json.dump(new_data, f, indent=4, ensure_ascii=False)




