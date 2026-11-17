import math
VECTORS = {0: (0, 1), 1: (-1, 0), 2: (1, 0), 3: (0, -1)}
OPPOSITE = {0: 3, 3: 0, 1: 2, 2: 1}

def allowed(m, x, y, nx, ny):
    t = m['tile_size']
    a = (int(x // t), int(y // t))
    b = (int(nx // t), int(ny // t))
    if [*b] in m['blocked']:
        return False
    if a != b:
        dirs = []
        if b[0] > a[0]:
            dirs.append(2)
        if b[0] < a[0]:
            dirs.append(1)
        if b[1] > a[1]:
            dirs.append(0)
        if b[1] < a[1]:
            dirs.append(3)
        if any(([*a, d] in m.get('edges', []) for d in dirs)):
            return False
    for body in m.get('_bodies', []):
        bx, by, r = body
        if abs(nx - bx) < r and abs(ny - by) < r and (math.hypot(nx - bx, ny - by) <= math.hypot(x - bx, y - by)):
            return False
    return True
