import os
import json
import glob
import re
import logging
from sort_methods.metadataextractor import MetadataExtractor
from sort_methods.sort_by_metadata import sort_by_metadata
from sort_methods.sort_by_orientation import get_orientation_folder
from sort_methods.sort_by_resolution import get_resolution_folder
from sort_methods.file_mover import move_file

class ImageSorter:
    def __init__(self, input_folder, output_folder):
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.metadata_extractor = MetadataExtractor(metadata_folder=os.path.join(output_folder, "metadata"))
        self.metadata_dict = {}  # ✅ Store extracted metadata in the class
        self.last_sorted_folder = None # ✅ Track last used folder
        # ✅ Configure logging
        logging.basicConfig(filename="file_movement.log", level=logging.INFO, format="%(asctime)s - %(message)s")


    def process_images(self, config, metadata_dict):
        """Process images using metadata stored in memory."""
        
        self.metadata_dict = metadata_dict.copy()  # ✅ Store a copy to avoid modifying during iteration

        for image_name, metadata_content in list(metadata_dict.items()):  # ✅ Iterate over a copy
            image_path = os.path.join(self.input_folder, image_name)  # ✅ Ensure full path
            #print(f"Processing {image_path} with metadata...")

            try:
                # ✅ Store metadata for this image safely
                self.metadata_dict[image_path] = metadata_content
                #print(f"✅ Loaded metadata successfully for {image_path}")
            
            except Exception as e:
                print(f"❌ Error processing metadata for {image_path}: {e}")
                continue  # Skip this file if metadata loading fails

            # ✅ Process the image based on extracted metadata
            self.multi_sort(image_path, config, self.output_folder)

    def get_metadata(self, image_path):
        """Retrieve metadata for a specific image."""
        return self.metadata_dict.get(image_path, {})

    def multi_sort(self, image_path, config, output_folder):
        """
        Sort images using stored metadata.
        """
        if not os.path.exists(image_path):
            #print(f"⚠️ File does not exist (path issue?): {image_path}")
            return

        # ✅ Retrieve metadata for this image
        metadata = self.get_metadata(image_path)

        if not metadata:
            #print(f"⚠️ No metadata available for {image_path}, skipping sorting.")
            return

        # ✅ Ensure we're accessing the correct metadata values
        metadata_values = metadata.get("metadata", {})  # Extract nested metadata dictionary

        #print(f"🔍 Sorting {image_path} using metadata: {metadata_values.keys()}")

        # ✅ Retrieve sorting configuration
        sort_methods = config.get("sort_methods", [])
        metadata_keys = config.get("metadata_keys", [])
        resolution_thresholds = config.get("resolution_folders", {})
        use_output_folder = config.get("use_output_folder", False)

        sorting_criteria = []  # ✅ Will hold folder names

        # ✅ Apply sorting methods in the specified order
        for method in sort_methods:
            if method == "metadata":
                for key in metadata_keys:
                    if key in metadata_values:  # ✅ Ensure we're extracting from the correct dictionary
                        sanitized_value = self.sanitize_folder_name(str(metadata_values[key]))
                        sorting_criteria.append(sanitized_value)

            elif method == "orientation":
                width, height = self.get_image_dimensions(image_path)
                sorting_criteria.append(get_orientation_folder(width, height))

            elif method == "resolution":
                width, height = self.get_image_dimensions(image_path)
                resolution_folder = get_resolution_folder(width * height, resolution_thresholds)
                sorting_criteria.append(resolution_folder)

        # ✅ Determine the correct final folder path
        if use_output_folder:
            sorted_folder = os.path.join(output_folder, *sorting_criteria)
        else:
            sorted_folder = os.path.join(os.path.dirname(image_path), *sorting_criteria)  # ✅ Keep files in-place

        os.makedirs(sorted_folder, exist_ok=True)

        # ✅ Track last sorted folder for logging
        self.last_sorted_folder = sorted_folder
        
        # ✅ Move all associated files (image, JSON, text)
        base_name, _ = os.path.splitext(image_path)
        associated_files = glob.glob(f"{base_name}.*")  # ✅ Match all files with the same base name

        for file_path in associated_files:
            move_file(file_path, sorted_folder)  # ✅ Move all associated files
            #print(f"✅ Sorted {image_path} → {sorted_folder}")
            logging.info(f"Moved: {file_path} ➝ {sorted_folder}")  # ✅ Write to log file
            
    def get_sorted_folder(self):
        """Return the last used sorted folder."""
        return self.last_sorted_folder if self.last_sorted_folder else None
        
    def sanitize_folder_name(self, folder_name):
        """Remove characters that are invalid in Windows folder names."""
        invalid_chars = r'<>:"/\|?*'  # Windows disallowed characters
        sanitized_name = re.sub(f"[{re.escape(invalid_chars)}]", "_", folder_name)
        return sanitized_name.strip("_")  # Remove trailing underscores

    def get_image_dimensions(self, image_path):
        """Retrieve width and height of the image."""
        from PIL import Image
        try:
            with Image.open(image_path) as img:
                return img.size  # (width, height)
        except Exception as e:
            print(f"Error getting image dimensions for {image_path}: {e}")
            return (0, 0)
