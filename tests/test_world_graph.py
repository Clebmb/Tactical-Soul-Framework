import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from aria.rooms import Door
from aria.core import PatchError
from aria.world_graph import audit_world_graph,compare_world_graphs

class WorldGraphTests(unittest.TestCase):
    def test_bad_door_array_does_not_abort_other_rooms(self):
        rom=SimpleNamespace(profile={'id':'test'},data=b'original')
        with patch('aria.world_graph.sector_span',side_effect=lambda r,s:(0,2 if s==0 else 0)),patch('aria.world_graph.room_address',side_effect=lambda r,s,i:32+i*32),patch('aria.world_graph.doors',side_effect=lambda r,p:(_ for _ in ()).throw(PatchError('bad array')) if p==32 else [Door(32,255,0)]):
            g=audit_world_graph(rom)
        self.assertFalse(g['enumeration_complete']);self.assertEqual(len(g['edges']),1)
        self.assertEqual(g['diagnostics'][0]['code'],'doors_unavailable')
    def graph(self,rows,addresses=(32,64,96)):
        rom=SimpleNamespace(profile={'id':'test'},data=b'original')
        with patch('aria.world_graph.sector_span',side_effect=lambda r,s:(0,len(addresses) if s==0 else 0)),patch('aria.world_graph.room_address',side_effect=lambda r,s,i:addresses[i]),patch('aria.world_graph.doors',side_effect=lambda r,p:rows.get(p,[])):
            return audit_world_graph(rom)
    def test_reciprocal_and_outside_destinations(self):
        g=self.graph({32:[Door(64,1,0),Door(999,1,0)],64:[Door(32,255,0)]})
        self.assertTrue(g['edges'][0]['direct_return_observed']);self.assertFalse(g['edges'][1]['direct_return_observed'])
        self.assertEqual(g['summary']['unresolved_destinations'],1)
        self.assertEqual(len(g['nodes'][1]['incoming_edges']),1)
    def test_displaced_incoming_return_and_unchanged_graph(self):
        before=self.graph({32:[Door(64,1,0)],64:[Door(32,255,0)]})
        after=self.graph({32:[Door(96,1,0)],64:[Door(32,255,0)],96:[Door(32,255,0)]})
        d=compare_world_graphs(before,after)
        change=next(c for c in d['changed_edges'] if c['edge'].endswith('r000:base:door:000'))
        self.assertEqual(change['surviving_incoming_edges_without_return'],['test:s00:r001:base:door:000'])
        self.assertFalse(compare_world_graphs(before,before)['changed_edges'])
    def test_aliases_preserved(self):
        g=self.graph({32:[Door(64,1,0)]},(32,64,64))
        self.assertEqual(g['edges'][0]['destination_status'],'aliased');self.assertEqual(len(g['edges'][0]['targets']),2)
    def test_profiles_cannot_mix(self):
        a=self.graph({});b=self.graph({});b['profile']='other'
        with self.assertRaises(PatchError):compare_world_graphs(a,b)

class PrivateWorldGraphTests(unittest.TestCase):
    def test_original_and_three_room_delta(self):
        root=Path(__file__).resolve().parents[1];host=root/'CastlevaniaAoS.gba'
        if not host.exists():self.skipTest('Private original absent')
        from aria.cli import load_image,apply_manifest
        r=load_image(host);raw=bytes(r.data);a=audit_world_graph(r)
        self.assertEqual((a['summary']['rooms'],a['summary']['doors']),(343,725))
        self.assertTrue(a['enumeration_complete']);self.assertEqual(bytes(r.data),raw);self.assertFalse(r.ledger)
        apply_manifest(r,root/'examples/three-room-art/mod.json');patched=bytes(r.data);b=audit_world_graph(r)
        changes=compare_world_graphs(a,b)['changed_edges']
        self.assertEqual(len(changes),4);self.assertEqual(sum(len(c['surviving_incoming_edges_without_return']) for c in changes),4)
        self.assertEqual(bytes(r.data),patched)
