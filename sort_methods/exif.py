import os
#from sort_methods.find_exiftool import find_exiftool 
from sort_methods.find_exiftool import find_exiftool
import json
import subprocess

def extract_exiftool_metadata(image_path):
    """Runs ExifTool on an image and extracts metadata dynamically."""
    exiftool_path = find_exiftool()
    if not exiftool_path:
        return {"Error": "ExifTool not found. Please install and add it to PATH."}
    
    try:
        result = subprocess.run(
            [exiftool_path, "-json", image_path], 
            capture_output=True, text=True
        )
        metadata = json.loads(result.stdout)
        return metadata[0] if metadata else {}
    
    except Exception as e:
        return {"Error": str(e)}

def save_metadata(image_path):
    """Extracts metadata and saves it to a text file next to the image."""
    metadata = extract_exiftool_metadata(image_path)
    output_path = os.path.splitext(image_path)[0] + "_metadata.txt"
    
    with open(output_path, "w", encoding="utf-8") as file:
        for key, value in metadata.items():
            file.write(f"{key}: {value}\n")
    
    print(f"✅ Metadata extracted and saved to: {output_path}")
    return output_path



       
        



