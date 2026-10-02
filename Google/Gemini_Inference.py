import os
import json
import argparse
import time
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def load_json_files(folder, start, end):
    """Load JSON files from a specified folder range."""
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

def create_batch_data(loaded_jsons):
    """Prepare the data for batch processing in the required format."""
    batch_data = []
    for key, data in loaded_jsons.items():
        context = data["Context"]
        question = data["Question"]
        label = data["Answer"]
        category = data["Category"]
        
        # Format the prompt consistently across all models
        prompt = f"Instruction: You are given a short excerpt of text that provides financial or investment-related information. Based only on this information, answer the following question with either 'Yes' or 'No'. Do not add explanations, reasoning, or extra text. Your entire output must be exactly 'Yes' or 'No'. Context: [{context}] Question: [{question}] Response: ["

        batch_data.append({
            "context": context,
            "question": question,
            "label": label,
            "category": category,
            "prompt": prompt,
            "key": key  # Keep track of original key for file naming
        })
    
    return batch_data

def submit_batch(batch_data):
    """Submit the batch job with inline requests."""
    inline_requests = [
        {
            'contents': [{
                'parts': [{'text': data["prompt"]}],
                'role': 'user'
            }]
        }
        for data in batch_data
    ]

    # Create the batch job and return the job name
    inline_batch_job = client.batches.create(
        model="models/gemini-2.5-flash",  # Use the appropriate model version
        src=inline_requests,
        config={
            'display_name': "batch-job-financial-questions"
        },
    )

    print(f"Created batch job: {inline_batch_job.name}")
    return inline_batch_job.name

def wait_for_batch_completion(job_names, batch_datas, folders):
    """Poll the batch job status until all finish."""
    completed_states = {'JOB_STATE_SUCCEEDED', 'JOB_STATE_FAILED', 'JOB_STATE_CANCELLED', 'JOB_STATE_EXPIRED'}
    succeeded_state = {'JOB_STATE_SUCCEEDED'}
    
    # Create a dictionary to store the job states for each job
    job_status = {job_name: None for job_name in job_names}

    time_taken = 0
    # Poll the status of each job in the list
    while any(status is None for status in job_status.values()):
        for i, job_name in enumerate(job_names):
            if job_status[job_name] is None:
                # Fetch the current status of the batch job
                batch_job = client.batches.get(name=job_name)
                if batch_job.state.name in completed_states:
                    job_status[job_name] = batch_job.state.name
                    print(f"Job {job_name} finished with state: {batch_job.state.name}")
                    if batch_job.state.name in succeeded_state:
                        save_results(batch_job, folders[i], batch_datas[i])
                else:
                    print(f"Job {job_name} still in {batch_job.state.name}. Waiting {int(time_taken/3600)} h, {int(time_taken/60)} min, {time_taken%60} s...")
        time_taken += 30
        time.sleep(30)  # Wait for 30 seconds before the next poll

    # All jobs are finished
    return job_status

def save_results(batch_job, folder, batch_data):
    """Save the results once the batch job is completed."""
    if batch_job.state.name == 'JOB_STATE_SUCCEEDED':
        # Process and save the results for each request in the batch
        for i, inline_response in enumerate(batch_job.dest.inlined_responses):
            print(f"Processing response {i + 1}")

            answer = inline_response.response.text if inline_response.response else "Error"
            data = batch_data[i]

            # Save the response along with the original data using the original filename
            new_data = {
                "Context": data["context"],
                "Question": data["question"],
                "True Answer": data["label"],
                "Answer": answer,
                "Category": data["category"],
                "Model": "gemini-2.5-flash"
            }

            os.makedirs(folder, exist_ok=True)
            file_path = f"{folder}/{data['key']}.json"  # Use original file name (integer key)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(new_data, f, indent=4, ensure_ascii=False)
    else:
        print(f"Job did not succeed. Final state: {batch_job.state.name}")
        if batch_job.error:
            print(f"Error: {batch_job.error}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load JSON files within a specified range.")
    parser.add_argument("start", type=int, help="Starting integer for JSON filenames.")
    parser.add_argument("end", type=int, help="Ending integer for JSON filenames.")
    
    args = parser.parse_args()
    folders = [
        # "neutral", "confirmation", "herding", "anchoring", "loss-aversion", "recency"
        "anchoring", "loss-aversion", "recency"
    ]

    batch_datas = []
    for folder in folders:
        loaded_jsons = load_json_files(folder, args.start, args.end)
        batch_data = create_batch_data(loaded_jsons)
        batch_datas.append(batch_data)
    # Store job names and submit them concurrently
    job_names = []
    for i in range(len(folders)):
        job_name = submit_batch(batch_datas[i])
        job_names.append(job_name)

    # Wait for all jobs to complete in one loop
    job_status = wait_for_batch_completion(job_names, batch_datas, folders)


