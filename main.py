import logging
import platform
from pathlib import Path
from datetime import datetime
from collections import deque
ROOT = Path(__file__).resolve().parent
RECORDS = deque(maxlen=3000)

class Buffer(logging.Handler):

    def emit(self, r):
        RECORDS.extend(self.format(r).splitlines())

def main():
    folder = ROOT / 'logs'
    folder.mkdir(exist_ok=True)
    path = folder / (datetime.now().strftime('session_%Y%m%d_%H%M%S_%f') + '.log')
    log = logging.getLogger('rpg')
    log.setLevel(logging.INFO)
    fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    for h in (logging.FileHandler(path, encoding='utf-8'), logging.StreamHandler(), Buffer()):
        h.setFormatter(fmt)
        log.addHandler(h)
    try:
        log.info('RPG Constructor 0.9.5 | %s', platform.platform())
        from support.dpi import configure
        configure(log)
        from editor.app import App
        App(ROOT, log, RECORDS, path).run()
    except Exception:
        log.exception('Fatal error')
        return 1
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
