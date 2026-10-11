"""Private-host level contracts; no commercial test fixtures distributed."""
import copy,json,unittest
from pathlib import Path
from aria.cli import load_image,apply_manifest
from aria.level import apply_level_edits,audit_room,MAP
from aria.rooms import room_address,entities,doors
from aria.core import PatchError
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless((ROOT/'CastlevaniaAoS.gba').exists(),'private original unavailable')
class LevelContracts(unittest.TestCase):
 def setUp(self):
  self.rom=load_image(ROOT/'CastlevaniaAoS.gba')
  self.spec=json.loads((ROOT/'examples/room-workshop/mod.json').read_text())['room_edits']
 def test_example_identity_map_and_reciprocal_doors(self):
  original=self.rom.read(MAP,6016);apply_level_edits(self.rom,self.spec)
  self.assertEqual(original,self.rom.read(MAP,6016))
  hall=room_address(self.rom,0,3);save=room_address(self.rom,0,31)
  self.assertEqual(next(e for e in entities(self.rom,hall) if e.unique_id==3).x,192)
  self.assertEqual(doors(self.rom,hall)[2].destination,save)
  self.assertEqual(doors(self.rom,save)[0].destination,hall)
  self.assertEqual(audit_room(self.rom,0,31)['errors'],[])
 def test_precondition(self):
  self.spec['moves'][0]['from']=[0,0]
  with self.assertRaises(PatchError):apply_level_edits(self.rom,self.spec)
 def test_script_entity_protected(self):
  self.spec['moves'][0].update(entity_id=0,**{'from':[8,160]})
  with self.assertRaises(PatchError):apply_level_edits(self.rom,self.spec)
 def test_outside_room(self):
  self.spec['moves'][0]['to']=[1280,176]
  with self.assertRaises(PatchError):apply_level_edits(self.rom,self.spec)
 def test_wrong_sides(self):
  self.spec['connections'][0]['a']['door']=0
  with self.assertRaises(PatchError):apply_level_edits(self.rom,self.spec)
 def test_repeated_endpoint(self):
  self.spec['connections']*=2
  with self.assertRaises(PatchError):apply_level_edits(self.rom,self.spec)
 def test_save_marker_detected(self):
  report=audit_room(self.rom,0,31);tile=next(t for t in report['map_tiles'] if t['save'])
  address=MAP+(tile['y']*64+tile['x'])*2
  value=self.rom.integer(address,2)&0x7fff
  self.rom.write(address,value.to_bytes(2,'little'),'test-save-marker')
  self.assertIn('save statue lacks an owned map save marker',audit_room(self.rom,0,31)['errors'])
if __name__=='__main__':unittest.main()
