import os
import shutil
import logging
import tkinter as tk
from pathlib import Path

log = logging.getLogger('rpg')

def prepare_vlc():
    base = Path(__file__).resolve().parent.parent
    candidates = [
        base / 'vlc',
        base / 'VLC',
        base / 'VLCPortable',
        base / 'vlc-3.0.21',
        Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')) / 'VideoLAN' / 'VLC',
        Path(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')) / 'VideoLAN' / 'VLC',
        Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'VideoLAN' / 'VLC',
        Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')) / 'VLC',
    ]
    exe = shutil.which('vlc.exe')
    if exe:
        candidates.append(Path(exe).resolve().parent)
    vlc_folder = None
    for folder in candidates:
        try:
            if folder.exists() and (folder / 'libvlc.dll').exists():
                vlc_folder = folder
                break
        except Exception:
            pass
    if not vlc_folder:
        searched = '\n'.join(('  ' + str(p)) for p in candidates)
        log.error('VLC not found. Searched:\n' + searched)
        raise RuntimeError('VLC не найден. Установи VLC Media Player и перезапусти программу.\n\nПроверены:\n' + searched)
    log.info('Using VLC: ' + str(vlc_folder))
    if hasattr(os, 'add_dll_directory'):
        os.add_dll_directory(str(vlc_folder))
    os.environ['PATH'] = str(vlc_folder) + os.pathsep + os.environ.get('PATH', '')
    previous = os.getcwd()
    os.chdir(vlc_folder)
    try:
        import vlc
    finally:
        os.chdir(previous)
    return vlc

class VideoWindow:

    def __init__(self, app, file, on_close):
        self.app = app
        self.on_close = on_close
        self.closed = False
        vlc = prepare_vlc()
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        width, height = app.project['output_size']
        # встроенное видео поверх игрового окна
        self.frame = tk.Frame(app.window, background='black', width=width, height=height)
        self.frame.place(x=0, y=0, relwidth=1, relheight=1)
        self.frame.lift()
        self.frame.update_idletasks()
        self.window = self.frame  # для совместимости с прежним кодом
        app.window.protocol('WM_DELETE_WINDOW', self.close)
        app.window.bind('<space>', lambda event: self.close())
        app.window.bind('<Return>', lambda event: self.close())
        self.frame.focus_set()
        if hasattr(self.player, 'set_hwnd'):
            self.player.set_hwnd(self.frame.winfo_id())
        media = self.instance.media_new(str(file))
        self.player.set_media(media)
        self.player.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached, lambda event: app.root.after(0, self.close))
        self.player.play()

    def close(self):
        if self.closed:
            return
        self.closed = True
        try:
            self.player.stop()
        except Exception:
            pass
        try:
            self.frame.destroy()
        except Exception:
            pass
        callback = self.on_close
        self.on_close = None
        if callback:
            callback()
