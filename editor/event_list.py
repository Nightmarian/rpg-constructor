import tkinter as tk
from tkinter import ttk
from PIL import ImageTk
from project.schema import active_page
from editor.graphics_ui import preview
from editor.event_ui import show

class EventList:

    def __init__(self, a, parent):
        self.a = a
        self.photos = []
        self.lookup = {}
        self.frame = ttk.Frame(parent, width=240, padding=6)
        self.frame.pack(side='left', fill='y')
        self.frame.pack_propagate(False)
        ttk.Label(self.frame, text='События текущей карты').pack(anchor='w')
        self.query = tk.StringVar()
        ttk.Entry(self.frame, textvariable=self.query).pack(fill='x', pady=6)
        ttk.Style().configure('Events.Treeview', rowheight=54)
        self.tree = ttk.Treeview(self.frame, show='tree', style='Events.Treeview', selectmode='browse')
        self.tree.column('#0', width=215, stretch=True)
        self.tree.pack(fill='both', expand=True)
        ttk.Button(self.frame, text='Открыть выбранное', command=self.edit).pack(fill='x', pady=5)
        self.tree.bind('<<TreeviewSelect>>', self.select)
        self.tree.bind('<Double-1>', lambda e: self.edit())
        self.query.trace_add('write', lambda *_: self.refresh())
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        self.lookup = {}
        self.photos = []
        a = self.a
        for i, e in enumerate(a.world.map['events'], 1):
            name = e.get('name', e['id'])
            caption = f'{i}. {name} ({e['x']}, {e['y']})'
            if self.query.get().casefold() not in (caption + ' ' + e['id']).casefold():
                continue
            pg = active_page(e, a.world.flags, a.world.self_flags, a.world.map_id + ':' + e['id']) or (e['pages'][0] if e['pages'] else None)
            try:
                photo = ImageTk.PhotoImage(preview(a.project, pg, (44, 44))) if pg else None
            except Exception:
                photo = None
            if photo:
                self.photos.append(photo)
            args = {'image': photo} if photo else {}
            node = self.tree.insert('', 'end', text=caption, **args)
            self.lookup[node] = e

    def select(self, event=None):
        selection = self.tree.selection()
        if not selection or selection[0] not in self.lookup:
            return
        a = self.a
        if a.playing or a.job or a.modal:
            return
        e = self.lookup[selection[0]]
        a.selected = e['id']
        t = a.world.map['tile_size']
        a.cx = (e['x'] + 0.5) * t - a.canvas.winfo_width() / a.zoom / 2
        a.cy = (e['y'] + 0.5) * t - a.canvas.winfo_height() / a.zoom / 2
        a.cache = None

    def edit(self):
        a = self.a
        if a.playing or a.job or a.modal:
            return
        e = next((e for e in a.world.map['events'] if e['id'] == a.selected), None)
        if e:
            show(a, e['x'], e['y'])
            a.invalidate()
