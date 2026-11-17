class Transition:

    def __init__(self):
        self.phase = 'idle'
        self.elapsed = 0.0
        self.duration = 0.25
        self.command = None

    @property
    def active(self):
        return self.phase != 'idle'

    @property
    def alpha(self):
        if self.phase == 'idle':
            return 0.0
        ratio = min(1.0, max(0.0, self.elapsed / self.duration))
        return ratio if self.phase == 'out' else 1.0 - ratio

    def start(self, command, duration):
        self.command = dict(command)
        self.duration = max(0.001, duration)
        self.elapsed = 0.0
        self.phase = 'out'

    def update(self, dt, commit):
        if not self.active:
            return False
        self.elapsed = min(self.duration, self.elapsed + max(0.0, dt))
        if self.elapsed + 1e-09 < self.duration:
            return False
        if self.phase == 'out':
            commit(self.command)
            self.phase = 'in'
            self.elapsed = 0.0
            return False
        self.phase = 'idle'
        self.elapsed = 0.0
        self.command = None
        return True
