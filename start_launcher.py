from pathlib import Path
import ctypes
import json
import subprocess
import sys
import tkinter as tk
from tkinter import ttk

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

def choose_mode():
    root = tk.Tk()
    root.title('Запуск игры')
    root.geometry('380x200')
    root.resizable(False, False)
    root.attributes('-topmost', True)
    choice = {'mode': None}
    ttk.Label(root, text='Как запустить игру?', font=('Segoe UI', 12, 'bold')).pack(pady=(18, 10))
    ttk.Label(root, text='Обычный запуск — без консоли.\nЗапуск с консолью — видны логи и ошибки.').pack()
    buttons = ttk.Frame(root)
    buttons.pack(pady=16)
    def normal():
        choice['mode'] = 'normal'
        root.destroy()
    def console():
        choice['mode'] = 'console'
        root.destroy()
    ttk.Button(buttons, text='Обычный запуск', command=normal).pack(side='left', padx=6)
    ttk.Button(buttons, text='Запуск с консолью', command=console).pack(side='left', padx=6)
    root.protocol('WM_DELETE_WINDOW', root.destroy)
    root.mainloop()
    return choice['mode']

def main():
    root = Path(__file__).resolve().parent
    if (root / '.update_incomplete').exists():
        print('Update is incomplete. Run the updater again into a new folder.')
        return 1
    scripts = root / '.venv' / 'Scripts'
    python = scripts / 'python.exe'
    pythonw = scripts / 'pythonw.exe'
    if python.is_file():
        exe = str(python)
    else:
        env = root / '_environment_090.json'
        exe = json.loads(env.read_text(encoding='utf-8'))['python'] if env.exists() else sys.executable
    if not Path(exe).is_file():
        print('Python environment not found. Run install.bat in this folder.')
        return 1
    mode = choose_mode()
    if mode is None:
        return 0
    if mode == 'normal' and pythonw.is_file():
        exe = str(pythonw)
    args = ['-m', 'unittest', 'discover', '-s', 'tests', '-v'] if '--tests' in sys.argv else [str(root / 'main.py')]
    process = subprocess.Popen([exe, *args], cwd=root)
    try:
        process.wait()
    except KeyboardInterrupt:
        process.terminate()
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
