import os
import shutil
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECORDINGS = ROOT / 'recordings'

class RecorderApp:
    def __init__(self):
        self.process = None
        self.window = tk.Tk()
        self.window.title('Запись игры')
        self.window.geometry('520x260')
        self.window.resizable(False, False)
        ttk.Label(self.window, text='Название окна игры').pack(anchor='w', padx=14, pady=(16, 3))
        self.title_var = tk.StringVar(value='Игра')
        ttk.Entry(self.window, textvariable=self.title_var, width=48).pack(fill='x', padx=14)
        ttk.Label(self.window, text='Будет записано видео окна и звук этого приложения. Микрофон не записывается.').pack(anchor='w', padx=14, pady=10)
        self.status = tk.StringVar(value='Готово к записи')
        ttk.Label(self.window, textvariable=self.status, anchor='w').pack(fill='x', padx=14)
        buttons = ttk.Frame(self.window)
        buttons.pack(fill='x', padx=14, pady=16)
        self.start_button = ttk.Button(buttons, text='Начать запись', command=self.start)
        self.start_button.pack(side='left', padx=(0, 6))
        self.stop_button = ttk.Button(buttons, text='Стоп', command=self.stop, state='disabled')
        self.stop_button.pack(side='left', padx=6)
        ttk.Button(buttons, text='Открыть папку', command=self.open_folder).pack(side='left', padx=6)
        self.window.protocol('WM_DELETE_WINDOW', self.close)

    def recap_command(self):
        exe = shutil.which('recap')
        if exe:
            return [exe]
        local = ROOT / '.venv' / 'Scripts' / 'recap.exe'
        if local.exists():
            return [str(local)]
        raise RuntimeError('Не найдена программа recap. Установи зависимости через install.bat.')

    def start(self):
        if self.process and self.process.poll() is None:
            return
        title = self.title_var.get().strip()
        if not title:
            messagebox.showerror('Запись', 'Введите название окна игры.', parent=self.window)
            return
        try:
            command = self.recap_command()
        except Exception as exc:
            messagebox.showerror('Запись', str(exc), parent=self.window)
            return
        RECORDINGS.mkdir(exist_ok=True)
        output = RECORDINGS / ('screen_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.mp4')
        full = command + ['record', '--window-title', title, '--output', str(output)]
        try:
            self.process = subprocess.Popen(full, cwd=ROOT, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except Exception as exc:
            messagebox.showerror('Запись', 'Не удалось начать запись:\n' + str(exc), parent=self.window)
            return
        self.status.set('ЗАПИСЬ: ' + output.name)
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')

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
