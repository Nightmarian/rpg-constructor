import threading
import time
from queue import Queue, Empty, Full
import imageio.v2 as imageio
from PIL import Image, ImageDraw, ImageFont
from engine.resources import Resources
from engine.render_cache import RenderCache
from engine.text import path
from project.schema import active_page

class VideoBuffer:

    def __init__(self, file):
        self.file = file
        self.queue = Queue(maxsize=30)
        self.reader = imageio.get_reader(file)
        meta = self.reader.get_meta_data()
        self.fps = float(meta.get('fps', 24) or 24)
        self.thread = threading.Thread(target=self._fill, daemon=True)
        self.thread.start()

    def _fill(self):
        try:
            for frame in self.reader:
                image = Image.fromarray(frame).convert('RGB')
                while True:
                    try:
                        self.queue.put_nowait(image)
                        break
                    except Full:
                        time.sleep(0.01)
        except Exception:
            pass

    def next_frame(self):
        try:
            return self.queue.get_nowait()
        except Empty:
            return None

    def close(self):
        try:
            self.reader.close()
        except Exception:
            pass

class Scene:

    def __init__(self, root, p):
        self.root = root
        self.resources = Resources(p['profiles'])
        self.backgrounds = {}
        self.fonts = {}
        self.cache = RenderCache()
        self.image_cache = {}
        self.video_cache = {}
        self.picture_cache = {}
        self.mask_cache = {}
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
        key = item['file']
        if key not in self.image_cache:
            source = Image.open(item['file'])
            if getattr(source, 'is_animated', False):
                frames = []
                durations = []
                for index in range(source.n_frames):
                    source.seek(index)
                    frames.append(source.convert('RGBA'))
                    durations.append(max(0.02, source.info.get('duration', 100) / 1000))
                self.image_cache[key] = (frames, durations)
            else:
                self.image_cache[key] = ([source.convert('RGBA')], [0.0])
        frames, durations = self.image_cache[key]
        if len(frames) > 1:
            elapsed = max(0.0, time.monotonic() - item.get('shown_at', time.monotonic()))
            total = sum(durations)
            position = elapsed % total
            passed = 0.0
            for frame, duration in zip(frames, durations):
                passed += duration
                if position < passed:
                    return frame
            return frames[-1]
        return frames[0]

    def video(self, item, size):
        key = item['file']
        entry = self.video_cache.get(key)
        if not isinstance(entry, dict):
            entry = {'buffer': VideoBuffer(key), 'last': 0.0, 'frame': None, 'size': None, 'resized': None}
            self.video_cache[key] = entry
        now = time.monotonic()
        if entry['frame'] is None or now - entry['last'] >= 1 / entry['buffer'].fps:
            frame = entry['buffer'].next_frame()
            if frame is not None:
                entry['frame'] = frame
                entry['last'] = now
                entry['size'] = None
        if entry['frame'] is None:
            entry['frame'] = Image.new('RGB', size, (0, 0, 0))
        return entry['frame'], entry

    def media(self, item, size):
        if item['type'] == 'show_video':
            return self.video(item, size)
        return self.image(item), None

    def picture_geometry(self, item, picture, size):
        w, h = size
        fit = item.get('fit', 'fit')
        if fit == 'cover':
            factor = max(w / picture.width, h / picture.height)
        else:
            factor = min(w / picture.width, h / picture.height)
        pw = max(1, round(picture.width * factor))
        ph = max(1, round(picture.height * factor))
        px = (w - pw) // 2
        py = (h - ph) // 2
        return pw, ph, px, py

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
                d.rectangle((round((cx * t - x) * sx), round((cy * t - y) * sy), round(((cx + 1) * t - x) * sx), round(((cx + 1) * t - y) * sy)), outline=(245, 70, 70), width=2)
        if grid:
            for cx in range(max(0, int(x // t)), min(m['width'], int((x + vw) // t) + 1) + 1):
                xx = round((cx * t - x) * sx)
                d.line((xx, 0, xx, h), fill=(100, 130, 150))
            for cy in range(max(0, int(y // t)), min(m['height'], int((y + vw) // t) + 1)):
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
        for item in ([] if editor else state.get('images', [])):
            picture, entry = self.media(item, size)
            pw, ph, px, py = self.picture_geometry(item, picture, size)
            if entry is not None:
                if entry.get('size') == (pw, ph) and entry.get('resized') is not None:
                    picture = entry['resized']
                else:
                    if picture.size != (pw, ph):
                        picture = picture.resize((pw, ph), Image.BILINEAR)
                    entry['resized'] = picture
                    entry['size'] = (pw, ph)
            else:
                key = (item['file'], pw, ph, item.get('fit', 'fit'))
                cached = self.picture_cache.get(key)
                if cached is None:
                    if picture.size != (pw, ph):
                        cached = picture.resize((pw, ph), Image.BILINEAR)
                    else:
                        cached = picture
                    self.picture_cache[key] = cached
                picture = cached
            if item.get('fit', 'fit') == 'cover' and (pw > w or ph > h):
                left = max(0, (pw - w) // 2)
                top = max(0, (ph - h) // 2)
                picture = picture.crop((left, top, left + min(w, pw), top + min(h, ph)))
                px = 0
                py = 0
            alpha = 1.0
            if item.get('transition', 'fade') == 'fade':
                age = max(0.0, time.monotonic() - item.get('shown_at', time.monotonic()))
                alpha = min(1.0, age / max(0.05, item.get('duration', 0.5)))
            if alpha < 1.0:
                mask_key = (item['file'], picture.size, round(alpha * 255))
                mask = self.mask_cache.get(mask_key)
                if mask is None:
                    if entry is not None:
                        mask = Image.new('L', picture.size, int(255 * alpha))
                    else:
                        mask = picture.getchannel('A').point(lambda value: int(value * alpha))
                    self.mask_cache[mask_key] = mask
                out.paste(picture, (px, py), mask)
            else:
                out.paste(picture, (px, py))
        if state['dialogue'] and (not editor):
            self.dialogue(out, p, state['dialogue'][0])
        fade = min(1.0, max(0.0, state.get('fade', 0.0))) if not editor else 0.0
        if fade:
            out = out.point([round(v * (1 - fade)) for v in range(256)] * 3)
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
