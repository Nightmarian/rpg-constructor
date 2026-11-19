@echo off
cd /d %~dp0
if not exist .venv\Scripts\python.exe (
  echo Сначала запусти install.bat
  pause
  exit /b 1
)
.venv\Scripts\python.exe screen_recorder\recorder_app.py
if errorlevel 1 pause
