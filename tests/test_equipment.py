"""Equipment contracts. Native fixtures are local-only and skipped without host."""
import json,unittest
from pathlib import Path
from aria.cli import load_image
from aria.core import PatchError
from aria.equipment import apply_equipment_edits,catalog,resolve,flags_view
from aria.tables import read_record,layout
ROOT=Path(__file__).resolve().parents[1]
class FlagContracts(unittest.TestCase):
 def test_unknown_bits_visible(self):
  view=flags_view('effects',0x4003)
  self.assertEqual(view['names'],['slash','flame'])
  self.assertEqual(view['unknown_mask'],'0x4000')
@unittest.skipUnless((ROOT/'CastlevaniaAoS.gba').exists(),'private original unavailable')
class EquipmentContracts(unittest.TestCase):
 def setUp(self):self.rom=load_image(ROOT/'CastlevaniaAoS.gba')
 def edit(self,**changes):
  edit={'table':'weapons','item':'knife','expect':{'strength':0},'fields':{'strength':-2}}
  edit.update(changes);return edit
 def test_catalog_identity_and_slot(self):
  rows=catalog(self.rom)
  self.assertEqual(len(rows),104);self.assertTrue(all(r['identity_matches'] for r in rows))
  self.assertEqual(len({r['key'] for r in rows}),104)
  cape=resolve(self.rom,'armor','Cape')
  self.assertEqual((cape['index'],cape['global_id'],cape['pickup_id'],cape['slot']),(25,116,117,'accessory'))
 def test_signed_roundtrip_preserves_raw_api(self):
  apply_equipment_edits(self.rom,[self.edit()])
  self.assertEqual(read_record(self.rom,'weapons',0)['strength'],254)
  self.assertEqual(resolve(self.rom,'weapons','knife')['fields']['strength'],-2)
 def test_native_negative_stats(self):
  self.assertEqual(resolve(self.rom,'weapons','dainslef')['fields']['constitution'],-2)
  self.assertEqual(resolve(self.rom,'armor','skull-necklace')['fields']['luck'],-1)
 def test_wrong_expected(self):
  with self.assertRaises(PatchError):apply_equipment_edits(self.rom,[self.edit(expect={'strength':1})])
  self.assertEqual(self.rom.ledger,[])
 def test_missing_expected(self):
  with self.assertRaises(PatchError):apply_equipment_edits(self.rom,[self.edit(expect={})])
 def test_signed_range(self):
  for value in [-129,128,True]:
   with self.assertRaises(PatchError):apply_equipment_edits(self.rom,[self.edit(fields={'strength':value})])
 def test_resource_field_rejected(self):
  with self.assertRaises(PatchError):apply_equipment_edits(self.rom,[self.edit(fields={'gfx_index':0})])
 def test_identity_rejected(self):
  with self.assertRaises(PatchError):apply_equipment_edits(self.rom,[self.edit(fields={'item_id':33})])
 def test_unknown_name(self):
  with self.assertRaises(PatchError):resolve(self.rom,'weapons','knif')
 def test_unknown_and_contradictory_flags(self):
  for flags in [{'add':['mystery']},{'add':['flame'],'remove':['flame']},{'add':'flame'}]:
   with self.assertRaises(PatchError):apply_equipment_edits(self.rom,[self.edit(fields={},expect={'effects':1},flags={'effects':flags})])
 def test_unknown_bits_preserved(self):
  # Simulated preexisting unknown flag, without a ledger entry for fixture setup.
  address=layout('weapons',0)[1]+16;offset=self.rom.offset(address,2)
  self.rom.data[offset:offset+2]=(0x4001).to_bytes(2,'little')
  apply_equipment_edits(self.rom,[self.edit(fields={},expect={'effects':0x4001},flags={'effects':{'add':['flame'],'remove':['slash']}})])
  self.assertEqual(read_record(self.rom,'weapons',0)['effects'],0x4002)
 def test_batch_validation_before_mutation(self):
  with self.assertRaises(PatchError):apply_equipment_edits(self.rom,[self.edit(),self.edit(fields={'strength':128})])
  self.assertEqual(self.rom.ledger,[])
 def test_duplicate_field(self):
  with self.assertRaises(PatchError):apply_equipment_edits(self.rom,[self.edit(),self.edit()])
 def test_resource_and_unknown_bytes_preserved(self):
  before=self.rom.read(layout('weapons',0)[1],28)
  apply_equipment_edits(self.rom,[self.edit()])
  after=self.rom.read(layout('weapons',0)[1],28)
  self.assertEqual([i for i,(a,b) in enumerate(zip(before,after)) if a!=b],[12])
if __name__=='__main__':unittest.main()
