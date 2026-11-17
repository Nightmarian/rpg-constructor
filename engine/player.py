import math
from engine.passage import allowed

class Player:

    def __init__(self, pos):
        self.x, self.y = pos
        self.direction = 0
        self.phase = 0.0
        self.moving = False

    def step(self, keys, dt, size, m, settings, collisions):
        dx = int('d' in keys or 'Right' in keys) - int('a' in keys or 'Left' in keys)
        dy = int('s' in keys or 'Down' in keys) - int('w' in keys or 'Up' in keys)
        self.moving = bool(dx or dy)
        if not self.moving:
            self.phase = 0.0
            return
        self.direction = (2 if dx > 0 else 1) if dx else 0 if dy > 0 else 3
        self.phase += dt * settings['animation_fps']
        distance = settings['speed'] * dt
        steps = max(1, math.ceil(distance / max(1, m['tile_size'] / 4)))
        length = math.hypot(dx, dy)
        for _ in range(steps):
            nx = max(16, min(max(16, size[0] - 16), self.x + dx / length * distance / steps))
            ny = max(4, min(max(4, size[1] - 4), self.y + dy / length * distance / steps))
            t = m['tile_size']
            if not collisions or allowed(m, self.x, self.y, nx, self.y):
                self.x = nx
            if not collisions or allowed(m, self.x, self.y, self.x, ny):
                self.y = ny

    def state(self):
        return dict(x=self.x, y=self.y, direction=self.direction, phase=self.phase, moving=self.moving)
