"""Enemy/drop/placement contracts, with optional local exact-host fixtures."""
import json,unittest
from pathlib import Path
from aria.cli import load_image,apply_manifest
from aria.core import PatchError
from aria.enemies import catalog,resolve,resolve_drop,apply_enemy_edits,flags_view,soul_catalog,resolve_soul
from aria.encounters import audit_encounters
from aria.level import apply_level_edits
from aria.rooms import entities,room_address
from aria.tables import layout,read_record
ROOT=Path(__file__).resolve().parents[1]
class EnemyFlagContracts(unittest.TestCase):
 def test_unknown_bits_visible(self):
  self.assertEqual(flags_view('weaknesses',0x4003)['unknown_mask'],'0x4000')
  self.assertEqual(flags_view('resistances',0x400)['names'],['time_stop'])
@unittest.skipUnless((ROOT/'CastlevaniaAoS.gba').exists(),'private original unavailable')
class EnemyContracts(unittest.TestCase):
 def setUp(self):self.rom=load_image(ROOT/'CastlevaniaAoS.gba')
 def edit(self,**kw):
  edit={'enemy':'zombie','expect':{'hp':18},'fields':{'hp':30}};edit.update(kw);return edit
 def clone(self,**kw):
  edit={'op':'clone','room':{'sector':0,'room':6},'source_id':2,'entity_id':9,'enemy':'skeleton','to':[560,176]};edit.update(kw);return edit
 def test_names_and_native_drops(self):
  rows=catalog(self.rom);self.assertEqual(len(rows),113);self.assertEqual(len({r['key'] for r in rows}),113)
  self.assertEqual(resolve(self.rom,'Zombie')['drops']['item_1']['item'],'Cloth Tunic')
  self.assertEqual(resolve_drop(self.rom,'potion'),1)
  self.assertEqual(resolve_drop(self.rom,'baselard'),34)
 def test_bad_selector(self):
  with self.assertRaises(PatchError):resolve(self.rom,'zomb')
  with self.assertRaises(PatchError):resolve(self.rom,'zombie',1)
 def test_soul_catalog_groups_and_shared_soul(self):
  groups=soul_catalog(self.rom);self.assertEqual(len(groups),111)
  zombie=resolve_soul(self.rom,'2:12')
  self.assertEqual([h['enemy'] for h in zombie['holders']],['zombie'])
  self.assertEqual(zombie['holders'][0]['rarity'],180)
  shared=resolve_soul(self.rom,'0:0')
  self.assertEqual(shared['holder_count'],3)
  self.assertTrue(all(h['rarity']==0 and h['protected_encounter'] for h in shared['holders']))
  zeroes={h['enemy'] for g in groups for h in g['holders'] if h['rarity']==0}
  self.assertEqual(zeroes,{'headhunter','death','legion','balore','belmont','graham','chaos'})
 def test_soul_lookup_rejected(self):
  for spec in ('2-12','2:12:3','x:12','2:-1',2):
   with self.assertRaises(PatchError):resolve_soul(self.rom,spec)
  with self.assertRaisesRegex(PatchError,'No enemy drops soul'):resolve_soul(self.rom,'3:99')
 def test_field_ranges(self):
  for fields,expect in [({'hp':0},{'hp':18}),({'hp':65536},{'hp':18}),({'attack':256},{'attack':9}),({'hp':True},{'hp':18})]:
   with self.assertRaises(PatchError):apply_enemy_edits(self.rom,[self.edit(fields=fields,expect=expect)])
 def test_ai_and_soul_reassignment_rejected(self):
  for field in ['create_code','update_code','soul','soul_type']:
   with self.assertRaises(PatchError):apply_enemy_edits(self.rom,[self.edit(fields={field:0})])
 def test_expected_and_batch_validation(self):
  with self.assertRaises(PatchError):apply_enemy_edits(self.rom,[self.edit(),self.edit(expect={'hp':17})])
  self.assertEqual(self.rom.ledger,[])
 def test_drop_expectation_and_rarity(self):
  for expect,drop in [({'item_1':93},{'item':'potion','rarity':0}),({'item_1':93,'item_1_rarity':20},{'item':'missing','rarity':0}),({'item_1':93,'item_1_rarity':20},{'item':'potion','rarity':256})]:
   with self.assertRaises(PatchError):apply_enemy_edits(self.rom,[self.edit(fields={},expect=expect,drops={'item_1':drop})])
 def test_drop_disabled(self):
  apply_enemy_edits(self.rom,[self.edit(fields={},expect={'item_1':93,'item_1_rarity':20},drops={'item_1':{'item':None,'rarity':20}})])
  self.assertEqual(read_record(self.rom,'enemies',1)['item_1'],0)
 def test_unknown_flags_preserved(self):
  off=self.rom.offset(layout('enemies',1)[1]+26,2);self.rom.data[off:off+2]=(0x4021).to_bytes(2,'little')
  apply_enemy_edits(self.rom,[self.edit(fields={},expect={'weaknesses':0x4021},flags={'weaknesses':{'add':['flame']}})])
  self.assertEqual(read_record(self.rom,'enemies',1)['weaknesses'],0x4023)
 def test_clone_structure_resources_and_sort(self):
  p=room_address(self.rom,0,6);before=entities(self.rom,p)
  apply_level_edits(self.rom,{},[self.clone()]);after=entities(self.rom,p)
  self.assertEqual(len(after),len(before)+1);self.assertEqual([e.x for e in after],sorted(e.x for e in after))
  clone=next(e for e in after if e.unique_id==9)
  self.assertEqual((clone.subtype,clone.byte_8,clone.var_a,clone.var_b),(2,0,0,0))
  self.assertEqual(audit_encounters(self.rom,0,6)['errors'],[])
 def test_move_spawner_preserves_parameters(self):
  p=room_address(self.rom,0,3);before=entities(self.rom,p)
  move={'op':'move','room':{'sector':0,'room':3},'entity_id':3,'enemy':'zombie','from':[128,176],'to':[192,176]}
  apply_level_edits(self.rom,{},[move]);after=entities(self.rom,p)
  old=next(e for e in before if e.unique_id==3);new=next(e for e in after if e.unique_id==3)
  self.assertEqual((new.byte_8,new.var_a,new.var_b),(old.byte_8,old.var_a,old.var_b))
  self.assertEqual(sorted(e.pack() for e in before if e.unique_id!=3),sorted(e.pack() for e in after if e.unique_id!=3))
 def test_reused_identity(self):
  with self.assertRaises(PatchError):apply_level_edits(self.rom,{},[self.clone(entity_id=2)])
 def test_clone_from_clone_rejected(self):
  with self.assertRaises(PatchError):apply_level_edits(self.rom,{},[self.clone(),self.clone(source_id=9,entity_id=10)])
 def test_clone_limit(self):
  with self.assertRaises(PatchError):apply_level_edits(self.rom,{},[self.clone(entity_id=i) for i in [9,10,11]])
  self.assertEqual(self.rom.ledger,[])
 def test_spawner_clone_rejected(self):
  with self.assertRaises(PatchError):apply_level_edits(self.rom,{},[self.clone(room={'sector':0,'room':3},source_id=3,enemy='zombie')])
 def test_foreign_subtype_rejected(self):
  with self.assertRaises(PatchError):apply_level_edits(self.rom,{},[self.clone(room={'sector':0,'room':3},source_id=3)])
 def test_boss_and_script_entities_protected(self):
  with self.assertRaises(PatchError):apply_level_edits(self.rom,{},[self.clone(enemy='creaking-skull')])
  with self.assertRaises(PatchError):apply_level_edits(self.rom,{},[self.clone(source_id=0)])
 def test_out_of_bounds(self):
  with self.assertRaises(PatchError):apply_level_edits(self.rom,{},[self.clone(to=[768,176])])
 def test_changed_native_code_rejected(self):
  self.rom.write_integer(layout('enemies',2)[1]+4,0,4,'test-native-code')
  with self.assertRaises(PatchError):apply_level_edits(self.rom,{},[self.clone()])
 def test_workshop_preserves_native_dna_unknown_bytes(self):
  address=layout('enemies',1)[1];before=self.rom.read(address,36)
  apply_manifest(self.rom,ROOT/'examples/enemy-workshop/mod.json');after=self.rom.read(address,36)
  self.assertEqual(before[:8],after[:8]);self.assertEqual(before[23:26],after[23:26]);self.assertEqual(before[28:],after[28:])
if __name__=='__main__':unittest.main()
