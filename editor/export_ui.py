import copy
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from engine.exporter import Job

def start(a):
    if not a.take:
        messagebox.showinfo('Нет дубля', 'Записать → исполнить → Стоп.', parent=a.window)
        return
    path = filedialog.asksaveasfilename(parent=a.window, initialdir=str(a.root / 'recordings'), defaultextension='.mp4', filetypes=[('MP4', '*.mp4')])
    if not path:
        return
    samples, p, scene = a.take
    a.playing = False
    a.keys.clear()
    a.job = Job(copy.copy(scene), copy.deepcopy(p), samples, path, a.project['output_size'], a.log)
    w = tk.Toplevel(a.window)
    w.title('Экспорт')
    w.geometry('470x150')
    label = ttk.Label(w, text='Подготовка…', padding=12)
    label.pack(fill='x')
    bar = ttk.Progressbar(w, maximum=100)
    bar.pack(fill='x', padx=12)

    def cancel():
        if a.job:
            a.job.cancel.set()
            label.config(text='Отмена…')
    ttk.Button(w, text='Отмена', command=cancel).pack(pady=10)
    w.protocol('WM_DELETE_WINDOW', cancel)

    def poll():
        if not a.job:
            return
        try:
            while True:
                kind, value = a.job.events.get_nowait()
                if kind == 'progress':
                    done, total = value
                    bar['value'] = 100 * done / total
                    label.config(text=f'Кадр {done} / {total}')
                else:
                    a.job = None
                    w.destroy()
                    a.status.set('Видео готово: ' + value if kind == 'done' else 'Отменено' if kind == 'cancelled' else 'Ошибка: ' + value)
                    a.invalidate()
                    if kind == 'error':
                        a.show_log()
                    return
        except queue.Empty:
            pass
        a.window.after(100, poll)
    poll()
