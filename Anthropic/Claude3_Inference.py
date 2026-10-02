import os
import json
import argparse
import anthropic

client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
)



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
            "loss_aversion",
            "recency"
        ]

    for folder in folders:
        loaded_jsons = load_json_files(folder, args.start, args.end)
        
        for key, data in loaded_jsons.items():
            # print(f"Content of {key}.json:\n", json.dumps(data, indent=4))
            # print(data["Context"])
            context = data["Context"]
            question = data["Question"]
            label = data["Answer"]

            
            # print(prompt)
            # ask gpt for perturb

            message = client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": f"{context} {question} Do not explain your answer. Just respond with: Yes / No / Cannot determine."}
                ]
            )
            # print(message.content)
            answer = message.content[0].text
            new_data = {
                "Context": context,
                "Question": question,
                "True Answer": label,
                "Answer": answer,
                "Perturbation": "gpt-4o-mini"

            }

            os.makedirs(folder, exist_ok=True)


            with open(f"{folder}/{key}.json", "w", encoding="utf-8") as f:
                json.dump(new_data, f, indent=4, ensure_ascii=False)


