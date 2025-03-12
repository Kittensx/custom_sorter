import os
import shutil
from PIL import Image

def get_resolution_folder(total_pixels, resolution_thresholds):
    """Determine the appropriate resolution folder."""
    for folder, dimensions in resolution_thresholds.items():
        try:
            width, height = map(int, dimensions.split('x'))  # Convert 'widthxheight' to total pixels
            max_pixels = width * height
        except ValueError:
            print(f"Warning: Invalid resolution threshold '{dimensions}' in config.")
            continue

        if total_pixels <= max_pixels:
            return folder
    return "other"

def sort_by_resolution(folder_path, resolution_thresholds, use_output_folder, output_folder):
    if not os.path.exists(folder_path):
        print(f"Folder does not exist: {folder_path}")
        return

    for file in os.listdir(folder_path):
        if file.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            file_path = os.path.join(folder_path, file)

            try:
                with Image.open(file_path) as img:
                    width, height = img.size
                    total_pixels = width * height

                for folder, max_pixels in resolution_thresholds.items():
                    if total_pixels <= max_pixels:
                        target_folder = os.path.join(output_folder, folder) if use_output_folder else os.path.join(folder_path, folder)                    
                        break
            except Exception as e:
                print(f"Error processing {file}: {e}")

