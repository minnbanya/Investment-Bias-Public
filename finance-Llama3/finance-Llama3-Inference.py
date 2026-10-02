from huggingface_hub import login
import os

login(token=os.getenv("HUGGINGFACE_TOKEN"))

from transformers import AutoTokenizer, AutoModelForCausalLM
from tqdm import tqdm
import re
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
            # "neutral",
            # "confirmation",
            # "herding",
            # "anchoring",
            # "loss-aversion",
            "recency"
        ]

    model = AutoModelForCausalLM.from_pretrained("instruction-pretrain/finance-Llama3-8B")
    tokenizer = AutoTokenizer.from_pretrained("instruction-pretrain/finance-Llama3-8B")
    
    # after you load the tokenizer/model
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token  # Llama-style models have no PAD; use EOS
    model.config.pad_token_id = tokenizer.pad_token_id


    for folder in folders:
        loaded_jsons = load_json_files(folder, args.start, args.end)
        
        for key, data in tqdm(loaded_jsons.items(), desc=f"Processing {folder}"):
            context = data["Context"]
            question = data["Question"]
            label = data["Answer"]
            category = data["Category"]
            
            # Final prompt combining the instruction, context, and question
            user_input = f"Instruction: You are given a short excerpt of text that provides financial or investment-related information. Based only on this information, answer the following question with either 'Yes' or 'No'. Do not add explanations, reasoning, or extra text. Your entire output must be exactly 'Yes' or 'No'.Context: [{context}] Question: [{question}] "
            
            # Tokenizing and generating the input as before
            enc = tokenizer(
                user_input,
                return_tensors="pt",
                add_special_tokens=True,
                padding=True,        # ensures attention_mask is created
                truncation=False     # keep your original behavior (set True if you want a max length)
            )
            input_ids = enc.input_ids.to(model.device)
            attention_mask = enc.attention_mask.to(model.device)
            
            outputs = model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,   # <— this removes the warning & stabilizes decoding
                max_new_tokens=400,
                pad_token_id=tokenizer.pad_token_id
            )[0]

            answer_start = int(input_ids.shape[-1])
            pred = tokenizer.decode(outputs[answer_start:], skip_special_tokens=True)
            # This extracts everything after 'Response: [' and removes trailing bracket if present
            PUNCT_TRIM = " \t\r\n[](){}.,;:!?\"'“”‘’"
            s2 = pred.strip(PUNCT_TRIM)
            s2l = s2.lower()
            if s2l.startswith("yes"): answer = "Yes"
            elif s2l.startswith("no"):  answer = "No"
            else: answer = s2l

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




