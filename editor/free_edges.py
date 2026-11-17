from tkinter import ttk
from editor.edge_edit import closest_edge, set_wall

def add_toolbar(a):
    bar = ttk.Frame(a.window, padding=(4, 0, 4, 3))
    bar.pack(fill='x')
    ttk.Radiobutton(bar, text='Свободные границы', variable=a.tool, value='edge_free').pack(side='left', padx=5)
    ttk.Label(bar, text='Ближе к краю клетки: ЛКМ — поставить стену, ПКМ — убрать. Любое сочетание сторон.', wraplength=760).pack(side='left', padx=6)

def paint_free(a, x, y, erase=False):
    edge = closest_edge(a.world.map, x, y)
    if edge is None:
        return
    cx, cy, direction = edge
    changed = set_wall(a.world.map, cx, cy, direction, not erase)
    if changed:
        a.dirty = True
        a.invalidate()
    a.status.set(f'Граница ({cx}, {cy}), {['низ', 'лево', 'право', 'верх'][direction]}: ' + ('открыта' if erase else 'стена'))
