import ast
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

class LayoutStructure(unittest.TestCase):

    def test_tree_is_child_of_actual_area(self):
        source = (ROOT / 'editor/command_tree.py').read_text(encoding='utf-8')
        tree = ast.parse(source)
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and (n.func.attr == 'Treeview')]
        self.assertEqual(len(calls), 1)
        self.assertEqual(ast.unparse(calls[0].args[0]), 'area')
        self.assertNotIn('in_=', source)

    def test_event_has_resizable_split_and_fixed_footer(self):
        source = (ROOT / 'editor/event_ui.py').read_text(encoding='utf-8')
        self.assertIn('Panedwindow', source)
        self.assertIn('ScrollPanel', source)
        self.assertLess(source.index('bottom.pack'), source.index('body.pack'))

class ActualTkSmoke(unittest.TestCase):

    def setUp(self):
        try:
            import tkinter as tk
            from tkinter import ttk
            self.tk = tk
            self.ttk = ttk
            self.root = tk.Tk()
            self.root.title('Event UI smoke test')
            self.root.geometry('860x500')
        except (ImportError, RuntimeError) as exc:
            self.skipTest(str(exc))
        except Exception as exc:
            if exc.__class__.__name__ == 'TclError':
                self.skipTest(str(exc))
            raise

    def tearDown(self):
        if hasattr(self, 'root'):
            self.root.destroy()

    def test_commands_actually_visible(self):
        from editor.command_tree import CommandTree
        widget = CommandTree(self.root, None, {'switches': {}})
        widget.frame.pack(fill='both', expand=True)
        widget.set([{'type': 'text', 'name': 'NPC', 'text': 'Visible command'}, {'type': 'if', 'condition': {}, 'then': [{'type': 'separator'}], 'else': []}])
        self.root.update()
        first = widget.tree.get_children()[0]
        self.assertTrue(widget.tree.winfo_viewable())
        self.assertTrue(widget.tree.bbox(first))
        self.assertGreater(widget.tree.winfo_height(), 100)
        self.root.geometry('760x420')
        self.root.update()
        self.assertTrue(widget.tree.bbox(first))

    def test_long_panel_scrolls(self):
        from editor.scroll_panel import ScrollPanel
        panel = ScrollPanel(self.root)
        panel.pack(fill='both', expand=True)
        for i in range(40):
            self.ttk.Label(panel.content, text='Row ' + str(i)).pack()
        self.root.update()
        panel.canvas.yview_moveto(1)
        self.root.update()
        self.assertGreater(panel.canvas.yview()[0], 0)
        self.assertTrue(panel.vertical.winfo_viewable())
