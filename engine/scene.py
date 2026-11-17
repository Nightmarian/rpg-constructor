from PIL import Image, ImageDraw, ImageFont
from engine.resources import Resources
from engine.render_cache import RenderCache
from engine.text import path
from project.schema import active_page

class Scene:

    def __init__(self, root, p):
        self.root = root
        self.resources = Resources(p['profiles'])
        self.backgrounds = {}
        self.fonts = {}
        self.cache = RenderCache()
        self.image_cache = {}
        for mid, m in p['maps'].items():
            image = Image.open(m['image']).convert('RGB') if m.get('image') else None
            if image is not None and m.get('image_size') and (list(image.size) != m['image_size']):
                raise ValueError('Background dimensions changed: ' + mid)
            self.backgrounds[mid] = image
        ImageFont.truetype(path(root, p), int(p['font_size']))

    def size(self, p, mid):
        im = self.backgrounds[mid]
        m = p['maps'][mid]
        return im.size if im is not None else (m['width'] * m['tile_size'], m['height'] * m['tile_size'])

    def image(self, item):
        key = (item['file'], item.get('scale', 100))
        if key not in self.image_cache:
            im = Image.open(item['file']).convert('RGBA')
            scale = max(1, int(round(im.width * item.get('scale', 100) / 100)))
            height = max(1, int(round(im.height * item.get('scale', 100) / 100)))
            self.image_cache[key] = im.resize((scale, height), Image.LANCZOS)
        return self.image_cache[key]

    def draw(self, p, state, size=(960, 540), origin=None, view=None, grid=False, marks=False, editor=False):
        size = tuple(size)
        w, h = size
        mid = state['map_id']
        m = p['maps'][mid]
        player = state['player']
        vw, vh = view or (960 / p['camera_zoom'], 540 / p['camera_zoom'])
        bw, bh = self.size(p, mid)
        x, y = origin if origin is not None else (max(0, min(max(0, bw - vw), player['x'] - vw / 2)), max(0, min(max(0, bh - vh), player['y'] - vh / 2)))
        sx = w / vw
        sy = h / vh
        x = round(x * sx) / sx
        y = round(y * sy) / sy
        im = self.backgrounds[mid]
        out = self.cache.background(im, mid, size, (x, y, x + vw, y + vh)) if im is not None else Image.new('RGB', size, (34, 38, 46))
        d = ImageDraw.Draw(out)
        t = m['tile_size']
        actors = []
        for e in m['events']:
            pg = active_page(e, state['flags'], state['self_flags'], mid + ':' + e['id'])
            if editor and (not pg):
                pg = e['pages'][0] if e['pages'] else None
            if pg:
                n = state.get('actors', {}).get(e['id'], {}) if not editor else {}
                actors.append((n.get('y', (e['y'] + 0.85) * t), n.get('x', (e['x'] + 0.5) * t), pg['profile'], n.get('direction', pg['direction']), n.get('phase', 0) if n.get('moving', False) else pg['frame']))
        if marks:
            for cx, cy in m['blocked']:
                d.rectangle((round((cx * t - x) * sx), round((cy * t - y) * sy), round(((cx + 1) * t - x) * sx), round(((cy + 1) * t - y) * sy)), outline=(245, 70, 70), width=2)
        if grid:
            for cx in range(max(0, int(x // t)), min(m['width'], int((x + vw) // t) + 1) + 1):
                xx = round((cx * t - x) * sx)
                d.line((xx, 0, xx, h), fill=(100, 130, 150))
            for cy in range(max(0, int(y // t)), min(m['height'], int((y + vh) // t) + 1) + 1):
                yy = round((cy * t - y) * sy)
                d.line((0, yy, w, yy), fill=(100, 130, 150))
        actors.append((player['y'], player['x'], p['hero'], player['direction'], player['phase'] if player['moving'] else 0))
        for ay, ax, key, direction, frame in sorted(actors, key=lambda a: a[0]):
            sprite, anchor = self.resources.sprite(key, direction, frame)
            if sprite is None:
                continue
            sw, sh = sprite.size
            sprite = self.cache.sprite(sprite, (max(1, round(sw * sx)), max(1, round(sh * sy))))
            out.paste(sprite, (round((ax - x - anchor[0]) * sx), round((ay - y - anchor[1]) * sy)), sprite)
        for item in state.get('images', []):
            try:
                picture = self.image(item)
            except Exception:
                continue
            px = round(item.get('x', 0) - x)
            py = round(item.get('y', 0) - y)
            out.paste(picture, (px, py), picture)
        if state['dialogue'] and (not editor):
            self.dialogue(out, p, state['dialogue'][0])
        alpha = min(1.0, max(0.0, state.get('fade', 0.0))) if not editor else 0.0
        if alpha:
            out = out.point([round(v * (1 - alpha)) for v in range(256)] * 3)
        return out

    def dialogue(self, image, p, page):
        w, h = image.size
        factor = w / 960
        fs = max(8, round(p['font_size'] * factor))
        key = (path(self.root, p), fs)
        if key not in self.fonts:
            self.fonts[key] = ImageFont.truetype(*key)
        font = self.fonts[key]
        d = ImageDraw.Draw(image)
        pad = round(24 * factor)
        top = h - round(180 * h / 540)
        d.rounded_rectangle((pad, top, w - pad, h - pad), radius=max(3, round(10 * factor)), fill=(19, 25, 39), outline=(193, 207, 230), width=max(1, round(2 * factor)))
        y = top + round(12 * factor)
        if page['name']:
            d.text((pad * 2, y), page['name'], font=font, fill=(235, 204, 125))
        y += round(p['font_size'] * 1.5 * factor)
        for line in page['lines']:
            d.text((pad * 2, y), line, font=font, fill=(240, 243, 250))
            y += round(p['font_size'] * 1.3 * factor)
