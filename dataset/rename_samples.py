import os
import random

# Path to the folder containing the JSON files
folder_path = './neutral'

# Get a list of all the JSON files in the folder
json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]

# Shuffle the list of files
random.shuffle(json_files)

# Rename files sequentially
for i, old_name in enumerate(json_files, start=1):
    old_file_path = os.path.join(folder_path, old_name)
    new_name = f"{i}.json"
    new_file_path = os.path.join(folder_path, new_name)
    
    # Rename the file
    os.rename(old_file_path, new_file_path)

# Confirmation
f"Renaming completed from 401 to 700, files shuffled randomly."
