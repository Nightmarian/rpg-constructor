import ast
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class OriginalLayout(unittest.TestCase):
    def test_original_two_columns_and_footer(self):
        source=(ROOT/'editor/event_ui.py').read_text(encoding='utf-8')
        self.assertNotIn('Panedwindow',source);self.assertNotIn('ScrollPanel',source)
        self.assertIn("left.pack(side='left'",source);self.assertIn("right.pack(side='left'",source)
        self.assertLess(source.index('bottom.pack'),source.index('body.pack'))
    def test_original_single_button_row_reserved(self):
        source=(ROOT/'editor/command_tree.py').read_text(encoding='utf-8')
        self.assertIn("ttk.Button(bar, text=text, command=fn).pack(side='left'",source)
        self.assertLess(source.index('bar.pack'),source.index('self.tree.pack'))
        self.assertNotIn('in_=',source)
class ActualTk(unittest.TestCase):
    def setUp(self):
        try:
            import tkinter as tk
            self.root=tk.Tk();self.root.geometry('1000x640');self.root.title('0.9.3 command panel check')
        except ImportError as exc:self.skipTest(str(exc))
        except Exception as exc:
            if exc.__class__.__name__=='TclError':self.skipTest(str(exc))
            raise
    def tearDown(self):
        if hasattr(self,'root'):self.root.destroy()
    def test_command_and_buttons_visible(self):
        from editor.command_tree import CommandTree
        widget=CommandTree(self.root,None,{'switches':{}});widget.frame.pack(fill='both',expand=True)
        widget.set([{'type':'text','name':'NPC','text':'Test command'}]);self.root.update()
        self.assertTrue(widget.tree.winfo_viewable());self.assertTrue(widget.tree.bbox(widget.tree.get_children()[0]))
        buttons=[]
        def collect(parent):
            for child in parent.winfo_children():
                if child.winfo_class()=='TButton':buttons.append(child)
                collect(child)
        collect(widget.frame);self.assertEqual(len(buttons),5)
        for button in buttons:
            self.assertTrue(button.winfo_viewable());self.assertLessEqual(button.winfo_rooty()+button.winfo_height(),self.root.winfo_rooty()+self.root.winfo_height())
