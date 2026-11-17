def fit(a):
    w, h = a.scene.size(a.project, a.world.map_id)
    a.zoom = max(0.05, min(4.0, min(max(1, a.canvas.winfo_width()) / w, max(1, a.canvas.winfo_height()) / h) * 0.94))
    a.cx = 0.0
    a.cy = 0.0
    a.invalidate()

def wheel(a, e):
    if a.playing or a.job:
        return
    old = a.zoom
    a.zoom = max(0.05, min(4.0, old * 1.15 ** (e.delta / 120)))
    a.cx += e.x / old - e.x / a.zoom
    a.cy += e.y / old - e.y / a.zoom
    a.invalidate()
