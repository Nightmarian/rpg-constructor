import unittest
import random
import tempfile
import json
from pathlib import Path
from engine.random_movement import resolve_command
from editor.theme_preferences import load_theme, save_theme

class RandomCommands(unittest.TestCase):

    def test_random_step_all_directions(self):
        rng = random.Random(5)
        values = {resolve_command({'op': 'random_step'}, rng)['op'] for _ in range(100)}
        self.assertEqual(values, {'up', 'down', 'left', 'right'})

    def test_wait_range(self):
        rng = random.Random(10)
        values = [resolve_command({'op': 'random_wait', 'min_seconds': 1, 'max_seconds': 3}, rng)['seconds'] for _ in range(100)]
        self.assertTrue(all((1 <= v <= 3 for v in values)))
        self.assertGreater(len(set(values)), 1)

    def test_no_mutation(self):
        c = {'op': 'random_wait', 'min_seconds': 1, 'max_seconds': 2}
        resolve_command(c, random.Random())
        self.assertEqual(c, {'op': 'random_wait', 'min_seconds': 1, 'max_seconds': 2})

    def test_regular_command_unchanged(self):
        c = {'op': 'left'}
        self.assertIs(resolve_command(c, random.Random()), c)

    def test_seed_repeatable(self):
        a = random.Random(42)
        b = random.Random(42)
        self.assertEqual([resolve_command({'op': 'random_step'}, a) for _ in range(20)], [resolve_command({'op': 'random_step'}, b) for _ in range(20)])

class Preferences(unittest.TestCase):

    def test_default_and_persist(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'settings.json'
            self.assertEqual(load_theme(p), 'light')
            save_theme(p, 'dark')
            self.assertEqual(load_theme(p), 'dark')
            save_theme(p, 'light')
            self.assertEqual(load_theme(p), 'light')

    def test_preserve_other_keys(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'settings.json'
            p.write_text('{"other":1}')
            save_theme(p, 'dark')
            self.assertEqual(json.loads(p.read_text())['other'], 1)

    def test_bad_config(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'settings.json'
            p.write_text('[]')
            self.assertEqual(load_theme(p), 'light')

    def test_bad_theme(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                save_theme(Path(d) / 'settings.json', 'unknown')

class CompactLayout(unittest.TestCase):

    def test_left_actions_reserved_and_original_columns(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / 'editor/event_ui.py').read_text(encoding='utf-8')
        self.assertNotIn('Panedwindow', source)
        self.assertNotIn('ScrollPanel', source)
        self.assertLess(source.index('general_actions.pack'), source.index('pgname ='))
        self.assertLess(source.index('bottom.pack'), source.index('body.pack'))

    def test_movement_footer_grid(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / 'editor/movement_ui.py').read_text(encoding='utf-8')
        self.assertIn('rowconfigure(1, weight=1)', source)
        self.assertIn('random_wait', source)

class ActualTkTheme(unittest.TestCase):

    def test_dark_light_switch(self):
        try:
            import tkinter as tk
            from tkinter import ttk
            root = tk.Tk()
        except ImportError as exc:
            self.skipTest(str(exc))
        except Exception as exc:
            if exc.__class__.__name__ == 'TclError':
                self.skipTest(str(exc))
            raise
        try:
            from types import SimpleNamespace
            import logging
            from editor.theme import ThemeManager
            with tempfile.TemporaryDirectory() as d:
                menu = tk.Menu(root)
                view = tk.Menu(menu, tearoff=False)
                menu.add_cascade(label='Вид', menu=view)
                root.configure(menu=menu)
                a = SimpleNamespace(window=root, root=Path(d), log=logging.getLogger('test'), invalidate=lambda: None)
                theme = ThemeManager(a)
                theme.install()
                box = tk.Listbox(root)
                box.pack()
                entry = ttk.Entry(root)
                entry.pack()
                theme.choice.set('dark')
                theme.change()
                root.update()
                self.assertEqual(box.cget('background'), theme.colors['field'])
                self.assertEqual(load_theme(Path(d) / 'editor_settings.json'), 'dark')
                theme.choice.set('light')
                theme.change()
                root.update()
                self.assertEqual(box.cget('background'), theme.colors['field'])
        finally:
            root.destroy()

class RouteIntegration(unittest.TestCase):

    def project(self):
        from project import storage
        root = Path(__file__).resolve().parents[1]
        p = storage.load(root / 'assets/demo_project.json', root)
        p['maps']['room']['events'] = p['maps']['room']['events'][:1]
        return (root, p)

    def test_random_wait_runs(self):
        from engine.world import World
        from project.schema import validate
        root, p = self.project()
        pg = p['maps']['room']['events'][0]['pages'][0]
        pg['movement'] = {'mode': 'route', 'route': [{'op': 'random_wait', 'min_seconds': 1, 'max_seconds': 2}], 'repeat': False}
        validate(p)
        w = World(root, p)
        w.update(set(), 0.01, (1536, 1024), False)
        self.assertTrue(1 <= w.npcs.states['room:Сосед']['wait'] <= 2)

    def test_seeded_random_step_runs(self):
        from engine.world import World
        import copy
        root, p = self.project()
        p['random_seed'] = 72
        p['maps']['room']['events'][0]['pages'][0]['movement'] = {'mode': 'route', 'route': [{'op': 'random_step'}], 'speed': 80, 'repeat': False}
        a = World(root, p)
        b = World(root, copy.deepcopy(p))
        a.update(set(), 0.1, (1536, 1024), False)
        b.update(set(), 0.1, (1536, 1024), False)
        self.assertEqual(a.npcs.snapshot(), b.npcs.snapshot())

    def test_invalid_wait_rejected(self):
        from project.schema import validate
        root, p = self.project()
        p['maps']['room']['events'][0]['pages'][0]['movement'] = {'mode': 'route', 'route': [{'op': 'random_wait', 'min_seconds': 3, 'max_seconds': 1}]}
        with self.assertRaises(ValueError):
            validate(p)
