PALETTES = {'light': dict(bg='#edf0f4', panel='#ffffff', fg='#202a36', muted='#657284', field='#ffffff', stripe='#f2f5f9', branch='#dbe7f4', branch_fg='#1c344e', note='#3e6232', button='#f3f5f8', hover='#dce6f2', pressed='#c6d5e8', select='#c7dbf0', selected='#182432', disabled_bg='#e2e7ee'), 'dark': dict(bg='#252c36', panel='#2e3744', fg='#e6eaf2', muted='#a4afbf', field='#1f2630', stripe='#28313e', branch='#34475e', branch_fg='#e1efff', note='#bdd5a4', button='#303b4b', hover='#40516a', pressed='#263343', select='#365c83', selected='#ffffff', disabled_bg='#303744')}

def contrast(a, b):

    def luminance(color):
        v = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        v = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in v]
        return sum((x * w for x, w in zip(v, (0.2126, 0.7152, 0.0722))))
    lo, hi = sorted((luminance(a), luminance(b)))
    return (hi + 0.05) / (lo + 0.05)
