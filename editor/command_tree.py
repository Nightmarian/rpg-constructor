from tkinter import ttk, font as tkfont
from editor.command_ui import edit
from editor.command_view_model import build_rows, max_depth
_KEEP = object()

class CommandTree:

    def __init__(self, parent, a, p):
        self.a = a
        self.p = p
        self.items = []
        self.lookup = {}
        self.records = {}
        self.pending = None
        self.last_width = 0
        self.frame = ttk.Frame(parent)
        bar = ttk.Frame(self.frame)
        bar.pack(side='bottom', fill='x', pady=3)
        for text, fn in [('Добавить', self.add), ('Изменить', self.change), ('Удалить', self.delete), ('Выше', lambda: self.move(-1)), ('Ниже', lambda: self.move(1))]:
            ttk.Button(bar, text=text, command=fn).pack(side='left', padx=3)
        area = ttk.Frame(self.frame)
        area.pack(fill='both', expand=True)
        self.font = tkfont.Font(root=self.frame, font=('Segoe UI', 10))
        ttk.Style(self.frame).configure('Commands.Treeview', rowheight=max(34, self.font.metrics('linespace') + 10), font=self.font)
        self.tree = ttk.Treeview(area, show='tree', selectmode='browse', style='Commands.Treeview')
        self.tree.column('#0', width=260, minwidth=120, stretch=False)
        xbar = ttk.Scrollbar(area, orient='horizontal', command=self.tree.xview)
        xbar.pack(side='bottom', fill='x')
        ybar = ttk.Scrollbar(area, orient='vertical', command=self.tree.yview)
        ybar.pack(side='right', fill='y')
        self.tree.configure(xscrollcommand=xbar.set, yscrollcommand=ybar.set)
        self.tree.pack(fill='both', expand=True)
        for tag, opts in [('even', dict(background='#f1f4f8')), ('odd', dict(background='#ffffff')), ('branch', dict(background='#dce8f5', foreground='#193755')), ('note', dict(foreground='#657450'))]:
            self.tree.tag_configure(tag, **opts)
        self.tree.bind('<Double-1>', lambda e: self.change())
        self.tree.bind('<Configure>', self.resize)
        self.frame.bind('<Destroy>', self.destroy, add='+')

    def destroy(self, event):
        if event.widget is self.frame and self.pending is not None:
            try:
                self.frame.after_cancel(self.pending)
            except Exception:
                pass
            self.pending = None

    def resize(self, event):
        if abs(event.width - self.last_width) < 2:
            return
        self.last_width = event.width
        if self.pending is not None:
            self.frame.after_cancel(self.pending)
        self.pending = self.frame.after(80, self.reflow)

    def reflow(self):
        self.pending = None
        if self.frame.winfo_exists():
            self.refresh()

    def set(self, items):
        self.items = items
        self.refresh(focus=None, keep_scroll=False)

    def refresh(self, focus=_KEEP, keep_scroll=True):
        selected = self.tree.selection()
        previous = self.records.get(selected[0]) if selected else None
        if focus is _KEEP:
            focus = previous['items'] if previous and previous['branch'] else previous['command'] if previous else None
        opened = {key: bool(self.tree.tk.getboolean(self.tree.item(key, 'open'))) for key in self.records if self.tree.exists(key)}
        scroll = self.tree.yview()[0] if keep_scroll else 0
        width = max(120 + 20 * max_depth(self.items), self.tree.winfo_width() - 4)
        self.tree.column('#0', width=width, stretch=False)
        rows = build_rows(self.items, self.p, width, self.font.measure)
        self.tree.delete(*self.tree.get_children())
        self.lookup = {}
        self.records = {}
        restore = None
        for row in rows:
            key = row['key']
            self.tree.insert(row['parent'], 'end', iid=key, text=row['text'], open=opened.get(key, True), tags=(row['tag'],))
            self.lookup[key] = (row['items'], row['index'], row['branch'])
            self.records[key] = row
            if restore is None and focus is not None and (row['branch'] and row['items'] is focus or (not row['branch'] and row['command'] is focus)):
                restore = key
        if restore:
            self.tree.selection_set(restore)
            self.tree.focus(restore)
        self.tree.yview_moveto(scroll)
        if hasattr(self.a, 'theme'):
            self.a.theme.apply_window(self.frame)

    def selected(self):
        return self.lookup.get(self.tree.selection()[0]) if self.tree.selection() else None

    def add(self):
        selection = self.selected()
        items, i, branch = selection if selection else (self.items, None, True)
        c = edit(self.a, self.p)
        if c:
            items.insert(len(items) if branch or i is None else i + 1, c)
            self.refresh(focus=c)

    def change(self):
        selected = self.selected()
        if not selected or selected[2]:
            return
        items, i, _ = selected
        c = edit(self.a, self.p, items[i])
        if c:
            items[i] = c
            self.refresh(focus=c)

    def delete(self):
        selected = self.selected()
        if selected and (not selected[2]):
            selected[0].pop(selected[1])
            self.refresh(focus=None)

    def move(self, delta):
        selected = self.selected()
        if selected and (not selected[2]):
            items, i, _ = selected
            if 0 <= i + delta < len(items):
                c = items[i]
                items[i], items[i + delta] = (items[i + delta], items[i])
                self.refresh(focus=c)
