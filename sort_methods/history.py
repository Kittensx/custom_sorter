import os
import yaml

HISTORY_FILE = "file_history.yaml"

def log_file_move(original_path, new_path, metadata=None):
    """
    Log the original and new file paths along with metadata to a history file.

    :param original_path: The file's original location.
    :param new_path: The new location after sorting.
    :param metadata: Extracted metadata, if applicable.
    """
    history = load_history()
    
    history_entry = {
        "original_path": original_path,
        "new_path": new_path,
        "metadata": metadata if metadata else {},
    }

    # Store history using filename as key
    file_name = os.path.basename(original_path)
    history[file_name] = history_entry

    # Save to YAML file
    with open(HISTORY_FILE, "w") as f:
        yaml.safe_dump(history, f)

def load_history():
    """
    Load the history file.
    """
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return yaml.safe_load(f) or {}
    return {}
