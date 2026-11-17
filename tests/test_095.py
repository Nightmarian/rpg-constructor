import unittest
from pathlib import Path
from editor.edge_edit import closest_edge, set_wall
from editor.command_view_model import wrap_text, build_rows
from editor.theme_colors import PALETTES, contrast

class Edges(unittest.TestCase):

    def setUp(self):
        self.m = {'width': 5, 'height': 5, 'tile_size': 100, 'blocked': [], 'edges': []}

    def test_three_sides_independent(self):
        for d in (1, 2, 3):
            set_wall(self.m, 2, 2, d)
        self.assertEqual({tuple(e) for e in self.m['edges'] if e[:2] == [2, 2]}, {(2, 2, 1), (2, 2, 2), (2, 2, 3)})
        self.assertNotIn([2, 2, 0], self.m['edges'])

    def test_three_sides_block_but_fourth_open(self):
        from engine.passage import allowed
        for d in (1, 2, 3):
            set_wall(self.m, 2, 2, d)
        self.assertFalse(allowed(self.m, 201, 250, 199, 250))
        self.assertFalse(allowed(self.m, 299, 250, 301, 250))
        self.assertFalse(allowed(self.m, 250, 201, 250, 199))
        self.assertTrue(allowed(self.m, 250, 299, 250, 301))

    def test_four_sides_and_one_removal(self):
        for d in range(4):
            set_wall(self.m, 2, 2, d)
        set_wall(self.m, 2, 2, 2, False)
        self.assertEqual(len([e for e in self.m['edges'] if e[:2] == [2, 2]]), 3)
        self.assertNotIn([3, 2, 1], self.m['edges'])

    def test_idempotent_drag(self):
        for _ in range(10):
            set_wall(self.m, 2, 2, 3)
        self.assertEqual(len(self.m['edges']), 2)

    def test_click_nearest_side(self):
        for x, y, d in [(201, 250, 1), (299, 250, 2), (250, 201, 3), (250, 299, 0)]:
            self.assertEqual(closest_edge(self.m, x, y), (2, 2, d))

    def test_outside(self):
        self.assertIsNone(closest_edge(self.m, -1, 0))

    def test_edge_of_map(self):
        set_wall(self.m, 0, 0, 3)
        self.assertEqual(self.m['edges'], [[0, 0, 3]])

    def test_passage_engine_unchanged(self):
        from engine.passage import allowed
        set_wall(self.m, 2, 2, 2)
        self.assertFalse(allowed(self.m, 299, 250, 301, 250))
        self.assertFalse(allowed(self.m, 301, 250, 299, 250))
        self.assertTrue(allowed(self.m, 250, 299, 250, 301))

class Wrapping(unittest.TestCase):

    def test_wrap_full_text_no_truncation(self):
        text = 'Длинный текст ' * 50
        lines = wrap_text(text, 25, len)
        self.assertTrue(all((len(s) <= 25 for s in lines)))
        self.assertEqual(''.join(lines).replace(' ', ''), text.replace(' ', ''))

    def test_long_word(self):
        self.assertEqual(wrap_text('abcdefghij', 4, len), ['abcd', 'efgh', 'ij'])

    def test_manual_lines(self):
        self.assertEqual(wrap_text('first\n\nsecond', 100, len), ['first', '', 'second'])

    def test_continuations_reference_one_command(self):
        c = {'type': 'text', 'name': 'NPC', 'text': 'Long dialogue ' * 100}
        items = [c]
        rows = build_rows(items, {'switches': {}}, 90, len)
        self.assertGreater(len(rows), 1)
        for row in rows:
            self.assertIs(row['items'], items)
            self.assertEqual(row['index'], 0)
            self.assertIs(row['command'], c)
        self.assertEqual(len(items), 1)
        self.assertEqual(c['text'], 'Long dialogue ' * 100)

    def test_nested_branch_targets(self):
        inside = {'type': 'text', 'name': '', 'text': 'Nested ' * 50}
        c = {'type': 'if', 'condition': {}, 'then': [inside], 'else': []}
        rows = build_rows([c], {'switches': {}}, 110, len)
        branch = next((r for r in rows if r['branch'] and r['items'] is c['then']))
        self.assertEqual(branch['index'], None)
        for row in rows:
            if row['command'] is inside:
                self.assertIs(row['items'], c['then'])
                self.assertEqual(row['parent'], branch['key'])

    def test_unique_keys(self):
        rows = build_rows([{'type': 'if', 'condition': {}, 'then': [{'type': 'text', 'name': '', 'text': 'abc ' * 50}], 'else': []}], {'switches': {}}, 100, len)
        keys = [r['key'] for r in rows]
        self.assertEqual(len(keys), len(set(keys)))

    def test_wider_fewer_rows(self):
        c = {'type': 'text', 'name': '', 'text': 'Word ' * 100}
        self.assertGreater(len(build_rows([c], {'switches': {}}, 100, len)), len(build_rows([c], {'switches': {}}, 250, len)))

class Colors(unittest.TestCase):

    def test_all_interactive_pairs_contrast(self):
        for name, p in PALETTES.items():
            for state in ('button', 'hover', 'pressed', 'field', 'bg'):
                self.assertGreaterEqual(contrast(p['fg'], p[state]), 4.5, (name, state))
            self.assertGreaterEqual(contrast(p['selected'], p['select']), 4.5)

    def test_light_foreground_not_white(self):
        self.assertNotEqual(PALETTES['light']['fg'], '#ffffff')

    def test_two_column_conditions(self):
        import ast
        root = Path(__file__).resolve().parents[1]
        tree = ast.parse((root / 'editor/conditions.py').read_text(encoding='utf-8'))
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and (n.func.attr == 'grid'):
                for k in n.keywords:
                    if k.arg == 'column' and isinstance(k.value, ast.Constant):
                        self.assertLess(k.value.value, 2)

class RealTk(unittest.TestCase):

    def setUp(self):
        try:
            import tkinter as tk
            from tkinter import ttk
            self.tk = tk
            self.ttk = ttk
            self.root = tk.Tk()
            self.root.geometry('950x650')
        except ImportError as exc:
            self.skipTest(str(exc))
        except Exception as exc:
            if exc.__class__.__name__ == 'TclError':
                self.skipTest(str(exc))
            raise

    def tearDown(self):
        if hasattr(self, 'root'):
            self.root.destroy()

    def test_narrow_conditions(self):
        from editor.conditions import Condition
        host = self.ttk.Frame(self.root, width=280, height=240)
        host.pack_propagate(False)
        host.pack()
        c = Condition(host, {'switches': {'s': 'A very long switch name'}})
        c.frame.pack(fill='x')
        self.root.update()
        self.assertLessEqual(c.value_box.winfo_rootx() + c.value_box.winfo_width(), c.frame.winfo_rootx() + c.frame.winfo_width())
        self.assertLessEqual(c.local_value_box.winfo_rootx() + c.local_value_box.winfo_width(), c.frame.winfo_rootx() + c.frame.winfo_width())

    def test_hover_foreground_both_themes(self):
        from editor.theme import ThemeManager
        from types import SimpleNamespace
        import tempfile, logging
        with tempfile.TemporaryDirectory() as d:
            menu = self.tk.Menu(self.root)
            view = self.tk.Menu(menu, tearoff=False)
            menu.add_cascade(label='Вид', menu=view)
            self.root.config(menu=menu)
            theme = ThemeManager(SimpleNamespace(window=self.root, root=Path(d), log=logging.getLogger('test'), invalidate=lambda: None))
            theme.install()
            for value in ('light', 'dark'):
                theme.choice.set(value)
                theme.change()
                self.assertEqual(theme.style.lookup('TButton', 'foreground', ('active',)), theme.colors['fg'])
                self.assertEqual(theme.style.lookup('TButton', 'foreground', ('pressed',)), theme.colors['fg'])

    def test_delete_continuation_deletes_whole_command(self):
        from editor.command_tree import CommandTree
        widget = CommandTree(self.root, None, {'switches': {}})
        widget.frame.pack(fill='both', expand=True)
        items = [{'type': 'text', 'name': 'NPC', 'text': 'long ' * 500}]
        widget.set(items)
        self.root.update()
        widget.refresh()
        key = next((k for k, r in widget.records.items() if '_line' in k))
        widget.tree.selection_set(key)
        widget.delete()
        self.assertEqual(items, [])
