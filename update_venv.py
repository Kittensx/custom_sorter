import os
import subprocess
import sys

def get_venv_python():
    """
    Return the path to the Python executable inside the local 'venv' folder.
    """
    if os.name == "nt":
        return os.path.join("venv", "Scripts", "python.exe")
    else:
        return os.path.join("venv", "bin", "python")

def install_requirements():
    venv_python = get_venv_python()

    if not os.path.exists(venv_python):
        print("❌ Virtual environment not found at expected location: ./venv")
        print("➡️  You can create it with: python -m venv venv")
        return

    requirements_file = "requirements.txt"
    if not os.path.exists(requirements_file):
        print("❌ requirements.txt not found.")
        return

    print(f"🔄 Installing packages from {requirements_file} into venv...")
    try:
        subprocess.check_call([venv_python, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([venv_python, "-m", "pip", "install", "-r", requirements_file])
        print("✅ venv updated successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")

if __name__ == "__main__":
    install_requirements()
