"""Exact-host room asset isolation and rejection contracts; no private fixtures packaged."""
import copy,json,struct,unittest
from pathlib import Path
from aria.core import PatchError
from aria.room_assets import plan_room_assets,install_room_assets

class RoomAssetTests(unittest.TestCase):
    def test_three_room_art_preserves_resources_and_distinct_loads(self):
        from aria.cli import apply_manifest
        from aria.rooms import room_address,metadata,doors
        from aria.geometry import inspect_geometry,verify_roundtrip
        from aria.rendering import read_graphics,read_palettes
        original={i:inspect_geometry(self.r,0,i,full=True) for i in (3,6,31)}
        apply_manifest(self.r,self.root/'examples/three-room-art/mod.json')
        graphics=[];palettes=[]
        for i in (3,6,31):
            old=original[i];new=inspect_geometry(self.r,0,i,full=True)
            self.assertEqual(sum(a!=b for a,b in zip(old['cells'],new['cells'])),1)
            self.assertEqual(new['metatiles_including_blank'],old['metatiles_including_blank']+1)
            self.assertEqual(self.r.read(old['layout_address'],len(old['cells'])*2).hex(),verify_roundtrip(old)['layout_hex'])
            m=metadata(self.r,room_address(self.r,0,i));graphics.append(read_graphics(self.r,m[4])[0][24]);palettes.append(tuple(read_palettes(self.r,m[5])[0][8]))
        self.assertEqual(len(set(graphics)),3);self.assertEqual(len(set(palettes)),3)
        self.assertEqual(doors(self.r,room_address(self.r,0,3))[2].destination,room_address(self.r,0,6))
        self.assertEqual(doors(self.r,room_address(self.r,0,6))[1].destination,room_address(self.r,0,31))
    def test_two_room_art_isolated_slots_and_original_inputs(self):
        from aria.cli import apply_manifest
        from aria.rooms import room_address,metadata
        from aria.rendering import read_graphics,read_palettes
        from aria.geometry import inspect_geometry,verify_roundtrip
        before=bytes(self.r.data);originals={i:inspect_geometry(self.r,0,i,full=True) for i in (3,31)}
        apply_manifest(self.r,self.root/'examples/two-room-art/mod.json')
        chunks={};banks={}
        for i in (3,31):
            b=inspect_geometry(self.r,0,i,full=True);old=originals[i]
            self.assertEqual(b['metatiles_including_blank'],old['metatiles_including_blank']+1)
            self.assertEqual(sum(x!=y for x,y in zip(b['cells'],old['cells'])),1)
            self.assertEqual(self.r.read(old['layout_address'],len(old['cells'])*2),bytes.fromhex(verify_roundtrip(old)['layout_hex']))
            m=metadata(self.r,room_address(self.r,0,i));chunks[i]=read_graphics(self.r,m[4])[0][24];banks[i]=read_palettes(self.r,m[5])[0][8]
        self.assertNotEqual(chunks[3],chunks[31]);self.assertNotEqual(banks[3],banks[31])
        self.assertEqual(self.r.original,before)
        self.assertEqual(self.r.read(originals[31]['collision_tileset_address'],originals[31]['collision_resource']['compressed_bytes']).hex(),originals[31]['collision_resource']['compressed_hex'])
    def test_bridge_art_reskin_preserves_collision_and_loads(self):
        from aria.cli import apply_manifest
        from aria.rooms import room_address,metadata
        from aria.rendering import read_graphics,read_palettes
        from aria.geometry import inspect_geometry
        before=inspect_geometry(self.r,0,5,full=True)
        old_visual=bytes.fromhex(before['visual_resource']['data_hex']);old_collision=bytes.fromhex(before['collision_resource']['data_hex'])
        apply_manifest(self.r,self.root/'examples/bridge-art/mod.json')
        after=inspect_geometry(self.r,0,5,full=True)
        new_visual=bytes.fromhex(after['visual_resource']['data_hex'])
        self.assertEqual(bytes.fromhex(after['collision_resource']['data_hex']),old_collision)
        self.assertNotEqual(new_visual[5*32:6*32],old_visual[5*32:6*32])
        self.assertEqual(new_visual[:5*32],old_visual[:5*32]);self.assertEqual(new_visual[6*32:],old_visual[6*32:])
        m=metadata(self.r,room_address(self.r,0,5));chunks,_=read_graphics(self.r,m[4]);banks,_=read_palettes(self.r,m[5])
        self.assertIn(24,chunks);self.assertIn(8,banks)
    def test_unregistered_additional_room_still_rejected(self):
        row=copy.deepcopy(self.entry);row['room']['room']=7
        with self.assertRaisesRegex(PatchError,'not registered'):plan_room_assets(self.r,[row],self.folder)
        self.assertFalse(self.r.ledger)
    def setUp(self):
        self.root=Path(__file__).resolve().parents[1];host=self.root/'CastlevaniaAoS.gba'
        if not host.exists():self.skipTest('Private original not present')
        from aria.cli import load_image
        self.r=load_image(host);self.folder=self.root/'examples/original-room-art'
        self.entry=json.loads((self.folder/'mod.json').read_text())['room_assets'][0]
    def test_plan_does_not_mutate(self):
        before=bytes(self.r.data);p=plan_room_assets(self.r,[self.entry],self.folder)[0]
        self.assertEqual(len(p['graphics']),2048);self.assertEqual(len(p['colors']),32)
        self.assertEqual(bytes(self.r.data),before);self.assertFalse(self.r.ledger);self.assertFalse(self.r.allocations)
    def test_isolated_lists_and_resource_budgets(self):
        from aria.rooms import room_address,metadata
        from aria.rendering import read_graphics,read_palettes
        pointer=room_address(self.r,0,3);before=metadata(self.r,pointer);original=bytes(self.r.data)
        oldchunks,_=read_graphics(self.r,before[4]);oldbanks,_=read_palettes(self.r,before[5])
        report=install_room_assets(self.r,[self.entry],self.folder)[0];after=metadata(self.r,pointer)
        self.assertNotEqual(before[4:6],after[4:6]);self.assertEqual(before[:4]+before[6:],after[:4]+after[6:])
        chunks,_=read_graphics(self.r,after[4]);banks,_=read_palettes(self.r,after[5])
        self.assertEqual({i:chunks[i] for i in oldchunks},oldchunks);self.assertEqual({i:banks[i] for i in oldbanks},oldbanks)
        self.assertEqual(set(chunks)-set(oldchunks),{24});self.assertEqual(set(banks)-set(oldbanks),{8})
        for address,size in [(before[4],20),(before[5],20)]:self.assertEqual(self.r.read(address,size),original[address-self.r.base:address-self.r.base+size])
        self.assertEqual(report['budget']['rom_payload_bytes'],sum(e['size'] for e in self.r.ledger)-8)
    def test_schema_slots_preimages_and_sources_rejected_before_mutation(self):
        for key,value in [('target_chunk',23),('palette_bank',7),('target_chunk',True),('expected_graphics_list_sha256','wrong'),('expected_palette_list_sha256','wrong'),('graphics_source','../../CastlevaniaAoS.gba'),('palette_source','neon-bricks.json'),('provenance','')]:
            row=copy.deepcopy(self.entry);row[key]=value;before=bytes(self.r.data)
            with self.assertRaises((PatchError,ValueError)):install_room_assets(self.r,[row],self.folder)
            self.assertEqual(bytes(self.r.data),before);self.assertFalse(self.r.ledger);self.assertFalse(self.r.allocations)
    def test_duplicate_batch_rejected(self):
        with self.assertRaises(PatchError):install_room_assets(self.r,[self.entry,self.entry],self.folder)
        self.assertFalse(self.r.ledger)
    def test_existing_load_overlap_rejected(self):
        row=copy.deepcopy(self.entry);row['target_chunk']=23
        self.r.profile['room_asset_slots']=[{'sector':0,'room':3,'target_chunk':23,'palette_bank':8}]
        with self.assertRaisesRegex(PatchError,'overlaps existing'):plan_room_assets(self.r,[row],self.folder)
    def test_tilemap_overlap_rejected(self):
        row=copy.deepcopy(self.entry);row['target_chunk']=29
        self.r.profile['room_asset_slots']=[{'sector':0,'room':3,'target_chunk':29,'palette_bank':8}]
        with self.assertRaisesRegex(PatchError,'overlap a layer tilemap'):plan_room_assets(self.r,[row],self.folder)
    def test_combines_with_geometry_and_is_deterministic(self):
        from aria.cli import apply_manifest,load_image
        apply_manifest(self.r,self.folder/'mod.json');other=load_image(self.root/'CastlevaniaAoS.gba');apply_manifest(other,self.folder/'mod.json')
        self.assertEqual(self.r.data,other.data);self.assertEqual(self.r.room_asset_report,other.room_asset_report)
