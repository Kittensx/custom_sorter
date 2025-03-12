import os
import yaml
import tempfile

def fix_yaml_paths(config_path):
    """
    Reads the YAML config, detects path-related fields, and converts all Windows paths
    from `C:\path\to\folder` to `C:/path/to/folder`. Saves the corrected config to a temp file.
    """

    # 🔍 Load the YAML file
    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    # 🔥 List of known path-related keys
    path_keys = [
        "folder_to_scan", "folders_to_scan",
        "static_temp", "other_files_folder",
        "index_file_path", "processed_files_log",
        "skipped_files_log", "exiftool_path", "gallery_folder"
    ]

    def convert_path(path):
        """Normalize and convert to Unix format (forward slashes)."""
        normalized = os.path.normpath(path)  # Normalize first (handles `..`, double slashes, etc.)
        return normalized.replace("\\", "/")  # Convert Windows backslashes to Unix forward slashes

    # 🔄 Normalize and convert paths
    for key in path_keys:
        if key in config:
            if isinstance(config[key], str):  # Single path
                config[key] = convert_path(config[key])
            elif isinstance(config[key], list):  # List of paths
                config[key] = [convert_path(path) for path in config[key]]

    # 📝 Write corrected config to a temp file
    temp_config = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml", mode="w", encoding="utf-8")
    yaml.safe_dump(config, temp_config, default_flow_style=False)
    temp_config.close()  # Close the file so it can be read later

    print(f"✅ Fixed config saved to: {temp_config.name}")
    return temp_config.name  # Return path to fixed YAML file
