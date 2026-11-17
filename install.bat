@echo off
setlocal

echo === RPG Constructor setup ===

where python >nul 2>nul
if errorlevel 1 (
  echo Python not found. Install Python 3.12 first.
  pause
  exit /b 1
)

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

where ffmpeg >nul 2>nul
if errorlevel 1 (
  echo ffmpeg not found. Installing via winget...
  winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
) else (
  echo ffmpeg found.
)

where vlc >nul 2>nul
if errorlevel 1 (
  if not exist "%ProgramFiles%\VideoLAN\VLC\vlc.exe" (
    echo VLC not found. Installing via winget...
    winget install --id VideoLAN.VLC -e --accept-source-agreements --accept-package-agreements
  ) else (
    echo VLC found.
  )
) else (
  echo VLC found.
)

if not exist "recordings" mkdir recordings

echo Setup complete.
pause
