def wrap_text(text, width, measure):
    width = max(1, width)
    result = []
    for paragraph in str(text).replace('\r\n', '\n').replace('\r', '\n').split('\n'):
        line = ''
        for word in paragraph.split():
            joined = line + ' ' + word if line else word
            if measure(joined) <= width:
                line = joined
                continue
            if line:
                result.append(line)
                line = ''
            for ch in word:
                if line and measure(line + ch) > width:
                    result.append(line)
                    line = ''
                line += ch
        result.append(line)
    return result or ['']

def describe(c, p):

    def switch(key):
        return key + ' — ' + p['switches'].get(key, key)
    kind = c['type']
    if kind == 'text':
        return 'Показать текст: ' + c.get('name', '') + ' — ' + c.get('text', '')
    if kind == 'comment':
        return 'Комментарий: ' + c.get('text', '')
    if kind == 'separator':
        return '────────────────────'
    if kind in ('switch', 'self_switch'):
        return ('Общий: ' + switch(c['flag']) if kind == 'switch' else 'Локальный: ' + c['flag']) + ' → ' + {'on': 'ВКЛ', 'off': 'ВЫКЛ', 'toggle': 'переключить'}[c['operation']]
    if kind == 'transfer':
        return f'Переход: {c['target']} ({c['tx']}, {c['ty']})'
    condition = c['condition']
    parts = []
    if condition.get('switch'):
        parts.append(switch(condition['switch']) + (' = ВКЛ' if condition.get('value', True) else ' = ВЫКЛ'))
    if condition.get('self'):
        parts.append('Локальный ' + condition['self'] + (' = ВКЛ' if condition.get('self_value', True) else ' = ВЫКЛ'))
    return 'Если ' + (' и '.join(parts) or 'всегда')

def build_rows(items, p, width, measure):
    rows = []

    def fill(parent, commands, path, depth):
        for i, c in enumerate(commands):
            key = 'c' + path + str(i)
            kind = c['type']
            tag = 'branch' if kind == 'if' else 'note' if kind in ('comment', 'separator') else 'even' if i % 2 == 0 else 'odd'
            available = max(40, width - 44 - depth * 20 - (20 if kind == 'if' else 0) - measure('    '))
            lines = wrap_text(str(i + 1) + '. ' + describe(c, p), available, measure)
            for part, line in enumerate(lines):
                rows.append(dict(key=key if part == 0 else key + '_line' + str(part), parent=parent if part == 0 or kind != 'if' else key, text=line if part == 0 else '    ' + line, items=commands, index=i, branch=False, command=c, tag=tag, owner=key))
            if kind == 'if':
                for branch, title in [('then', 'ТО — условие выполнено'), ('else', 'ИНАЧЕ — условие не выполнено')]:
                    branch_key = key + '_' + branch
                    rows.append(dict(key=branch_key, parent=key, text=title, items=c[branch], index=None, branch=True, command=None, tag='branch', owner=branch_key))
                    fill(branch_key, c[branch], path + str(i) + '_' + branch + '_', depth + 2)
    fill('', items, '', 0)
    return rows

def max_depth(items):
    return max((2 + max(max_depth(c['then']), max_depth(c['else'])) for c in items if c['type'] == 'if'), default=0)
