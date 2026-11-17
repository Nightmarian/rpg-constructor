import os
import shutil
import logging
import subprocess
import tkinter as tk
from pathlib import Path

log = logging.getLogger('rpg')

def find_vlc_exe():
    base = Path(__file__).resolve().parent.parent
    candidates = [
        base / 'vlc' / 'vlc.exe',
        base / 'VLC' / 'vlc.exe',
        base / 'VLCPortable' / 'vlc.exe',
        base / 'vlc-3.0.21' / 'vlc.exe',
        Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')) / 'VideoLAN' / 'VLC' / 'vlc.exe',
        Path(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')) / 'VideoLAN' / 'VLC' / 'vlc.exe',
        Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'VideoLAN' / 'VLC' / 'vlc.exe',
        Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')) / 'VLC' / 'vlc.exe',
    ]
    exe = shutil.which('vlc.exe')
    if exe:
        candidates.append(Path(exe))
    for p in candidates:
        try:
            if p.exists():
                return p
        except Exception:
            pass
    searched = '\n'.join(('  ' + str(p)) for p in candidates)
    log.error('VLC not found. Searched:\n' + searched)
    raise RuntimeError('VLC не найден. Установи VLC Media Player и перезапусти программу.\n\nПроверены:\n' + searched)

class VideoWindow:

    def __init__(self, app, file, on_close):
        self.app = app
        self.on_close = on_close
        self.closed = False
        self.vlc_exe = find_vlc_exe()
        log.info('Using VLC: ' + str(self.vlc_exe))
        width, height = app.project['output_size']
        self.frame = tk.Frame(app.window, background='black', width=width, height=height)
        self.frame.place(x=0, y=0, relwidth=1, relheight=1)
        self.frame.lift()
        self.frame.update_idletasks()
        self.window = self.frame
        app.window.protocol('WM_DELETE_WINDOW', self.close)
        app.window.bind('<space>', lambda event: self.close())
        app.window.bind('<Return>', lambda event: self.close())
        self.frame.focus_set()
        args = [
            str(self.vlc_exe),
            '--intf=dummy',
            '--play-and-exit',
            '--avcodec-hw=none',
            '--no-video-title-show',
            str(file),
        ]
        log.info('VLC args: ' + ' '.join(args))
        self.process = subprocess.Popen(args, cwd=str(self.vlc_exe.parent), creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0)
        self.app.window.after(200, self.check)

    def check(self):
        if self.closed:
            return
        if self.process.poll() is not None:
            self.close()
        else:
            self.app.window.after(200, self.check)

    def close(self):
        if self.closed:
            return
        self.closed = True
        try:
            if self.process.poll() is None:
                self.process.kill()
        except Exception:
            pass
        def destroy():
            try:
                self.frame.destroy()
            except Exception:
                pass
            callback = self.on_close
            self.on_close = None
            if callback:
                callback()
        self.app.window.after(50, destroy)
