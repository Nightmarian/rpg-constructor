import tkinter as tk
from tkinter import ttk, font as tkfont
from editor.theme_preferences import load_theme, save_theme
from editor.theme_colors import PALETTES

class ThemeManager:

    def __init__(self, a):
        self.a = a
        self.root = a.window
        self.path = a.root / 'editor_settings.json'
        self.style = ttk.Style(self.root)
        self.choice = tk.StringVar(self.root, value=load_theme(self.path))

    def install(self):
        menu = self.root.nametowidget(self.root.cget('menu'))
        view = None
        for i in range((menu.index('end') or 0) + 1):
            try:
                if menu.entrycget(i, 'label') == 'Вид':
                    view = self.root.nametowidget(menu.entrycget(i, 'menu'))
                    break
            except tk.TclError:
                continue
        if view is not None:
            view.add_separator()
            sub = tk.Menu(view, tearoff=False)
            for title, value in [('Светлая', 'light'), ('Тёмная', 'dark')]:
                sub.add_radiobutton(label=title, value=value, variable=self.choice, command=self.change)
            view.add_cascade(label='Тема', menu=sub)
        self.root.bind_all('<Map>', self.mapped, add='+')
        self.apply()

    def mapped(self, event):
        if isinstance(event.widget, tk.Toplevel):
            window = event.widget
            self.root.after_idle(lambda: self.apply_window(window) if window.winfo_exists() else None)

    def change(self):
        try:
            save_theme(self.path, self.choice.get())
        except OSError:
            self.a.log.exception('Cannot save editor theme')
        self.apply()
        self.a.invalidate()

    def apply(self):
        p = PALETTES[self.choice.get()]
        self.colors = p
        self.style.theme_use('clam')
        self.style.configure('.', background=p['bg'], foreground=p['fg'])
        for name in ('TFrame', 'TLabel', 'TLabelframe', 'TLabelframe.Label', 'TCheckbutton', 'TRadiobutton'):
            self.style.configure(name, background=p['bg'], foreground=p['fg'])
        foreground = [('disabled', p['muted']), ('pressed', p['fg']), ('active', p['fg']), ('!disabled', p['fg'])]
        self.style.configure('TButton', background=p['button'], foreground=p['fg'], padding=(6, 4))
        self.style.map('TButton', background=[('disabled', p['disabled_bg']), ('pressed', p['pressed']), ('active', p['hover']), ('!disabled', p['button'])], foreground=foreground)
        for name in ('TCheckbutton', 'TRadiobutton'):
            self.style.map(name, foreground=foreground, background=[('active', p['bg']), ('!disabled', p['bg'])], indicatorcolor=[('selected', p['select']), ('!selected', p['field'])])
        for name in ('TEntry', 'TCombobox', 'TSpinbox'):
            self.style.configure(name, fieldbackground=p['field'], background=p['button'], foreground=p['fg'], insertcolor=p['fg'])
            self.style.map(name, fieldbackground=[('disabled', p['disabled_bg']), ('readonly', p['field']), ('!disabled', p['field'])], foreground=foreground, selectbackground=[('!disabled', p['select'])], selectforeground=[('!disabled', p['selected'])])
        self.style.configure('Treeview', background=p['panel'], fieldbackground=p['panel'], foreground=p['fg'])
        self.style.map('Treeview', background=[('selected', p['select'])], foreground=[('selected', p['selected'])])
        self.style.configure('Events.Treeview', rowheight=54)
        rowheight = max(34, tkfont.Font(root=self.root, font=('Segoe UI', 10)).metrics('linespace') + 10)
        self.style.configure('Commands.Treeview', rowheight=rowheight, font=('Segoe UI', 10))
        self.style.configure('TNotebook', background=p['bg'])
        self.style.configure('TNotebook.Tab', background=p['button'], foreground=p['fg'])
        self.style.map('TNotebook.Tab', background=[('selected', p['select']), ('active', p['hover'])], foreground=[('disabled', p['muted']), ('selected', p['selected']), ('active', p['fg'])])
        for name in ('Vertical.TScrollbar', 'Horizontal.TScrollbar'):
            self.style.configure(name, background=p['button'], troughcolor=p['field'], arrowcolor=p['fg'])
            self.style.map(name, background=[('pressed', p['pressed']), ('active', p['hover'])], arrowcolor=[('active', p['fg']), ('!disabled', p['fg'])])
        for option, color in [('background', p['field']), ('foreground', p['fg']), ('selectBackground', p['select']), ('selectForeground', p['selected'])]:
            self.root.option_add('*TCombobox*Listbox.' + option, color)
        self.apply_window(self.root)

    def apply_window(self, window):
        p = self.colors

        def paint(widget):
            try:
                if isinstance(widget, (tk.Tk, tk.Toplevel)):
                    widget.configure(background=p['bg'])
                elif isinstance(widget, (tk.Text, tk.Listbox)):
                    widget.configure(background=p['field'], foreground=p['fg'], selectbackground=p['select'], selectforeground=p['selected'])
                    if isinstance(widget, tk.Text):
                        widget.configure(insertbackground=p['fg'])
                elif isinstance(widget, (tk.Entry, tk.Spinbox)):
                    widget.configure(background=p['field'], foreground=p['fg'], insertbackground=p['fg'], selectbackground=p['select'], selectforeground=p['selected'])
                elif isinstance(widget, (tk.Checkbutton, tk.Radiobutton)):
                    widget.configure(background=p['bg'], foreground=p['fg'], activebackground=p['hover'], activeforeground=p['fg'], selectcolor=p['field'])
                elif isinstance(widget, tk.Button):
                    widget.configure(background=p['button'], foreground=p['fg'], activebackground=p['hover'], activeforeground=p['fg'])
                elif isinstance(widget, (tk.Frame, tk.LabelFrame, tk.Label)):
                    widget.configure(background=p['bg'])
                    if isinstance(widget, (tk.LabelFrame, tk.Label)):
                        widget.configure(foreground=p['fg'])
                elif isinstance(widget, tk.Canvas):
                    widget.configure(background=p['bg'])
                elif isinstance(widget, tk.Menu):
                    widget.configure(background=p['panel'], foreground=p['fg'], activebackground=p['select'], activeforeground=p['selected'])
                if isinstance(widget, ttk.Treeview):
                    for tag, opts in [('even', dict(background=p['stripe'], foreground=p['fg'])), ('odd', dict(background=p['panel'], foreground=p['fg'])), ('branch', dict(background=p['branch'], foreground=p['branch_fg'])), ('note', dict(foreground=p['note']))]:
                        widget.tag_configure(tag, **opts)
                for child in widget.winfo_children():
                    paint(child)
            except tk.TclError:
                self.a.log.debug('Theme widget disappeared: %s', widget)
        paint(window)
