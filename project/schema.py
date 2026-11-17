import math

def page(name='Состояние', profile='none', frame=0, commands=None, condition=None):
    return dict(name=name, profile=profile, frame=frame, direction=0, trigger='action', condition=condition or {}, commands=commands or [])

def condition_ok(condition, flags, self_flags, event_key=''):
    if condition.get('switch'):
        if bool(flags.get(condition['switch'], False)) != bool(condition.get('value', True)):
            return False
    if condition.get('self'):
        if bool(self_flags.get(event_key + ':' + condition['self'], False)) != bool(condition.get('self_value', True)):
            return False
    return True

def active_page(event, flags, self_flags, event_key):
    return next((p for p in reversed(event['pages']) if condition_ok(p.get('condition', {}), flags, self_flags, event_key)), None)

def validate(p):
    if p.get('format_version') != 7:
        raise ValueError('Unsupported project format')
    if not p.get('maps') or p.get('start_map') not in p['maps']:
        raise ValueError('Invalid maps/start map')
    for key, lo, hi in (('speed', 1, 2000), ('animation_fps', 1, 60), ('camera_zoom', 0.25, 4), ('font_size', 12, 48)):
        v = p[key]
        if type(v) not in (int, float) or not math.isfinite(v) or (not lo <= v <= hi):
            raise ValueError('Invalid ' + key)
    w, h = p['output_size']
    if type(w) is not int or type(h) is not int or (not (320 <= w <= 3840 and 180 <= h <= 2160)) or w % 2 or h % 2 or (w * 9 != h * 16):
        raise ValueError('Invalid video dimensions')
    if p['hero'] not in p['profiles'] or p['profiles'][p['hero']]['kind'] != 'character':
        raise ValueError('Invalid hero profile')

    def check_condition(c):
        if c.get('switch') and c['switch'] not in p['switches']:
            raise ValueError('Missing switch')
        if c.get('self') and c['self'] not in ('A', 'B', 'C', 'D'):
            raise ValueError('Invalid local switch')

    def commands(items, depth=0):
        if depth > 20:
            raise ValueError('Condition nesting exceeds 20')
        for c in items:
            kind = c['type']
            if kind == 'if':
                check_condition(c['condition'])
                commands(c['then'], depth + 1)
                commands(c['else'], depth + 1)
            elif kind == 'switch':
                if c['flag'] not in p['switches'] or c['operation'] not in ('on', 'off', 'toggle'):
                    raise ValueError('Invalid switch command')
            elif kind == 'self_switch':
                if c['flag'] not in ('A', 'B', 'C', 'D') or c['operation'] not in ('on', 'off', 'toggle'):
                    raise ValueError('Invalid local command')
            elif kind == 'transfer':
                if c['target'] not in p['maps']:
                    raise ValueError('Missing destination map')
                m = p['maps'][c['target']]
                if any((type(c[k]) is not int for k in ('tx', 'ty'))) or not (0 <= c['tx'] < m['width'] and 0 <= c['ty'] < m['height']) or c.get('direction', 0) not in range(4):
                    raise ValueError('Invalid destination')
            elif kind == 'sound':
                if not c.get('file'):
                    raise ValueError('Missing sound file')
                volume = c.get('volume', 100)
                if type(volume) not in (int, float) or not 0 <= volume <= 100:
                    raise ValueError('Invalid sound volume')
            elif kind == 'show_image':
                if not c.get('file'):
                    raise ValueError('Missing image file')
                if any(type(c.get(key, 0)) not in (int, float) for key in ('x', 'y', 'scale')):
                    raise ValueError('Invalid image settings')
                if c.get('scale', 100) <= 0:
                    raise ValueError('Invalid image scale')
            elif kind == 'hide_image':
                pass
            elif kind not in ('text', 'comment', 'separator'):
                raise ValueError('Unknown command')
    from project.extra_validation import check
    check(p)
    for mid, m in p['maps'].items():
        for key in ('width', 'height', 'tile_size'):
            if type(m[key]) is not int or m[key] < 1:
                raise ValueError('Invalid map ' + mid)
        if len(m['spawn']) != 2 or any((type(v) not in (int, float) or not math.isfinite(v) for v in m['spawn'])):
            raise ValueError('Invalid spawn')
        seen = set()
        for e in m['events']:
            if not e['id'] or e['id'] in seen:
                raise ValueError('Duplicate event ID')
            seen.add(e['id'])
            if type(e['x']) is not int or type(e['y']) is not int or (not (0 <= e['x'] < m['width'] and 0 <= e['y'] < m['height'])):
                raise ValueError('Event outside map')
            for pg in e['pages']:
                check_condition(pg.get('condition', {}))
                key = pg['profile']
                if key != 'none':
                    if key not in p['profiles']:
                        raise ValueError('Missing profile: ' + key)
                    spec = p['profiles'][key]
                    count = spec['counts'][pg['direction']] if spec['kind'] == 'character' else spec['counts'][0]
                    if type(pg['frame']) is not int or not 0 <= pg['frame'] < count:
                        raise ValueError('Invalid frame')
                if pg['direction'] not in range(4) or pg['trigger'] not in ('action', 'touch'):
                    raise ValueError('Invalid page settings')
                commands(pg['commands'])
    return p
