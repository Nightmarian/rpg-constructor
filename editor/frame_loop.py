import time
from PIL import Image, ImageTk

def tick(a):
    if not a.running:
        return
    started = time.perf_counter()
    try:
        dt = min(0.25, max(0, started - a.last))
        a.last = started
        if a.modal or a.job:
            a.window.after(50, a.tick)
            return
        if 'Escape' in a.keys and (not a.recording):
            a.playing = False
            a.keys.clear()
            a.invalidate()
        vw = max(1, a.canvas.winfo_width())
        vh = max(1, a.canvas.winfo_height())
        if a.playing:
            a.world.update(a.keys, dt, a.scene.size(a.project, a.world.map_id), a.collisions.get())
            if a.recording:
                a.samples.append(a.world.snapshot(started - a.record_start))
            a.map_var.set(a.world.map_id)
            scale = min(vw / 16, vh / 9)
            dw = max(1, int(scale * 16))
            dh = max(1, int(scale * 9))
            quality = a.project['preview']
            rw, rh = (960, 540) if quality == 'economy' else (dw, dh)
            if quality == '1080p' and rw > 1920:
                rw, rh = (1920, 1080)
            frame = a.scene.draw(a.project, a.world.view_state(), (rw, rh))
            display = Image.new('RGB', (vw, vh), (18, 21, 27))
            display.paste(frame if frame.size == (dw, dh) else frame.resize((dw, dh), Image.Resampling.BILINEAR), ((vw - dw) // 2, (vh - dh) // 2))
        else:
            a.cx += (int('Right' in a.keys) - int('Left' in a.keys)) * 500 * dt / a.zoom
            a.cy += (int('Down' in a.keys) - int('Up' in a.keys)) * 500 * dt / a.zoom
            key = (vw, vh, a.cx, a.cy, a.zoom, a.world.map_id, a.grid.get(), a.marks.get(), a.revision)
            if key == a.cache:
                a.window.after(33, a.tick)
                return
            display = a.scene.draw(a.project, a.world.view_state(), (vw, vh), (a.cx, a.cy), (vw / a.zoom, vh / a.zoom), a.grid.get(), a.marks.get(), True)
            a.cache = key
        if not a.playing:
            from editor.overlay import draw
            display = draw(a, display)
        a.photo = ImageTk.PhotoImage(display)
        a.canvas.itemconfig(a.item, image=a.photo)
        if a.recording:
            a.status.set(f'ЗАПИСЬ {started - a.record_start:.1f} с | Стоп → MP4')
        elif a.playing:
            a.status.set(f'ПРОСМОТР {a.world.map_id} | кадр {(time.perf_counter() - started) * 1000:.1f} мс | {dw}×{dh} | WASD/стрелки, Пробел, Escape')
    except Exception:
        a.log.exception('Frame map=%s', a.world.map_id)
        a.playing = False
        a.recording = False
        a.keys.clear()
        a.status.set('Ошибка кадра: журнал')
    a.window.after(max(1, round(1000 / 30 - (time.perf_counter() - started) * 1000)), a.tick)
