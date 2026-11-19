@echo off
cd /d "%~dp0"
py -3.12 -m venv .venv
if errorlevel 1 goto fail

.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail

.venv\Scripts\python.exe -m pip install imageio imageio-ffmpeg python-vlc keyboard
if errorlevel 1 goto fail

.venv\Scripts\python.exe -c "import tkinter; import PIL; import imageio; import imageio_ffmpeg; import vlc; import keyboard; print(imageio_ffmpeg.get_ffmpeg_exe())"
if errorlevel 1 goto fail

echo Installation completed.
pause
exit /b 0

:fail
echo Installation failed. Copy console output.
pause
exit /b 1
