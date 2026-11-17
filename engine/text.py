from PIL import ImageFont

def path(root, p):
    return p.get('font') or str(root / 'assets' / 'DejaVuSans.ttf')

def pages(root, p, name, text):
    font = ImageFont.truetype(path(root, p), int(p['font_size']))
    lines = []
    for paragraph in text.replace('\r', '').split('\n'):
        line = ''
        for word in paragraph.split(' '):
            candidate = line + ' ' + word if line else word
            if font.getlength(candidate) <= 850:
                line = candidate
                continue
            if line:
                lines.append(line)
                line = ''
            for ch in word:
                if line and font.getlength(line + ch) > 850:
                    lines.append(line)
                    line = ''
                line += ch
        lines.append(line)
    count = max(1, int(100 / (p['font_size'] * 1.3)))
    return [dict(name=name, lines=lines[i:i + count]) for i in range(0, len(lines), count)]
