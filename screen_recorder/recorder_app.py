import os
import shutil
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from pathlib import Path

try:
    import ctypes
    if sys.platform == 'win32':
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
RECORDINGS = ROOT / 'recordings'

class RecorderApp:
    def __init__(self):
        self.process = None
        self.window = tk.Tk()
        self.window.title('Запись игры')
        self.window.geometry('580x420')
        self.window.resizable(False, False)
        ttk.Label(self.window, text='Режим записи').pack(anchor='w', padx=14, pady=(16, 3))
        self.mode = tk.StringVar(value='game')
        ttk.Radiobutton(self.window, text='Окно игры — записать окно «Игра» и звук игры', value='window', variable=self.mode, command=self.update_hint).pack(anchor='w', padx=14)
        ttk.Radiobutton(self.window, text='Полный экран — весь монитор', value='monitor', variable=self.mode, command=self.update_hint).pack(anchor='w', padx=14)
        ttk.Radiobutton(self.window, text='Полный экран — только игра 16:9', value='game', variable=self.mode, command=self.update_hint).pack(anchor='w', padx=14)
        ttk.Label(self.window, text='Название окна игры').pack(anchor='w', padx=14, pady=(14, 3))
        self.title_var = tk.StringVar(value='Игра')
        ttk.Entry(self.window, textvariable=self.title_var, width=48).pack(fill='x', padx=14)
        self.hint = tk.StringVar(value='Будет записана центральная область 1920×1080 — только игра, без чёрных полос.\nГлобальная клавиша F9: начать или остановить запись.\nПеред стартом будет 3-секундный отсчёт.')
        ttk.Label(self.window, textvariable=self.hint, wraplength=520, justify='left').pack(anchor='w', padx=14, pady=10)
        self.status = tk.StringVar(value='Готово к записи')
        ttk.Label(self.window, textvariable=self.status, anchor='w').pack(fill='x', padx=14)
        buttons = ttk.Frame(self.window)
        buttons.pack(fill='x', padx=14, pady=16)
        self.start_button = ttk.Button(buttons, text='Начать запись', command=self.start_countdown)
        self.start_button.pack(side='left', padx=(0, 6))
        self.stop_button = ttk.Button(buttons, text='Стоп', command=self.stop, state='disabled')
        self.stop_button.pack(side='left', padx=6)
        ttk.Button(buttons, text='Открыть папку', command=self.open_folder).pack(side='left', padx=6)
        ttk.Button(buttons, text='Параметры recap', command=self.show_options).pack(side='left', padx=6)
        self.window.protocol('WM_DELETE_WINDOW', self.close)
        self.register_hotkey()

    def register_hotkey(self):
        try:
            import keyboard
            keyboard.add_hotkey('f9', lambda: self.window.after(0, self.toggle))
        except Exception as exc:
            self.status.set('F9 недоступна: ' + str(exc))

    def update_hint(self):
        if self.mode.get() == 'window':
            self.hint.set('Будет записано окно игры и звук игры. Микрофон не записывается.\nГлобальная клавиша F9: начать или остановить запись.\nПеред стартом будет 3-секундный отсчёт.')
        elif self.mode.get() == 'monitor':
            self.hint.set('Будет записан весь монитор в разрешении 1920×1200 и системный звук.\nГлобальная клавиша F9: начать или остановить запись.\nПеред стартом будет 3-секундный отсчёт.')
        else:
            self.hint.set('Будет записана центральная область 1920×1080 — только игра, без чёрных полос.\nГлобальная клавиша F9: начать или остановить запись.\nПеред стартом будет 3-секундный отсчёт.')

    def recap_command(self):
        exe = shutil.which('recap')
        if exe:
            return [exe]
        local = ROOT / '.venv' / 'Scripts' / 'recap.exe'
        if local.exists():
            return [str(local)]
        raise RuntimeError('Не найдена программа recap. Установи зависимости через install.bat.')

    def show_options(self):
        try:
            command = self.recap_command() + ['record', '--help']
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            text = (result.stdout or '') + '\n' + (result.stderr or '')
        except Exception as exc:
            text = str(exc)
        win = tk.Toplevel(self.window)
        win.title('Параметры recap')
        win.geometry('760x520')
        box = tk.Text(win, wrap='word')
        box.pack(fill='both', expand=True, padx=10, pady=10)
        box.insert('1.0', text)
        box.config(state='disabled')

    def toggle(self):
        if self.process and self.process.poll() is None:
            self.stop()
        else:
            self.start_countdown()

    def start_countdown(self):
        if self.process and self.process.poll() is not None and self.process is not None:
            pass
        if self.process and self.process.poll() is None:
            return
        self.window.withdraw()
        self.countdown(3)

    def countdown(self, seconds):
        if seconds <= 0:
            self.start()
            return
        self.notify('Запись через ' + str(seconds) + '...', 'Окно записи скрыто. Переключись в игру.')
        self.window.after(1000, lambda: self.countdown(seconds - 1))

    def start(self):
        if self.process and self.process.poll() is None:
            return
        title = self.title_var.get().strip()
        if self.mode.get() == 'window' and not title:
            self.window.deiconify()
            messagebox.showerror('Запись', 'Введите название окна игры.', parent=self.window)
            return
        try:
            command = self.recap_command()
        except Exception as exc:
            self.window.deiconify()
            messagebox.showerror('Запись', str(exc), parent=self.window)
            return
        RECORDINGS.mkdir(exist_ok=True)
        output = RECORDINGS / ('screen_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.mp4')
        if self.mode.get() == 'window':
            full = command + ['record', '--window-title', title, '--output', str(output)]
        elif self.mode.get() == 'monitor':
            full = command + ['record', '--output', str(output)]
        else:
            full = command + ['record', '--crop-size', '1920x1080', '--crop-position', 'middle', '--output', str(output)]
        try:
            self.process = subprocess.Popen(full, cwd=ROOT, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except Exception as exc:
            self.window.deiconify()
            messagebox.showerror('Запись', 'Не удалось начать запись:\n' + str(exc), parent=self.window)
            return
        self.status.set('ЗАПИСЬ: ' + output.name)
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.notify('Запись началась', 'Нажми F9, чтобы остановить запись.')

    def stop(self):
        if not self.process or self.process.poll() is not None:
            return
        try:
            self.process.terminate()
            self.process.wait(timeout=10)
        except Exception:
            try:
                self.process.kill()
            except Exception:
                pass
        self.process = None
        self.status.set('Запись завершена. Файл в папке recordings.')
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.window.deiconify()
        self.notify('Запись остановлена', 'Файл сохранён в папке recordings.')

    def notify(self, title, text):
        try:
            win = tk.Toplevel(self.window)
            win.overrideredirect(True)
            win.attributes('-topmost', True)
            width, height = 300, 100
            screen_w = self.window.winfo_screenwidth()
            screen_h = self.window.winfo_screenheight()
            win.geometry(f'{width}x{height}+{screen_w - width - 24}+{screen_h - height - 64}')
            frame = ttk.Frame(win, padding=12)
            frame.pack(fill='both', expand=True)
            ttk.Label(frame, text=title, font=('Segoe UI', 11, 'bold')).pack(anchor='w')
            ttk.Label(frame, text=text, wraplength=270).pack(anchor='w', pady=(4, 0))
            win.after(900, win.destroy)
        except Exception:
            pass

    def open_folder(self):
        RECORDINGS.mkdir(exist_ok=True)
        os.startfile(str(RECORDINGS))

    def close(self):
        if self.process and self.process.poll() is None:
            if not messagebox.askyesno('Запись', 'Идёт запись. Остановить и выйти?', parent=self.window):
                return
            self.stop()
        self.window.destroy()

    def run(self):
        self.window.mainloop()

if __name__ == '__main__':
    RecorderApp().run()
