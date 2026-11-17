import threading
import queue
import subprocess
from pathlib import Path
from engine.take import sample, frame_count

class Job:

    def __init__(self, scene, p, samples, path, size, log):
        self.events = queue.Queue()
        self.cancel = threading.Event()
        self.thread = threading.Thread(target=self.work, args=(scene, p, samples, Path(path), tuple(size), log), daemon=True)
        self.thread.start()

    def work(self, scene, p, samples, path, size, log):
        process = None
        errors = None
        temp = path.with_name(path.stem + '.partial.mp4')
        try:
            import imageio_ffmpeg
            path.parent.mkdir(parents=True, exist_ok=True)
            errors = open(path.with_suffix('.ffmpeg.log'), 'wb')
            cmd = [imageio_ffmpeg.get_ffmpeg_exe(), '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{size[0]}x{size[1]}', '-r', '30', '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(temp)]
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=errors, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            total = frame_count(samples)
            log.info('Export started %s frames=%s size=%s', path, total, size)
            for i in range(total):
                if self.cancel.is_set():
                    break
                process.stdin.write(scene.draw(p, sample(samples, i / 30), size).tobytes())
                if i % 15 == 0:
                    self.events.put(('progress', (i + 1, total)))
            if self.cancel.is_set():
                process.kill()
                process.wait()
                self.events.put(('cancelled', None))
                return
            process.stdin.close()
            code = process.wait(timeout=60)
            if code:
                raise RuntimeError('FFmpeg exit ' + str(code))
            temp.replace(path)
            log.info('Export completed %s', path)
            self.events.put(('done', str(path)))
        except Exception as exc:
            log.exception('Export failed')
            self.events.put(('error', str(exc)))
        finally:
            if process:
                if process.poll() is None:
                    process.kill()
                    process.wait()
                try:
                    process.stdin.close()
                except OSError:
                    pass
            if errors:
                errors.close()
            if temp.exists():
                try:
                    temp.unlink()
                except OSError:
                    log.warning('Cannot remove partial %s', temp)
