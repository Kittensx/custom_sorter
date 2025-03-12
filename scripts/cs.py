from sort_methods.sort_by_resolution import sort_by_resolution
from sort_methods.sort_by_metadata import sort_by_metadata
from sort_methods.sort_by_orientation import sort_by_orientation
from scripts.cs_queue import QueueManager
from scripts.post_processing_manager import PostProcessingManager
from sort_methods.multi_sort import ImageSorter
from sort_methods.metadataextractor import MetadataExtractor
import os
import shutil
import yaml
import re
from PIL import Image
from filelock import FileLock, Timeout
import psutil
import time
import atexit
from send2trash import send2trash
from tqdm import tqdm
import concurrent.futures
import logging


class CustomSorter:
    def __init__(self, config_path="custom_sorter_config.yaml"):
        # ✅ Configure logging for execution times
        logging.basicConfig(filename="execution_time.log", level=logging.INFO, format="%(asctime)s - %(message)s")

        self.config = self.load_config(config_path)
        self.input_folders = self.config.get("input_folders", ["input"])
        self.output_folder = self.config.get("output_folder", "output")
        self.use_output_folder = self.config.get("use_output_folder", True)  # Default to True
        self.sort_method = self.config.get("sort_method", "resolution").lower()  # Default to resolution
        # Handle resolution_folders: Use default if missing or empty
        self.resolution_folders = self.config.get("resolution_folders", None)     
        self.dynamic_thresholds = self.config.get("dynamic_thresholds", False) #default to false to allow for customization        
        self.imagesorter = ImageSorter(self.input_folders[0], self.output_folder) 
        self.metadata_extractor = MetadataExtractor()  
        self.metadata_key = self.config.get("metadata_key", "model").lower()
        # ✅ Ensure `sort_methods` is always a list of lowercase values
        self.sort_methods = [m.lower() for m in self.config.get("sort_methods", ["metadata"])]
        # ✅ Ensure `metadata_keys` is always a list of lowercase values
        self.metadata_keys = [k.lower() for k in self.config.get("metadata_keys", ["model"])]
       
        
        
        
        self.folder_path = self.config.get("folder_path", "D:/images")  # Default folder path
        self.sort_by = self.config.get("sort_by", "resolution")  # Default sorting method
        
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
                    #print(f"Created input folder: {folder}")
                except Exception as e:
                    print(f"Error creating input folder {folder}: {e}")
        
        # Ensure output folder exists if use_output_folder is True
        if self.use_output_folder and not os.path.exists(self.output_folder):
            try:
                os.makedirs(self.output_folder)
                print(f"Created output folder: {self.output_folder}")
            except Exception as e:
                #print(f"Error creating output folder: {e}. Using fallback.")
                fallback_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
                try:
                    os.makedirs(fallback_path)
                    self.output_folder = fallback_path
                    #print(f"Created fallback output folder: {self.output_folder}")
                except Exception as fallback_error:
                    #print(f"Failed to create fallback output folder: {fallback_error}")
                    raise  

        self.log_file = "file_operations_log.yaml"
        self.lock_file = "file_operations_log.lock"
        self.queue_manager = QueueManager(lock_file=self.lock_file, log_file=self.log_file)        
        self.LOCK_TIMEOUT = 5  # Seconds
        
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
   
  
   

    def sort_images_and_texts(self):
        """Sort images and texts while keeping metadata in memory, with a progress bar."""
        start_time=time.time()
        metadata_dict = {}  # Store extracted metadata in memory       

        # ✅ Count total image files for progress bar
        total_files = sum(
            len([f for f in files if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))])
            for root, _, files in os.walk(self.input_folders[0])
        )
        sort_start_time = time.time()  # ✅ Start time tracking
        with tqdm(total=total_files, desc="Processing Files", unit="file") as pbar:
            for input_folder in self.input_folders:
                for root, _, files in os.walk(input_folder):          
                    with concurrent.futures.ProcessPoolExecutor() as executor:
                        futures_sorting = []
                        futures_analysis = []

                        for file in files:
                            if not file.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                                continue  # ✅ Skip non-image files
                            
                            file_path = os.path.join(root, file)
                            metadata = self.metadata_extractor.extract_metadata(file_path)

                            if metadata:
                                metadata_dict[file_path] = metadata  # ✅ Store metadata with full path

                            # ✅ Submit sorting first
                            future_sort = executor.submit(self.imagesorter.process_images, self.config, metadata_dict)
                            futures_sorting.append(future_sort)

                        # ✅ Wait for sorting to finish before analyzing
                        concurrent.futures.wait(futures_sorting)
                        
                        # ✅ End timing sorting
                        sort_end_time = time.time()
                        sort_duration = sort_end_time - sort_start_time
                        print(f"⏳ Sorting completed in {sort_duration:.2f} seconds.")
                        logging.info(f"Sorting completed in {sort_duration:.2f} seconds.")
                        

                        # ✅ Now set sorted folder dynamically
                        sorted_folder = self.imagesorter.get_sorted_folder()
                       
                        
                         # ✅ Start timing analysis
                        analysis_start_time = time.time()

                        # ✅ Submit analysis after sorting completes
                        for file in files:
                            file_path = os.path.join(root, file)
                           

                        # ✅ Wait for analysis to complete
                        concurrent.futures.wait(futures_analysis)
                        
                        # ✅ End timing analysis
                        analysis_end_time = time.time()
                        analysis_duration = analysis_end_time - analysis_start_time
                        print(f"⏳ Analysis completed in {analysis_duration:.2f} seconds.")
                        logging.info(f"Analysis completed in {analysis_duration:.2f} seconds.")

                        # ✅ Log total time taken
                        total_time = sort_duration + analysis_duration
                        print(f"✅ Total processing time: {total_time:.2f} seconds.")
                        logging.info(f"Total processing time: {total_time:.2f} seconds.")
                        

                        pbar.update(len(files))

            print("✅ Sorting & Analysis completed in parallel!")



            end_time = time.time()  # ✅ End time tracking
            elapsed_time = end_time - start_time  # ✅ Calculate total time taken                        
            print("\nAssigning to Queue")
            self.queue_manager.process_queue()
            #print("Running Queue Manager")
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
            print(f"\n✅ Processed {total_files} files in {elapsed_time:.2f} seconds.\n")
           
           

            

    @classmethod
    def terminate_locking_process(self, file_path):
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
        """Parses pixel dimensions in 'widthxheight' format and returns the total pixel count."""
        if isinstance(dimension_str, float):  
            return dimension_str  # ✅ Return float as-is (for `inf` case)

        try:
            width, height = map(int, dimension_str.split('x'))  # ✅ Only split if it's a string
            return width * height
        except ValueError:
            raise ValueError(f"Invalid dimension format: {dimension_str}. Expected format: 'widthxheight'.")

    
if __name__ == "__main__":
    # Initialize the sorter with the test configuration
    sorter = CustomSorter("custom_sorter_config.yaml")

    # Run the sorting process
    sorter.sort_images_and_texts()
    
