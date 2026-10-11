"""Original synthetic native-layout fixture and checked replacement contracts."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
from aria.core import RomImage,PatchError
from aria.content import lz77
from aria.sprite_assets import install_sprite_assets,source_path,WRAPPER,SOURCE,PALETTE_DATA
from aria.sprite_rendering import resolve_sprite_resources

TEST_RAW_WRAPPER=0x082052F8
TEST_RAW_PALETTE_DATA=0x0820C554

ROOT=Path(__file__).resolve().parents[1]

class SpriteAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data=bytearray(0x800000)
        def put(address,payload):data[address-0x08000000:address-0x08000000+len(payload)]=payload
        put(WRAPPER,bytes.fromhex('0104100420bf5f08'))
        put(0x08209EE8,bytes([0,4,1,0]))
        for address,value in ((0x0804F1A0,WRAPPER),(0x0804F540,WRAPPER),(0x0804F1A4,0x08209EE8),
                              (0x0804F544,0x08209EE8),(0x0804F1A8,0x0820FE44),(0x0804F5B4,0x0820FE44)):
            put(address,struct.pack('<I',value))
        expanded=((2048+4)<<8).to_bytes(4,'little')+bytes(2048)
        cls.stream=lz77(expanded);put(SOURCE,cls.stream)
        cls.original=bytes(data)
        cls.profile=dict(id='synthetic',rom_base=0x08000000,size=len(data),sha256=hashlib.sha256(data).hexdigest(),
                         allocation_ranges=[dict(start=0x08680000,end=0x08800000)])

    def setUp(self):
        folder=ROOT/'local/sprite-asset-tests';folder.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=folder);self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)
        assert self.folder.resolve().is_relative_to(ROOT.resolve())
        self.rom=RomImage(self.original,self.profile)
        self.page_hash=hashlib.sha256(bytes(2048)).hexdigest();self.palette_hash=hashlib.sha256(bytes(32)).hexdigest()
        self.entry=dict(resource='background-bats',scope='all_registered_consumers',source='art.json',
                        expected_page_sha256=self.page_hash,provenance='Original synthetic pixels')
        self.document=dict(width=128,height=32,pixels=[1]*4096)
        self.write('art.json',self.document);self.write('palette.json',[[248,0,0]]*16)
        self.addCleanup(patch.stopall)
        from aria import sprite_assets as sprite_assets_module
        registry=dict(sprite_assets_module.REGISTRY['background-bats'])
        registry.update(page_sha=self.page_hash,palette_sha=self.palette_hash)
        patch.dict(sprite_assets_module.REGISTRY,{'background-bats':registry}).start()

    def write(self,name,value):(self.folder/name).write_text(json.dumps(value),encoding='utf-8')
    def apply(self):return install_sprite_assets(self.rom,[self.entry],self.folder)

    def test_relocated_page_redecodes_and_original_stream_preserved(self):
        report=self.apply();page=resolve_sprite_resources(self.rom,'background-bats')['pages'][0]
        self.assertEqual(page,bytes([0x11])*2048)
        self.assertEqual(self.rom.read(SOURCE,len(self.stream)),self.stream)
        self.assertEqual(self.rom.integer(WRAPPER+4),report[0]['allocated_address'])
        self.assertEqual(len(self.rom.ledger),2)

    def test_optional_palette_contract_and_output(self):
        self.entry.update(palette_source='palette.json',expected_palette_sha256=self.palette_hash)
        result=self.apply();self.assertTrue(result[0]['palette_replaced'])
        self.assertEqual(self.rom.read(PALETTE_DATA,32),b'\x1f\x00'*16)
        self.assertEqual(len(self.rom.ledger),3)

    def test_shape_pixel_type_and_palette_count_rejections(self):
        for document in [dict(self.document,width=64),dict(self.document,pixels=[True]*4096),dict(self.document,pixels=[16]*4096)]:
            self.write('art.json',document)
            with self.assertRaises(PatchError):self.apply()
        self.write('art.json',self.document)
        self.entry.update(palette_source='palette.json',expected_palette_sha256=self.palette_hash)
        self.write('palette.json',[[0,0,0]])
        with self.assertRaisesRegex(PatchError,'exactly 16'):self.apply()

    def test_explicit_global_scope_target_hashes_and_provenance(self):
        good=copy.deepcopy(self.entry)
        for key,value in [('scope','one_room'),('resource','julius'),('expected_page_sha256','0'*64),('provenance','')]:
            self.entry=dict(good,**{key:value})
            with self.assertRaises(PatchError):self.apply()
        for entries in [[],[good,good],{},[dict(good,unknown=1)]]:
            with self.assertRaises(PatchError):install_sprite_assets(self.rom,entries,self.folder)

    def test_palette_fields_must_pair(self):
        for fields in [dict(palette_source='palette.json'),dict(expected_palette_sha256=self.palette_hash),
                       dict(palette_source='palette.json',expected_palette_sha256='0'*64)]:
            with self.assertRaises(PatchError):install_sprite_assets(self.rom,[dict(self.entry,**fields)],self.folder)

    def test_source_confinement_and_size(self):
        for name in ['../art.json',str(self.folder/'art.json'),'art.png',True]:
            with self.assertRaises(PatchError):source_path(self.folder,name)
        (self.folder/'art.json').write_bytes(b' '*(512*1024+1))
        with self.assertRaisesRegex(PatchError,'512 KiB'):self.apply()

    def test_current_wrapper_literal_palette_and_page_guards(self):
        for address in [WRAPPER,0x0804F1A0,PALETTE_DATA,SOURCE+9]:
            self.rom=RomImage(self.original,self.profile)
            self.rom.data[address-0x08000000]^=1
            before=copy.deepcopy(self.rom.__dict__)
            with self.assertRaises(PatchError):self.apply()
            self.assertEqual(self.rom.__dict__,before)

    def test_late_conflict_rolls_back_allocation_and_ledger(self):
        self.rom.write(WRAPPER+4,struct.pack('<I',SOURCE),'existing claim')
        before=copy.deepcopy(self.rom.__dict__)
        with self.assertRaisesRegex(PatchError,'conflict'):self.apply()
        self.assertEqual(self.rom.__dict__,before)

    def test_allocator_exhaustion_leaves_image_unchanged(self):
        self.rom.cursors=[0x08800000];before=copy.deepcopy(self.rom.__dict__)
        with self.assertRaises(PatchError):self.apply()
        self.assertEqual(self.rom.__dict__,before)

    def test_project_module_rebasing_and_raw_patch_combination(self):
        from aria.cli import apply_manifest_data
        from aria.projects import compose_project
        module=dict(schema_version=1,id='art',sprite_assets=[self.entry])
        self.write('module.json',module)
        self.write('project.json',dict(schema_version=1,kind='tsf-project',id='test',modules=['module.json']))
        bundle=compose_project(self.folder/'project.json')
        self.assertEqual(bundle['manifest']['sprite_assets'][0]['source'],'art.json')
        self.assertEqual(len(bundle['report']['assets']),1)
        with self.assertRaisesRegex(PatchError,'raw patches'):
            apply_manifest_data(self.rom,dict(module,patches=[{}]),self.folder)
        self.assertEqual(self.rom.ledger,[])

class RawAssetTests(unittest.TestCase):
    """Registry-driven raw in-place replacement on a synthetic layout."""
    @classmethod
    def setUpClass(cls):
        data=bytearray(0x800000)
        def put(address,payload):data[address-0x08000000:address-0x08000000+len(payload)]=payload
        put(TEST_RAW_WRAPPER,bytes.fromhex('00041008'))
        put(0x0820C550,bytes([0,4,1,0]))
        put(TEST_RAW_WRAPPER+4,bytes(4096))
        put(TEST_RAW_PALETTE_DATA,bytes(32))
        cls.original=bytes(data)
        cls.profile=dict(id='synthetic',rom_base=0x08000000,size=len(data),sha256=hashlib.sha256(data).hexdigest(),
                         allocation_ranges=[dict(start=0x08680000,end=0x08800000)])

    def setUp(self):
        folder=ROOT/'local/sprite-asset-tests';folder.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=folder);self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)
        assert self.folder.resolve().is_relative_to(ROOT.resolve())
        self.rom=RomImage(self.original,self.profile)
        self.page_hash=hashlib.sha256(bytes(4096)).hexdigest();self.palette_hash=hashlib.sha256(bytes(32)).hexdigest()
        self.entry=dict(resource='test-raw',scope='single_entry_consumers',source='art.json',
                        expected_page_sha256=self.page_hash,provenance='Original synthetic pixels')
        self.document=dict(width=128,height=64,pixels=[2]*8192)
        self.write('art.json',self.document);self.write('palette.json',[[0,248,0]]*16)
        self.addCleanup(patch.stopall)
        from aria import sprite_assets as sprite_assets_module
        from aria import sprite_rendering as sprite_rendering_module
        patch.dict(sprite_assets_module.REGISTRY,{'test-raw':dict(
            page_sha=self.page_hash,palette_sha=self.palette_hash,wrapper=TEST_RAW_WRAPPER,
            wrapper_bytes='00041008',palette_data=TEST_RAW_PALETTE_DATA,compressed_source=None,
            encoding='raw',width=128,height=64,scope='single_entry_consumers',literals=())}).start()
        patch.dict(sprite_rendering_module.SPRITE_RESOURCES,{'test-raw':dict(
            pages=[TEST_RAW_WRAPPER],palette=0x0820C550,bank=0)}).start()

    def write(self,name,value):(self.folder/name).write_text(json.dumps(value),encoding='utf-8')
    def apply(self):return install_sprite_assets(self.rom,[self.entry],self.folder)

    def test_raw_in_place_replacement_without_allocation(self):
        before_allocations=copy.deepcopy(self.rom.allocations)
        report=self.apply()
        self.assertEqual(self.rom.read(TEST_RAW_WRAPPER+4,4096),bytes([0x22])*4096)
        self.assertIsNone(report[0]['allocated_address'])
        self.assertEqual(len(self.rom.ledger),1)
        self.assertEqual(self.rom.allocations,before_allocations)
        self.entry.update(palette_source='palette.json',expected_palette_sha256=self.palette_hash)
        self.rom=RomImage(self.original,self.profile)
        report=self.apply()
        self.assertTrue(report[0]['palette_replaced'])
        self.assertEqual(len(self.rom.ledger),2)

    def test_scope_dimensions_and_wrapper_guards(self):
        good=copy.deepcopy(self.entry)
        for key,value in [('scope','all_registered_consumers'),('resource','julius'),('expected_page_sha256','0'*64)]:
            self.entry=dict(good,**{key:value})
            with self.assertRaises(PatchError):self.apply()
        self.write('art.json',dict(self.document,height=32))
        self.entry=dict(good)
        with self.assertRaisesRegex(PatchError,'128x64'):self.apply()
        self.rom=RomImage(self.original,self.profile)
        self.rom.data[TEST_RAW_WRAPPER-0x08000000]^=1
        before=copy.deepcopy(self.rom.__dict__)
        with self.assertRaises(PatchError):self.apply()
        self.assertEqual(self.rom.__dict__,before)

class NativeSpriteAssetTests(unittest.TestCase):
    @unittest.skipUnless((ROOT/'CastlevaniaAoS.gba').exists(),'Private host unavailable')
    def test_example_is_deterministic_preserves_structures_and_stream(self):
        from aria.cli import load_image,apply_manifest
        from aria.sprites import SPRITES,inspect_sprite
        a=load_image(ROOT/'CastlevaniaAoS.gba');b=load_image(ROOT/'CastlevaniaAoS.gba')
        before=inspect_sprite(a,SPRITES['background-bats']);original=bytes(a.data)
        for rom in (a,b):apply_manifest(rom,ROOT/'examples/sky-invaders/mod.json')
        self.assertEqual(a.data,b.data);self.assertEqual(a.ledger,b.ledger)
        self.assertEqual(inspect_sprite(a,SPRITES['background-bats']),before)
        self.assertEqual(a.read(SOURCE,1024),original[SOURCE-a.base:SOURCE-a.base+1024])
        self.assertEqual(hashlib.sha256(a.data).hexdigest(),'3b17a2fd90da7c332d0181c66da55583432d56b1a3013af3378ae9ed4b02f1bd')

    @unittest.skipUnless((ROOT/'CastlevaniaAoS.gba').exists(),'Private host unavailable')
    def test_cli_preserves_sprite_source_and_report_inputs(self):
        import contextlib,io
        from aria.cli import main
        folder=ROOT/'local/sprite-asset-tests';folder.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=folder) as temp:
            target=Path(temp);assert target.resolve().is_relative_to(ROOT.resolve())
            (target/'mod.json').write_bytes((ROOT/'examples/sky-invaders/mod.json').read_bytes())
            for name in ('invaders.json','palette.json'):
                destination=target/'modules'/'assets'/name;destination.parent.mkdir(parents=True,exist_ok=True)
                destination.write_bytes((ROOT/'examples/sky-invaders/modules/assets'/name).read_bytes())
            for out in [target/'modules'/'assets'/'invaders.json',target/'modules'/'assets'/'palette.json',target/'mod.json']:
                before=out.read_bytes()
                with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                    self.assertNotEqual(main(['build',str(target/'mod.json'),'--out',str(out)]),0)
                self.assertEqual(out.read_bytes(),before)
            document=json.loads((target/'mod.json').read_text());document['sprite_assets'][0]['palette_source']='palette.manifest.json'
            (target/'mod.json').write_text(json.dumps(document))
            (target/'palette.manifest.json').write_bytes((target/'modules'/'assets'/'palette.json').read_bytes())
            before=(target/'palette.manifest.json').read_bytes()
            with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                self.assertNotEqual(main(['build',str(target/'mod.json'),'--out',str(target/'palette.gba')]),0)
            self.assertEqual((target/'palette.manifest.json').read_bytes(),before)

if __name__=='__main__':unittest.main()
