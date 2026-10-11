"""Synthetic room discovery/diagnostic boundaries, plus bounded private audit."""
import hashlib,struct,unittest
from pathlib import Path
from unittest.mock import patch
from aria.core import RomImage,PatchError
from aria.rooms import sector_span,room_address
from aria.room_catalog import catalog_rooms

class RoomCatalogTests(unittest.TestCase):
    def image(self):
        base=0x08001000;raw=bytearray(4096)
        struct.pack_into('<I',raw,0x990,base+0x130)
        for s in range(12):
            struct.pack_into('<I',raw,0x130+s*4,base+0x100+s*4)
            struct.pack_into('<I',raw,0x100+s*4,base+0x200)
        struct.pack_into('<HH8I',raw,0x200,0,0,0,base+0x300,0,0,0,0,0,0)
        return RomImage(raw,{'id':'synthetic','rom_base':base,'size':len(raw),
                            'sha256':hashlib.sha256(raw).hexdigest(),'allocation_ranges':[]})
    def test_last_sector_ends_at_area(self):
        r=self.image();self.assertEqual(sector_span(r,11),(r.base+0x12C,1))
        self.assertEqual(room_address(r,11,0),r.base+0x200)
        with self.assertRaises(PatchError):room_address(r,11,1)
    def test_pagination_and_stable_ids(self):
        r=self.image();a=catalog_rooms(r,offset=2,limit=3)
        self.assertEqual(a['total_known_slots'],12);self.assertEqual(a['next_offset'],5)
        self.assertEqual([x['sector'] for x in a['rooms']],[2,3,4])
        self.assertEqual(a['rooms'][0]['id'],'synthetic:s02:r000:base')
        struct.pack_into('<I',r.data,0x108,r.base+0x240)
        b=catalog_rooms(r,offset=2,limit=3)
        self.assertEqual(a['rooms'][0]['id'],b['rooms'][0]['id']);self.assertNotEqual(a['image_sha256'],b['image_sha256'])
    def test_empty_layers_and_out_of_range_page(self):
        a=catalog_rooms(self.image(),sector=11,check_rendering=True)
        self.assertTrue(a['enumeration_complete']);self.assertEqual(len(a['rooms']),1)
        self.assertTrue(all(x['geometry_status']=='empty' for x in a['rooms'][0]['layers']))
        b=catalog_rooms(self.image(),offset=12);self.assertEqual(b['rooms'],[]);self.assertIsNone(b['next_offset'])
    def test_invalid_options_raise(self):
        for kw in [{'sector':12},{'sector':True},{'offset':-1},{'limit':0},{'limit':129},{'check_rendering':1}]:
            with self.assertRaises(PatchError):catalog_rooms(self.image(),**kw)
    def test_bad_sector_does_not_abort_others(self):
        r=self.image();struct.pack_into('<I',r.data,0x130,r.base+0x101)
        c=catalog_rooms(r)
        self.assertFalse(c['enumeration_complete']);self.assertEqual(c['diagnostics'][0]['sector'],0)
        self.assertEqual(c['total_known_slots'],11);self.assertEqual(len(c['rooms']),11)
    def test_bad_room_does_not_abort_page(self):
        r=self.image();struct.pack_into('<I',r.data,0x104,0xDEADBEEF)
        c=catalog_rooms(r,limit=3)
        self.assertEqual([x['status'] for x in c['rooms']],['available','invalid','available'])
        self.assertEqual(c['rooms'][1]['diagnostics'][0]['code'],'invalid_room_metadata')
    def test_bad_and_unsupported_layers_are_independent(self):
        r=self.image()
        struct.pack_into('<BBHHHI',r.data,0x300,0,0,0,256,256,r.base+0x400)
        struct.pack_into('<BBH',r.data,0x400,1,1,4)
        struct.pack_into('<BBHHHI',r.data,0x30C,0,0,0,256,256,0xDEADBEEF)
        c=catalog_rooms(r,sector=0)['rooms'][0]
        self.assertEqual(c['status'],'partial')
        self.assertEqual([x['geometry_status'] for x in c['layers']],['unsupported','invalid','empty'])
    def test_render_failure_is_a_diagnostic(self):
        r=self.image();struct.pack_into('<BBHHHI',r.data,0x300,0,0,0,256,256,r.base+0x400)
        struct.pack_into('<BBH',r.data,0x400,1,1,2)
        with patch('aria.room_catalog.inspect_geometry',return_value={'width_screens':1}),patch('aria.room_catalog.render_layer',side_effect=PatchError('Inherited graphics unavailable')):
            c=catalog_rooms(r,sector=0,check_rendering=True)['rooms'][0]
        self.assertEqual(c['layers'][0]['geometry_status'],'available')
        self.assertEqual(c['layers'][0]['render_status'],'unavailable')
        self.assertEqual(c['layers'][0]['diagnostics'][0]['code'],'render_unavailable')
    def test_no_mutation(self):
        r=self.image();before=bytes(r.data);cursors=r.cursors[:];catalog_rooms(r)
        self.assertEqual(bytes(r.data),before);self.assertEqual(r.ledger,[]);self.assertEqual(r.cursors,cursors)
    def test_invalid_sector_spans_rejected(self):
        for address,value in [(0x130,0),(0x130,0x08001104),(0x134,0x08001103),(0x134,0x08001700)]:
            r=self.image();struct.pack_into('<I',r.data,address,value)
            with self.assertRaises(PatchError):sector_span(r,0)

class PrivateCatalogTests(unittest.TestCase):
    def test_background_available_is_source_only(self):
        root=Path(__file__).resolve().parents[1];host=root/'CastlevaniaAoS.gba'
        if not host.exists():self.skipTest('Private original not present')
        from aria.cli import load_image
        r=load_image(host);before=bytes(r.data)
        c=catalog_rooms(r,sector=4,offset=0,limit=1,check_rendering=True)
        b=c['rooms'][0]['layers'][1]
        self.assertEqual(c['schema_version'],2);self.assertEqual(b['geometry_status'],'available')
        self.assertEqual(b['geometry_format'],'background_byte_index');self.assertEqual(b['render_status'],'available')
        self.assertEqual(b['render_summary']['scope'],'static_source_raster_no_affine_viewport')
        self.assertFalse(b['render_summary']['viewport_pixels_verified'])
        self.assertFalse(c['rooms'][0]['terrain_write_registered']);self.assertEqual(bytes(r.data),before)
    def test_final_sector_and_mod_identity(self):
        root=Path(__file__).resolve().parents[1];host=root/'CastlevaniaAoS.gba'
        if not host.exists():self.skipTest('Private original not present')
        from aria.cli import load_image,apply_manifest
        r=load_image(host);c=catalog_rooms(r,sector=11,limit=128)
        self.assertTrue(c['enumeration_complete']);self.assertEqual(c['total_known_slots'],41)
        self.assertEqual(len(c['rooms']),41);self.assertIsNone(c['next_offset'])
        before=catalog_rooms(r,sector=0,offset=3,limit=1)['rooms'][0]
        apply_manifest(r,root/'examples/geometry-workshop/mod.json')
        after=catalog_rooms(r,sector=0,offset=3,limit=1)['rooms'][0]
        self.assertEqual(before['id'],after['id']);self.assertTrue(after['terrain_write_registered'])
        self.assertNotEqual(before['layers'][0]['geometry']['layout_sha256'],after['layers'][0]['geometry']['layout_sha256'])
