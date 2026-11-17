from PIL import ImageDraw, ImageFont
from engine.passage import VECTORS

def draw(a, image):
    from editor.obstacle_overlay import draw_obstacles
    image = draw_obstacles(a, image)
    d = ImageDraw.Draw(image)
    t = a.world.map['tile_size']
    z = a.zoom
    font = ImageFont.truetype(str(a.root / 'assets' / 'DejaVuSans.ttf'), 13)
    for i, e in enumerate(a.world.map['events'], 1):
        x = round((e['x'] * t - a.cx) * z)
        y = round((e['y'] * t - a.cy) * z)
        side = max(8, round(t * z))
        box = (x, y, x + side, y + side)
        color = '#55e5ff' if a.selected == e['id'] else '#ffce50'
        width = 5 if a.selected == e['id'] else 3
        d.rectangle((x - 2, y - 2, x + side + 2, y + side + 2), outline='#18202b', width=width + 2)
        d.rectangle(box, outline=color, width=width)
        text = f'{i}: {e.get('name', e['id'])}'
        bounds = d.textbbox((x + 4, y + 3), text, font=font)
        d.rectangle((bounds[0] - 2, bounds[1] - 2, bounds[2] + 3, bounds[3] + 2), fill='#18202b')
        d.text((x + 4, y + 3), text, font=font, fill=color)
    return image
