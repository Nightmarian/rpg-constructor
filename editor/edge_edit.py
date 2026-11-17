import math
from engine.passage import VECTORS, OPPOSITE

def closest_edge(m, x, y):
    t = m['tile_size']
    cx = math.floor(x / t)
    cy = math.floor(y / t)
    if not (0 <= cx < m['width'] and 0 <= cy < m['height']):
        return None
    lx = x - cx * t
    ly = y - cy * t
    direction = min(((ly, 3), (t - lx, 2), (t - ly, 0), (lx, 1)), key=lambda pair: pair[0])[1]
    return (cx, cy, direction)

def set_wall(m, x, y, direction, blocked=True):
    if not (0 <= x < m['width'] and 0 <= y < m['height'] and (direction in VECTORS)):
        raise ValueError('Invalid boundary')
    edges = m.setdefault('edges', [])
    changed = False
    targets = [[x, y, direction]]
    dx, dy = VECTORS[direction]
    nx = x + dx
    ny = y + dy
    if 0 <= nx < m['width'] and 0 <= ny < m['height']:
        targets.append([nx, ny, OPPOSITE[direction]])
    for edge in targets:
        if blocked:
            if edge not in edges:
                edges.append(edge)
                changed = True
        else:
            while edge in edges:
                edges.remove(edge)
                changed = True
    return changed
