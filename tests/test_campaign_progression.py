import copy
import unittest
from pathlib import Path

from aria.campaign_progression import plan_progression
from aria.core import PatchError


def graph(links):
    return {'schema_version': 1, 'profile': 'test', 'image_sha256': 'image',
            'nodes': [{'id': room} for room in 'abcd'],
            'edges': [{'id': str(index), 'source': a, 'targets': [b], 'destination_status': 'resolved'}
                      for index, (a, b) in enumerate(links)],
            'enumeration_complete': True, 'diagnostics': []}


def policy(**updates):
    spec = {'schema_version': 1, 'profile': 'test', 'image_sha256': 'image',
            'start': 'a', 'flags': ['key'], 'required_rooms': ['d']}
    spec.update(updates)
    return spec


class ProgressionTests(unittest.TestCase):
    def test_key_acquisition_requires_room_revisit(self):
        source = graph([('a', 'b'), ('b', 'c'), ('c', 'b'), ('b', 'd')])
        spec = policy(room_grants={'c': ['key']}, edge_requirements={'3': ['key']})
        original = copy.deepcopy((source, spec))
        report = plan_progression(source, spec)
        self.assertEqual(report['required_routes'][0]['door_path'], ['0', '1', '2', '3'])
        self.assertEqual(report['required_routes'][0]['flags_on_arrival'], ['key'])
        self.assertTrue(report['gate_observations'][0]['traversable_in_some_state'])
        self.assertEqual((source, spec), original)

    def test_key_behind_own_gate(self):
        report = plan_progression(graph([('a', 'd')]),
                                  policy(room_grants={'d': ['key']}, edge_requirements={'0': ['key']}))
        self.assertFalse(report['all_required_paths_observed'])
        self.assertEqual(report['required_routes'][0]['status'], 'not_observed')
        self.assertEqual(report['gate_observations'][0]['missing_flags_observed'], ['key'])

    def test_start_grants_and_initial_flags(self):
        source = graph([('a', 'd')])
        for spec in (policy(room_grants={'a': ['key']}, edge_requirements={'0': ['key']}),
                     policy(initial_flags=['key'], edge_requirements={'0': ['key']})):
            self.assertTrue(plan_progression(source, spec)['all_required_paths_observed'])

    def test_incompatible_branches_do_not_merge_inventories(self):
        source = graph([('a', 'b'), ('a', 'c'), ('b', 'd'), ('c', 'd')])
        spec = policy(flags=['x', 'y'], room_grants={'b': ['x'], 'c': ['y']},
                      edge_requirements={'2': ['x', 'y'], '3': ['x', 'y']})
        self.assertFalse(plan_progression(source, spec)['all_required_paths_observed'])

    def test_budgets_report_partial_not_unreachable(self):
        source = graph([('a', 'b'), ('b', 'd')])
        for kwargs in ({'max_states': 1}, {'max_transitions': 1}):
            report = plan_progression(source, policy(), **kwargs)
            self.assertFalse(report['search_complete'])
            self.assertEqual(report['required_routes'][0]['status'], 'not_reached_before_limit')

    def test_aliases_and_diagnostics_are_not_hidden(self):
        source = graph([('a', 'd')])
        source['edges'][0].update(targets=['b', 'd'], destination_status='aliased')
        source.update(enumeration_complete=False, diagnostics=[{'code': 'missing'}])
        report = plan_progression(source, policy())
        self.assertFalse(report['graph_complete_for_audit'])
        self.assertEqual(len(report['excluded_edges']), 1)
        self.assertEqual(report['source_diagnostics'], source['diagnostics'])
        with self.assertRaises(PatchError):
            plan_progression(source, policy(edge_requirements={'0': ['key']}))

    def test_invalid_policy_targets_flags_and_identity(self):
        for updates in ({'profile': 'other'}, {'image_sha256': 'stale'}, {'flags': ['key', 'key']},
                        {'flags': ['Bad Name']}, {'flags': ['f'+str(i) for i in range(17)]},
                        {'initial_flags': ['unknown']}, {'room_grants': {'missing': ['key']}},
                        {'edge_requirements': {'missing': ['key']}}, {'extra': True},
                        {'schema_version': True}):
            with self.assertRaises(PatchError):
                plan_progression(graph([]), policy(**updates))
        with self.assertRaises(PatchError):
            plan_progression(graph([]), policy(), max_states=0)

    def test_determinism_and_no_flag_cycle(self):
        source = graph([('a', 'b'), ('b', 'a'), ('b', 'd')])
        spec = policy(flags=[])
        report = plan_progression(source, spec)
        source['edges'].reverse()
        self.assertEqual(plan_progression(source, spec), report)
        self.assertEqual(report['states_explored'], 3)
        self.assertTrue(report['search_complete'])

    def test_independent_rooms_do_not_prove_an_itinerary(self):
        source = graph([('a', 'b'), ('a', 'c')])
        report = plan_progression(source, policy(required_rooms=['b', 'c'], itinerary=['b', 'c']))
        self.assertTrue(report['all_required_paths_observed'])
        self.assertEqual(report['itinerary_route']['status'], 'not_observed')
        self.assertEqual(report['itinerary_route']['waypoints_observed'], 1)

    def test_ordered_acquisition_and_return_witness(self):
        source = graph([('a', 'b'), ('b', 'a'), ('a', 'd'), ('d', 'a')])
        spec = policy(room_grants={'b': ['key']}, edge_requirements={'2': ['key']},
                      itinerary=['b', 'd', 'a'])
        before = copy.deepcopy((source, spec))
        report = plan_progression(source, spec)
        self.assertEqual(report['itinerary_route']['door_path'], ['0', '1', '2', '3'])
        self.assertEqual(report['itinerary_route']['flags_on_arrival'], ['key'])
        self.assertEqual(report['itinerary_route']['waypoints_observed'], 3)
        source['edges'].reverse()
        self.assertEqual(plan_progression(source, spec), report)
        source['edges'].reverse()
        self.assertEqual((source, spec), before)

    def test_repeated_waypoint_requires_another_arrival(self):
        source = graph([('a', 'b'), ('b', 'a')])
        route = plan_progression(source, policy(itinerary=['a', 'a']))['itinerary_route']
        self.assertEqual(route['door_path'], ['0', '1'])
        self.assertEqual(plan_progression(graph([]), policy(itinerary=[]))['itinerary_route']['door_path'], [])
        self.assertEqual(plan_progression(graph([]), policy(itinerary=['a']))['itinerary_route']['door_path'], [])
        self.assertIsNone(plan_progression(graph([]), policy())['itinerary_route'])

    def test_itinerary_budgets_and_validation(self):
        source = graph([('a', 'b'), ('b', 'a')])
        for budget in ({'max_states': 2}, {'max_transitions': 1}):
            row = plan_progression(source, policy(itinerary=['b', 'a']), **budget)
            self.assertEqual(row['itinerary_route']['status'], 'not_reached_before_limit')
        for invalid in (None, 'a', ['unknown'], [True], ['a'] * 65):
            with self.subTest(invalid=invalid), self.assertRaises(PatchError):
                plan_progression(source, policy(itinerary=invalid))

    def test_itinerary_witness_survives_later_budget_limit(self):
        report = plan_progression(graph([('a', 'b'), ('b', 'c')]),
                                  policy(itinerary=['b']), max_states=2)
        self.assertFalse(report['search_complete'])
        self.assertEqual(report['itinerary_route']['status'], 'observed')
        self.assertEqual(report['itinerary_route']['door_path'], ['0'])


class PrivateProgressionTests(unittest.TestCase):
    def test_image_bound_declared_gate_not_native_enforcement(self):
        from aria.cli import load_image, apply_manifest
        from aria.world_graph import audit_world_graph
        from aria.room_catalog import room_id
        root = Path(__file__).resolve().parents[1]
        if not (root/'CastlevaniaAoS.gba').exists():
            self.skipTest('Private original absent')
        rom = load_image(root/'CastlevaniaAoS.gba')
        apply_manifest(rom, root/'examples/custom_room/mod.json')
        source = audit_world_graph(rom)
        start, hallway = [room_id(rom.profile['id'], 0, index) for index in (31, 3)]
        edge = next(e['id'] for e in source['edges'] if e['source'] == start and e['targets'] == [hallway])
        spec = {'schema_version': 1, 'profile': source['profile'], 'image_sha256': source['image_sha256'],
                'start': start, 'required_rooms': [hallway], 'flags': ['key'],
                'edge_requirements': {edge: ['key']}, 'room_grants': {hallway: ['key']}}
        before = bytes(rom.data), copy.deepcopy(rom.ledger)
        self.assertFalse(plan_progression(source, spec)['all_required_paths_observed'])
        spec['room_grants'] = {start: ['key']}
        self.assertTrue(plan_progression(source, spec)['all_required_paths_observed'])
        spec['itinerary'] = [hallway, start]
        result = plan_progression(source, spec)['itinerary_route']
        self.assertEqual(result['status'], 'observed')
        self.assertEqual(len(result['door_path']), 2)
        self.assertEqual((bytes(rom.data), rom.ledger), before)
