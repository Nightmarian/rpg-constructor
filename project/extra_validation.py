import math

def number(v, lo, hi):
    return type(v) in (int, float) and math.isfinite(v) and (lo <= v <= hi)

def check(p):
    if p.get('random_seed') is not None and type(p['random_seed']) is not int:
        raise ValueError('Random seed must be an integer or null')
    if not number(p.get('transition_seconds', 0.25), 0, 2):
        raise ValueError('Invalid transition duration')
    for key, s in p['profiles'].items():
        if not number(s.get('scale', 1), 0.1, 8):
            raise ValueError('Invalid scale: ' + key)
        w, h = s['frame_size']
        if type(w) is not int or type(h) is not int or min(w, h) < 1:
            raise ValueError('Invalid frame size')
        if len(s['anchor']) != 2 or not all((number(v, 0, limit) for v, limit in zip(s['anchor'], (w, h)))):
            raise ValueError('Invalid anchor')
        if s['kind'] not in ('character', 'object') or len(s['counts']) != (4 if s['kind'] == 'character' else 1) or any((type(v) is not int or v < 1 for v in s['counts'])):
            raise ValueError('Invalid sprite rows')
    for m in p['maps'].values():
        for edge in m.get('edges', []):
            if len(edge) != 3 or any((type(v) is not int for v in edge)) or (not (0 <= edge[0] < m['width'] and 0 <= edge[1] < m['height'] and (edge[2] in range(4)))):
                raise ValueError('Invalid passage edge')
        for e in m['events']:
            for pg in e['pages']:
                if pg['direction'] not in range(4):
                    raise ValueError('Invalid direction')
                cfg = pg.get('movement', {})
                if cfg.get('mode', 'fixed') not in ('fixed', 'random', 'approach', 'route'):
                    raise ValueError('Invalid movement mode')
                if not number(cfg.get('speed', 100), 1, 2000) or not number(cfg.get('delay', 0.3), 0, 60) or (not number(cfg.get('radius', 3), 1, 100)):
                    raise ValueError('Invalid movement speed/delay/radius')
                for c in cfg.get('route', []):
                    if c.get('op') == 'random_wait':
                        lo = c.get('min_seconds', 1)
                        hi = c.get('max_seconds', 3)
                        if not number(lo, 0, 60) or not number(hi, 0, 60) or lo > hi:
                            raise ValueError('Invalid random wait range')
                    if c.get('op') not in ('up', 'down', 'left', 'right', 'turn', 'wait', 'random_step', 'random_wait'):
                        raise ValueError('Invalid route command')
                    if c['op'] == 'wait' and (not number(c.get('seconds', 1), 0, 60)):
                        raise ValueError('Invalid wait')
                    if c['op'] == 'turn' and c.get('direction', 0) not in range(4):
                        raise ValueError('Invalid turn')
