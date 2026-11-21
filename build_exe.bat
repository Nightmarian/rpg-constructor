@echo off
python -m pip install --upgrade pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "RPG-Constructor" --icon "icon.ico" --add-data "assets;assets" --add-data "project;project" --add-data "icon.ico;." main.py
pause
