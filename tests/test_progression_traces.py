import copy
import unittest
from aria.core import PatchError
from aria.progression_traces import compare_progression_trace
from test_campaign_progression import graph, policy


def trace(*samples):
    return {'schema_version': 1, 'profile': 'test', 'image_sha256': 'image',
            'samples': [{'room': room, 'flags': {'key': owned}, 'via': via}
                        for room, owned, via in samples]}


class ProgressionTraceTests(unittest.TestCase):
    def test_acquisition_gate_and_return(self):
        source = graph([('a', 'b'), ('b', 'a')])
        spec = policy(required_rooms=['b'], room_grants={'b': ['key']},
                      edge_requirements={'1': ['key']}, itinerary=['b', 'a'])
        observed = trace(('a', False, None), ('b', True, '0'), ('a', True, '1'))
        before = copy.deepcopy((source, spec, observed))
        report = compare_progression_trace(source, spec, observed)
        self.assertTrue(report['matches_policy'])
        self.assertTrue(report['itinerary_observed'])
        self.assertTrue(report['required_rooms_observed'])
        self.assertEqual((source, spec, observed), before)

    def test_gate_checks_observed_flags_before_crossing(self):
        spec = policy(room_grants={'b': ['key']}, edge_requirements={'0': ['key']})
        row = compare_progression_trace(graph([('a', 'b')]), spec,
                                        trace(('a', False, None), ('b', True, '0')))
        self.assertEqual(row['violations'][0]['code'], 'door_requirement_not_observed')

    def test_unexpected_acquisition_and_loss(self):
        source = graph([])
        for spec, observed in ((policy(), trace(('a', True, None))),
                               (policy(initial_flags=['key']), trace(('a', True, None), ('a', False, None)))):
            row = compare_progression_trace(source, spec, observed)
            self.assertFalse(row['matches_policy'])
            self.assertEqual(row['violations'][0]['code'], 'flag_state_mismatch')

    def test_wrong_start_room_and_endpoints(self):
        source = graph([('a', 'b'), ('b', 'c')])
        for observed, code in ((trace(('b', False, None)), 'start_room_mismatch'),
                               (trace(('a', False, None), ('b', False, None)), 'room_change_without_door'),
                               (trace(('a', False, None), ('c', False, '0')), 'door_endpoint_mismatch')):
            self.assertEqual(compare_progression_trace(source, policy(), observed)['violations'][0]['code'], code)

    def test_checkpoint_does_not_repeat_waypoint(self):
        row = compare_progression_trace(graph([]), policy(itinerary=['a', 'a']),
                                        trace(('a', False, None), ('a', False, None)))
        self.assertTrue(row['matches_policy'])
        self.assertFalse(row['itinerary_observed'])
        self.assertEqual(row['waypoints_observed'], 1)
        row = compare_progression_trace(graph([('a', 'a')]), policy(itinerary=['a', 'a']),
                                        trace(('a', False, None), ('a', False, '0')))
        self.assertTrue(row['itinerary_observed'])

    def test_incoming_first_door_and_aliased_edges_rejected(self):
        source = graph([('a', 'b')])
        with self.assertRaises(PatchError):
            compare_progression_trace(source, policy(), trace(('a', False, '0')))
        source['edges'][0].update(targets=['b', 'c'], destination_status='aliased')
        with self.assertRaises(PatchError):
            compare_progression_trace(source, policy(), trace(('a', False, None), ('b', False, '0')))

    def test_input_bounds_and_identity(self):
        source, spec = graph([]), policy()
        valid = trace(('a', False, None))
        for changes in ({'profile': 'other'}, {'image_sha256': 'stale'}, {'samples': []},
                        {'schema_version': True}, {'extra': True}, {'samples': valid['samples'] * 4097}):
            with self.subTest(changes=list(changes)), self.assertRaises(PatchError):
                compare_progression_trace(source, spec, {**valid, **changes})
        for sample in ({'room': 'a', 'flags': {}, 'via': None},
                       {'room': 'a', 'flags': {'key': 1}, 'via': None},
                       {'room': 'a', 'flags': {'key': False}, 'via': 'missing'}):
            with self.assertRaises(PatchError):
                compare_progression_trace(source, spec, {**valid, 'samples': [sample]})
