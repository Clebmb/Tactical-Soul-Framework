import copy
import unittest
from pathlib import Path

from aria.campaign_audit import audit_campaign
from aria.core import PatchError


def graph(links, rooms=('a', 'b', 'c', 'd')):
    return {'schema_version': 1, 'profile': 'test', 'image_sha256': 'test-hash',
            'nodes': [{'id': room} for room in rooms],
            'edges': [{'id': str(index), 'source': source, 'targets': [target],
                       'destination_status': 'resolved'}
                      for index, (source, target) in enumerate(links)],
            'diagnostics': [], 'enumeration_complete': True}


class CampaignAuditTests(unittest.TestCase):
    def test_multihop_route_and_different_return(self):
        source = graph([('a', 'b'), ('b', 'c'), ('c', 'd'), ('d', 'a')])
        before = copy.deepcopy(source)
        report = audit_campaign(source, 'a', ['c'])
        self.assertEqual(report['required_routes'],
                         [{'room': 'c', 'outward_edges': ['0', '1'], 'return_edges': ['2', '3']}])
        self.assertTrue(report['all_required_roundtrips_observed'])
        self.assertEqual(source, before)

    def test_reachable_sink_and_disconnected_room(self):
        report = audit_campaign(graph([('a', 'b'), ('b', 'c')]), 'a', ['c', 'd'])
        self.assertEqual(report['reachable_without_observed_return'], ['b', 'c'])
        self.assertEqual(report['unreachable_rooms'], ['d'])
        self.assertIsNone(report['required_routes'][1]['outward_edges'])
        self.assertFalse(report['all_required_outward_paths_observed'])

    def test_self_loop_and_start_requirement(self):
        report = audit_campaign(graph([('a', 'a')]), 'a', ['a', 'a'])
        self.assertEqual(report['required_routes'],
                         [{'room': 'a', 'outward_edges': [], 'return_edges': []}])
        self.assertTrue(report['all_required_roundtrips_observed'])

    def test_ambiguous_and_unknown_edges_do_not_invent_paths(self):
        source = graph([('a', 'b'), ('a', 'c')])
        source['edges'][0].update(targets=['b', 'c'], destination_status='aliased')
        source['edges'][1].update(targets=[], destination_status='outside_base_catalog')
        report = audit_campaign(source, 'a', ['b'])
        self.assertEqual(report['reachable_rooms'], ['a'])
        self.assertEqual(len(report['excluded_edges']), 2)
        self.assertFalse(report['graph_complete_for_audit'])

    def test_source_diagnostics_retained(self):
        source = graph([])
        source.update(enumeration_complete=False, diagnostics=[{'code': 'doors_unavailable'}])
        report = audit_campaign(source, 'a')
        self.assertFalse(report['graph_complete_for_audit'])
        self.assertEqual(report['source_diagnostics'], source['diagnostics'])

    def test_deterministic_shortest_path(self):
        source = graph([('a', 'b'), ('a', 'c'), ('b', 'd'), ('c', 'd')])
        report = audit_campaign(source, 'a', ['d'])
        source['edges'].reverse()
        source['nodes'].reverse()
        self.assertEqual(audit_campaign(source, 'a', ['d']), report)
        self.assertEqual(report['required_routes'][0]['outward_edges'], ['0', '2'])

    def test_unknown_ids_duplicates_and_bounds(self):
        for start, required in (('missing', []), ('a', ['missing']), ('a', ['a'] * 257)):
            with self.assertRaises(PatchError):
                audit_campaign(graph([]), start, required)
        for field in ('nodes', 'edges'):
            source = graph([('a', 'b')])
            source[field].append(source[field][0])
            with self.assertRaises(PatchError):
                audit_campaign(source, 'a')
        source = graph([])
        source['schema_version'] = 2
        with self.assertRaises(PatchError):
            audit_campaign(source, 'a')
        source = graph([])
        source['nodes'] = [{'id': str(index)} for index in range(4097)]
        with self.assertRaises(PatchError):
            audit_campaign(source, '0')
        source = graph([])
        source['edges'] = [{}] * 32769
        with self.assertRaises(PatchError):
            audit_campaign(source, 'a')


class PrivateCampaignAuditTests(unittest.TestCase):
    def test_host_and_custom_room_nonmutation(self):
        from aria.cli import load_image, apply_manifest
        from aria.world_graph import audit_world_graph
        from aria.room_catalog import room_id
        root = Path(__file__).resolve().parents[1]
        host = root / 'CastlevaniaAoS.gba'
        if not host.exists():
            self.skipTest('Private host absent')
        rom = load_image(host)
        start = room_id(rom.profile['id'], 0, 31)
        required = room_id(rom.profile['id'], 0, 3)
        for mod in (None, root / 'examples/custom_room/mod.json'):
            if mod:
                apply_manifest(rom, mod)
            before = bytes(rom.data), copy.deepcopy(rom.ledger)
            report = audit_campaign(audit_world_graph(rom), start, [required])
            self.assertEqual(report['summary']['rooms'], 343)
            self.assertIsNotNone(report['required_routes'][0]['outward_edges'])
            self.assertTrue(report['all_required_roundtrips_observed'])
            self.assertEqual((bytes(rom.data), rom.ledger), before)
