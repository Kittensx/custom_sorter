import os
import shutil



def move_file(file_path, target_folder):
    """
    Move a single file (image or text) to the target folder.

    :param file_path: Full path of the file
    :param target_folder: Destination folder
    """
    if not os.path.exists(target_folder):
        os.makedirs(target_folder, exist_ok=True)

    file_name = os.path.basename(file_path)
    destination = os.path.join(target_folder, file_name)
    #print(f"Moving {file_path} to {destination}")
    shutil.move(file_path, destination)



