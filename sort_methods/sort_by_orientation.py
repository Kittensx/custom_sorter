import os
import shutil
from PIL import Image



def get_orientation_folder(width, height):
    if width == height:
        return "square"
    elif width > height:
        return "landscape"
    else:
        return "portrait"

def sort_by_orientation(folder_path, use_output_folder, output_folder):
    if not os.path.exists(folder_path):
        print(f"Folder does not exist: {folder_path}")
        return

    for file in os.listdir(folder_path):
        if file.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            file_path = os.path.join(folder_path, file)

            try:
                with Image.open(file_path) as img:
                    width, height = img.size

                target_folder = get_orientation_folder(width, height)
                destination_folder = os.path.join(output_folder, target_folder) if use_output_folder else os.path.join(folder_path, target_folder)
                
            except Exception as e:
                print(f"Error processing {file}: {e}")
