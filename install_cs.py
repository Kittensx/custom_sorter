import os
import subprocess

class CustomSorterInstaller:
    def __init__(self, venv_dir="venv", requirements_file="requirements.txt", batch_file_name="cs_run.bat", script_name="custom_sorter.py", commands=None):
        self.venv_dir = venv_dir
        self.requirements_file = requirements_file        
        self.python_executable = os.path.join(self.venv_dir, "Scripts", "python.exe")
        self.batch_file_name = batch_file_name
        self.script_name = script_name
        self.commands = commands or []
        self.script_directory = os.path.dirname(os.path.abspath(__file__))
        
    def create_virtual_environment(self):
        """Check if the virtual environment exists; create it if not."""
        if not os.path.exists(self.venv_dir):
            print("Creating virtual environment...")
            subprocess.run(["python", "-m", "venv", self.venv_dir], check=True)
            print("Virtual environment created.")
        else:
            print("Virtual environment already exists.")

    def install_requirements(self):
        """Check and install missing or outdated requirements."""
        print("Ensuring pip is available in the virtual environment...")
        subprocess.run([self.python_executable, "-m", "ensurepip", "--upgrade"], check=True)
        print("Ensuring pip is up-to-date...")
        subprocess.run([self.python_executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)

        if os.path.exists(self.requirements_file):
            print("Checking for missing or outdated requirements...")
            subprocess.run([self.python_executable, "-m", "pip", "install", "-r", self.requirements_file], check=True)
            print("Requirements are up-to-date.")
        else:
            print("requirements.txt not found. Skipping installation of dependencies.")


     
    def create_batch_file(self):
        """Creates a Windows batch file with the specified commands."""
        try:
            batch_file_path = os.path.join(self.script_directory, self.batch_file_name)
            with open(batch_file_path, "w") as batch_file:
                # Add a command to change directory to the script's location
                batch_file.write(f"@echo off\n")
                batch_file.write(f"cd /d {self.script_directory}\n")
                
                # Command to run the Python script
                python_executable = os.path.join("venv", "Scripts", "python.exe")  # Path to Python executable
                script_name = self.script_name  # Assumes script is in the root directory
                batch_file.write(f"{python_executable} {script_name}\n")
                
                batch_file.write("pause\n")
            print(f"Batch file '{batch_file_path}' created successfully.")
        except Exception as e:
            print(f"Error creating batch file: {e}")



if __name__ == "__main__":
    commands = [
        "@echo off",
        f"cd /d {os.path.dirname(os.path.abspath(__file__))}",  # Ensure working directory is the root
        "echo Activating virtual environment...",
        "call venv\\Scripts\\activate.bat",
        "echo Running Custom Sorter...",
        "venv\\Scripts\\python.exe custom_sorter.py"  
    ]


    # Initialize the BatchFileCreator 
    setup = CustomSorterInstaller(commands=commands)

    try:
        # Create virtual environment
        setup.create_virtual_environment()

        # Install requirements
        setup.install_requirements()

        # Create batch file
        setup.create_batch_file()  # No need to pass commands
        
        print("Custom sorter setup and execution completed successfully.")
    except Exception as e:
        print(f"Error: {e}")
