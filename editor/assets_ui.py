import uuid
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from editor.modal import wait
from engine.resources import Resources

def import_image(a, p):
    source = filedialog.askopenfilename(parent=a.window, title='Один рисунок или лист PNG', filetypes=[('Изображения', '*.png *.webp *.jpg *.jpeg *.bmp')])
    if not source:
        return
    image = Image.open(source).convert('RGBA')
    w = tk.Toplevel(a.window)
    w.title('Добавить графику')
    values = {}
    mode = tk.StringVar(value='Статичный персонаж')
    ttk.Combobox(w, textvariable=mode, values=['Статичный персонаж', 'Персонаж: 4 строки ↓ ← → ↑', 'Объект: кадры в одной строке'], state='readonly', width=42).grid(row=0, column=0, columnspan=2, padx=10, pady=8)
    fields = [('name', 'Название', 'Моя графика'), ('fw', 'Ширина кадра', image.width), ('fh', 'Высота кадра', image.height), ('counts', 'Кадров по строкам (через запятую)', '1,1,1,1'), ('ax', 'Опора X (пусто = центр)', ''), ('ay', 'Опора Y (пусто = низ)', '')]
    for row, (key, text, value) in enumerate(fields, 1):
        ttk.Label(w, text=text).grid(row=row, column=0, sticky='w', padx=10, pady=5)
        v = tk.StringVar(value=str(value))
        values[key] = v
        ttk.Entry(w, textvariable=v, width=25).grid(row=row, column=1, padx=10, pady=5)
    ttk.Label(w, text='Для объекта: один PNG, состояния слева направо.\nНапример два кадра 96×112: лист 192×112, количество 2.').grid(row=7, column=0, columnspan=2, pady=8)

    def save():
        try:
            static = mode.get() == 'Статичный персонаж'
            obj = mode.get().startswith('Объект')
            name = values['name'].get().strip()
            if not name:
                raise ValueError('Введите название')
            if static:
                fw, fh = image.size
                counts = [1] * 4
                sheet = Image.new('RGBA', (fw, fh * 4))
                for row in range(4):
                    sheet.paste(image, (0, row * fh))
            else:
                fw = int(values['fw'].get())
                fh = int(values['fh'].get())
                counts = [int(v.strip()) for v in values['counts'].get().split(',')]
                sheet = image
                if obj:
                    counts = counts[:1]
                if len(counts) != (1 if obj else 4) or min(counts) < 1 or fw < 1 or (fh < 1) or (max(counts) * fw > image.width) or (len(counts) * fh > image.height):
                    raise ValueError('Лист не соответствует размерам/числу кадров')
            ax = int(values['ax'].get()) if values['ax'].get().strip() else fw // 2
            ay = int(values['ay'].get()) if values['ay'].get().strip() else fh
            if not (0 <= ax <= fw and 0 <= ay <= fh):
                raise ValueError('Опора за пределами кадра')
            key = 'custom_' + uuid.uuid4().hex[:12]
            folder = a.root / 'assets' / 'imported'
            folder.mkdir(exist_ok=True)
            dest = folder / (key + '.png')
            sheet.save(dest)
            p['profiles'][key] = dict(name=name, kind='object' if obj else 'character', file=str(dest.resolve()), frame_size=[fw, fh], counts=counts, anchor=[ax, ay])
            a.dirty = True
            w.destroy()
        except Exception as exc:
            a.log.exception('Import graphic')
            messagebox.showerror('Импорт', str(exc), parent=w)
    ttk.Button(w, text='Добавить', command=save).grid(row=8, column=0, pady=10)
    ttk.Button(w, text='Отмена', command=w.destroy).grid(row=8, column=1, pady=10)
    wait(a, w)

def choose(a, p, current='none', direction=0, frame=0, characters_only=False):
    w = tk.Toplevel(a.window)
    w.title('Изображение и кадр')
    w.geometry('840x620')
    result = [None]
    photos = []
    top = ttk.Frame(w, padding=8)
    top.pack(fill='x')
    left = ttk.Frame(w, padding=8)
    left.pack(side='left', fill='y')
    box = tk.Listbox(left, width=28, height=22, exportselection=False)
    box.pack(fill='both', expand=True)
    right = ttk.Frame(w, padding=8)
    right.pack(side='left', fill='both', expand=True)
    caption = ttk.Label(right, text='Выберите графику, затем щёлкните кадр')
    caption.pack()
    canvas = tk.Canvas(right, bg='#30343c', width=500, height=450)
    canvas.pack(fill='both', expand=True)
    keys = []
    rects = []
    selection = [current, direction, frame]

    def display(*_):
        if not box.curselection():
            return
        key = keys[box.curselection()[0]]
        selection[0] = key
        canvas.delete('all')
        photos.clear()
        rects.clear()
        if key == 'none':
            return
        spec = p['profiles'][key]
        sheet = Image.open(spec['file']).convert('RGBA')
        fw, fh = spec['frame_size']
        rows = spec['counts']
        scale = min(1.8, 470 / max(1, sheet.width), 420 / max(1, sheet.height))
        sw = max(1, round(sheet.width * scale))
        sh = max(1, round(sheet.height * scale))
        photo = ImageTk.PhotoImage(sheet.resize((sw, sh), Image.Resampling.NEAREST))
        photos.append(photo)
        canvas.create_image(0, 0, anchor='nw', image=photo)
        for row, count in enumerate(rows):
            for col in range(count):
                bounds = (col * fw * scale, row * fh * scale, (col + 1) * fw * scale, (row + 1) * fh * scale)
                rects.append((bounds, row, col))
                chosen = row == selection[1] and col == selection[2]
                canvas.create_rectangle(*bounds, outline='#ffd35e' if chosen else '#7f96ae', width=3 if chosen else 1)
        caption.config(text=spec['name'] + ' — щёлкните нужный кадр')

    def refresh():
        keys.clear()
        box.delete(0, 'end')
        if not characters_only:
            keys.append('none')
            box.insert('end', 'Без изображения')
        for key, spec in p['profiles'].items():
            if not characters_only or spec['kind'] == 'character':
                keys.append(key)
                box.insert('end', spec['name'])
        index = keys.index(selection[0]) if selection[0] in keys else 0
        box.selection_set(index)
        display()

    def click(e):
        for bounds, row, col in rects:
            if bounds[0] <= e.x < bounds[2] and bounds[1] <= e.y < bounds[3]:
                selection[1] = row if p['profiles'][selection[0]]['kind'] == 'character' else 0
                selection[2] = col
                display()
                break

    def add():
        import_image(a, p)
        refresh()
        w.grab_set()

    def save():
        key = selection[0]
        if key != 'none':
            spec = p['profiles'][key]
            selection[1] = min(selection[1], len(spec['counts']) - 1)
            selection[2] = min(selection[2], spec['counts'][selection[1]] - 1)
        result[0] = tuple(selection)
        w.destroy()
    ttk.Button(top, text='Добавить свою графику…', command=add).pack(side='left')
    ttk.Button(top, text='Выбрать', command=save).pack(side='right')
    ttk.Button(top, text='Отмена', command=w.destroy).pack(side='right', padx=8)
    box.bind('<<ListboxSelect>>', display)
    canvas.bind('<Button-1>', click)
    refresh()
    wait(a, w)
    return result[0]
