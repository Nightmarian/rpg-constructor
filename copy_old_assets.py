from pathlib import Path
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image

def main():
    root = Path(__file__).resolve().parent
    window = tk.Tk()
    window.withdraw()
    source = filedialog.askdirectory(title='Выберите папку старой 0.8.0 (где main.py)')
    if not source:
        return
    source = Path(source) / 'assets'
    names = ['hero_blue.png', 'hero_red.png', 'npc_green.png', 'npc_purple.png', 'lever_red.png', 'lever_brass.png', 'floor_button.png', 'room.png', 'kitchen.png']
    copied = []
    for name in names:
        src = source / name
        dst = root / 'assets' / name
        if not src.is_file() or src.resolve() == dst.resolve():
            continue
        with Image.open(src) as im:
            old_size = im.size
        with Image.open(dst) as im:
            new_size = im.size
        if old_size == new_size:
            shutil.copyfile(src, dst)
            copied.append(name)
    messagebox.showinfo('Ресурсы', 'Скопировано: ' + str(len(copied)) + ' файлов. Старые файлы не изменены.\nНовые двери и учебная карта сохранены.')
    window.destroy()
if __name__ == '__main__':
    main()
