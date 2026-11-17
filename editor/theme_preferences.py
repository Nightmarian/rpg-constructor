import json
THEMES = ('light', 'dark')

def load_theme(path):
    try:
        value = json.loads(path.read_text(encoding='utf-8')).get('theme', 'light')
        return value if value in THEMES else 'light'
    except (OSError, ValueError, AttributeError):
        return 'light'

def save_theme(path, value):
    if value not in THEMES:
        raise ValueError('Unknown theme')
    data = {}
    try:
        loaded = json.loads(path.read_text(encoding='utf-8'))
        if isinstance(loaded, dict):
            data = loaded
    except (OSError, ValueError):
        pass
    data['theme'] = value
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(path)
