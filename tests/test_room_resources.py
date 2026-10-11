import json,struct,unittest
from pathlib import Path
from types import SimpleNamespace
from aria.core import PatchError
from aria.room_resources import bg_tilemap_ranges,metatile_dependencies,audit_room_resources,background_dependencies

class ResourceDependencyTests(unittest.TestCase):
    def test_background_palette_dependencies_follow_used_texels(self):
        chunks={0:bytes([0,17,255])+bytes(2045)}
        a=background_dependencies([0],0,chunks,{1:[],15:[]},{0:8})
        self.assertTrue(a['available']);self.assertEqual(a['palette_banks'],[1,15])
        a=background_dependencies([0],0,chunks,{1:[]},{0:8})
        self.assertFalse(a['available']);self.assertEqual(a['missing_palette_banks'],[15])
    def test_background_unavailable_bytes_do_not_claim_complete_palettes(self):
        for chunks,modes in [({},{}),({0:bytes(2048)},{0:4}),({0:b''},{0:8})]:
            a=background_dependencies([0],0,chunks,{},modes)
            self.assertFalse(a['available']);self.assertFalse(a['palette_dependencies_complete'])
    def test_present_8bpp_chunks_are_incompatible_not_missing(self):
        a=metatile_dependencies([0],0,{0:b''},{0:[]},{0:8})
        self.assertFalse(a['available']);self.assertEqual(a['incompatible_character_chunks'],[0])
        self.assertEqual(a['missing_character_chunks'],[])
    def test_character_base_palette_and_flip_dependencies(self):
        a=metatile_dependencies([0x8200,0x8E00],2,{24:b''},{8:[]})
        self.assertTrue(a['available']);self.assertEqual(a['character_chunks'],[24]);self.assertEqual(a['palette_banks'],[8])
    def test_missing_dependencies_are_explicit(self):
        a=metatile_dependencies([0xF3FF],2,{},{});self.assertFalse(a['available'])
        self.assertEqual(a['missing_character_chunks'],[31]);self.assertEqual(a['missing_palette_banks'],[15])
    def test_tilemap_sizes_empty_layers_and_wrap(self):
        for size,blocks in enumerate([1,2,2,4]):
            raw=bytearray(80);struct.pack_into('<BBHHHI',raw,0,0,0,(size<<14)|(4<<8),256,256,64)
            struct.pack_into('<H',raw,66,2)
            r=SimpleNamespace(read=lambda p,n:bytes(raw[p:p+n]))
            self.assertEqual(bg_tilemap_ranges(r,0),[{'layer':0,'start':8192,'end':8192+blocks*2048}])
        struct.pack_into('<H',raw,2,(3<<14)|(31<<8))
        with self.assertRaises(PatchError):bg_tilemap_ranges(r,0)
    def test_affine_map_sizes_and_unknown_formats(self):
        raw=bytearray(80);r=SimpleNamespace(read=lambda p,n:bytes(raw[p:p+n]))
        for kind in (1,3):
            struct.pack_into('<H',raw,66,kind)
            for size,length in enumerate((256,1024,4096,16384)):
                struct.pack_into('<BBHHHI',raw,0,0,0,(size<<14)|(4<<8),256,256,64)
                self.assertEqual(bg_tilemap_ranges(r,0)[0]['end'],8192+length)
        struct.pack_into('<H',raw,2,(3<<14)|(31<<8))
        with self.assertRaises(PatchError):bg_tilemap_ranges(r,0)
        struct.pack_into('<H',raw,66,4)
        with self.assertRaisesRegex(PatchError,'Unknown'):bg_tilemap_ranges(r,0)

class PrivateResourceAuditTests(unittest.TestCase):
    def test_mixed_graphics_loads_remain_read_only(self):
        from aria.rendering import render_layer
        before=bytes(self.r.data);a=audit_room_resources(self.r,4,0)
        self.assertFalse(a['diagnostics']);self.assertEqual(set(a['character_chunk_bpp'].values()),{4,8})
        self.assertEqual(a['layers'][1]['status'],'inspected')
        self.assertEqual(a['layers'][1]['format'],'background_byte_index')
        self.assertFalse(a['layers'][1]['unavailable_referenced_ids'])
        affine=next(t for t in a['tilemaps'] if t['layer']==1)
        self.assertEqual(affine['end']-affine['start'],1024)
        self.assertNotIn(affine['start']//2048,a['budget']['static_unloaded_non_tilemap_chunks'])
        self.assertTrue(render_layer(self.r,4,0)['rgba'])
        self.assertEqual(bytes(self.r.data),before);self.assertFalse(self.r.ledger)
    def setUp(self):
        self.root=Path(__file__).resolve().parents[1]
        if not (self.root/'CastlevaniaAoS.gba').exists():self.skipTest('Private original not present')
        from aria.cli import load_image
        self.r=load_image(self.root/'CastlevaniaAoS.gba')
    def test_baseline_available_metatiles_and_nonmutation(self):
        before=bytes(self.r.data);a=audit_room_resources(self.r,0,3,True)
        self.assertFalse(a['diagnostics']);self.assertFalse(a['budget']['character_tilemap_overlaps'])
        self.assertIn(24,a['budget']['static_unloaded_non_tilemap_chunks']);self.assertIn(8,a['budget']['static_unloaded_palette_banks'])
        self.assertEqual(len(a['layers'][0]['metatiles']),144)
        self.assertTrue(all(not l['unavailable_referenced_ids'] for l in a['layers']))
        self.assertEqual(bytes(self.r.data),before);self.assertFalse(self.r.ledger)
    def test_imported_art_dependency_tracks_allocated_slot(self):
        from aria.cli import apply_manifest
        apply_manifest(self.r,self.root/'examples/original-room-art/mod.json');a=audit_room_resources(self.r,0,3)
        tile=a['layers'][0]['metatiles'][144];self.assertTrue(tile['available']);self.assertTrue(tile['referenced'])
        self.assertEqual(tile['character_chunks'],[24]);self.assertEqual(tile['palette_banks'],[8])
        self.assertNotIn(24,a['budget']['static_unloaded_non_tilemap_chunks']);self.assertEqual(a['budget']['loaded_character_bytes'],18432)
    def test_unsupported_layer_does_not_hide_other_layers(self):
        from aria.geometry import inspect_geometry
        b=inspect_geometry(self.r,0,3,1);p=b['layer_metadata_address']-self.r.base
        self.r.data[p+2:p+4]=(4).to_bytes(2,'little');a=audit_room_resources(self.r,0,3)
        self.assertEqual([l['status'] for l in a['layers']],['inspected','unavailable','inspected'])
        self.assertEqual(a['layers'][1]['diagnostics'][0]['code'],'geometry_unavailable')
    def test_invalid_option(self):
        with self.assertRaises(PatchError):audit_room_resources(self.r,0,3,1)
