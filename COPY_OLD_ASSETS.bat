@echo off
cd /d "%~dp0"
.venv\Scripts\python.exe copy_old_assets.py
if errorlevel 1 pause
