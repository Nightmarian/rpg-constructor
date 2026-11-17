import uuid
from tkinter import simpledialog, messagebox
from project.schema import page
from editor.assets_ui import choose

def lever(a, x, y):
    if any(((e['x'], e['y']) == (x, y) for e in a.world.map['events'])):
        messagebox.showinfo('Клетка занята', 'Сначала удалите или измените существующее событие.', parent=a.window)
        return
    name = simpledialog.askstring('Простой рычаг', 'Название рычага:', initialvalue='Доступ на кухню', parent=a.window)
    if not name:
        return
    result = choose(a, a.project, 'lever_red', 0, 0)
    if not result:
        return
    profile, _, _ = result
    spec = a.project['profiles'].get(profile)
    if not spec or spec['kind'] != 'object' or spec['counts'][0] < 2:
        messagebox.showerror('Два состояния', 'Выберите объект с двумя кадрами в одном PNG.', parent=a.window)
        return
    flag = 'sw_' + uuid.uuid4().hex[:10]
    a.project['switches'][flag] = name
    off = page('Выключен', profile, 0, [dict(type='switch', flag=flag, operation='on')])
    on = page('Включён', profile, 1, [dict(type='switch', flag=flag, operation='off')], dict(switch=flag, value=True))
    a.world.map['events'].append(dict(id='event_' + uuid.uuid4().hex[:10], name=name, x=x, y=y, pages=[off, on]))
    a.dirty = True
    a.reload_scene()
    a.invalidate()
