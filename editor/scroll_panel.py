import tkinter as tk
from tkinter import ttk

class ScrollPanel(ttk.Frame):

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(self, highlightthickness=0, width=280, height=180)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.vertical = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.vertical.grid(row=0, column=1, sticky='ns')
        self.horizontal = ttk.Scrollbar(self, orient='horizontal', command=self.canvas.xview)
        self.horizontal.grid(row=1, column=0, sticky='ew')
        self.canvas.configure(yscrollcommand=self.vertical.set, xscrollcommand=self.horizontal.set)
        self.content = ttk.Frame(self.canvas, padding=8)
        self.item = self.canvas.create_window(0, 0, anchor='nw', window=self.content)
        self._pending = None
        self._bound = set()
        self.content.bind('<Configure>', self.schedule)
        self.canvas.bind('<Configure>', self.schedule)
        self.canvas.bind('<MouseWheel>', self.wheel)
        self.canvas.bind('<Button-4>', lambda e: self.canvas.yview_scroll(-3, 'units'))
        self.canvas.bind('<Button-5>', lambda e: self.canvas.yview_scroll(3, 'units'))
        self.schedule()

    def schedule(self, event=None):
        if self._pending is None:
            self._pending = self.after_idle(self.layout)

    def layout(self, event=None):
        self._pending = None
        if not self.winfo_exists():
            return
        desired = max(self.content.winfo_reqwidth(), self.canvas.winfo_width())
        if int(float(self.canvas.itemcget(self.item, 'width'))) != desired:
            self.canvas.itemconfigure(self.item, width=desired)
        bounds = self.canvas.bbox(self.item)
        if bounds:
            self.canvas.configure(scrollregion=bounds)
        self.bind_children(self.content)

    def bind_children(self, parent):
        for child in parent.winfo_children():
            if str(child) not in self._bound:
                if not isinstance(child, (tk.Text, tk.Listbox, ttk.Treeview, ttk.Combobox, ttk.Scrollbar)):
                    child.bind('<MouseWheel>', self.wheel, add='+')
                self._bound.add(str(child))
            self.bind_children(child)

    def wheel(self, event):
        units = -int(event.delta / 120)
        if not units and event.delta:
            units = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(units, 'units')
        return 'break'

def fit_dialog(window, width=1000, height=660):
    width = min(width, max(560, window.winfo_screenwidth() - 100))
    height = min(height, max(360, window.winfo_screenheight() - 160))
    window.geometry(f'{width}x{height}')
    window.minsize(min(760, width), min(440, height))
