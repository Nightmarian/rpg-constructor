import sys

def normalize(symbol, code=None):
    if sys.platform == 'win32' and code in (87, 65, 83, 68):
        return {87: 'w', 65: 'a', 83: 's', 68: 'd'}[code]
    if symbol in ('Up', 'Down', 'Left', 'Right', 'Return', 'Escape', 'Delete'):
        return symbol
    return {'ц': 'w', 'ф': 'a', 'ы': 's', 'в': 'd'}.get(symbol.lower(), symbol.lower())
