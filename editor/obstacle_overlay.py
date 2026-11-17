import math
from PIL import Image, ImageDraw
from engine.passage import VECTORS, OPPOSITE
from project.schema import active_page

def arrow(draw, start, end, color, width=4):
    x, y = start
    ex, ey = end
    dx = ex - x
    dy = ey - y
    length = math.hypot(dx, dy)
    if length < 1:
        return
    ux = dx / length
    uy = dy / length
    head = min(12, length * 0.45)
    draw.line((x, y, ex, ey), fill=color, width=width)
    draw.polygon([(ex, ey), (ex - ux * head - uy * head * 0.65, ey - uy * head + ux * head * 0.65), (ex - ux * head + uy * head * 0.65, ey - uy * head - ux * head * 0.65)], fill=color)

def draw_obstacles(a, image):
    if not a.marks.get():
        return image
    m = a.world.map
    t = m['tile_size']
    z = a.zoom
    overlay = Image.new('RGBA', image.size)
    d = ImageDraw.Draw(overlay)

    def point(x, y):
        return ((x - a.cx) * z, (y - a.cy) * z)

    def cell(cx, cy, solid=False):
        x, y = point(cx * t, cy * t)
        side = t * z
        if x > image.width or y > image.height or x + side < 0 or (y + side < 0):
            return
        color = (235, 65, 67, 110) if not solid else (242, 133, 45, 90)
        d.rectangle((x, y, x + side, y + side), fill=color, outline=(255, 90, 85, 255) if not solid else (255, 174, 65, 255), width=4)
        if not solid:
            pad = max(3, min(12, side * 0.18))
            d.line((x + pad, y + pad, x + side - pad, y + side - pad), fill=(255, 225, 215, 240), width=4)
            d.line((x + side - pad, y + pad, x + pad, y + side - pad), fill=(255, 225, 215, 240), width=4)
        else:
            size = min(18, max(7, side * 0.25))
            d.rectangle((x + 4, y + 4, x + 4 + size, y + 4 + size), fill=(255, 174, 65, 255), outline=(40, 28, 20, 255), width=2)
    for x, y in m['blocked']:
        cell(x, y)
    for event in m['events']:
        pg = active_page(event, a.world.flags, a.world.self_flags, a.world.map_id + ':' + event['id'])
        if pg and pg.get('solid', False):
            cell(event['x'], event['y'], True)
    edges = {tuple(edge) for edge in m.get('edges', [])}
    visited = set()
    for x, y, direction in edges:
        vx, vy = VECTORS[direction]
        opposite = (x + vx, y + vy, OPPOSITE[direction])
        boundary = frozenset(((x, y, direction), opposite))
        cx = (x + 0.5) * t
        cy = (y + 0.5) * t
        ex = cx + vx * t * 0.5
        ey = cy + vy * t * 0.5
        ends = [point(ex - vy * t * 0.5, ey + vx * t * 0.5), point(ex + vy * t * 0.5, ey - vx * t * 0.5)]
        if opposite in edges:
            if boundary in visited:
                continue
            visited.add(boundary)
            d.line((*ends[0], *ends[1]), fill=(35, 20, 25, 255), width=10)
            d.line((*ends[0], *ends[1]), fill=(255, 64, 91, 255), width=6)
        else:
            d.line((*ends[0], *ends[1]), fill=(255, 194, 65, 255), width=5)
            arrow(d, point(ex + vx * t * 0.28, ey + vy * t * 0.28), point(ex - vx * t * 0.28, ey - vy * t * 0.28), (90, 255, 149, 255), max(3, min(6, round(z * 5))))
            bx, by = point(ex + vx * t * 0.36, ey + vy * t * 0.36)
            d.ellipse((bx - 5, by - 5, bx + 5, by + 5), fill=(255, 64, 91, 255))
    image = Image.alpha_composite(image.convert('RGBA'), overlay).convert('RGB')
    return image
