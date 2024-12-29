# Custom Sorter Program

## Overview
The Custom Sorter Program is a Python-based file organization tool designed to sort and manage images and text files into categorized folders based on user-defined configurations. It supports advanced features like resolution-based sorting, retry mechanisms for file operations, and cleaning up input folders.

## Features
- **Sort by resolution**: Categorizes files into user-defined resolution thresholds.
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
