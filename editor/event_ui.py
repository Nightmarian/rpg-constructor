import copy
import uuid
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import ImageTk
from editor.modal import wait
from editor.conditions import Condition, manage, label
from editor.assets_ui import choose
from editor.command_tree import CommandTree
from editor.graphics_ui import preview, edit as graphics
from editor.movement_ui import edit as movement
from project.schema import page, validate

def show(a, x, y):
    original = next((e for e in a.world.map['events'] if (e['x'], e['y']) == (x, y)), None)
    p = copy.deepcopy(a.project)
    event = copy.deepcopy(original) if original else dict(id='event_' + uuid.uuid4().hex[:10], name='Новое событие', x=x, y=y, pages=[page('Основное')])
    index = [0]
    photos = []
    w = tk.Toplevel(a.window)
    w.title(f'Событие ({x}, {y})')
    w.geometry('1100x760')
    w.minsize(960, 620)
    bottom = ttk.Frame(w, padding=6)
    bottom.pack(side='bottom', fill='x')
    top = ttk.Frame(w, padding=8)
    top.pack(fill='x')
    name = tk.StringVar(value=event.get('name', ''))
    ttk.Label(top, text='Название:').pack(side='left')
    ttk.Entry(top, textvariable=name, width=20).pack(side='left', padx=5)
    selector = ttk.Combobox(top, state='readonly', width=24)
    selector.pack(side='left', padx=5)
    body = ttk.Frame(w, padding=8)
    body.pack(fill='both', expand=True)
    left = ttk.Notebook(body, width=370)
    left.pack(side='left', fill='y', padx=(0, 8))
    general = ttk.Frame(left, padding=8)
    image = ttk.Frame(left, padding=8)
    left.add(general, text='Страница')
    left.add(image, text='Изображение')
    right = ttk.Frame(body)
    right.pack(side='left', fill='both', expand=True)
    general_actions = ttk.Frame(general)
    general_actions.pack(side='bottom', fill='x', pady=(4, 0))
    image_actions = ttk.Frame(image)
    image_actions.pack(side='bottom', fill='x', pady=(4, 0))
    pgname = tk.StringVar()
    ttk.Label(general, text='Название страницы').pack(anchor='w')
    ttk.Entry(general, textvariable=pgname).pack(fill='x', pady=2)
    condition = Condition(general, p)
    condition.frame.pack(fill='x', pady=3)
    trigger = tk.StringVar()
    ttk.Label(general, text='Запуск').pack(anchor='w')
    ttk.Combobox(general, textvariable=trigger, values=['Кнопка взаимодействия', 'Наступить на клетку'], state='readonly', width=30).pack(fill='x', pady=2)
    solid = tk.BooleanVar()
    ttk.Checkbutton(general, text='Событие преграждает путь', variable=solid).pack(anchor='w', pady=2)
    ttk.Label(general, text='Коллизии героя: меню «Сцена».', wraplength=320).pack(anchor='w', pady=1)
    move_label = tk.StringVar()
    ttk.Label(general, textvariable=move_label).pack(anchor='w', pady=2)
    graphic = tk.StringVar()
    ttk.Label(image, textvariable=graphic, wraplength=330).pack(pady=3)
    picture = ttk.Label(image)
    picture.pack(pady=3)
    tree = CommandTree(right, a, p)
    tree.frame.pack(fill='both', expand=True)

    def store():
        event['pages'][index[0]].update(name=pgname.get(), condition=condition.get(), trigger='action' if trigger.get() == 'Кнопка взаимодействия' else 'touch', solid=solid.get())

    def load():
        pg = event['pages'][index[0]]
        c = pg.get('condition', {})
        pgname.set(pg['name'])
        condition.switch.set(label(p, c.get('switch', '')))
        condition.value.set('ВКЛ' if c.get('value', True) else 'ВЫКЛ')
        condition.local.set(c.get('self', '') or '—')
        condition.local_value.set('ВКЛ' if c.get('self_value', True) else 'ВЫКЛ')
        condition.refresh()
        trigger.set('Кнопка взаимодействия' if pg['trigger'] == 'action' else 'Наступить на клетку')
        solid.set(pg.get('solid', False))
        key = pg['profile']
        spec = p['profiles'].get(key)
        graphic.set(spec['name'] + f"\nКадр {pg['frame'] + 1}, размер {spec['frame_size'][0]}×{spec['frame_size'][1]} px, масштаб {spec.get('scale', 1):g}" if spec else 'Без изображения')
        photo = ImageTk.PhotoImage(preview(p, pg, (180, 120)))
        photos[:] = [photo]
        picture.config(image=photo)
        move_label.set('Режим: ' + {'fixed': 'стоять', 'random': 'случайное блуждание', 'approach': 'к герою', 'route': 'по маршруту'}[pg.get('movement', {}).get('mode', 'fixed')])
        tree.set(pg['commands'])
        selector['values'] = [str(i + 1) + '. ' + v['name'] for i, v in enumerate(event['pages'])]
        selector.current(index[0])

    def select(e=None):
        store()
        index[0] = selector.current()
        load()
    selector.bind('<<ComboboxSelected>>', select)

    def pick():
        store()
        pg = event['pages'][index[0]]
        result = choose(a, p, pg['profile'], pg['direction'], pg['frame'])
        if result:
            pg['profile'], pg['direction'], pg['frame'] = result
        load()

    def size():
        store()
        key = event['pages'][index[0]]['profile']
        if key != 'none':
            graphics(a, p, key)
            load()

    def moves():
        store()
        movement(a, event['pages'][index[0]])
        load()

    def switches():
        manage(a, p)
        condition.refresh()
        tree.refresh()
    for parent, title, fn in [(image_actions, 'Выбрать изображение / кадр…', pick), (image_actions, 'Размер и точка опоры…', size), (general_actions, 'Движение NPC…', moves), (general_actions, 'Переключатели…', switches)]:
        ttk.Button(parent, text=title, command=fn).pack(fill='x', pady=2)

    def add(copy_page=False):
        store()
        event['pages'].append(copy.deepcopy(event['pages'][index[0]]) if copy_page else page('Новое состояние'))
        index[0] = len(event['pages']) - 1
        load()

    def remove():
        if len(event['pages']) == 1:
            messagebox.showinfo('Страница', 'Нужна хотя бы одна страница', parent=w)
            return
        if messagebox.askyesno('Удалить', 'Удалить страницу и команды?', parent=w):
            event['pages'].pop(index[0])
            index[0] = max(0, index[0] - 1)
            load()
    for title, fn in [('+ Страница', lambda: add()), ('Копия', lambda: add(True)), ('Удалить страницу', remove)]:
        ttk.Button(top, text=title, command=fn).pack(side='left', padx=3)

    def save():
        try:
            store()
            event['name'] = name.get()
            test = copy.deepcopy(p)
            events = test['maps'][a.world.map_id]['events']
            if original:
                events.remove(original)
            events.append(copy.deepcopy(event))
            validate(test)
            from engine.scene import Scene
            scene = Scene(a.root, test)
            a.project.clear()
            a.project.update(test)
            a.scene = scene
            a.invalidate()
            a.dirty = True
            w.destroy()
        except Exception as exc:
            a.log.exception('Save event')
            messagebox.showerror('Событие', str(exc), parent=w)

    def delete():
        if original and messagebox.askyesno('Удалить', 'Удалить событие целиком?', parent=w):
            a.world.map['events'].remove(original)
            a.dirty = True
            a.invalidate()
            w.destroy()
    for title, fn in [('Сохранить событие', save), ('Удалить событие', delete), ('Отмена', w.destroy)]:
        ttk.Button(bottom, text=title, command=fn).pack(side='left', padx=5)
    load()
    wait(a, w)
