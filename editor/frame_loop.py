import time

def tick(a):
    if a.recording and not hasattr(a, 'record_start'):
        a.record_start = time.perf_counter()
    if a.recording:
        a.samples.append(a.world.snapshot(time.perf_counter() - a.record_start))
    a.world.update(1 / 60)
    a.world.draw(a.scene, a.canvas, a.item, a.zoom, a.cx, a.cy, a.grid.get(), a.marks.get(), a.collisions.get())
    a.window.after(16, a.tick)
