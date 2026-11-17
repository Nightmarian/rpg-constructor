import bisect
import copy
import math

def sample(samples, t):
    i = max(0, min(len(samples) - 1, bisect.bisect_right(samples, t, key=lambda s: s['t']) - 1))
    a = samples[i]
    out = copy.deepcopy(a)
    if i + 1 < len(samples):
        b = samples[i + 1]
        span = b['t'] - a['t']
        r = max(0, min(1, (t - a['t']) / span)) if span > 0 else 0
        out['fade'] = a.get('fade', 0.0) + (b.get('fade', 0.0) - a.get('fade', 0.0)) * r
        if a['map_id'] == b['map_id']:
            p = out['player']
            q = b['player']
            p['x'] += (q['x'] - p['x']) * r
            p['y'] += (q['y'] - p['y']) * r
            if p['moving'] and q['moving'] and (p['direction'] == q['direction']):
                p['phase'] += (q['phase'] - p['phase']) * r
            for key, n in out.get('actors', {}).items():
                q = b.get('actors', {}).get(key)
                if q and n.get('page') == q.get('page'):
                    n['x'] += (q['x'] - n['x']) * r
                    n['y'] += (q['y'] - n['y']) * r
                    if n['moving'] and q['moving'] and (n['direction'] == q['direction']):
                        n['phase'] += (q['phase'] - n['phase']) * r
    return out

def frame_count(samples):
    return max(1, math.ceil(samples[-1]['t'] * 30))
