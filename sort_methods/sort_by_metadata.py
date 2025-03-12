import os
import re
import json
from sort_methods.history import load_history

def extract_metadata(text, key):
    """
    Extracts the correct metadata value.
    - For Hashes, extracts only the first valid {} entry.
    - For Booleans, converts True/False to key_True or key_False. #work in progress
    Extract metadata but first check if the file was moved using the history file.
    
    """
    history = load_history()
    # Get the correct file path if it's been moved
    #if text in history:
     #   new_path = history[text]["new_path"]
      #  print(f"Using new path for metadata extraction: {new_path}")
       # text = new_path
    # If metadata exists in history, use it instead of opening the file
    if text in history and "metadata" in history[text] and key in history[text]["metadata"]:
        return history[text]["metadata"][key]

    # If the metadata is missing, return "Unknown"
    return "Unknown"
    
    # Locate "Negative prompt:" and only search below it
    neg_prompt_index = text.lower().find("negative prompt:")
    if neg_prompt_index != -1:
        text = text[neg_prompt_index:]  # Only search after "Negative prompt:"

    # Handling Hashes
    if key.lower() == "hashes":
        pattern = r'Hashes:\s*({.*?})'  # Find first valid JSON-like structure
        match = re.search(pattern, text, re.MULTILINE)

        if match:
            try:
                hashes_dict = json.loads(match.group(1))  # Convert to dictionary
                first_key = next(iter(hashes_dict))  # Get the first key
                return hashes_dict[first_key].strip()  # Get the first value
            except json.JSONDecodeError:
                return "Unknown"

    # Handling Boolean values (ensure key is included in the return value)
    pattern_boolean = rf"^{key}:\s*(True|False)"  # Match 'Hypertile U-Net: True/False'
    match_boolean = re.search(pattern_boolean, text, re.MULTILINE)

    if match_boolean:
        return f"{key}_{match_boolean.group(1)}"  # Format: 'Hypertile U-Net_True'

    # Default metadata extraction for normal keys
    pattern = rf"(?<!hash\s)({key}:\s*([^,]+))"  # Match 'Model:' but ignore 'Model hash'
    match = re.search(pattern, text, re.IGNORECASE)  

    if match:
        return match.group(2).strip()  # Extract only the metadata value

    return "Unknown"

def sanitize_folder_name(folder_name):
    """
    Remove characters that are invalid in Windows folder names.
    """
    invalid_chars = r'<>:"/\|?*'  # Windows disallowed characters
    sanitized_name = re.sub(f"[{re.escape(invalid_chars)}]", "_", folder_name)
    return sanitized_name.strip("_")  # Remove trailing underscores

def sort_by_metadata(folder_path, metadata_key):
    """
    Sorts images and their corresponding text files based on metadata.
    """
    if not os.path.exists(folder_path):
        print(f"Folder does not exist: {folder_path}")
        return

    for file in os.listdir(folder_path):
        if file.endswith(".txt"):
            txt_path = os.path.join(folder_path, file)
            base_name = os.path.splitext(file)[0]
            image_extensions = [".png", ".jpg", ".jpeg", ".webp"]
            image_file = None

            for ext in image_extensions:
                potential_image = os.path.join(folder_path, base_name + ext)
                if os.path.exists(potential_image):
                    image_file = potential_image
                    break

            with open(txt_path, "r", encoding="utf-8") as f:
                text_data = f.read()
                metadata_value = extract_metadata(text_data, metadata_key)

            #print(f"Metadata extracted: '{metadata_value}' for {file}")  # Debug print

            if metadata_value == "Unknown":
                print(f"Warning: No valid metadata key '{metadata_key}' found in {file}. Skipping.")
                continue

            # Ensure the folder name is valid
            destination_folder = os.path.join(folder_path, sanitize_folder_name(metadata_value))          

    print(f"Sorting completed using metadata: {metadata_key}")
