import tkinter as tk
from tkinter import ttk
from engine.passage import VECTORS, OPPOSITE

def toolbar(a):
    bar = ttk.Frame(a.window, padding=4)
    bar.pack(fill='x')
    ttk.Radiobutton(bar, text='Проходимость', variable=a.tool, value='edge').pack(side='left', padx=5)
    a.edge_direction = tk.StringVar(value='Вправо →')
    ttk.Combobox(bar, textvariable=a.edge_direction, values=['Вниз ↓', 'Влево ←', 'Вправо →', 'Вверх ↑'], state='readonly', width=12).pack(side='left', padx=5)
    a.edge_mode = tk.StringVar(value='Стена в обе стороны')
    ttk.Combobox(bar, textvariable=a.edge_mode, values=['Стена в обе стороны', 'Запрет выхода в одну сторону'], state='readonly', width=29).pack(side='left', padx=5)
    ttk.Label(a.window, text='Разметка: красное × — клетка закрыта; красная линия — стена; зелёная стрелка — разрешённое направление; оранжевое — твёрдое событие.').pack(fill='x', padx=8)
    ttk.Radiobutton(bar, text='Дверь…', variable=a.tool, value='door').pack(side='left', padx=8)
    ttk.Button(bar, text='Размер героя…', command=lambda: a.action('hero_size')).pack(side='right')
    from editor.free_edges import add_toolbar
    add_toolbar(a)

def paint(a, x, y, erase):
    direction = ['Вниз ↓', 'Влево ←', 'Вправо →', 'Вверх ↑'].index(a.edge_direction.get())
    m = a.world.map
    edges = m.setdefault('edges', [])
    targets = [[x, y, direction]]
    if a.edge_mode.get() == 'Стена в обе стороны':
        dx, dy = VECTORS[direction]
        nx = x + dx
        ny = y + dy
        if 0 <= nx < m['width'] and 0 <= ny < m['height']:
            targets.append([nx, ny, OPPOSITE[direction]])
    for edge in targets:
        if erase:
            if edge in edges:
                edges.remove(edge)
        elif edge not in edges:
            edges.append(edge)
    a.dirty = True
    a.invalidate()
