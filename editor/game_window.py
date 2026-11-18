import time
import tkinter as tk
from PIL import ImageTk
from support.keys import normalize


class GameWindow:
    def __init__(self, a):
        self.a = a
        self.keys = set()
        self.running = True
        self.last = time.perf_counter()
        width, height = a.project['output_size']
        self.window = tk.Toplevel(a.window)
        self.window.title('Игра')
        self.window.geometry(f'{width}x{height}')
        self.window.resizable(False, False)
        self.canvas = tk.Canvas(self.window, bg='black', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.item = self.canvas.create_image(0, 0, anchor='nw')
        self.canvas.focus_set()
        self.window.protocol('WM_DELETE_WINDOW', self.close)
        self.window.bind('<KeyPress>', self.key_down)
        self.window.bind('<KeyRelease>', lambda e: self.keys.discard(normalize(e.keysym, e.keycode)))
        self.window.bind('<FocusOut>', lambda e: self.keys.clear())
        self.window.after(30, self.tick)

    def key_down(self, e):
        key = normalize(e.keysym, e.keycode)
        self.keys.add(key)
        if key == 'Escape':
            self.close()

    def close(self):
        self.running = False
        self.a.keys.clear()
        try:
            self.window.destroy()
        except Exception:
            pass

    def tick(self):
        if not self.running or not self.window.winfo_exists():
            return
        started = time.perf_counter()
        dt = min(0.25, max(0, started - self.last))
        self.last = started
        try:
            width = max(1, self.canvas.winfo_width())
            height = max(1, self.canvas.winfo_height())
            self.a.world.update(self.keys, dt, self.a.scene.size(self.a.project, self.a.world.map_id), self.a.collisions.get())
            frame = self.a.scene.draw(self.a.project, self.a.world.view_state(), (width, height))
            self.photo = ImageTk.PhotoImage(frame)
            self.canvas.itemconfig(self.item, image=self.photo)
        except Exception:
            self.a.log.exception('Game window')
            self.close()
            return
        delay = max(1, round(1000 / 30 - (time.perf_counter() - started) * 1000))
        self.window.after(delay, self.tick)
