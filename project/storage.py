import json
import copy
import os
import hashlib
from pathlib import Path
from PIL import Image
from project.migrate import convert
from project.schema import validate

def resolve_profiles(specs, base, root):
    specs = copy.deepcopy(specs)
    for key, spec in specs.items():
        if spec['kind'] == 'object' and 'files' in spec:
            frames = [Image.open(base / file).convert('RGBA') for file in spec.pop('files')]
            w = max((im.width for im in frames))
            h = max((im.height for im in frames))
            sheet = Image.new('RGBA', (w * len(frames), h))
            for i, im in enumerate(frames):
                sheet.paste(im, (i * w, 0))
            folder = root / 'assets' / 'imported'
            folder.mkdir(exist_ok=True)
            path = folder / ('migrated_' + hashlib.sha256(sheet.tobytes()).hexdigest()[:16] + '.png')
            sheet.save(path)
            spec.update(file=str(path.resolve()), frame_size=[w, h], counts=[len(frames)])
        else:
            spec['file'] = str((base / spec['file']).resolve())
    return specs

def load(path, root):
    path = Path(path)
    raw = json.loads(path.read_text(encoding='utf-8'))
    p = convert(raw)
    for m in p['maps'].values():
        if m.get('image'):
            m['image'] = str((path.parent / m['image']).resolve())
    if p.get('font'):
        p['font'] = str((path.parent / p['font']).resolve())
    if 'profiles' in p:
        p['profiles'] = resolve_profiles(p['profiles'], path.parent, root)
    else:
        manifest = root / 'assets' / 'profiles.json'
        specs = resolve_profiles(json.loads(manifest.read_text(encoding='utf-8')), manifest.parent, root)
        for folder in [path.parent, *list(path.parents)[:4]]:
            candidate = folder / 'assets' / 'profiles.json'
            if candidate.is_file() and candidate.resolve() != manifest.resolve():
                specs.update(resolve_profiles(json.loads(candidate.read_text(encoding='utf-8')), candidate.parent, root))
                break
        p['profiles'] = specs
    for m in p['maps'].values():
        for e in m['events']:
            for pg in e['pages']:
                if pg['profile'] != 'none':
                    spec = p['profiles'].get(pg['profile'])
                    if not spec:
                        raise ValueError('Missing custom graphics ' + pg['profile'] + '; open original project from its original folder')
                    count = spec['counts'][pg['direction']] if spec['kind'] == 'character' else spec['counts'][0]
                    pg['frame'] = min(pg['frame'], count - 1)
    return validate(p)

def save(path, project):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    p = copy.deepcopy(validate(project))

    def rel(value):
        try:
            return os.path.relpath(value, path.parent)
        except ValueError:
            return value
    for m in p['maps'].values():
        if m.get('image'):
            m['image'] = rel(m['image'])
    for spec in p['profiles'].values():
        spec['file'] = rel(spec['file'])
    if p.get('font'):
        p['font'] = rel(p['font'])
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(path)
