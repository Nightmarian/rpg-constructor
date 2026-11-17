import copy
import hashlib
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import ImageFont
from project.schema import validate
from editor.modal import wait

def show(a):
    w = tk.Toplevel(a.window)
    w.title('Камера, шрифт и качество')
    values = {}
    font = [a.project.get('font', '')]
    fields = [('camera_zoom', 'Масштаб сцены', a.project['camera_zoom']), ('speed', 'Скорость px/с', a.project['speed']), ('animation_fps', 'Кадров анимации/с', a.project['animation_fps']), ('font_size', 'Размер текста', a.project['font_size']), ('width', 'Ширина MP4', a.project['output_size'][0]), ('height', 'Высота MP4', a.project['output_size'][1])]
    for row, (key, text, value) in enumerate(fields):
        ttk.Label(w, text=text).grid(row=row, column=0, padx=12, pady=6)
        var = tk.StringVar(value=str(value))
        values[key] = var
        ttk.Entry(w, textvariable=var).grid(row=row, column=1, padx=12, pady=6)
    quality = tk.StringVar(value=a.project['preview'])
    ttk.Label(w, text='Предпросмотр').grid(row=6, column=0)
    ttk.Combobox(w, textvariable=quality, values=['native', 'economy', '1080p'], state='readonly').grid(row=6, column=1, pady=6)

    def pick():
        path = filedialog.askopenfilename(parent=w, filetypes=[('Шрифты', '*.ttf *.otf')])
        if path:
            try:
                ImageFont.truetype(path, 22)
                font[0] = path
                label.set(path)
            except Exception as exc:
                messagebox.showerror('Шрифт', str(exc), parent=w)
    label = tk.StringVar(value=font[0] or 'DejaVuSans')
    ttk.Label(w, textvariable=label, wraplength=440).grid(row=7, column=0, columnspan=2, pady=8)
    ttk.Button(w, text='Выбрать шрифт…', command=pick).grid(row=8, column=0)
    ttk.Button(w, text='Сбросить шрифт', command=lambda: (font.__setitem__(0, ''), label.set('DejaVuSans'))).grid(row=8, column=1)

    def save():
        try:
            p = copy.deepcopy(a.project)
            for key in ('camera_zoom', 'speed', 'animation_fps'):
                p[key] = float(values[key].get().replace(',', '.'))
            p.update(font_size=int(values['font_size'].get()), output_size=[int(values['width'].get()), int(values['height'].get())], preview=quality.get())
            validate(p)
            if font[0]:
                from pathlib import Path
                src = Path(font[0])
                dest = a.root / 'assets' / 'imported' / ('font_' + hashlib.sha256(src.read_bytes()).hexdigest()[:12] + src.suffix.lower())
                dest.parent.mkdir(exist_ok=True)
                if src.resolve() != dest.resolve():
                    shutil.copyfile(src, dest)
                p['font'] = str(dest.resolve())
            else:
                p['font'] = ''
            a.project.clear()
            a.project.update(p)
            a.dirty = True
            a.reload_scene()
            w.destroy()
        except Exception as exc:
            messagebox.showerror('Настройки', str(exc), parent=w)
    ttk.Label(w, text='native — чётко по окну; economy — 960×540; 1080p — ограничение.\nВидео: 16:9, чётные размеры до 3840×2160, 30 fps, без звука.').grid(row=9, column=0, columnspan=2, padx=10, pady=8)
    ttk.Button(w, text='Применить', command=save).grid(row=10, column=0, pady=10)
    ttk.Button(w, text='Отмена', command=w.destroy).grid(row=10, column=1, pady=10)
    wait(a, w)
