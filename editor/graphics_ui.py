import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageDraw, ImageTk
from editor.modal import wait
from editor.scroll_panel import ScrollPanel, fit_dialog
from engine.thumbnail import preview

def edit(a, p, key):
    s = p['profiles'][key]
    w = tk.Toplevel(a.window)
    w.title('Размер и опора ресурса')
    fit_dialog(w, 620, 600)
    footer = ttk.Frame(w, padding=8)
    footer.pack(side='bottom', fill='x')
    scroll = ScrollPanel(w)
    scroll.pack(fill='both', expand=True)
    content = scroll.content
    vars = {}
    fw, fh = s['frame_size']
    ttk.Label(content, text=s['name'] + f' — кадр {fw}×{fh} px\nНастройки общие для всех событий с этим ресурсом.').pack(padx=15, pady=10)
    for name, title, value in [('scale', 'Масштаб (1 = исходный)', s.get('scale', 1)), ('x', 'Точка опоры X', s['anchor'][0]), ('y', 'Точка опоры Y', s['anchor'][1])]:
        f = ttk.Frame(content, padding=5)
        f.pack(fill='x')
        ttk.Label(f, text=title, width=26).pack(side='left')
        v = tk.StringVar(value=str(value))
        vars[name] = v
        ttk.Entry(f, textvariable=v).pack(side='left')
    canvas = tk.Canvas(content, width=300, height=250, bg='#303643')
    canvas.pack(padx=10, pady=8)
    photos = []

    def values():
        import math
        scale = float(vars['scale'].get().replace(',', '.'))
        x = float(vars['x'].get().replace(',', '.'))
        y = float(vars['y'].get().replace(',', '.'))
        if not math.isfinite(scale + x + y) or not (0.1 <= scale <= 8 and 0 <= x <= fw and (0 <= y <= fh)):
            raise ValueError('Масштаб 0.1–8; опора внутри кадра')
        return (scale, x, y)

    def draw():
        try:
            scale, x, y = values()
            with Image.open(s['file']) as sheet:
                im = sheet.convert('RGBA').crop((0, 0, fw, fh))
            z = min(280 / fw, 220 / fh)
            im = im.resize((max(1, round(fw * z)), max(1, round(fh * z))), Image.Resampling.NEAREST)
            photo = ImageTk.PhotoImage(im)
            photos[:] = [photo]
            canvas.delete('all')
            canvas.create_image(10, 10, anchor='nw', image=photo)
            cx = 10 + x * z
            cy = 10 + y * z
            canvas.create_line(cx - 8, cy, cx + 8, cy, fill='#ffcf55', width=3)
            canvas.create_line(cx, cy - 8, cx, cy + 8, fill='#ffcf55', width=3)
            label.config(text=f'На карте: {round(fw * scale)} × {round(fh * scale)} px')
        except ValueError:
            pass

    def click(e):
        vars['x'].set(round(max(0, min(fw, (e.x - 10) / min(280 / fw, 220 / fh)))))
        vars['y'].set(round(max(0, min(fh, (e.y - 10) / min(280 / fw, 220 / fh)))))
        draw()
    canvas.bind('<Button-1>', click)
    label = ttk.Label(content)
    label.pack()

    def save():
        try:
            scale, x, y = values()
            s.update(scale=scale, anchor=[x, y])
            w.destroy()
        except ValueError as exc:
            messagebox.showerror('Размер', str(exc), parent=w)
    for var in vars.values():
        var.trace_add('write', lambda *_: draw())
    ttk.Button(footer, text='Применить', command=save).pack(pady=10)
    draw()
    wait(a, w)
