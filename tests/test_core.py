import unittest
import copy
import tempfile
from pathlib import Path
from project import storage
from project.schema import active_page, page, condition_ok
from project.migrate import convert
from engine.world import World
from engine.scene import Scene
from engine.take import sample
from engine.text import pages
from support.keys import normalize

class Tests(unittest.TestCase):

    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.p = storage.load(self.root / 'assets' / 'demo_project.json', self.root)
        self.p['transition_seconds'] = 0

    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'project.json'
            storage.save(path, self.p)
            self.assertEqual(storage.load(path, self.root), self.p)

    def test_last_page_wins(self):
        event = self.p['maps']['room']['events'][1]
        self.assertEqual(active_page(event, {}, {}, '')['frame'], 0)
        self.assertEqual(active_page(event, {'kitchen_open': True}, {}, '')['frame'], 1)

    def test_lever_two_pages(self):
        w = World(self.root, self.p)
        event = w.map['events'][1]
        w.start(event)
        self.assertTrue(w.flags['kitchen_open'])
        w.start(event)
        self.assertFalse(w.flags['kitchen_open'])

    def test_locked_branch(self):
        w = World(self.root, self.p)
        w.start(w.map['events'][2])
        self.assertEqual(w.map_id, 'room')
        self.assertTrue(w.dialogue)

    def test_open_branch(self):
        w = World(self.root, self.p)
        w.flags['kitchen_open'] = True
        w.start(w.map['events'][2])
        self.assertEqual(w.map_id, 'kitchen')

    def test_local_switch_isolation(self):
        self.assertTrue(condition_ok({'self': 'A'}, {}, {'room:a:A': True}, 'room:a'))
        self.assertFalse(condition_ok({'self': 'A'}, {}, {'room:a:A': True}, 'room:b'))

    def test_commands_continue_after_dialogue(self):
        w = World(self.root, self.p)
        event = w.map['events'][0]
        w.start(event)
        while w.dialogue:
            w.interact()
        self.assertTrue(w.self_flags['room:Сосед:A'])
        self.assertEqual(active_page(event, w.flags, w.self_flags, 'room:Сосед')['name'], 'Уже знакомы')

    def test_nested_if(self):
        w = World(self.root, self.p)
        w.pending = [dict(type='if', condition={}, then=[dict(type='if', condition={}, then=[dict(type='switch', flag='kitchen_open', operation='on')], **{'else': []})], **{'else': []})]
        w.advance()
        self.assertTrue(w.flags['kitchen_open'])

    def test_list_resolution(self):
        s = Scene(self.root, self.p)
        w = World(self.root, self.p)
        image = s.draw(self.p, w.snapshot(0), [1920, 1080])
        self.assertEqual(image.size, (1920, 1080))

    def test_migration_v5(self):
        old = copy.deepcopy(self.p)
        old['format_version'] = 5
        for m in old['maps'].values():
            m['events'] = []
        old['maps']['room']['events'] = [dict(id='lever', x=2, y=2, profile='lever_red', visual_flag='kitchen_open', direction=0, trigger='action', commands=[dict(type='switch', flag='kitchen_open', operation='toggle')])]
        new = convert(old)
        self.assertEqual(len(new['maps']['room']['events'][0]['pages']), 2)
        self.assertEqual(new['format_version'], 7)

    def test_migration_condition(self):
        old = copy.deepcopy(self.p)
        old['format_version'] = 5
        for m in old['maps'].values():
            m['events'] = []
        old['maps']['room']['events'] = [dict(id='e', x=1, y=1, profile='none', commands=[dict(type='text', name='', text='Hi', condition='kitchen_open', expected=False)])]
        command = convert(old)['maps']['room']['events'][0]['pages'][0]['commands'][0]
        self.assertEqual(command['type'], 'if')
        self.assertFalse(command['condition']['value'])

    def test_word_pagination(self):
        result = pages(self.root, self.p, 'Сосед', 'Длинная реплика ' * 300)
        self.assertGreater(len(result), 1)
        self.assertEqual(''.join((''.join(page['lines']) for page in result)).replace(' ', ''), ('Длинная реплика ' * 300).replace(' ', ''))

    def test_keys(self):
        self.assertEqual(normalize('ц'), 'w')
        self.assertEqual(normalize('W'), 'w')

    def test_map_cut(self):
        w = World(self.root, self.p)
        a = w.snapshot(0)
        w.flags['kitchen_open'] = True
        w.start(w.map['events'][2])
        b = w.snapshot(1)
        self.assertEqual(sample([a, b], 0.5)['map_id'], 'room')
