import os
import json
import time
import copy
import math
from pathlib import Path
from datetime import datetime
from tkinter import filedialog, simpledialog, messagebox
from PIL import Image
from project import storage
from engine.scene import Scene
from engine.world import World
from engine.player import Player
from editor import assets_ui, conditions, settings, export_ui

def perform(a, name):
    if a.job:
        if name == 'quit':
            a.job.cancel.set()
            a.status.set('Отмена экспорта; закройте после завершения')
        return
    if a.recording and name not in ('stop', 'quit', 'logs'):
        a.status.set('Сначала Стоп')
        return
    if name in ('open', 'demo'):
        if a.dirty and (not messagebox.askyesno('Изменения', 'Отбросить несохранённые изменения?', parent=a.window)):
            return
        path = str(a.root / 'assets' / 'demo_project.json') if name == 'demo' else filedialog.askopenfilename(parent=a.window, filetypes=[('Проект', '*.json')])
        if not path:
            return
        p = storage.load(path, a.root)
        scene = Scene(a.root, p)
        a.project = p
        a.scene = scene
        a.world = World(a.root, p)
        a.playing = False
        a.take = None
        a.dirty = name == 'demo'
        a.selected = None
        if name == 'open':
            a.path = Path(path)
            if json.loads(Path(path).read_text(encoding='utf-8')).get('format_version', 0) < 7:
                stamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                a.path = a.path.with_name(a.path.stem + '_090_' + stamp + '.json')
                a.dirty = True
                a.status.set('Преобразовано. Сохранение в новый файл: ' + a.path.name)
        else:
            a.path = a.root / 'projects' / ('demo_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f') + '.json')
        a.refresh_maps()
        a.fit()
        a.log.info('Loaded %s format=7', path)
    elif name in ('save', 'save_as'):
        path = a.path
        if name == 'save_as':
            value = filedialog.asksaveasfilename(parent=a.window, defaultextension='.json', filetypes=[('Проект', '*.json')])
            if not value:
                return
            path = Path(value)
        storage.save(path, a.project)
        a.path = path
        a.dirty = False
        a.status.set('Сохранено')
        a.log.info('Saved %s', path)
    elif name in ('add_map', 'background'):
        key = simpledialog.askstring('Локация', 'Уникальное имя:', parent=a.window) if name == 'add_map' else a.world.map_id
        if not key:
            return
        if name == 'add_map' and key in a.project['maps']:
            raise ValueError('Map exists')
        source = filedialog.askopenfilename(parent=a.window, filetypes=[('Фон', '*.png *.jpg *.jpeg *.webp')])
        if not source:
            return
        tile = simpledialog.askinteger('Клетка', 'Размер клетки:', initialvalue=128, minvalue=1, parent=a.window)
        if tile is None:
            return
        if name == 'background' and (not messagebox.askyesno('Замена', 'Удалить события и разметку текущей карты при замене?', parent=a.window)):
            return
        im = Image.open(source).convert('RGB')
        w, h = im.size
        a.project['maps'][key] = dict(width=math.ceil(w / tile), height=math.ceil(h / tile), tile_size=tile, image=str(Path(source).resolve()), image_size=[w, h], spawn=[w / 2, h / 2], blocked=[], events=[])
        a.reload_scene()
        a.world.map_id = key
        a.world.player = Player([w / 2, h / 2])
        a.world.dialogue = []
        a.world.pending = []
        a.take = None
        a.playing = False
        a.dirty = True
        a.refresh_maps()
        a.fit()
    elif name == 'fit':
        a.fit()
    elif name == 'settings':
        settings.show(a)
    elif name == 'switches':
        conditions.manage(a, a.project)
        a.dirty = True
    elif name == 'import':
        assets_ui.import_image(a, a.project)
        a.reload_scene()
    elif name == 'hero_size':
        from editor.graphics_ui import edit
        edit(a, a.project, a.project['hero'])
        a.reload_scene()
        a.dirty = True
    elif name == 'hero':
        result = assets_ui.choose(a, a.project, a.project['hero'], characters_only=True)
        if result:
            a.project['hero'] = result[0]
            a.dirty = True
        a.reload_scene()
    elif name == 'play':
        a.playing = not a.playing
        a.keys.clear()
    elif name == 'reset':
        a.world = World(a.root, a.project)
        a.refresh_maps()
        a.status.set('Общие и локальные состояния сброшены')
    elif name == 'delete_event':
        a.delete_selected()
    elif name == 'record':
        a.samples = [a.world.snapshot(0.0)]
        a.record_start = time.perf_counter()
        a.recording = True
        a.playing = True
        a.take = None
        a.log.info('Capture started')
    elif name == 'stop':
        if not a.recording:
            return
        a.samples.append(a.world.snapshot(time.perf_counter() - a.record_start))
        a.recording = False
        a.playing = False
        a.keys.clear()
        a.take = (copy.deepcopy(a.samples), copy.deepcopy(a.project), copy.copy(a.scene))
        path = a.root / 'recordings' / datetime.now().strftime('take_%Y%m%d_%H%M%S_%f.json')
        path.write_text(json.dumps(dict(take_version=4, project=a.project, samples=a.samples), ensure_ascii=False), encoding='utf-8')
        a.status.set('Дубль готов: MP4')
        a.log.info('Capture saved %s', path)
    elif name == 'export':
        export_ui.start(a)
    elif name == 'log':
        a.show_log()
    elif name in ('logs', 'videos'):
        os.startfile(str(a.log_path.parent if name == 'logs' else a.root / 'recordings'))
    elif name == 'test':
        raise RuntimeError('Intentional diagnostics test')
    elif name == 'help':
        os.startfile(str(a.root / 'README_RU.md'))
    elif name == 'quit':
        if a.recording:
            perform(a, 'stop')
        if a.take and (not messagebox.askyesno('Выход', 'Дубль только в текущем сеансе. Выйти?', parent=a.window)):
            return
        if a.dirty:
            storage.save(a.root / 'projects' / 'recovery.json', a.project)
        a.running = False
        a.window.destroy()
