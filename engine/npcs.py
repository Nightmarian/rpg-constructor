from engine.random_movement import resolve_command
import copy
import random
import math
from project.schema import active_page
from engine.passage import allowed, VECTORS

class NPCs:

    def __init__(self, world):
        self.world = world
        self.states = {}
        self.random = random.Random(world.project.get('random_seed'))
        self._signature = None
        self._active = {}

    def invalidate(self):
        self._signature = None

    def sync(self):
        w = self.world
        signature = (w.map_id, id(w.map), id(w.map['events']), len(w.map['events']), tuple(w.flags.items()), tuple(w.self_flags.items()))
        if signature == self._signature:
            return self._active
        t = w.map['tile_size']
        active = {}
        for e in w.map['events']:
            key = w.map_id + ':' + e['id']
            pg = active_page(e, w.flags, w.self_flags, key)
            if not pg:
                continue
            n = self.states.setdefault(key, dict(x=(e['x'] + 0.5) * t, y=(e['y'] + 0.85) * t, direction=pg['direction'], phase=0.0, moving=False, page=-1, target=None, wait=0.0, index=0))
            pi = e['pages'].index(pg)
            if n['page'] != pi:
                n.update(page=pi, target=None, wait=0.0, index=0, direction=pg['direction'], phase=0.0, moving=False)
            active[e['id']] = (e, pg, n)
        self._signature = signature
        self._active = active
        return active

    def snapshot(self):
        return {key: {field: n[field] for field in ('x', 'y', 'direction', 'phase', 'moving', 'page')} for key, (_, _, n) in self.sync().items()}

    def bodies(self, exclude=None):
        t = self.world.map['tile_size']
        return [(n['x'], n['y'], t * 0.4) for key, (_, pg, n) in self.sync().items() if key != exclude and pg.get('solid', False)]

    def position(self, event):
        item = self.sync().get(event['id'])
        t = self.world.map['tile_size']
        return (item[2]['x'], item[2]['y']) if item else ((event['x'] + 0.5) * t, (event['y'] + 0.85) * t)

    def face(self, event):
        item = self.sync().get(event['id'])
        if item:
            n = item[2]
            p = self.world.player
            dx = p.x - n['x']
            dy = p.y - n['y']
            n['direction'] = (2 if dx > 0 else 1) if abs(dx) > abs(dy) else 0 if dy > 0 else 3
            n['moving'] = False

    def update(self, dt, size):
        w = self.world
        t = w.map['tile_size']
        active = self.sync()
        solid = [(key, n, t * 0.4) for key, (_, pg, n) in active.items() if pg.get('solid', False)]
        for key, (e, pg, n) in active.items():
            cfg = pg.get('movement', {})
            mode = cfg.get('mode', 'fixed')
            n['moving'] = False
            if mode == 'fixed':
                continue
            if n['wait'] > 0:
                n['wait'] = max(0, n['wait'] - dt)
                continue
            speed = cfg.get('speed', 100)
            delay = cfg.get('delay', 0.3)
            if n['target'] is None:
                if mode == 'route':
                    route = cfg.get('route', [])
                    if not route:
                        continue
                    if n['index'] >= len(route):
                        if not cfg.get('repeat', True):
                            continue
                        n['index'] = 0
                    command = resolve_command(route[n['index']], self.random)
                    n['index'] += 1
                    op = command['op']
                    if op == 'wait':
                        n['wait'] = command.get('seconds', 1.0)
                        continue
                    if op == 'turn':
                        n['direction'] = command.get('direction', 0)
                        n['wait'] = delay
                        continue
                    direction = {'down': 0, 'left': 1, 'right': 2, 'up': 3}[op]
                elif mode == 'approach':
                    dx = w.player.x - n['x']
                    dy = w.player.y - n['y']
                    if math.hypot(dx, dy) < t * 0.8:
                        n['wait'] = delay
                        continue
                    direction = (2 if dx > 0 else 1) if abs(dx) > abs(dy) else 0 if dy > 0 else 3
                else:
                    direction = self.random.randrange(4)
                vx, vy = VECTORS[direction]
                tx = n['x'] + vx * t
                ty = n['y'] + vy * t
                if mode == 'random' and (abs(tx - (e['x'] + 0.5) * t) > cfg.get('radius', 3) * t or abs(ty - (e['y'] + 0.85) * t) > cfg.get('radius', 3) * t):
                    n['wait'] = delay
                    continue
                n['direction'] = direction
                n['target'] = [tx, ty]
            tx, ty = n['target']
            dx = tx - n['x']
            dy = ty - n['y']
            distance = math.hypot(dx, dy)
            if distance < 0.01:
                n['target'] = None
                n['wait'] = delay
                continue
            n['direction'] = (2 if dx > 0 else 1) if abs(dx) > abs(dy) else 0 if dy > 0 else 3
            step = min(distance, speed * dt)
            count = max(1, math.ceil(step / max(1, t / 8)))
            m = dict(w.map)
            m['_bodies'] = [(other['x'], other['y'], radius) for other_key, other, radius in solid if other_key != key] + [(w.player.x, w.player.y, t * 0.4)]
            for _ in range(count):
                nx = n['x'] + dx / distance * step / count
                ny = n['y'] + dy / distance * step / count
                if not (0 <= nx < size[0] and 0 <= ny < size[1]) or not allowed(m, n['x'], n['y'], nx, ny):
                    n['target'] = None
                    n['wait'] = delay
                    break
                n['x'] = nx
                n['y'] = ny
                n['moving'] = True
            if n['moving']:
                n['phase'] += dt * w.project['animation_fps']
            if math.hypot(tx - n['x'], ty - n['y']) < 0.01:
                n['target'] = None
                n['wait'] = delay
