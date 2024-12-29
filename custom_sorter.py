import os
import shutil
import yaml
from PIL import Image
from filelock import FileLock, Timeout
import psutil
import time
import atexit
from send2trash import send2trash
from scripts.cs_queue import QueueManager
from scripts.post_processing_manager import PostProcessingManager




class CustomSorter:
    def __init__(self, config_path):
        self.config = self.load_config(config_path)
        self.input_folders = self.config.get("input_folders", ["input"])
        self.output_folder = self.config.get("output_folder", "output")
        self.use_output_folder = self.config.get("use_output_folder", True)  # Default to True
        self.sort_method = self.config.get("sort_method", "resolution")  # Default to resolution
        # Handle resolution_folders: Use default if missing or empty
        self.resolution_folders = self.config.get("resolution_folders", None)     
        self.dynamic_thresholds = self.config.get("dynamic_thresholds", False) #default to false to allow for customization
        
        # Define default resolution folders as a class attribute
        self.default_resolution_folders = {
            "superlow": "0x0",
            "lores": "512x512",
            "medres": "640x960",
            "hires": "1080x1920",
            "superhigh": float("inf") #arbitrary high threshold
        }

        # Handle resolution_folders: Allow customization with fallback to defaults
        self.resolution_folders = self.config.get("resolution_folders", {})
        if not self.resolution_folders:
            print("Warning: 'resolution_folders' is missing or empty in the configuration. Using defaults.")
            self.resolution_folders = self.default_resolution_folders

        # Parse user-defined thresholds
        self.resolution_thresholds = {
            folder: self.parse_pixel_dimensions(dimensions)
            for folder, dimensions in self.resolution_folders.items()
        }
        
        # Set default paths if not provided or invalid
        self.input_folders = [folder if folder.strip() else "input" for folder in self.input_folders]
        if not self.output_folder.strip():
            self.output_folder = "output"
        
        # Ensure input folders exist
        for folder in self.input_folders:
            if not os.path.exists(folder):
                try:
                    os.makedirs(folder)
                    print(f"Created input folder: {folder}")
                except Exception as e:
                    print(f"Error creating input folder {folder}: {e}")
        
        # Ensure output folder exists if use_output_folder is True
        if self.use_output_folder and not os.path.exists(self.output_folder):
            try:
                os.makedirs(self.output_folder)
                print(f"Created output folder: {self.output_folder}")
            except Exception as e:
                print(f"Error creating output folder: {e}. Using fallback.")
                fallback_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
                try:
                    os.makedirs(fallback_path)
                    self.output_folder = fallback_path
                    print(f"Created fallback output folder: {self.output_folder}")
                except Exception as fallback_error:
                    print(f"Failed to create fallback output folder: {fallback_error}")
                    raise  

        self.log_file = "file_operations_log.yaml"
        self.lock_file = "file_operations_log.lock"
        self.queue_manager = QueueManager(lock_file=self.lock_file, log_file=self.log_file)        
        self.LOCK_TIMEOUT = 5  # Seconds
       
   
    @staticmethod
    def load_config(config_path):
        try:
            with open(config_path, "r") as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            print(f"Configuration file not found at {config_path}. Using defaults.")
            return {}

    @staticmethod
    def parse_pixel_dimensions(dimension_str):
        try:
            width, height = map(int, dimension_str.split('x'))
            return width * height
        except ValueError:
            raise ValueError(f"Invalid dimension format: {dimension_str}. Expected format: 'widthxheight'.")

    def load_log(self):
        """Load the YAML log file with locking."""
        try:
            with FileLock(self.lock_file, timeout=self.LOCK_TIMEOUT):
                if os.path.exists(self.log_file):
                    with open(self.log_file, "r") as f:
                        return yaml.safe_load(f) or {}
        except Timeout:
            print(f"Could not acquire lock on {self.lock_file}.")
        except PermissionError as e:
            print(f"PermissionError while accessing {self.lock_file}: {e}")
            self.get_process_locking_file(self.lock_file)
        except Exception as e:
            print(f"Unexpected error with {self.lock_file}: {e}")
        return {}

    def save_log(self, log_data):
        """Save the YAML log file with locking."""
        try:
            with FileLock(self.lock_file, timeout=self.LOCK_TIMEOUT):
                with open(self.log_file, "w") as f:
                    yaml.safe_dump(log_data, f)
        except Timeout:
            print(f"Could not acquire lock on {self.lock_file}.")
        except PermissionError as e:
            print(f"PermissionError while accessing {self.lock_file}: {e}")
            self.get_process_locking_file(self.lock_file)
        except Exception as e:
            print(f"Unexpected error with {self.lock_file}: {e}")


    def attempt_move_or_copy(self, src, dst, log_data):
        print(f"Adding {src} to the queue for processing...")
        self.queue_manager.add_to_queue(src, dst)    
                
    def monitor_and_cleanup(self, log_data):
        updated_log = {"copied_files": []}
        with FileLock(self.lock_file):
            for entry in log_data.get("copied_files", []):
                original = entry["original"]
                copy = entry["copy"]
                if os.path.exists(original):
                    try:
                        shutil.move(original, copy)
                        print(f"Moved locked file {original} to {copy}. Deleting copy.")
                        send2trash(copy)
                        entry["status"] = "completed"
                    except Exception as e:
                        print(f"Failed to move {original}: {e}")
                        updated_log["copied_files"].append(entry)
                else:
                    updated_log["copied_files"].append(entry)
            self.save_log(updated_log)

    def process_file(self, file_path, target_folder, log_data):
        # Ensure the target folder exists
        if not os.path.exists(target_folder):
            os.makedirs(target_folder, exist_ok=True)
            print(f"Created folder: {target_folder}")

        print(f"Processing file: {file_path} to folder: {target_folder}")
        dst = os.path.join(target_folder, os.path.basename(file_path))
        print(f"Adding to queue: Source: {file_path}, Destination: {dst}")  # Debug print
        self.queue_manager.add_to_queue(file_path, dst)
       # self.attempt_move_or_copy(file_path, dst, log_data)
        
    def get_process_locking_file(self, file_path):
        """Check which process is locking the specified file."""
        found = False
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                for open_file in proc.open_files():
                    if open_file.path == file_path:
                        print(f"File {file_path} is locked by process {proc.info['name']} (PID: {proc.info['pid']})")
                        found = True
                        return proc.info
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue
        if not found:
            print(f"No process is locking the file: {file_path}")
   
    def sort_images_and_texts(self):
        log_data = self.load_log()
        log_data.setdefault("copied_files", [])

        for input_folder in self.input_folders:
            print(f"Sorting files in folder: {input_folder}")
            
            # Recursively traverse input folders and subfolders
            for root, _, files in os.walk(input_folder):    
                print(f"Currently processing folder: {root}")  # Debug: show current folder being processed               
                print(f"Found files: {files}")  # Debug: show files in the current directory                          
              
                images = [f for f in files if f.endswith((".png", ".jpg", ".jpeg", ".webp"))]
                text_files = [f for f in files if f.endswith(".txt")]               
                

                for image_file in images:
                    try:
                        file_path = os.path.join(root, image_file)
                        with Image.open(file_path) as img:                       

                            width, height = img.size
                            total_pixels = width * height

                            # Determine target folder based on sort_method
                            if self.sort_method == "resolution":
                                target_folder = self.get_resolution_folder(total_pixels)
                            elif self.sort_method == "orientation":
                                target_folder = self.get_orientation_folder(width, height)                           
                            else:
                                raise ValueError(f"Unsupported sort method: {self.sort_method}")
                            
                            # Decide target folder based on use_output_folder
                            if self.use_output_folder:
                                relative_path = os.path.relpath(root, input_folder)
                                output_subfolder = os.path.join(self.output_folder, relative_path)
                                target_folder = os.path.join(output_subfolder, self.get_resolution_folder(total_pixels))
                            else:
                                target_folder = os.path.join(root, self.get_resolution_folder(total_pixels))   
                            
                            self.process_file(file_path, target_folder, log_data)

                            txt_file = os.path.splitext(image_file)[0] + ".txt"
                            if txt_file in text_files:
                                txt_path = os.path.join(root, txt_file)                           
                                self.process_file(txt_path, target_folder, log_data)  

                                
                    except Exception as e:
                        print(f"Error processing {image_file}: {e}")
        
        # Process all files in the queue
        self.queue_manager.process_queue()
        
        # Wait briefly to ensure all files are processed and locks are released
        time.sleep(2)
        
        try:
            # Run post-processing to clean up input folders
            post_processor = PostProcessingManager(self.input_folders, self.output_folder)
            post_processor.compare_and_clean()
        except PermissionError as e:
            print(f"PermissionError during post-processing: {e}")
            terminate_locking_process(file_path)
            time.sleep(2)  # Delay before retry
            try:
                post_processor.compare_and_clean()  # Retry after clearing locks
            except Exception as retry_error:
                print(f"Failed post-processing even after retry: {retry_error}")    
    
    def cleanup_lock_file(self):
        if os.path.exists(self.lock_file):
            try:
                send2trash(self.lock_file)
                print(f"Sent file to trash: {self.lock_file}")
            except Exception as e:
                print(f"Error cleaning up lock file: {e}")
    
    @classmethod
    def terminate_locking_process(file_path):
        """
        Identify and terminate the process locking a specific file.
        :param file_path: The file path to check for locks.
        """
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                for open_file in proc.open_files():
                    if open_file.path == file_path:
                        print(f"File {file_path} is locked by process {proc.info['name']} (PID: {proc.info['pid']}). Terminating process...")
                        proc.terminate()
                        proc.wait(timeout=5)  # Wait for the process to terminate
                        print(f"Terminated process {proc.info['name']} (PID: {proc.info['pid']}).")
                        return
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue
        print(f"No process found locking the file: {file_path}")
    
    def get_resolution_folder(self, total_pixels):
        """
        Determine the appropriate folder name based on total pixels.
        """
        for folder, max_pixels in self.resolution_thresholds.items():
            if total_pixels <= max_pixels:
                return folder  # Return folder name as a string

        # Handle cases for "superlow" or "superhigh"
        if self.dynamic_thresholds:
            sorted_thresholds = sorted(self.resolution_thresholds.items(), key=lambda x: x[1])
            lowest_folder, lowest_pixels = sorted_thresholds[0]
            highest_folder, highest_pixels = sorted_thresholds[-1]

            if total_pixels < lowest_pixels:
                return "superlow"
            elif total_pixels > highest_pixels:
                return "superhigh"

        return "other"  # Default fallback

    def get_orientation_folder(self, width, height):
        """
        Categorize images based on orientation:
        - "square" if width == height.
        - "portrait" if height > width.
        - "landscape" if width > height.
        """
        if width == height:
            return "square"
        elif width > height:
            return "landscape"
        else:
            return "portrait"

   

if __name__ == "__main__":
    '''
    Known features not working: orientation not working yet
    UNDO operation with a Command line interface not implemented yet
    '''
    #load config
    sorter = CustomSorter("custom_sorter_config.yaml")
    
    # Register the cleanup function for the lock file
    atexit.register(sorter.cleanup_lock_file)

    # Start sorting
    sorter.sort_images_and_texts()
