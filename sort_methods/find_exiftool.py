import shutil
import subprocess
import logging

# Check if ExifTool is available
def find_exiftool():
    exiftool_path = shutil.which("exiftool")
    if exiftool_path:
        logging.info(f"ExifTool found at: {exiftool_path}")
        return exiftool_path
    else:
        logging.warning("ExifTool is not installed or not in PATH.")
        return None

# Get ExifTool path
exiftool_path = find_exiftool()
