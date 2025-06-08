# Custom Sorter Program
# Last Updated 
# Changelog
## [Latest Version]- 2025-6-7
# Install / Update
If installing into the same folder, download the changed files. Run update_venv.bat inside the same folder. It will activate the venv and update your venv with the new requirements (we added wmi which is a program used with windows and checking what kind of harddrive you're using. This is a program that is core to how file_mover.py works). 

If installing new, see the install instructions below.
### **🚀 New Features**
# ✅ New Config Options (2025-06-07)

---

## 🟩 `save_metadata_json: false`

**Purpose:**  
Controls whether metadata files (in `.yaml`) are saved for each image during sorting. Ignore the name of the variable and just go with it :-)

**How to use:**
- `true` → Creates a metadata file for each image, saved alongside or in a `metadata/` folder.
- `false` → No extra files created.

---

## 🟩 `file_move_threads: "auto"`

**Purpose:**  
Optimizes how quickly files are moved during sorting using multithreading.

**How it works:**
- `"auto"` → Detects drive type:
  - SSD ➝ uses 8 threads
  - HDD ➝ uses 3 threads
- You can also manually set it:

```yaml
file_move_threads: 6
```
A safety check has been added to ensure you don't fail because threads are negative, 0, or more than your system can handle. If you don't need to control threading, I'd recommend to leave it on auto. Power Users can configure it as they like.

---

## 🟩 `include_subfolders: true`

**Purpose:**  
Controls whether the program processes files in subfolders of your `input_folder`.

### When set to `true`:
- The program **recursively looks inside all subfolders**.
- It **only processes folders that do not have a `.sorted.flag`** file.
- Useful when you want to continually drop new folders into your input folder and let the sorter handle them all.

### When set to `false`:
- Only the **top-level folder** is scanned.
- Subfolders are ignored completely.
- Best used when you're manually managing subfolders or only want to sort "unsorted" new files you just dropped in.

---

## 🏷️ How the `.sorted.flag` System Works

### What it does:
- After sorting files into a folder (e.g. `portrait/`), the system writes a `.sorted.flag` file inside that folder.
- This flag acts as a marker: “🛑 Do not sort anything here again.”

### How it’s used:
- During future runs, if `include_subfolders: true`, the sorter checks for `.sorted.flag` in each subfolder.
- If the flag **exists**, that folder is **skipped entirely** (no metadata read required).
- If the flag **does not exist**, the folder and its images **will be sorted**.

### When to delete `.sorted.flag`:
- If you want to reprocess/re-sort a folder for any reason, **just delete the `.sorted.flag` file** inside it.
- Next time the sorter runs, that folder will be treated as new.




# Updated 3/12/2025
# Changelog

# Requires EXIFTOOL for metadata scanning: https://exiftool.org/

## [Version] - 2025-03-12
### **🚀 New Features**
- **Enhanced Sorting Capabilities**
  - Added support for **multiple sorting methods**, including:
    - **Metadata-based sorting** (sorts based on extracted metadata fields, such as model name, sampler, etc.)
    - **Resolution-based sorting** (categorizes images based on resolution thresholds)
    - **Orientation-based sorting** (groups images based on portrait/landscape orientation)
  - Configurable **sort order**: Users can specify sorting priorities in `config.yaml`.
  - Can now sort using multiple methods at the same time. In the config file you specify exactly what you want:
  - Example: if you update these lines:
    	sort_methods: ["metadata", "orientation", "resolution"] #metadata, orientation, resolution
	metadata_keys: ["model", "CFG Scale"]
	- The program would start by looking at the sort_methods and it sees that you have 3 sort methods selected. Since metadata contains "metadata_keys", and since you have 2 keys, it would sort first by model and then by CFG Scale.  Then it would look at the next method in sort_methods, which is "orientation" and would sort into either portrait or landscape. Finally, it would sort according to your resolution folder settings (hires, lores, etc). If sorting varied files you may want to use multiple methods. If sorting a smaller folder you may want to just use one. I like keeping my models seperate so I generally just sort by models. But you can sort by anything at the moment in the metadata, except by prompts. I plan to add this method in the next version.
    
- **Improved Metadata Extraction**
  - **Enhanced `MetadataExtractor`**:
    - Extracts metadata using ExifTool (primary method).
    - Falls back to parsing `.txt` sidecar files when ExifTool fails.
    - Stores extracted metadata in JSON format for better accessibility.
  - **New `PromptFilter` module**:
    - Cleans and structures metadata fields.
    - Preserves positive and negative prompts as lists instead of strings.

### **🛠 Improvements**
- **Refactored `sort_images_and_texts()`**:
  - Now **stores metadata in memory** before sorting, improving performance.
  - Ensures that files are **only processed once**.
  - Debugging logs added for better tracking of file movements.
- **Refactored `sort_by_metadata()`**:
  - Now **creates folders dynamically** based on extracted metadata values.
  - Handles cases where metadata keys are missing or contain invalid characters.
  - Debug logs added to track file movement and sorting errors.
- **Recursive scanning reworked**:
  - Option to enable/disable recursive scanning in `config.yaml`.
  - `max_depth` setting allows users to control how deep folder scanning goes.

### **🐛 Bug Fixes**
- **Fixed incorrect metadata formatting**:
  - `positive_prompts` and `negative_prompt` now **always remain lists**.
  - Previously stored as strings, causing issues in metadata-based sorting.
- **Fixed issue where sorting did not trigger correctly**:
  - Ensured `sort_images_and_texts()` correctly calls `sort_by_metadata()`.
  - Added debug logs to trace sorting failures.
- **Fixed file locking issue**:
  - Implemented a **file lock check** before moving files to prevent failures when files are open in another process.

### **🔧 Configuration Updates**
- `config.yaml` now supports:
  - `sort_methods`: Allows users to specify multiple sorting methods.
  - `metadata_keys`: Defines which metadata fields should be used for sorting.
  - `use_recursive_scan`: Improved handling of `true`/`false`, supporting values like "yes", "no", "1", "0".

---

### **Previous Versions**
For earlier changelogs, visit the [GitHub repository](https://github.com/Kittensx/custom_sorter).

## Overview
The Custom Sorter Program is a Python-based file organization tool designed to sort and manage images and text files into categorized folders based on user-defined configurations. It supports advanced features like resolution-based sorting, retry mechanisms for file operations, and cleaning up input folders.

## Features
- **Sort by resolution**: Categorizes files into user-defined resolution thresholds.
- **Sort by orientation**: (new!!) Now sorts into portrait or landscape
- **Sort by Metadata**: (new!!) Using Exifreader for images, can sort with metadata (requires Exifreader)
- **Dynamic thresholds**: Supports flexible sorting based on custom configurations.
- **Organize in place or move**: Choose whether to organize files within the input folder or move them to an output folder.
- **Retry mechanism**: Automatically retries file operations on failure.
- **Post-processing cleanup**: Removes empty folders from the input directory after processing.


---

## Installation

### Prerequisites
- Python 3.8 or later
- `pip` (Python package manager)

### Steps
1. Clone or download the repository.
  - git clone https://github.com/Kittensx/custom_sorter
	

2. Open a terminal and/or navigate to the project directory.
  - cd custom_sorter
	
3. Run the installer script:   
- python install_cs.py
   
4. The script will:
  Create a virtual environment (venv).
  Install the required dependencies from requirements.txt.
  Generate a batch file (cs_run.bat) for easier execution.

## Usage
### Running the Program
1. Execute the batch file:
  - cs.run.bat

This will:
  - Activate the virtual environment.
  - Run the custom_sorter.py script.
  - Use the configuration specified in custom_sorter_config.yaml. 

2. Alternatively, run the script directly:
- python custom_sorter.py

## Configuration
The program reads settings from the custom_sorter_config.yaml file. Below is an example configuration:


### Configuration Options
1. input_folders: List of folders to process.
2. output_folder: Destination folder for sorted files.
3. use_output_folder: Set to false to organize files within the input folder.
4. resolution_folders: Define custom folder names and resolution thresholds.
5. sort_method:
  **resolution: Sort by image resolution.**  
6. dynamic_thresholds: Automatically handle resolutions outside defined thresholds.

## Features
### Sorting
Categorize images based on:
#### Resolution: Total pixels (width × height).

### File Operations
Move or copy files while avoiding duplicates.
Automatically retry failed operations.

### Post-Processing
Cleans up empty input folders.
Compares input and output folders to remove duplicates.


## Screenshots
Sample run organized **input** folder
Sample run organized **output** folder


## Modules
1. install_cs.py
  Sets up a virtual environment and installs dependencies.
  Creates a batch file for convenient execution.
  
2. custom_sorter.py
  Reads configurations and sorts files accordingly.
  Handles file operations and organizes them into structured folders.
  
3. custom_sorter_config.yaml
  User-defined settings for sorting logic and folder management.
  
4. post_processing_manager.py
  Removes duplicates from input folders based on the output folder.
  Cleans up empty folders.
  
5. cs_queue.py
  Manages file operations with retry mechanisms.
  Supports hash-based file comparison to avoid duplicates.

## Dependencies
Listed in requirements.txt:
  pillow
  filelock
  psutil
  send2trash
  pyyaml

### Install them using:
pip install -r requirements.txt

### Troubleshooting
**Common Issues**
*Configuration Errors*

### Ensure custom_sorter_config.yaml is correctly formatted.
*Use YAML validators to check for syntax errors.*

### Permission Denied:
Close other programs that might lock the files.
Run the script with elevated permissions if required.

### Virtual Environment Issues:
Delete and recreate the venv folder:
python install_cs.py

## Future Features
Add functionality to sort by orientation
Add undo functionality to reverse file operations based on a log.
Enhance configuration validation and error reporting.

## Contributing
Feel free to submit pull requests or report issues for improvements.

## License
This project is open-source and available under the MIT License.
