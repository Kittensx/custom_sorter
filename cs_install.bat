@echo off
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Running Custom Sorter...
python install_cs.py
pause


