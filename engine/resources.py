from PIL import Image

class Resources:

    def __init__(self, profiles):
        self.specs = profiles
        self.images = {}
        for key, spec in profiles.items():
            sheet = Image.open(spec['file']).convert('RGBA')
            w, h = spec['frame_size']
            rows = []
            for row, count in enumerate(spec['counts']):
                if count < 1 or count * w > sheet.width or (row + 1) * h > sheet.height:
                    raise ValueError('Invalid sprite sheet ' + key)
                rows.append([sheet.crop((i * w, row * h, (i + 1) * w, (row + 1) * h)) for i in range(count)])
            scale = spec.get('scale', 1.0)
            if scale != 1:
                rows = [[im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.Resampling.NEAREST) for im in row] for row in rows]
            self.images[key] = rows

    def sprite(self, key, direction=0, frame=0):
        if key == 'none':
            return (None, (0, 0))
        spec = self.specs[key]
        row = direction if spec['kind'] == 'character' else 0
        frames = self.images[key][row]
        return (frames[int(frame) % len(frames)], tuple((v * spec.get('scale', 1.0) for v in spec['anchor'])))
