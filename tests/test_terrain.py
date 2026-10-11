import copy,struct,unittest
from pathlib import Path
from aria.core import PatchError
from aria.terrain import encode_definitions,extend_resource
from aria.compression import decode_lz10

class TerrainTests(unittest.TestCase):
    def definition(self):return {'id':2,'minitiles':[0]*16,'collision':[3]*16}
    def test_definition_encoding(self):
        v,c,d=encode_definitions([self.definition()],2)
        self.assertEqual(v,bytes(32));self.assertEqual(c,bytes([3])*16);self.assertEqual(d,[0]*16)
    def test_bounds_and_schema(self):
        for definitions in [[],[self.definition()]*33,{},[{'id':2}]]:
            with self.assertRaises(PatchError):encode_definitions(definitions,2)
        for key,value in [('id',3),('id',True),('minitiles',[0]*15),('minitiles',[65536]*16),('collision',[2]*16),('collision',[True]*16)]:
            row=self.definition();row[key]=value
            with self.assertRaises(PatchError):encode_definitions([row],2)
        row=self.definition();row['id']=511
        with self.assertRaises(PatchError):encode_definitions([row,row],511)
    def test_inner_header_length_and_flag_preserved(self):
        stream=extend_resource({'data_hex':'0102','inner_header_hex':'10060000'},b'\x03\x04')
        decoded,_=decode_lz10(stream);self.assertEqual(decoded,bytes.fromhex('1008000001020304'))

class PrivateTerrainTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(__file__).resolve().parents[1];host=self.root/'CastlevaniaAoS.gba'
        if not host.exists():self.skipTest('Private original not present')
        from aria.cli import load_image
        import json
        self.r=load_image(host);self.edit=json.loads((self.root/'examples/custom-terrain-workshop/mod.json').read_text())['geometry_edits'][0]
    def test_isolated_append_and_deterministic_build(self):
        from aria.geometry import inspect_geometry,apply_geometry_edits
        before=inspect_geometry(self.r,0,3,full=True);original=bytes(self.r.data)
        apply_geometry_edits(self.r,[self.edit]);after=inspect_geometry(self.r,0,3,full=True)
        self.assertEqual(after['metatiles_including_blank'],145);self.assertEqual(after['cells'][210],144)
        for key,addr in [('visual_resource','visual_tileset_address'),('collision_resource','collision_tileset_address')]:
            self.assertTrue(after[key]['data_hex'].startswith(before[key]['data_hex']))
            self.assertEqual(self.r.read(before[addr],before[key]['compressed_bytes']).hex(),before[key]['compressed_hex'])
        from aria.core import RomImage
        other=RomImage(original,self.r.profile);apply_geometry_edits(other,[self.edit])
        self.assertEqual(self.r.data,other.data);self.assertEqual(self.r.ledger,other.ledger)
    def test_rejections_do_not_allocate_or_patch(self):
        from aria.geometry import apply_geometry_edits
        for change in ['bad_collision','missing_character','missing_palette','unused','wrong_id','duplicate_cell']:
            row=copy.deepcopy(self.edit)
            if change=='bad_collision':row['metatiles'][0]['collision'][0]=2
            if change=='missing_character':row['metatiles'][0]['minitiles'][0]=1023
            if change=='missing_palette':row['metatiles'][0]['minitiles'][0]=0xF000
            if change=='unused':row['cells'][0]['value']=49
            if change=='wrong_id':row['metatiles'][0]['id']=145
            if change=='duplicate_cell':row['cells']*=2
            before=bytes(self.r.data);cursors=self.r.cursors[:]
            with self.assertRaises(PatchError):apply_geometry_edits(self.r,[row])
            self.assertEqual(bytes(self.r.data),before);self.assertEqual(self.r.ledger,[]);self.assertEqual(self.r.cursors,cursors)
