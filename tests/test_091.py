import unittest
import copy
from pathlib import Path
from PIL import Image
from project import storage
from engine.world import World
from engine.scene import Scene
from engine.take import sample
from engine.transition import Transition
from engine.render_cache import ImageCache

class Fixes(unittest.TestCase):

    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.p = storage.load(self.root / 'assets/demo_project.json', self.root)

    def test_fade_commits_at_black(self):
        w = World(self.root, self.p)
        door = w.map['events'][2]
        w.flags['kitchen_open'] = True
        w.start(door)
        self.assertEqual(w.map_id, 'room')
        self.assertTrue(w.transition.active)
        w.update(set(), 0.125, (1536, 1024), False)
        self.assertAlmostEqual(w.snapshot(0)['fade'], 0.5)
        self.assertEqual(w.map_id, 'room')
        w.update(set(), 0.125, (1536, 1024), False)
        self.assertEqual(w.map_id, 'kitchen')
        self.assertEqual(w.snapshot(0)['fade'], 1.0)
        w.update(set(), 0.125, (1536, 1024), False)
        self.assertAlmostEqual(w.snapshot(0)['fade'], 0.5)
        w.update(set(), 0.125, (1536, 1024), False)
        self.assertFalse(w.transition.active)
        self.assertEqual(w.snapshot(0)['fade'], 0.0)

    def test_movement_locked_during_transition(self):
        w = World(self.root, self.p)
        w.flags['kitchen_open'] = True
        w.start(w.map['events'][2])
        x = w.player.x
        w.update({'d'}, 0.1, (1536, 1024), False)
        self.assertEqual(w.player.x, x)

    def test_interaction_locked(self):
        w = World(self.root, self.p)
        w.flags['kitchen_open'] = True
        w.start(w.map['events'][2])
        pending = copy.deepcopy(w.pending)
        w.interact()
        self.assertEqual(w.pending, pending)
        self.assertFalse(w.dialogue)

    def test_commands_wait_for_fade(self):
        w = World(self.root, self.p)
        w.pending = [dict(type='transfer', target='kitchen', tx=2, ty=4), dict(type='text', name='', text='Arrived')]
        w.advance()
        self.assertFalse(w.dialogue)
        for _ in range(4):
            w.update(set(), 0.125, (1536, 1024), False)
        self.assertTrue(w.dialogue)

    def test_fade_disable_per_command(self):
        w = World(self.root, self.p)
        w.pending = [dict(type='transfer', target='kitchen', tx=2, ty=4, fade=False)]
        w.advance()
        self.assertEqual(w.map_id, 'kitchen')
        self.assertFalse(w.transition.active)

    def test_fade_interpolates_across_map(self):
        w = World(self.root, self.p)
        a = w.snapshot(0)
        a['fade'] = 0.5
        b = copy.deepcopy(a)
        b.update(t=1, map_id='kitchen', fade=1.0)
        self.assertAlmostEqual(sample([a, b], 0.5)['fade'], 0.75)

    def test_black_frame(self):
        w = World(self.root, self.p)
        s = Scene(self.root, self.p)
        state = w.snapshot(0)
        state['fade'] = 1.0
        self.assertEqual(s.draw(self.p, state, (320, 180)).getextrema(), ((0, 0), (0, 0), (0, 0)))

    def test_editor_ignores_fade(self):
        w = World(self.root, self.p)
        s = Scene(self.root, self.p)
        state = w.snapshot(0)
        state['fade'] = 1.0
        self.assertNotEqual(s.draw(self.p, state, (320, 180), editor=True).getextrema(), ((0, 0), (0, 0), (0, 0)))

    def test_sync_reused(self):
        w = World(self.root, self.p)
        a = w.npcs.sync()
        self.assertIs(a, w.npcs.sync())
        w.flags['kitchen_open'] = True
        self.assertIsNot(a, w.npcs.sync())

    def test_cache_invalidation(self):
        w = World(self.root, self.p)
        a = w.npcs.sync()
        w.npcs.invalidate()
        self.assertIsNot(a, w.npcs.sync())

    def test_light_state_and_snapshot(self):
        w = World(self.root, self.p)
        a = w.snapshot(0)
        view = w.view_state()
        w.flags['kitchen_open'] = True
        self.assertNotIn('kitchen_open', a['flags'])
        self.assertTrue(view['flags']['kitchen_open'])

    def test_cache_bounded(self):
        cache = ImageCache(300)
        for i in range(5):
            cache.get(i, lambda: Image.new('RGB', (10, 10)))
        self.assertLessEqual(cache.bytes, 300)
        self.assertEqual(len(cache.items), 1)

    def test_render_cache_does_not_retain_drawn_actors(self):
        w = World(self.root, self.p)
        s = Scene(self.root, self.p)
        state = w.snapshot(0)
        a = s.draw(self.p, state, (320, 180))
        state['player']['x'] += 100
        s.draw(self.p, state, (320, 180))
        state['player']['x'] -= 100
        b = s.draw(self.p, state, (320, 180))
        self.assertEqual(a.tobytes(), b.tobytes())

    def test_cache_hit_same_view(self):
        w = World(self.root, self.p)
        s = Scene(self.root, self.p)
        state = w.snapshot(0)
        s.draw(self.p, state, (960, 540))
        s.draw(self.p, state, (960, 540))
        self.assertGreater(s.cache.scaled.hits + s.cache.backgrounds.hits, 0)

    def test_block_overlay(self):
        from types import SimpleNamespace
        from editor.obstacle_overlay import draw_obstacles
        w = World(self.root, self.p)
        w.map['events'] = []
        w.map['blocked'] = [[1, 1]]
        a = SimpleNamespace(world=w, zoom=1, cx=0, cy=0, marks=SimpleNamespace(get=lambda: True))
        im = Image.new('RGB', (384, 384), (60, 60, 60))
        out = draw_obstacles(a, im)
        self.assertNotEqual(out.getpixel((150, 170)), im.getpixel((150, 170)))

    def test_scroll_layout_structure(self):
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        event=(root/'editor/event_ui.py').read_text(encoding='utf-8')
        tree=(root/'editor/command_tree.py').read_text(encoding='utf-8')
        self.assertLess(event.index('bottom.pack'),event.index('body.pack'))
        self.assertNotIn('Panedwindow',event)
        self.assertLess(tree.index('bar.pack'),tree.index('self.tree.pack'))
