import copy
import math
import time
from engine.player import Player
from engine.npcs import NPCs
from engine.transition import Transition
from engine.text import pages
from project.schema import active_page, condition_ok

class World:

    def __init__(self, root, project):
        self.root = root
        self.project = project
        self.map_id = project['start_map']
        self.player = Player(self.map['spawn'])
        self.flags = {}
        self.self_flags = {}
        self.dialogue = []
        self.pending = []
        self.event_key = ''
        self.touch_lock = None
        self.images = []
        self.dialogue_images = []
        self.npcs = NPCs(self)
        self.transition = Transition()

    @property
    def map(self):
        return self.project['maps'][self.map_id]

    def snapshot(self, t):
        return dict(t=t, map_id=self.map_id, player=self.player.state(), flags=copy.deepcopy(self.flags), self_flags=copy.deepcopy(self.self_flags), dialogue=copy.deepcopy(self.dialogue), actors=self.npcs.snapshot(), fade=self.transition.alpha, images=copy.deepcopy(self.images))

    def view_state(self):
        return dict(map_id=self.map_id, player=self.player.state(), flags=self.flags, self_flags=self.self_flags, dialogue=self.dialogue, actors=self.npcs.snapshot(), fade=self.transition.alpha, images=self.images)

    def _transfer(self, c):
        self.map_id = c['target']
        t = self.map['tile_size']
        self.player = Player([(c['tx'] + 0.5) * t, (c['ty'] + 0.85) * t])
        self.player.direction = c.get('direction', 0)
        self.touch_lock = (self.map_id, int(self.player.x // t), int(self.player.y // t))

    def start(self, event):
        if self.transition.active:
            return
        self.event_key = self.map_id + ':' + event['id']
        pg = active_page(event, self.flags, self.self_flags, self.event_key)
        if pg:
            self.npcs.face(event)
            self.pending = copy.deepcopy(pg['commands'])
            self.advance()

    def advance(self):
        processed = 0
        while self.pending and (not self.dialogue or (self.pending[0].get('type') == 'and' and len(self.pending) > 1 and self.pending[1].get('type') != 'hide_image')) and (not self.transition.active):
            processed += 1
            if processed > 10000:
                raise RuntimeError('Too many event commands in one interaction')
            c = self.pending.pop(0)
            if c.get('type') == 'and':
                if not self.pending or self.pending[0].get('type') not in ('sound', 'show_image', 'show_video', 'hide_image'):
                    raise ValueError('После И используйте звук, картинку, видео или скрытие')
                c = self.pending.pop(0)
            kind = c['type']
            if kind == 'text':
                self.dialogue = pages(self.root, self.project, c.get('name', ''), c.get('text', ''))
            elif kind in ('switch', 'self_switch'):
                states = self.flags if kind == 'switch' else self.self_flags
                key = c['flag'] if kind == 'switch' else self.event_key + ':' + c['flag']
                states[key] = not states.get(key, False) if c['operation'] == 'toggle' else c['operation'] == 'on'
            elif kind == 'if':
                branch = 'then' if condition_ok(c['condition'], self.flags, self.self_flags, self.event_key) else 'else'
                self.pending = copy.deepcopy(c[branch]) + self.pending
            elif kind == 'transfer':
                duration = self.project.get('transition_seconds', 0.25)
                if c.get('fade', True) and duration > 0:
                    self.player.moving = False
                    self.transition.start(c, duration)
                else:
                    self._transfer(c)
            elif kind == 'sound':
                self._play_sound(c)
            elif kind in ('show_image', 'show_video'):
                item = dict(c)
                item['shown_at'] = time.monotonic()
                self.images.append(item)
                if self.dialogue:
                    self.dialogue_images.append(len(self.images) - 1)
            elif kind == 'hide_image':
                if self.images:
                    self.images.pop()
                    if self.dialogue_images and self.dialogue_images[-1] >= len(self.images):
                        self.dialogue_images.pop()

    def _play_sound(self, c):
        import os
        try:
            if os.name == 'nt':
                import winsound
                flags = winsound.SND_FILENAME | winsound.SND_ASYNC
                winsound.PlaySound(c['file'], flags)
        except Exception:
            pass

    def interact(self):
        if self.transition.active:
            return
        if self.dialogue:
            self.dialogue.pop(0)
            if not self.dialogue:
                for index in reversed(self.dialogue_images):
                    if 0 <= index < len(self.images):
                        self.images.pop(index)
                self.dialogue_images.clear()
                self.advance()
            return
        p = self.player
        t = self.map['tile_size']
        vx, vy = {0: (0, 1), 1: (-1, 0), 2: (1, 0), 3: (0, -1)}[p.direction]
        candidates = []
        for e in self.map['events']:
            pg = active_page(e, self.flags, self.self_flags, self.map_id + ':' + e['id'])
            if not pg or pg['trigger'] != 'action':
                continue
            ex, ey = self.npcs.position(e)
            dx = ex - p.x
            dy = ey - p.y
            distance = math.hypot(dx, dy)
            if distance <= t * 1.65 and dx * vx + dy * vy >= -t * 0.3:
                candidates.append((distance, e))
        if candidates:
            self.start(min(candidates, key=lambda pair: pair[0])[1])

    def update(self, keys, dt, size, collisions):
        if self.transition.active:
            if self.transition.update(dt, self._transfer):
                self.advance()
            return
        if self.dialogue:
            self.player.moving = False
            return
        self.npcs.update(dt, size)
        m = dict(self.map)
        m['_bodies'] = self.npcs.bodies()
        self.player.step(keys, dt, size, m, self.project, collisions)
        t = m['tile_size']
        location = (self.map_id, int(self.player.x // t), int(self.player.y // t))
        if location != self.touch_lock:
            self.touch_lock = None
            for e in m['events']:
                pg = active_page(e, self.flags, self.self_flags, self.map_id + ':' + e['id'])
                if pg and pg['trigger'] == 'touch' and (tuple((int(v // t) for v in self.npcs.position(e))) == location[1:]):
                    self.touch_lock = location
                    self.start(e)
                    break
