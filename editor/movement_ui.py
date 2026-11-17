import copy
import math
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from editor.modal import wait
MODES = {'Стоять': 'fixed', 'Случайное блуждание': 'random', 'Подходить к герою': 'approach', 'По маршруту': 'route'}
OPS = {'Шаг вверх': 'up', 'Шаг вниз': 'down', 'Шаг влево': 'left', 'Шаг вправо': 'right', 'Случайный шаг': 'random_step', 'Подождать': 'wait', 'Случайная пауза': 'random_wait', 'Повернуться': 'turn'}

def edit(a, page):
    cfg = copy.deepcopy(page.get('movement', {}))
    route = cfg.get('route', [])
    w = tk.Toplevel(a.window)
    w.title('Движение NPC')
    width = min(640, max(520, w.winfo_screenwidth() - 100))
    height = min(600, max(420, w.winfo_screenheight() - 160))
    w.geometry(f'{width}x{height}')
    w.minsize(520, 420)
    w.columnconfigure(0, weight=1)
    w.rowconfigure(1, weight=1)
    form = ttk.Frame(w, padding=8)
    form.grid(row=0, column=0, sticky='ew')
    form.columnconfigure(1, weight=1)
    values = {}
    fields = [('mode', 'Движение', next((k for k, v in MODES.items() if v == cfg.get('mode', 'fixed'))), list(MODES)), ('speed', 'Скорость, px/с', cfg.get('speed', 100), None), ('delay', 'Пауза между шагами, с', cfg.get('delay', 0.3), None), ('radius', 'Радиус блуждания, клеток', cfg.get('radius', 3), None)]
    for row, (key, title, value, choices) in enumerate(fields):
        ttk.Label(form, text=title).grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        var = tk.StringVar(value=str(value))
        values[key] = var
        widget = ttk.Combobox(form, textvariable=var, values=choices, state='readonly') if choices else ttk.Entry(form, textvariable=var)
        widget.grid(row=row, column=1, sticky='ew', pady=2)
    repeat = tk.BooleanVar(value=cfg.get('repeat', True))
    ttk.Checkbutton(form, text='Повторять маршрут', variable=repeat).grid(row=4, column=0, columnspan=2, sticky='w', pady=3)
    area = ttk.Frame(w, padding=(8, 0))
    area.grid(row=1, column=0, sticky='nsew')
    area.columnconfigure(0, weight=1)
    area.rowconfigure(0, weight=1)
    box = tk.Listbox(area, height=6, exportselection=False)
    box.grid(row=0, column=0, sticky='nsew')
    scroll = ttk.Scrollbar(area, orient='vertical', command=box.yview)
    scroll.grid(row=0, column=1, sticky='ns')
    box.configure(yscrollcommand=scroll.set)

    def refresh():
        box.delete(0, 'end')
        for i, c in enumerate(route):
            title = next((k for k, v in OPS.items() if v == c['op']))
            if c['op'] == 'wait':
                title += ': ' + str(c.get('seconds', 1)) + ' с'
            elif c['op'] == 'random_wait':
                title += f': {c.get('min_seconds', 1)}–{c.get('max_seconds', 3)} с'
            elif c['op'] == 'turn':
                title += ' ' + ['↓', '←', '→', '↑'][c.get('direction', 0)]
            box.insert('end', str(i + 1) + '. ' + title)
    controls = ttk.Frame(w, padding=8)
    controls.grid(row=2, column=0, sticky='ew')
    controls.columnconfigure(0, weight=1)
    op = tk.StringVar(value='Шаг вверх')
    ttk.Combobox(controls, textvariable=op, values=list(OPS), state='readonly').grid(row=0, column=0, sticky='ew', padx=(0, 6))

    def add():
        c = {'op': OPS[op.get()]}
        try:
            if c['op'] == 'wait':
                value = simpledialog.askfloat('Ожидание', 'Секунд (0–60):', minvalue=0, maxvalue=60, parent=w)
                if value is None:
                    return
                c['seconds'] = value
            elif c['op'] == 'random_wait':
                lo = simpledialog.askfloat('Случайная пауза', 'Минимум секунд (0–60):', initialvalue=1, minvalue=0, maxvalue=60, parent=w)
                if lo is None:
                    return
                hi = simpledialog.askfloat('Случайная пауза', 'Максимум секунд:', initialvalue=max(lo, 3), minvalue=lo, maxvalue=60, parent=w)
                if hi is None:
                    return
                c.update(min_seconds=lo, max_seconds=hi)
            elif c['op'] == 'turn':
                direction = simpledialog.askinteger('Поворот', '0 вниз / 1 влево / 2 вправо / 3 вверх', minvalue=0, maxvalue=3, parent=w)
                if direction is None:
                    return
                c['direction'] = direction
            route.append(c)
            refresh()
        finally:
            if w.winfo_exists():
                w.grab_set()

    def remove():
        if box.curselection():
            route.pop(box.curselection()[0])
            refresh()

    def move(delta):
        if box.curselection():
            i = box.curselection()[0]
            j = i + delta
            if 0 <= j < len(route):
                route[i], route[j] = (route[j], route[i])
                refresh()
                box.selection_set(j)
    ttk.Button(controls, text='Добавить', command=add).grid(row=0, column=1, sticky='ew')
    buttons = ttk.Frame(controls)
    buttons.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(4, 0))
    for col, (title, fn) in enumerate([('Удалить', remove), ('Выше', lambda: move(-1)), ('Ниже', lambda: move(1))]):
        buttons.columnconfigure(col, weight=1)
        ttk.Button(buttons, text=title, command=fn).grid(row=0, column=col, sticky='ew', padx=2)
    footer = ttk.Frame(w, padding=(8, 0, 8, 8))
    footer.grid(row=3, column=0, sticky='ew')

    def save():
        try:
            speed = float(values['speed'].get().replace(',', '.'))
            delay = float(values['delay'].get().replace(',', '.'))
            radius = int(values['radius'].get())
            if not math.isfinite(speed + delay) or not (1 <= speed <= 2000 and 0 <= delay <= 60 and (1 <= radius <= 100)):
                raise ValueError('Проверьте скорость, паузу и радиус')
            updated = dict(cfg)
            updated.update(mode=MODES[values['mode'].get()], speed=speed, delay=delay, radius=radius, repeat=repeat.get(), route=route)
            page['movement'] = updated
            w.destroy()
        except ValueError as exc:
            messagebox.showerror('Движение', str(exc), parent=w)
    ttk.Button(footer, text='Применить', command=save).pack(side='left', padx=(0, 6))
    ttk.Button(footer, text='Отмена', command=w.destroy).pack(side='left')
    refresh()
    wait(a, w)
