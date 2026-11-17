def wait(a, w):
    if hasattr(a, 'theme'):
        a.theme.apply_window(w)
    previous = a.window.grab_current()
    a.modal += 1
    a.keys.clear()
    w.transient(previous or a.window)
    w.grab_set()
    try:
        a.window.wait_window(w)
    finally:
        a.modal -= 1
        a.keys.clear()
        a.last = __import__('time').perf_counter()
        a.invalidate()
        if previous is not None and previous.winfo_exists():
            previous.grab_set()
            previous.focus_set()
        elif a.running and a.modal == 0:
            a.canvas.focus_set()
