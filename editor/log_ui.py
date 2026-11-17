import tkinter as tk

def show(a):
    if a.log_window and a.log_window.winfo_exists():
        a.log_window.lift()
        return
    from tkinter.scrolledtext import ScrolledText
    w = tk.Toplevel(a.window)
    w.title('Журнал')
    w.geometry('1000x500')
    a.log_window = w
    text = ScrolledText(w, wrap='none')
    text.pack(fill='both', expand=True)
    last = ['']

    def refresh():
        if not w.winfo_exists():
            return
        current = '\n'.join(a.records)
        if current != last[0]:
            text.configure(state='normal')
            text.delete('1.0', 'end')
            text.insert('end', current)
            text.configure(state='disabled')
            last[0] = current
        w.after(1000, refresh)
    refresh()
