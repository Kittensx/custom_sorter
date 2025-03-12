import os
import sys
import subprocess
import venv

# Define the virtual environment directory
VENV_DIR = "venv"

def create_virtual_environment():
    """Creates a virtual environment if it doesn't exist."""
    if not os.path.exists(VENV_DIR):
        print(f"Creating virtual environment in '{VENV_DIR}'...")
        venv.create(VENV_DIR, with_pip=True)
        print("Virtual environment created successfully!")
    else:
        print(f"Virtual environment '{VENV_DIR}' already exists.")

def get_venv_python():
    """Returns the path to the Python interpreter inside the virtual environment."""
    if sys.platform == "win32":
        return os.path.join(VENV_DIR, "Scripts", "python.exe")
    else:
        return os.path.join(VENV_DIR, "bin", "python")

def install_requirements():
    """Installs the dependencies from requirements.txt inside the virtual environment."""
    python_exec = get_venv_python()

    if not os.path.exists(python_exec):
        print("Error: Virtual environment not found or Python executable missing!")
        sys.exit(1)

    if not os.path.exists("requirements.txt"):
        print("Error: requirements.txt file not found!")
        sys.exit(1)

    print("Installing dependencies from requirements.txt...")
    subprocess.run([python_exec, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([python_exec, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    print("All dependencies installed successfully!")

def main():
    create_virtual_environment()
    install_requirements()

if __name__ == "__main__":
    main()
