@echo off
cd /d ./
pyinstaller Velwether.py --onefile --collect-data pyfiglet
pause