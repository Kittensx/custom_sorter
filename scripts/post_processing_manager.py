import os
import time
from send2trash import send2trash

class PostProcessingManager:
    def __init__(self, input_folders, output_folder):
        """
        Initialize the post-processing manager with input and output folder paths.
        :param input_folders: List of input folder paths
        :param output_folder: Path to the output folder
        """
        self.input_folders = input_folders
        self.output_folder = output_folder

    def compare_and_clean(self):
        """
        Compare files in output folders with input folders and delete duplicates from input folders.
        """
        # Get a list of all files in the output folder
        output_files = self._get_all_files(self.output_folder)

        for input_folder in self.input_folders:
            # Get all files in the current input folder
            input_files = self._get_all_files(input_folder)

            for input_file in input_files:
                # Compare file names only (ignoring directory structure)
                if os.path.basename(input_file) in output_files:
                    print(f"File {input_file} exists in output. Deleting from input...")
                    try:                        
                        delete_file_with_retry(input_file)  
                    except Exception as e:
                        print(f"Error deleting file {input_file}: {e}")
        self.cleanup_empty_folders()
        
    def cleanup_empty_folders(self):
        """
        Recursively delete empty folders from the input directories.
        """
        for input_folder in self.input_folders:
            print(f"Checking for empty folders in: {input_folder}")  # Debugging log
            for root, dirs, files in os.walk(input_folder, topdown=False):  # Bottom-up to remove empty subdirectories
                for directory in dirs:
                    dir_path = os.path.join(root, directory)
                    if not os.listdir(dir_path):  # Check if directory is empty
                        try:
                            os.rmdir(dir_path)
                            print(f"Removed empty folder: {dir_path}")
                        except Exception as e:
                            print(f"Error removing folder {dir_path}: {e}")

    def _get_all_files(self, folder_path):
        """
        Recursively retrieve all files in the given folder.
        :param folder_path: Path to the folder
        :return: Set of file names in the folder (including relative paths)
        """
        file_set = set()
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_set.add(os.path.join(root, file))
        return file_set
        
    @classmethod
    def delete_file_with_retry(file_path, retries=3, delay=2):
        """
        Attempt to delete a file with retries if it is locked or temporarily unavailable.
        :param file_path: Path to the file to delete
        :param retries: Number of retry attempts
        :param delay: Delay in seconds between retries
        """
        for attempt in range(retries):
            try:
                send2trash(file_path)
                print(f"Sent to trash: {file_path}")
                return
            except PermissionError as e:
                print(f"PermissionError: {e}. Retrying in {delay} seconds (Attempt {attempt + 1}/{retries})...")
                time.sleep(delay)
            except FileNotFoundError:
                print(f"File not found: {file_path}. Skipping deletion.")
                return
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}. Retrying...")
                time.sleep(delay)
        print(f"Failed to delete {file_path} after {retries} retries.")
