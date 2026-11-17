from pathlib import Path
import json
import subprocess
import sys

def main():
    root = Path(__file__).resolve().parent
    if (root / '.update_incomplete').exists():
        print('Update is incomplete. Run the updater again into a new folder.')
        return 1
    own = root / '.venv' / 'Scripts' / 'python.exe'
    if own.is_file():
        exe = str(own)
    else:
        env = root / '_environment_090.json'
        exe = json.loads(env.read_text(encoding='utf-8'))['python'] if env.exists() else sys.executable
    if not Path(exe).is_file():
        print('Python environment not found. Run install.bat in this folder.')
        return 1
    args = ['-m', 'unittest', 'discover', '-s', 'tests', '-v'] if '--tests' in sys.argv else [str(root / 'main.py')]
    return subprocess.call([exe, *args], cwd=root)
if __name__ == '__main__':
    raise SystemExit(main())
