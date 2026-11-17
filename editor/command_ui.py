import copy
import tkinter as tk
from tkinter import ttk, messagebox
from editor.modal import wait
from editor.scroll_panel import ScrollPanel, fit_dialog
from editor.conditions import Condition, options, get_key, label
TYPES = {'Показать текст': 'text', 'Общий переключатель': 'switch', 'Локальный переключатель': 'self_switch', 'Перейти на локацию': 'transfer', 'Если / Иначе': 'if', 'Комментарий': 'comment', 'Разделитель': 'separator'}

def edit(a, p, old=None):
    c = copy.deepcopy(old) if old else dict(type='text', name='', text='')
    result = [None]
    w = tk.Toplevel(a.window)
    w.title('Команда')
    fit_dialog(w, 760, 600)
    footer = ttk.Frame(w, padding=8)
    footer.pack(side='bottom', fill='x')
    kind = tk.StringVar(value=next((k for k, v in TYPES.items() if v == c['type'])))
    ttk.Combobox(w, textvariable=kind, values=list(TYPES), state='readonly', width=40).pack(padx=10, pady=8)
    scroll = ScrollPanel(w)
    scroll.pack(fill='both', expand=True)
    body = scroll.content
    values = {}
    extra = [None]

    def field(row, key, text, value, choices=None):
        ttk.Label(body, text=text).grid(row=row, column=0, sticky='w', pady=6)
        var = tk.StringVar(value=str(value))
        values[key] = var
        widget = ttk.Combobox(body, textvariable=var, values=choices, state='readonly', width=38) if choices is not None else ttk.Entry(body, textvariable=var, width=41)
        widget.grid(row=row, column=1, pady=6)

    def rebuild(*_):
        for child in body.winfo_children():
            child.destroy()
        values.clear()
        extra[0] = None
        scroll.canvas.yview_moveto(0)
        t = TYPES[kind.get()]
        if t in ('text', 'comment'):
            field(0, 'name', 'Имя', c.get('name', ''))
            text = tk.Text(body, width=65, height=12, wrap='word', font=('Segoe UI', 11))
            text.grid(row=1, column=0, columnspan=2)
            text.insert('1.0', c.get('text', ''))
            extra[0] = text
        elif t == 'separator':
            ttk.Label(body, text='Визуальная разделительная строка. Ничего не выполняет.').pack(pady=12)
        elif t in ('switch', 'self_switch'):
            choices = options(p)[1:] if t == 'switch' else ['A', 'B', 'C', 'D']
            value = label(p, c.get('flag', '')) if t == 'switch' else c.get('flag', 'A')
            field(0, 'flag', 'Переключатель', value if value in choices else choices[0] if choices else '', choices)
            field(1, 'operation', 'Действие', {'on': 'Включить', 'off': 'Выключить', 'toggle': 'Переключить'}.get(c.get('operation'), 'Включить'), ['Включить', 'Выключить', 'Переключить'])
        elif t == 'transfer':
            field(0, 'target', 'Карта', c.get('target', a.world.map_id), list(p['maps']))
            field(1, 'tx', 'Клетка X', c.get('tx', 1))
            field(2, 'ty', 'Клетка Y', c.get('ty', 1))
            field(3, 'direction', 'Направление 0↓1←2→3↑', c.get('direction', 0), ['0', '1', '2', '3'])
            field(4, 'fade', 'Переход', 'Затемнение' if c.get('fade', True) else 'Без эффекта', ['Затемнение', 'Без эффекта'])
        else:
            cond = Condition(body, p, c.get('condition', {}))
            cond.frame.pack()
            extra[0] = cond
    kind.trace_add('write', rebuild)
    rebuild()

    def save():
        try:
            t = TYPES[kind.get()]
            n = dict(type=t)
            if t in ('text', 'comment'):
                n.update(name=values['name'].get(), text=extra[0].get('1.0', 'end-1c'))
            elif t == 'separator':
                pass
            elif t in ('switch', 'self_switch'):
                flag = get_key(values['flag'].get()) if t == 'switch' else values['flag'].get()
                if not flag:
                    raise ValueError('Сначала создайте переключатель кнопкой в редакторе события')
                n.update(flag=flag, operation={'Включить': 'on', 'Выключить': 'off', 'Переключить': 'toggle'}[values['operation'].get()])
            elif t == 'transfer':
                n.update(target=values['target'].get(), tx=int(values['tx'].get()), ty=int(values['ty'].get()), direction=int(values['direction'].get()))
                n['fade'] = values['fade'].get() == 'Затемнение'
                m = p['maps'][n['target']]
                if not (0 <= n['tx'] < m['width'] and 0 <= n['ty'] < m['height']):
                    raise ValueError('Точка вне карты')
            else:
                n.update(condition=extra[0].get(), then=copy.deepcopy(c.get('then', [])), **{'else': copy.deepcopy(c.get('else', []))})
            result[0] = n
            w.destroy()
        except Exception as exc:
            messagebox.showerror('Команда', str(exc), parent=w)
    ttk.Button(footer, text='ОК', command=save).pack(side='left')
    ttk.Button(footer, text='Отмена', command=w.destroy).pack(side='right')
    wait(a, w)
    return result[0]
