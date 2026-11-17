import copy
from project.schema import page

def convert(d):
    d = copy.deepcopy(d)
    v = d.get('format_version')
    if v in (1, 2, 3):
        m = {k: d.get(k) for k in ('width', 'height', 'tile_size', 'image', 'image_size')}
        m.update(spawn=d.get('spawn', [m['width'] * m['tile_size'] / 2, m['height'] * m['tile_size'] / 2]), blocked=d.get('blocked', []), events=[])
        d = dict(format_version=4, start_map='map_1', maps={'map_1': m}, speed=d.get('speed', 240), animation_fps=d.get('animation_fps', 10), camera_zoom=d.get('camera_zoom', 1))
        v = 4
    if v == 4:
        d['switches'] = {}
        for m in d['maps'].values():
            for e in m['events']:
                kind = e.pop('kind')
                flag = e.get('flag', '')
                e['profile'] = 'npc_green' if kind == 'npc' else 'lever_red' if kind == 'lever' else 'none'
                e['visual_flag'] = flag
                if kind in ('text', 'npc'):
                    cmds = [dict(type='text', name=e.get('name', ''), text=text.strip()) for text in e.get('text', '').split('|') if text.strip()]
                elif kind == 'lever':
                    flag = flag or e['id']
                    e['visual_flag'] = flag
                    cmds = [dict(type='switch', flag=flag, operation='toggle')]
                else:
                    cmds = [dict(type='transfer', target=e['target'], tx=e['tx'], ty=e['ty'], direction=e.get('direction', 0))]
                    if flag:
                        cmds[0].update(condition=flag, expected=True)
                        cmds.insert(0, dict(type='text', name='', text=e.get('text') or 'Заперто.', condition=flag, expected=False))
                if flag:
                    d['switches'][flag] = flag
                e['commands'] = cmds
        v = 5
    if v == 5:

        def commands(old):
            result = []
            for c in old:
                c = copy.deepcopy(c)
                cond = c.pop('condition', '')
                expected = c.pop('expected', True)
                if cond:
                    c = dict(type='if', condition=dict(switch=cond, value=expected), then=[c], **{'else': []})
                result.append(c)
            return result
        for m in d['maps'].values():
            for e in m['events']:
                p = page('Основное', e.get('profile', 'none'), 0, commands(e.get('commands', [])))
                p.update(trigger=e.get('trigger', 'action'), direction=e.get('direction', 0))
                pages = [p]
                flag = e.get('visual_flag', '')
                if flag:
                    other = copy.deepcopy(p)
                    other.update(name='Включено', frame=1, condition=dict(switch=flag, value=True))
                    pages.append(other)
                e['pages'] = pages
                for key in ('commands', 'profile', 'visual_flag', 'trigger', 'direction'):
                    e.pop(key, None)
        d['format_version'] = 6
    if d.get('format_version') == 6:
        d['format_version'] = 7
    d.setdefault('hero', 'hero_blue')
    d.setdefault('switches', {})
    d.setdefault('font', '')
    d.setdefault('font_size', 22)
    d.setdefault('preview', 'native')
    d.setdefault('output_size', [1920, 1080])
    return d
