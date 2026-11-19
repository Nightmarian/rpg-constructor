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

    def __init__(self, app, file, on_close, parent=None, canvas=None, controller=None):
        self.app = app
        self.on_close = on_close
        self.closed = False
        self.controller = controller
        vlc = prepare_vlc()
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        width, height = app.project['output_size']
        if parent is not None:
            self.window = parent
            self.canvas = canvas or parent.canvas
            if self.controller:
                self.controller.video_active = True
            self.window.update_idletasks()
            if hasattr(self.player, 'set_hwnd'):
                self.player.set_hwnd(self.canvas.winfo_id())
        else:
            self.window = tk.Toplevel(app.window)
            self.window.title('Видео')
            self.window.geometry(f'{width}x{height}')
            self.window.resizable(False, False)
            self.window.configure(background='black')
            self.window.protocol('WM_DELETE_WINDOW', self.close)
            self.window.focus_set()
            self.window.update_idletasks()
            if hasattr(self.player, 'set_hwnd'):
                self.player.set_hwnd(self.window.winfo_id())
        media = self.instance.media_new(str(file))
        self.player.set_media(media)
        self.player.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached, lambda event: app.window.after(0, self.close))
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
            if hasattr(self.player, 'set_hwnd'):
                self.player.set_hwnd(0)
        except Exception:
            pass
        if self.controller:
            self.controller.video_active = False
            self.controller.canvas.focus_set()
        callback = self.on_close
        self.on_close = None
        if callback:
            callback()
