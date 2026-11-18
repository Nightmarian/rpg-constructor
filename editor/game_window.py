import copy
import json
import time
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from pathlib import Path
from PIL import ImageTk
from support.keys import normalize


class GameWindow:
    def __init__(self, a):
        self.a = a
        self.keys = set()
        self.running = True
        self.recording = False
        self.samples = []
        self.record_start = 0.0
        self.last = time.perf_counter()
        width, height = a.project['output_size']
        self.window = tk.Toplevel(a.window)
        self.window.title('Игра')
        self.window.geometry(f'{width}x{height}')
        self.window.resizable(False, False)
        self.canvas = tk.Canvas(self.window, bg='black', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.item = self.canvas.create_image(0, 0, anchor='nw')
        bar = ttk.Frame(self.window, padding=4)
        bar.pack(side='bottom', fill='x')
        self.status = tk.StringVar(value='WASD/стрелки — движение, Пробел/Enter — действие, Escape — выход')
        ttk.Label(bar, textvariable=self.status, anchor='w').pack(side='left', fill='x', expand=True)
        self.record_button = ttk.Button(bar, text='Запись', command=self.start_record)
        self.record_button.pack(side='right', padx=3)
        self.stop_button = ttk.Button(bar, text='Стоп', command=self.stop_record, state='disabled')
        self.stop_button.pack(side='right', padx=3)
        self.canvas.focus_set()
        self.window.protocol('WM_DELETE_WINDOW', self.close)
        self.window.bind('<KeyPress>', self.key_down)
        self.window.bind('<KeyRelease>', lambda e: self.keys.discard(normalize(e.keysym, e.keycode)))
        self.window.bind('<FocusOut>', lambda e: self.keys.clear())
        self.window.after(30, self.tick)

    def key_down(self, e):
        key = normalize(e.keysym, e.keycode)
        first = key not in self.keys
        self.keys.add(key)
        if key == 'Escape':
            self.close()
            return
        if first and key in ('space', 'Return'):
            try:
                self.a.world.interact()
                if self.recording:
                    self.samples.append(self.a.world.snapshot(time.perf_counter() - self.record_start))
            except Exception:
                self.a.log.exception('Game interact')

    def start_record(self):
        if self.recording:
            return
        self.samples = [self.a.world.snapshot(0.0)]
        self.record_start = time.perf_counter()
        self.recording = True
        self.record_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.a.log.info('Game capture started')

    def stop_record(self):
        if not self.recording:
            return
        self.samples.append(self.a.world.snapshot(time.perf_counter() - self.record_start))
        self.recording = False
        self.record_button.config(state='normal')
        self.stop_button.config(state='disabled')
        folder = self.a.root / 'recordings'
        folder.mkdir(exist_ok=True)
        path = folder / datetime.now().strftime('take_%Y%m%d_%H%M%S_%f.json')
        path.write_text(json.dumps(dict(take_version=4, project=self.a.project, samples=self.samples), ensure_ascii=False), encoding='utf-8')
        self.status.set('Дубль готов: ' + path.name)
        self.a.log.info('Game capture saved %s', path)

    def close(self):
        if self.recording:
            self.stop_record()
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
            if self.recording:
                self.samples.append(self.a.world.snapshot(started - self.record_start))
            frame = self.a.scene.draw(self.a.project, self.a.world.view_state(), (width, height))
            self.photo = ImageTk.PhotoImage(frame)
            self.canvas.itemconfig(self.item, image=self.photo)
            if self.recording:
                self.status.set(f'ЗАПИСЬ {started - self.record_start:.1f} с | Стоп → дубль')
        except Exception:
            self.a.log.exception('Game window')
            self.close()
            return
        delay = max(1, round(1000 / 30 - (time.perf_counter() - started) * 1000))
        self.window.after(delay, self.tick)
