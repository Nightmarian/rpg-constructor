import copy
import json
import subprocess
import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageTk
from support.keys import normalize

ICON_URL = 'https://raw.githubusercontent.com/Nightmarian/rpg-constructor/main/%D0%B8%D0%BA%D0%BE%D0%BD%D0%BA%D0%B0/%D0%9C%D1%80%D0%B0%D1%87%D0%BD%D0%B0%D1%8F%20%D0%B8%D0%BA%D0%BE%D0%BD%D0%BA%D0%B0.png'

def load_icon(window):
    root = Path(__file__).resolve().parent.parent
    icon_path = root / 'иконка' / 'Мрачная иконка.png'
    try:
        if not icon_path.exists():
            icon_path.parent.mkdir(exist_ok=True)
            import urllib.request
            urllib.request.urlretrieve(ICON_URL, icon_path)
        icon = ImageTk.PhotoImage(Image.open(icon_path))
        window.iconphoto(True, icon)
        window._icon = icon
    except Exception:
        pass

class GameWindow:
    def __init__(self, a, display_mode='fit'):
        self.a = a
        self.display_mode = display_mode
        self.keys = set()
        self.running = True
        self.recording = False
        self.samples = []
        self.record_start = 0.0
        self.last = time.perf_counter()
        self.video = None
        self.video_active = False
        self.fullscreen = False
        width, height = a.project['output_size']
        self.window = tk.Toplevel(a.window)
        self.window.title('Игра')
        self.window.geometry(f'{width}x{height}')
        self.window.resizable(False, False)
        load_icon(self.window)
        self.canvas = tk.Canvas(self.window, bg='black', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.item = self.canvas.create_image(0, 0, anchor='nw')
        self.bar = ttk.Frame(self.window, padding=4)
        self.bar.pack(side='bottom', fill='x')
        self.status = tk.StringVar(value='WASD/стрелки — движение, Пробел/Enter — действие, F11 — полный экран, Escape — выход')
        ttk.Label(self.bar, textvariable=self.status, anchor='w').pack(side='left', fill='x', expand=True)
        self.record_button = ttk.Button(self.bar, text='Запись', command=self.start_record)
        self.record_button.pack(side='right', padx=3)
        self.stop_button = ttk.Button(self.bar, text='Стоп', command=self.stop_record, state='disabled')
        self.stop_button.pack(side='right', padx=3)
        self.mp4_button = ttk.Button(self.bar, text='MP4', command=self.export_mp4, state='disabled')
        self.mp4_button.pack(side='right', padx=3)
        self.screen_record_button = ttk.Button(self.bar, text='Запись экрана', command=self.open_screen_recorder)
        self.screen_record_button.pack(side='right', padx=3)
        self.canvas.focus_set()
        self.window.protocol('WM_DELETE_WINDOW', self.close)
        self.window.bind('<KeyPress>', self.key_down)
        self.window.bind('<KeyRelease>', lambda e: self.keys.discard(normalize(e.keysym, e.keycode)))
        self.window.bind('<FocusOut>', lambda e: self.keys.clear())
        self.a.world.video_callback = self.play_video
        self.window.after(30, self.tick)

    def open_screen_recorder(self):
        root = Path(self.a.root)
        script = root / 'screen_recorder' / 'recorder_app.py'
        python = Path(sys.executable)
        try:
            subprocess.Popen([str(python), str(script)], cwd=str(root), creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except Exception:
            self.a.log.exception('Screen recorder')
            messagebox.showerror('Запись экрана', 'Не удалось открыть запись экрана. Смотри журнал.', parent=self.window)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.window.attributes('-fullscreen', self.fullscreen)
        if self.fullscreen:
            self.bar.pack_forget()
        else:
            width, height = self.a.project['output_size']
            self.window.geometry(f'{width}x{height}')
            self.bar.pack(side='bottom', fill='x')
        self.canvas.focus_set()

    def play_video(self, file):
        try:
            from engine.video_player import VideoWindow
            self.video = VideoWindow(self.a, file, self.a.world.video_finished, parent=self.window, canvas=self.canvas, controller=self)
        except Exception:
            self.a.log.exception('Game video')
            messagebox.showerror('Видео', 'Не удалось открыть видео. Смотри журнал.', parent=self.window)
            self.video_active = False
            self.a.world.video_finished()

    def close_video(self):
        if self.video:
            self.video.close()
            self.video = None

    def key_down(self, e):
        key = normalize(e.keysym, e.keycode)
        first = key not in self.keys
        self.keys.add(key)
        if key == 'f11':
            if first:
                self.toggle_fullscreen()
            return
        if key == 'Escape':
            if self.fullscreen:
                self.toggle_fullscreen()
                return
            self.close()
            return
        if self.video_active and key in ('space', 'Return'):
            if first:
                self.close_video()
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
        self.mp4_button.config(state='disabled')
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
        self.a.take = (copy.deepcopy(self.samples), copy.deepcopy(self.a.project), copy.copy(self.a.scene))
        self.mp4_button.config(state='normal')
        self.status.set('Дубль готов: ' + path.name + ' | Нажми MP4')
        self.a.log.info('Game capture saved %s', path)

    def export_mp4(self):
        if not self.a.take:
            messagebox.showinfo('MP4', 'Сначала сделай запись и нажми «Стоп».', parent=self.window)
            return
        try:
            from editor.export_ui import start
            start(self.a)
        except Exception:
            self.a.log.exception('MP4 export')
            messagebox.showerror('MP4', 'Ошибка экспорта. Смотри журнал.', parent=self.window)

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
            target_w, target_h = self.a.project['output_size']
            frame = self.a.scene.draw(self.a.project, self.a.world.view_state(), (target_w, target_h))
            scale = min(width / target_w, height / target_h)
            draw_w = max(1, round(target_w * scale))
            draw_h = max(1, round(target_h * scale))
            if (frame.width, frame.height) != (draw_w, draw_h):
                frame = frame.resize((draw_w, draw_h), Image.Resampling.LANCZOS)
            display = Image.new('RGB', (width, height), (0, 0, 0))
            display.paste(frame, ((width - draw_w) // 2, (height - draw_h) // 2))
            self.photo = ImageTk.PhotoImage(display)
            self.canvas.itemconfig(self.item, image=self.photo)
            if self.recording:
                self.status.set(f'ЗАПИСЬ {started - self.record_start:.1f} с | Стоп → MP4')
        except Exception:
            self.a.log.exception('Game window')
            self.close()
            return
        delay = max(1, round(1000 / 30 - (time.perf_counter() - started) * 1000))
        self.window.after(delay, self.tick)
