from PIL import Image

def preview(p, page, size=(180, 140)):
    out = Image.new('RGB', size, (46, 52, 63))
    key = page['profile']
    if key == 'none':
        return out
    s = p['profiles'][key]
    w, h = s['frame_size']
    row = page['direction'] if s['kind'] == 'character' else 0
    col = min(page['frame'], s['counts'][row] - 1)
    with Image.open(s['file']) as sheet:
        im = sheet.convert('RGBA').crop((col * w, row * h, (col + 1) * w, (row + 1) * h))
    im.thumbnail((size[0] - 12, size[1] - 12), Image.Resampling.NEAREST)
    out.paste(im, ((size[0] - im.width) // 2, (size[1] - im.height) // 2), im)
    return out
