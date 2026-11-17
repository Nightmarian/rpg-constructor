import tkinter as tk
from tkinter import ttk

def build(a):
    menu = tk.Menu(a.window)
    a.window.config(menu=menu)
    groups = [('Файл', [('Новый тестовый проект', 'demo'), ('Открыть…', 'open'), ('Сохранить', 'save'), ('Сохранить как…', 'save_as'), ('Добавить локацию…', 'add_map'), ('Заменить фон…', 'background'), ('Выход', 'quit')]), ('Вид', [('Вписать карту', 'fit'), ('Настройки…', 'settings'), ('Журнал', 'log')]), ('Сцена', [('Просмотр / редактор', 'play'), ('Выбрать героя…', 'hero'), ('Общие переключатели…', 'switches'), ('Удалить выбранное событие', 'delete_event'), ('Сбросить исполнение', 'reset')]), ('Ресурсы', [('Добавить графику…', 'import')]), ('Запись', [('Начать исполнение', 'record'), ('Стоп', 'stop'), ('Экспорт MP4…', 'export'), ('Папка записей', 'videos')]), ('Справка', [('Инструкция', 'help'), ('Журналы', 'logs'), ('Тест ошибки', 'test')])]
    for text, items in groups:
        sub = tk.Menu(menu, tearoff=False)
        menu.add_cascade(label=text, menu=sub)
        for label, action in items:
            sub.add_command(label=label, command=lambda name=action: a.action(name))
        if text == 'Вид':
            sub.add_checkbutton(label='Сетка', variable=a.grid)
            sub.add_checkbutton(label='Разметка', variable=a.marks)
        if text == 'Сцена':
            sub.add_checkbutton(label='Проверять препятствия', variable=a.collisions)
    bar = ttk.Frame(a.window, padding=5)
    bar.pack(fill='x')
    for label, action in [('Открыть', 'open'), ('Сохранить', 'save'), ('Вписать', 'fit'), ('Настройки', 'settings'), ('Герой…', 'hero'), ('Просмотр', 'play'), ('Записать', 'record'), ('Стоп', 'stop'), ('MP4…', 'export')]:
        ttk.Button(bar, text=label, command=lambda name=action: a.action(name)).pack(side='left', padx=3)
    tools = ttk.Frame(a.window, padding=5)
    tools.pack(fill='x')
    a.map_var = tk.StringVar()
    a.map_box = ttk.Combobox(tools, textvariable=a.map_var, state='readonly', width=14)
    a.map_box.pack(side='left', padx=4)
    a.map_box.bind('<<ComboboxSelected>>', lambda e: a.choose_map())
    for text, value in [('Событие / выбор', 'event'), ('Преграда', 'block'), ('Стереть', 'erase'), ('Старт героя', 'spawn'), ('Простой рычаг', 'lever')]:
        ttk.Radiobutton(tools, text=text, variable=a.tool, value=value).pack(side='left', padx=4)
    ttk.Button(tools, text='Удалить событие', command=lambda: a.action('delete_event')).pack(side='left', padx=6)
