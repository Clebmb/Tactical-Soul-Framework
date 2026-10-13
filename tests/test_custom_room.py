"""Private-host start, isolated definition and final-example contracts."""
import copy,json,unittest
from pathlib import Path
from aria.cli import load_image,apply_manifest
from aria.core import PatchError
from aria.starts import install_new_game_start
from aria.geometry import inspect_geometry,apply_geometry_edits
from aria.rooms import room_address,doors
from aria.palette_tints import install_palette_tints,TARGETS,blood_palette
ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless((ROOT/'CastlevaniaAoS.gba').exists(),'private host unavailable')
class CustomRoomContracts(unittest.TestCase):
 def setUp(self):
  self.rom=load_image(ROOT/'CastlevaniaAoS.gba')
  self.path=ROOT/'examples/custom_room/mod.json'
 def test_start_guards_and_preimages(self):
  before=bytes(self.rom.data)
  for spec in ({'sector':0,'room':3,'position':[128,141]},
               {'sector':0,'room':31,'position':[True,141]},
               {'sector':0,'room':31,'position':[256,141]}):
   with self.assertRaises(PatchError):install_new_game_start(self.rom,spec)
   self.assertEqual(bytes(self.rom.data),before)
  install_new_game_start(self.rom,{'sector':0,'room':31,'position':[128,141]})
  self.assertEqual(self.rom.read(0x084F0D8C,10),bytes.fromhex('001f0000000080008d00'))
  with self.assertRaises(PatchError):install_new_game_start(self.rom,{'sector':0,'room':31,'position':[128,141]})
 def test_second_start_registry_and_encoding(self):
  before=bytes(self.rom.data)
  for spec in ({'sector':0,'room':5,'position':[128,160]},
               {'sector':0,'room':14,'position':[128,141]},
               {'sector':0,'room':14,'position':[0,0]}):
   with self.assertRaises(PatchError):install_new_game_start(self.rom,spec)
   self.assertEqual(bytes(self.rom.data),before)
  report=install_new_game_start(self.rom,{'sector':0,'room':14,'position':[128,160]})
  self.assertEqual(self.rom.read(0x084F0D8C,10),bytes.fromhex('000e000000008000a000'))
  self.assertEqual(report['position'],[128,160])
  other=load_image(ROOT/'CastlevaniaAoS.gba')
  install_new_game_start(other,{'sector':0,'room':14,'position':[128,160]})
  self.assertEqual(bytes(self.rom.data),bytes(other.data))
  with self.assertRaises(PatchError):install_new_game_start(self.rom,{'sector':0,'room':14,'position':[128,160]})
 def test_palette_preimages_shared_scope_and_atomic_validation(self):
  before=bytes(self.rom.data)
  good={'target':'zombie','style':'blood','scope':'shared-native-palette'}
  for bad in (dict(good,target='soma'),dict(good,scope='local'),dict(good,style='blue'),good):
   with self.assertRaises(PatchError):install_palette_tints(self.rom,[good,bad])
   self.assertEqual(bytes(self.rom.data),before)
  source={target:self.rom.read(address,32) for target,(address,_) in TARGETS.items()}
  install_palette_tints(self.rom,[dict(good,target=target) for target in TARGETS])
  for target,(address,_) in TARGETS.items():
   self.assertEqual(self.rom.read(address,32),blood_palette(source[target]))
   self.assertEqual(self.rom.read(address,2),source[target][:2])
  self.assertEqual(self.rom.read(0x082097D8,32),before[0x2097D8:0x2097F8])
  with self.assertRaises(PatchError):install_palette_tints(self.rom,[good])
 def test_isolated_definitions_and_route(self):
  originals=[inspect_geometry(self.rom,0,i,full=True) for i in (31,3)]
  first=load_image(ROOT/'CastlevaniaAoS.gba');apply_manifest(first,self.path)
  apply_manifest(self.rom,self.path)
  self.assertEqual(bytes(self.rom.data),bytes(first.data))
  for old in originals:
   new=inspect_geometry(self.rom,0,old['room'],full=True)
   self.assertEqual(new['metatiles_including_blank'],old['metatiles_including_blank'])
   self.assertEqual(new['collision_resource']['data_hex'][4*32:],old['collision_resource']['data_hex'][4*32:])
   self.assertEqual(new['visual_resource']['data_hex'][4*64:],old['visual_resource']['data_hex'][4*64:])
   data=bytes.fromhex(old['visual_resource']['compressed_hex'])
   self.assertEqual(self.rom.read(old['visual_tileset_address'],len(data)),data)
  save=room_address(self.rom,0,31);hall=room_address(self.rom,0,3)
  self.assertEqual((doors(self.rom,save)[0].x,doors(self.rom,save)[0].destination),(1,hall))
  self.assertEqual((doors(self.rom,hall)[0].x,doors(self.rom,hall)[0].destination),(255,save))
 def test_replacement_errors_leave_rom_unchanged(self):
  bundle=inspect_geometry(self.rom,0,31,full=True)
  base={'room':{'sector':0,'room':31},'layer':0,'expected_layout_sha256':bundle['layout_sha256'],
        'cells':[{'x':0,'y':0,'expect':16,'value':1}],
        'metatile_replacements':[{'id':1,'minitiles':[0]*16,'collision':[0]*16}]}
  before=bytes(self.rom.data)
  for kind in ('duplicate','range','collision','unused','too_many'):
   spec=copy.deepcopy(base)
   if kind=='duplicate':spec['metatile_replacements']*=2
   if kind=='range':spec['metatile_replacements'][0]['id']=255
   if kind=='collision':spec['metatile_replacements'][0]['collision'][0]=1
   if kind=='unused':spec['metatile_replacements'][0]['id']=250
   if kind=='too_many':
    del spec['metatile_replacements']
    spec['metatiles']=[{'id':255+k,'minitiles':[0]*16,'collision':[0]*16} for k in range(2)]
   with self.assertRaises(PatchError):apply_geometry_edits(self.rom,[spec])
   self.assertEqual(bytes(self.rom.data),before)


if __name__=='__main__':unittest.main()
