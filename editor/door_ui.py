import copy
import json
import uuid
import tkinter as tk
from tkinter import ttk, messagebox
from editor.modal import wait
from editor.conditions import options, get_key
from project.schema import page, validate

def create(a, x, y):
    if any(((e['x'], e['y']) == (x, y) for e in a.world.map['events'])):
        messagebox.showinfo('Дверь', 'Клетка занята событием', parent=a.window)
        return
    p = copy.deepcopy(a.project)
    w = tk.Toplevel(a.window)
    w.title('Поставить дверь')
    v = {}

    def row(key, title, value, choices=None):
        f = ttk.Frame(w, padding=6)
        f.pack(fill='x')
        ttk.Label(f, text=title, width=23).pack(side='left')
        var = tk.StringVar(value=str(value))
        v[key] = var
        widget = ttk.Combobox(f, textvariable=var, values=choices, state='readonly', width=36) if choices is not None else ttk.Entry(f, textvariable=var, width=39)
        widget.pack(side='left')
    row('name', 'Название', 'Дверь')
    row('kind', 'Тип', 'Дверь по переключателю', ['Обычный переход', 'Дверь по переключателю', 'Открыть без перехода'])
    row('switch', 'Общий переключатель', '— нет —', options(p))
    row('target', 'Куда ведёт', a.world.map_id, list(p['maps']))
    row('tx', 'Клетка X', 1)
    row('ty', 'Клетка Y', 1)
    row('locked', 'Если закрыто', 'Заперто.')
    ttk.Label(w, text='Переключатель создайте заранее: Сцена → Общие переключатели.\nМастер создаёт обычные страницы и команды.').pack(padx=10, pady=10)

    def save():
        try:
            kind = v['kind'].get()
            flag = get_key(v['switch'].get())
            target = v['target'].get()
            tx = int(v['tx'].get())
            ty = int(v['ty'].get())
            if kind == 'Дверь по переключателю' and (not flag):
                raise ValueError('Выберите общий переключатель от рычага')
            if kind != 'Открыть без перехода' and (not (0 <= tx < p['maps'][target]['width'] and 0 <= ty < p['maps'][target]['height'])):
                raise ValueError('Точка появления вне карты')
            manifest = json.loads((a.root / 'assets' / 'profiles.json').read_text(encoding='utf-8'))
            spec = manifest['door_wood']
            spec['file'] = str((a.root / 'assets' / spec['file']).resolve())
            p['profiles'].setdefault('door_wood', spec)
            transfer = dict(type='transfer', target=target, tx=tx, ty=ty, direction=0)
            if kind == 'Обычный переход':
                pages = [page('Вход', 'door_wood', 1, [transfer])]
            elif kind == 'Дверь по переключателю':
                closed = page('Заперто', 'door_wood', 0, [dict(type='text', name='', text=v['locked'].get())])
                closed['solid'] = True
                opened = page('Открыто', 'door_wood', 1, [transfer], dict(switch=flag, value=True))
                opened['solid'] = False
                pages = [closed, opened]
            else:
                closed = page('Закрыто', 'door_wood', 0, [dict(type='self_switch', flag='A', operation='on')])
                closed['solid'] = True
                opened = page('Открыто', 'door_wood', 1, [dict(type='self_switch', flag='A', operation='off')], {'self': 'A', 'self_value': True})
                opened['solid'] = False
                pages = [closed, opened]
            event = dict(id='door_' + uuid.uuid4().hex[:10], name=v['name'].get() or 'Дверь', x=x, y=y, pages=pages)
            p['maps'][a.world.map_id]['events'].append(event)
            validate(p)
            from engine.scene import Scene
            scene = Scene(a.root, p)
            a.project.clear()
            a.project.update(p)
            a.scene = scene
            a.dirty = True
            a.invalidate()
            w.destroy()
        except Exception as exc:
            a.log.exception('Create door')
            messagebox.showerror('Дверь', str(exc), parent=w)
    bar = ttk.Frame(w, padding=10)
    bar.pack()
    ttk.Button(bar, text='Поставить дверь', command=save).pack(side='left')
    ttk.Button(bar, text='Отмена', command=w.destroy).pack(side='left', padx=8)
    wait(a, w)
