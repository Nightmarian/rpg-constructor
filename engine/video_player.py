import os
import tkinter as tk
from pathlib import Path

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
    ]
    for folder in candidates:
        if folder.exists() and (folder / 'libvlc.dll').exists():
            if hasattr(os, 'add_dll_directory'):
                os.add_dll_directory(str(folder))
            os.environ['PATH'] = str(folder) + os.pathsep + os.environ.get('PATH', '')
            break
    import vlc
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
        self.window = tk.Toplevel(app.window)
        self.window.title('Видео')
        self.window.geometry(f'{width}x{height}')
        self.window.resizable(False, False)
        self.window.configure(background='black')
        self.window.protocol('WM_DELETE_WINDOW', self.close)
        self.window.bind('<space>', lambda event: self.close())
        self.window.bind('<Return>', lambda event: self.close())
        self.window.focus_set()
        self.window.update_idletasks()
        if hasattr(self.player, 'set_hwnd'):
            self.player.set_hwnd(self.window.winfo_id())
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
            self.window.destroy()
        except Exception:
            pass
        callback = self.on_close
        self.on_close = None
        if callback:
            callback()
