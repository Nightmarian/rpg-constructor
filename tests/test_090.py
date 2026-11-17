import copy
import unittest
from pathlib import Path
from project import storage
from project.schema import validate
from project.migrate import convert
from engine.world import World
from engine.scene import Scene
from engine.take import sample
from engine.passage import allowed

class NewFeatures(unittest.TestCase):

    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.p = storage.load(self.root / 'assets/demo_project.json', self.root)
        self.p['transition_seconds'] = 0

    def world(self):
        w = World(self.root, self.p)
        w.map['events'] = w.map['events'][:1]
        pg = w.map['events'][0]['pages'][0]
        pg['movement'] = dict(mode='route', speed=128, delay=0, repeat=False, route=[{'op': 'right'}])
        return w

    def test_npc_route(self):
        w = self.world()
        x = w.npcs.snapshot()['Сосед']['x']
        for _ in range(4):
            w.update(set(), 0.25, (1536, 1024), False)
        n = w.npcs.snapshot()['Сосед']
        self.assertAlmostEqual(n['x'], x + 128)
        for _ in range(4):
            w.update(set(), 0.25, (1536, 1024), False)
        self.assertAlmostEqual(w.npcs.snapshot()['Сосед']['x'], x + 128)

    def test_npc_dialogue_freeze(self):
        w = self.world()
        w.update(set(), 0.25, (1536, 1024), False)
        x = w.npcs.snapshot()['Сосед']['x']
        w.start(w.map['events'][0])
        w.update(set(), 1, (1536, 1024), False)
        self.assertEqual(w.npcs.snapshot()['Сосед']['x'], x)

    def test_moving_interaction_position(self):
        w = self.world()
        e = w.map['events'][0]
        w.npcs.sync()
        n = w.npcs.states['room:Сосед']
        n.update(x=1100, y=600)
        w.player.x = 1050
        w.player.y = 600
        w.player.direction = 2
        w.interact()
        self.assertTrue(w.dialogue)

    def test_npc_blocked_tile(self):
        w = self.world()
        w.map['blocked'] = [[5, 4]]
        for _ in range(6):
            w.update(set(), 0.25, (1536, 1024), False)
        self.assertLess(w.npcs.snapshot()['Сосед']['x'], 640)

    def test_one_way(self):
        m = dict(tile_size=100, blocked=[], edges=[[0, 0, 2]])
        self.assertFalse(allowed(m, 99, 50, 101, 50))
        self.assertTrue(allowed(m, 101, 50, 99, 50))

    def test_two_way_wall(self):
        m = dict(tile_size=100, blocked=[], edges=[[0, 0, 2], [1, 0, 1]])
        self.assertFalse(allowed(m, 99, 50, 101, 50))
        self.assertFalse(allowed(m, 101, 50, 99, 50))

    def test_player_respects_direction(self):
        w = World(self.root, self.p)
        w.map['events'] = []
        w.player.x = 630
        w.player.y = 600
        w.map['edges'] = [[4, 4, 2]]
        w.update({'d'}, 0.2, (1536, 1024), True)
        self.assertLess(w.player.x, 640)

    def test_player_collision_toggle(self):
        w = World(self.root, self.p)
        w.map['events'] = []
        w.player.x = 630
        w.player.y = 600
        w.map['edges'] = [[4, 4, 2]]
        w.update({'d'}, 0.2, (1536, 1024), False)
        self.assertGreater(w.player.x, 640)

    def test_solid_event(self):
        w = World(self.root, self.p)
        w.map['events'] = w.map['events'][:1]
        w.map['events'][0]['pages'][0]['movement'] = {'mode': 'fixed'}
        w.player.x = 500
        w.player.y = 620
        w.update({'d'}, 0.25, (1536, 1024), True)
        self.assertLess(w.player.x, 560)

    def test_actor_snapshot_is_copy(self):
        w = self.world()
        a = w.snapshot(0)
        x = a['actors']['Сосед']['x']
        w.update(set(), 0.25, (1536, 1024), False)
        self.assertEqual(a['actors']['Сосед']['x'], x)

    def test_actor_interpolation(self):
        w = self.world()
        a = w.snapshot(0)
        w.update(set(), 0.25, (1536, 1024), False)
        b = w.snapshot(1)
        middle = sample([a, b], 0.5)
        self.assertAlmostEqual(middle['actors']['Сосед']['x'], (a['actors']['Сосед']['x'] + b['actors']['Сосед']['x']) / 2)

    def test_scale(self):
        self.p['profiles']['hero_blue']['scale'] = 2
        s = Scene(self.root, self.p)
        sprite, anchor = s.resources.sprite('hero_blue')
        self.assertEqual(sprite.size, (160, 224))
        self.assertEqual(anchor, (80, 216))

    def test_invalid_scale(self):
        self.p['profiles']['hero_blue']['scale'] = float('nan')
        with self.assertRaises(ValueError):
            validate(self.p)

    def test_comment_separator(self):
        w = World(self.root, self.p)
        w.pending = [{'type': 'comment', 'text': 'test'}, {'type': 'separator'}, {'type': 'switch', 'flag': 'kitchen_open', 'operation': 'on'}]
        w.advance()
        self.assertTrue(w.flags['kitchen_open'])

    def test_v6_migration(self):
        self.p['format_version'] = 6
        new = convert(self.p)
        self.assertEqual(new['format_version'], 7)
        self.assertEqual(self.p['format_version'], 6)

    def test_door_page_solid(self):
        from project.schema import page, active_page
        e = {'pages': [page('closed', 'door_wood'), page('open', 'door_wood', 1, condition={'switch': 'kitchen_open'})]}
        e['pages'][0]['solid'] = True
        e['pages'][1]['solid'] = False
        self.assertTrue(active_page(e, {}, {}, '')['solid'])
        self.assertFalse(active_page(e, {'kitchen_open': True}, {}, '')['solid'])

    def test_scene_runtime_and_editor(self):
        w = self.world()
        w.update(set(), 0.25, (1536, 1024), False)
        s = Scene(self.root, self.p)
        self.assertEqual(s.draw(self.p, w.snapshot(0), [960, 540]).size, (960, 540))
        self.assertEqual(s.draw(self.p, w.snapshot(0), [960, 540], editor=True).size, (960, 540))
