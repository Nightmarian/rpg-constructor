@echo off
cd /d "%~dp0"
py -3.12 start_launcher.py
if errorlevel 1 pause
