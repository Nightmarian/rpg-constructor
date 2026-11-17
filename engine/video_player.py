import tkinter as tk
from pyvidplayer2 import VideoTkinter

class VideoWindow:

    def __init__(self, app, file, on_close):
        self.app = app
        self.on_close = on_close
        self.closed = False
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
        self.player = VideoTkinter(self.window, str(file))
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
