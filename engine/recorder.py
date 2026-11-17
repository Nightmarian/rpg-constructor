import os
import shutil
import subprocess
import logging
from pathlib import Path
from datetime import datetime

log = logging.getLogger('rpg')

def find_ffmpeg():
    exe = shutil.which('ffmpeg')
    if exe:
        return Path(exe)
    base = Path(__file__).resolve().parent.parent
    candidates = [base / 'ffmpeg' / 'bin' / 'ffmpeg.exe', base / 'ffmpeg.exe']
    for p in candidates:
        if p.exists():
            return p
    return None

class Recorder:

    def __init__(self, app):
        self.app = app
        self.process = None
        self.file = None

    def start(self):
        if self.process:
            return False
        ffmpeg = find_ffmpeg()
        if not ffmpeg:
            log.error('ffmpeg not found')
            raise RuntimeError('ffmpeg не найден. Установи ffmpeg и добавь в PATH или положи ffmpeg.exe в папку проекта.')
        out_dir = Path('recordings')
        out_dir.mkdir(exist_ok=True)
        self.file = out_dir / (datetime.now().strftime('rec_%Y-%m-%d_%H-%M-%S') + '.mp4')
        w, h = self.app.project['output_size']
        # запись всего экрана + системного звука, если доступен virtual-audio-capturer
        args = [
            str(ffmpeg), '-y',
            '-f', 'gdigrab', '-framerate', '30', '-offset_x', '0', '-offset_y', '0', '-video_size', f'{w}x{h}', '-i', 'desktop',
            '-f', 'dshow', '-i', 'audio=virtual-audio-capturer',
            '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23',
            '-c:a', 'aac', '-b:a', '128k',
            str(self.file),
        ]
        log.info('Recorder args: ' + ' '.join(args))
        try:
            self.process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0)
        except Exception as e:
            self.process = None
            log.error('Recorder start failed: ' + str(e))
            raise
        return True

    def stop(self):
        if not self.process:
            return None
        try:
            self.process.terminate()
            self.process.wait(timeout=5)
        except Exception:
            try:
                self.process.kill()
            except Exception:
                pass
        self.process = None
        return self.file

    def toggle(self):
        if self.process:
            return self.stop()
        self.start()
        return None
