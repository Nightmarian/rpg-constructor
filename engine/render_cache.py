from collections import OrderedDict
from PIL import Image
import math

class ImageCache:

    def __init__(self, budget=48 * 1024 * 1024):
        self.items = OrderedDict()
        self.bytes = 0
        self.budget = budget
        self.hits = 0
        self.misses = 0

    def get(self, key, create):
        if key in self.items:
            self.hits += 1
            self.items.move_to_end(key)
            return self.items[key]
        self.misses += 1
        image = create()
        cost = image.width * image.height * len(image.getbands())
        if cost > self.budget:
            return image
        while self.items and self.bytes + cost > self.budget:
            _, old = self.items.popitem(last=False)
            self.bytes -= old.width * old.height * len(old.getbands())
        self.items[key] = image
        self.bytes += cost
        return image

class RenderCache:

    def __init__(self):
        self.backgrounds = ImageCache()
        self.sprites = ImageCache(24 * 1024 * 1024)
        self.scaled = ImageCache(48 * 1024 * 1024)

    def background(self, image, mid, size, box):
        sx = size[0] / (box[2] - box[0])
        sy = size[1] / (box[3] - box[1])
        sw = max(1, math.ceil(image.width * sx))
        sh = max(1, math.ceil(image.height * sy))
        if sw * sh * 3 <= self.scaled.budget:
            scaled = self.scaled.get((mid, sx, sy), lambda: image.transform((sw, sh), Image.Transform.EXTENT, (0, 0, sw / sx, sh / sy), Image.Resampling.BILINEAR, fillcolor=(34, 38, 46)))
            left = round(box[0] * sx)
            top = round(box[1] * sy)
            if left >= 0 and top >= 0 and (left + size[0] <= sw) and (top + size[1] <= sh):
                return scaled.crop((left, top, left + size[0], top + size[1]))
            result = Image.new('RGB', size, (34, 38, 46))
            l = max(0, left)
            t = max(0, top)
            r = min(sw, left + size[0])
            b = min(sh, top + size[1])
            if r > l and b > t:
                result.paste(scaled.crop((l, t, r, b)), (l - left, t - top))
            return result
        return self.backgrounds.get((mid, size, box), lambda: image.transform(size, Image.Transform.EXTENT, box, Image.Resampling.BILINEAR, fillcolor=(34, 38, 46))).copy()

    def sprite(self, image, size):
        if image.size == size:
            return image
        return self.sprites.get((id(image), size), lambda: image.resize(size, Image.Resampling.NEAREST))
