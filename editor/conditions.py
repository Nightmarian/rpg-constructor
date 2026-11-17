import tkinter as tk
from tkinter import ttk, simpledialog
from editor.modal import wait

def options(p):
    return ['— нет —'] + [key + ' — ' + name for key, name in p['switches'].items()]

def get_key(value):
    return '' if value == '— нет —' else value.split(' — ', 1)[0]

def label(p, key):
    return key + ' — ' + p['switches'][key] if key in p['switches'] else '— нет —'

class Condition:

    def __init__(self, parent, p, value=None):
        value = value or {}
        self.p = p
        self.frame = ttk.LabelFrame(parent, text='Условия страницы', padding=5)
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=0)
        self.switch = tk.StringVar(value=label(p, value.get('switch', '')))
        self.value = tk.StringVar(value='ВКЛ' if value.get('value', True) else 'ВЫКЛ')
        self.local = tk.StringVar(value=value.get('self', '') or '—')
        self.local_value = tk.StringVar(value='ВКЛ' if value.get('self_value', True) else 'ВЫКЛ')
        ttk.Label(self.frame, text='Общий переключатель').grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 2))
        self.box = ttk.Combobox(self.frame, textvariable=self.switch, values=options(p), state='readonly', width=1)
        self.box.grid(row=1, column=0, sticky='ew', padx=(0, 5))
        self.value_box = ttk.Combobox(self.frame, textvariable=self.value, values=['ВКЛ', 'ВЫКЛ'], state='readonly', width=6)
        self.value_box.grid(row=1, column=1, sticky='e')
        ttk.Label(self.frame, text='Локальный переключатель').grid(row=2, column=0, columnspan=2, sticky='w', pady=(5, 2))
        self.local_box = ttk.Combobox(self.frame, textvariable=self.local, values=['—', 'A', 'B', 'C', 'D'], state='readonly', width=1)
        self.local_box.grid(row=3, column=0, sticky='ew', padx=(0, 5))
        self.local_value_box = ttk.Combobox(self.frame, textvariable=self.local_value, values=['ВКЛ', 'ВЫКЛ'], state='readonly', width=6)
        self.local_value_box.grid(row=3, column=1, sticky='e')

    def get(self):
        return dict(switch=get_key(self.switch.get()), value=self.value.get() == 'ВКЛ', **{'self': '' if self.local.get() == '—' else self.local.get(), 'self_value': self.local_value.get() == 'ВКЛ'})

    def refresh(self):
        self.box['values'] = options(self.p)

def manage(a, p):
    w = tk.Toplevel(a.window)
    w.title('Общие переключатели')
    box = tk.Listbox(w, width=60, height=12)
    box.pack(padx=10, pady=10)

    def refresh():
        box.delete(0, 'end')
        [box.insert('end', item) for item in options(p)[1:]]

    def add():
        name = simpledialog.askstring('Переключатель', 'Понятное название:', parent=w)
        if name:
            n = 1
            while f'sw_{n:03}' in p['switches']:
                n += 1
            p['switches'][f'sw_{n:03}'] = name
            refresh()
        w.grab_set()

    def rename():
        if not box.curselection():
            return
        key = get_key(box.get(box.curselection()[0]))
        name = simpledialog.askstring('Название', 'Новое название:', initialvalue=p['switches'][key], parent=w)
        if name:
            p['switches'][key] = name
            refresh()
        w.grab_set()
    bar = ttk.Frame(w)
    bar.pack(pady=8)
    for text, fn in [('Добавить переключатель', add), ('Переименовать', rename), ('Закрыть', w.destroy)]:
        ttk.Button(bar, text=text, command=fn).pack(side='left', padx=5)
    refresh()
    wait(a, w)
