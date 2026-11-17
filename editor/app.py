import time
import math
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from project import storage
from project.schema import active_page
from engine.world import World
from engine.scene import Scene
from engine.player import Player
from engine.video_player import VideoWindow
from support.keys import normalize
from editor.menus import build
from editor.actions import perform
from editor.event_ui import show as edit_event
from editor.templates import lever

class App:

    def __init__(self, root, log, records, log_path):
        self.root = root
        self.log = log
        self.records = records
        self.log_path = log_path
        self.window = tk.Tk()
        self.window.title('RPG Constructor 0.9.5')
        self.window.geometry('1320x870')
        self.window.minsize(1150, 650)
        ttk.Style().configure('TButton', padding=(6, 6))
        self.project = storage.load(root / 'assets' / 'demo_project.json', root)
        self.scene = Scene(root, self.project)
        self.world = World(root, self.project)
        self.world.video_callback = self.play_video
        self.video_window = None
        self.path = root / 'projects' / 'project.json'
        self.grid = tk.BooleanVar(value=True)
        self.marks = tk.BooleanVar(value=True)
        self.collisions = tk.BooleanVar(value=False)
        self.tool = tk.StringVar(value='event')
        self.status = tk.StringVar(value='Двойной щелчок по событию — страницы. Один щелчок — выбрать. Delete — удалить.')
        self.playing = False
        self.recording = False
        self.dirty = False
        self.running = True
        self.job = None
        self.take = None
        self.samples = []
        self.keys = set()
        self.zoom = 0.6
        self.cx = 0.0
        self.cy = 0.0
        self.last = time.perf_counter()
        self.modal = 0
        self.revision = 0
        self.cache = None
        self.selected = None
        self.log_window = None
        (root / 'recordings').mkdir(exist_ok=True)
        build(self)
        from editor.passage_ui import toolbar
        toolbar(self)
        ttk.Label(self.window, textvariable=self.status, anchor='w', padding=5).pack(side='bottom', fill='x')
        body = ttk.Frame(self.window)
        body.pack(fill='both', expand=True)
        from editor.event_list import EventList
        self.event_list = EventList(self, body)
        self.canvas = tk.Canvas(body, bg='#161a22', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.item = self.canvas.create_image(0, 0, anchor='nw')
        self.canvas.bind('<Button-1>', lambda e: self.paint(e, False, False))
        self.canvas.bind('<B1-Motion>', lambda e: self.paint(e, False, True))
        self.canvas.bind('<Button-3>', lambda e: self.paint(e, True, False))
        self.canvas.bind('<B3-Motion>', lambda e: self.paint(e, True, True))
        self.canvas.bind('<Double-1>', self.open_event)
        self.canvas.bind('<MouseWheel>', self.wheel)
        self.window.bind('<KeyPress>', self.key_down)
        self.window.bind('<KeyRelease>', lambda e: self.keys.discard(normalize(e.keysym, e.keycode)))
        self.window.bind('<FocusOut>', lambda e: self.keys.clear())
        self.window.protocol('WM_DELETE_WINDOW', lambda: self.action('quit'))
        self.window.report_callback_exception = lambda k, v, t: self.log.error('Tk callback', exc_info=(k, v, t))
        self.refresh_maps()
        self.window.after(120, self.fit)
        from editor.theme import ThemeManager
        self.theme = ThemeManager(self)
        self.theme.install()

    def play_video(self, file):
        if self.video_window is not None:
            try:
                self.video_window.close()
            except Exception:
                pass
            self.video_window = None
        self.video_window = VideoWindow(self, file, on_close=lambda: self.world.video_finished())

    def invalidate(self):
        self.revision += 1
        self.cache = None
        self.world.npcs.invalidate()
        if hasattr(self, 'event_list'):
            self.event_list.refresh()

    def reload_scene(self):
        self.scene = Scene(self.root, self.project)
        self.invalidate()

    def refresh_maps(self):
        self.map_box['values'] = list(self.project['maps'])
        self.map_var.set(self.world.map_id)

    def choose_map(self):
        if self.playing or self.job:
            self.refresh_maps()
            return
        self.world.map_id = self.map_var.get()
        self.world.player = Player(self.world.map['spawn'])
        self.world.dialogue = []
        self.world.pending = []
        self.selected = None
        self.fit()
        self.canvas.focus_set()

    def action(self, name):
        self.modal += 1
        self.keys.clear()
        try:
            perform(self, name)
        except Exception:
            self.log.exception('Action=%s map=%s', name, self.world.map_id)
            self.status.set('Ошибка: Вид → Журнал')
            self.show_log()
        finally:
            self.modal -= 1
            self.keys.clear()
            self.last = time.perf_counter()
            self.invalidate()
            if self.running:
                self.canvas.focus_set()

    def key_down(self, e):
        if e.widget != self.canvas or self.modal or self.job:
            return
        key = normalize(e.keysym, e.keycode)
        first = key not in self.keys
        self.keys.add(key)
        if first and key == 'Delete' and (not self.playing):
            self.action('delete_event')
        elif first and key in ('space', 'Return') and self.playing:
            try:
                self.world.interact()
                if self.recording:
                    self.samples.append(self.world.snapshot(time.perf_counter() - self.record_start))
            except Exception:
                self.log.exception('Interact map=%s', self.world.map_id)
                self.show_log()

    def fit(self):
        from editor.navigation import fit
        fit(self)

    def wheel(self, e):
        from editor.navigation import wheel
        wheel(self, e)

    def locate(self, e):
        x = e.x / self.zoom + self.cx
        y = e.y / self.zoom + self.cy
        t = self.world.map['tile_size']
        cx = math.floor(x / t)
        cy = math.floor(y / t)
        for event in sorted(self.world.map['events'], key=lambda ev: ev['y'], reverse=True):
            pg = active_page(event, self.world.flags, self.world.self_flags, self.world.map_id + ':' + event['id']) or (event['pages'][0] if event['pages'] else None)
            if not pg:
                continue
            sprite, anchor = self.scene.resources.sprite(pg['profile'], pg['direction'], pg['frame'])
            if sprite is not None:
                ex = (event['x'] + 0.5) * t - anchor[0]
                ey = (event['y'] + 0.85) * t - anchor[1]
                if ex <= x < ex + sprite.width and ey <= y < ey + sprite.height:
                    return (event['x'], event['y'])
        return (cx, cy)

    def open_event(self, e):
        if self.playing or self.job or self.tool.get() != 'event':
            return
        cx, cy = self.locate(e)
        if 0 <= cx < self.world.map['width'] and 0 <= cy < self.world.map['height']:
            edit_event(self, cx, cy)
            self.invalidate()

    def paint(self, e, erase, drag):
        self.canvas.focus_set()
        if self.playing or self.job:
            return
        x = e.x / self.zoom + self.cx
        y = e.y / self.zoom + self.cy
        m = self.world.map
        t = m['tile_size']
        cx = math.floor(x / t)
        cy = math.floor(y / t)
        if self.tool.get() == 'event':
            if not drag and (not erase):
                cx, cy = self.locate(e)
                self.selected = next((ev['id'] for ev in m['events'] if (ev['x'], ev['y']) == (cx, cy)), None)
                self.status.set('Выбрано: ' + (self.selected or 'пустая клетка') + '. Двойной щелчок — редактор.')
                self.invalidate()
            return
        if not (0 <= cx < m['width'] and 0 <= cy < m['height']):
            return
        if self.tool.get() == 'edge_free':
            from editor.free_edges import paint_free
            paint_free(self, x, y, erase)
            return
        if self.tool.get() == 'edge':
            from editor.passage_ui import paint
            paint(self, cx, cy, erase)
            return
        if self.tool.get() == 'door':
            if not drag and (not erase):
                from editor.door_ui import create
                create(self, cx, cy)
            return
        if self.tool.get() == 'lever':
            if not drag and (not erase):
                lever(self, cx, cy)
            return
        if self.tool.get() == 'spawn' and (not erase):
            m['spawn'] = [x, y]
            self.world.player = Player([x, y])
        else:
            cell = [cx, cy]
            if not erase and self.tool.get() == 'block':
                if cell not in m['blocked']:
                    m['blocked'].append(cell)
            elif cell in m['blocked']:
                m['blocked'].remove(cell)
        self.dirty = True
        self.invalidate()

    def delete_selected(self):
        if self.playing:
            return
        event = next((e for e in self.world.map['events'] if e['id'] == self.selected), None)
        if not event:
            messagebox.showinfo('Удаление', 'Выберите событие одним щелчком инструментом «Событие / выбор».', parent=self.window)
            return
        if messagebox.askyesno('Удалить', 'Удалить ' + event.get('name', event['id']) + '?', parent=self.window):
            self.world.map['events'].remove(event)
            self.selected = None
            self.dirty = True
            self.invalidate()

    def show_log(self):
        from editor.log_ui import show
        show(self)

    def tick(self):
        from editor.frame_loop import tick
        tick(self)

    def run(self):
        self.window.after(100, self.tick)
        self.window.mainloop()
