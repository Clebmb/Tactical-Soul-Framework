import copy,json,tempfile,unittest
from pathlib import Path
from aria.projects import compose_project
from aria.cli import apply_manifest,load_image
from aria.core import PatchError
ROOT=Path(__file__).resolve().parents[1]
def local_temp():
 folder=(ROOT/'local/project-tests').resolve();folder.mkdir(parents=True,exist_ok=True)
 result=tempfile.TemporaryDirectory(dir=folder)
 if not Path(result.name).resolve().is_relative_to(folder):raise RuntimeError('Unexpected temporary directory')
 return result
class ProjectTests(unittest.TestCase):
 def setUp(self):
  self.tmp=local_temp();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
 def write(self,name,value):
  p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value));return p
 def module(self,name='one',**fields):return dict(schema_version=1,id=name,**fields)
 def project(self,paths):return self.write('project.json',dict(schema_version=1,kind='tsf-project',id='test-project',modules=paths))
 def geometry(self,x=1,preimage='a'*64):return {'room':{'sector':0,'room':5},'layer':0,'expected_layout_sha256':preimage,'cells':[{'x':x,'y':3,'expect':0,'value':6}]}
 def test_terrain_batches_merge_in_order(self):
  self.write('a.json',self.module('a',geometry_edits=[self.geometry(1)]));self.write('b.json',self.module('b',geometry_edits=[self.geometry(2)]))
  p=self.project(['a.json','b.json']);a=compose_project(p);b=compose_project(p)
  self.assertEqual(a,b);self.assertEqual(len(a['manifest']['geometry_edits']),1);self.assertEqual([c['x'] for c in a['manifest']['geometry_edits'][0]['cells']],[1,2]);self.assertEqual(a['report']['geometry_cells'],2)
 def test_geometry_collision_names_both_modules(self):
  for name in ('a','b'):self.write(name+'.json',self.module(name,geometry_edits=[self.geometry()]))
  with self.assertRaisesRegex(PatchError,'between a and b'):compose_project(self.project(['a.json','b.json']))
 def test_preimages_must_agree(self):
  self.write('a.json',self.module('a',geometry_edits=[self.geometry()]));self.write('b.json',self.module('b',geometry_edits=[self.geometry(2,'b'*64)]))
  with self.assertRaisesRegex(PatchError,'preimage disagreement'):compose_project(self.project(['a.json','b.json']))
 def test_custom_definition_provider_is_unique(self):
  for name,x in [('a',1),('b',2)]:
   g=self.geometry(x);g['metatiles']=[];self.write(name+'.json',self.module(name,geometry_edits=[g]))
  with self.assertRaisesRegex(PatchError,'Multiple custom metatile providers'):compose_project(self.project(['a.json','b.json']))
 def test_duplicate_door_endpoint(self):
  connection={'a':{'room':{'sector':0,'room':3},'door':2,'spawn':[0,0]},'b':{'room':{'sector':0,'room':6},'door':0,'spawn':[0,0]}}
  for name in ('a','b'):self.write(name+'.json',self.module(name,room_edits={'connections':[connection]}))
  with self.assertRaisesRegex(PatchError,'Door endpoint conflict'):compose_project(self.project(['a.json','b.json']))
 def test_duplicate_entity_move(self):
  move={'room':{'sector':0,'room':3},'entity_id':1,'from':[0,0],'to':[1,1]}
  for name in ('a','b'):self.write(name+'.json',self.module(name,room_edits={'moves':[move]}))
  with self.assertRaisesRegex(PatchError,'Entity move conflict'):compose_project(self.project(['a.json','b.json']))
 def test_paths_and_schema_rejected(self):
  self.write('one.json',self.module())
  for paths in ([],['../outside.json'],[str((self.root/'one.json').resolve())],['one.json','one.json']):
   with self.assertRaises(PatchError):compose_project(self.project(paths))
  p=self.project(['one.json']);data=json.loads(p.read_text());data['schema_version']=True;p.write_text(json.dumps(data))
  with self.assertRaises(PatchError):compose_project(p)
 def test_duplicate_ids_and_unsupported_fields(self):
  self.write('a.json',self.module());self.write('b.json',self.module())
  with self.assertRaisesRegex(PatchError,'Duplicate module id'):compose_project(self.project(['a.json','b.json']))
  self.write('a.json',self.module(frame_hook={}))
  with self.assertRaisesRegex(PatchError,'unsupported project fields'):compose_project(self.project(['a.json']))
 def test_assets_rebased_and_fingerprinted(self):
  self.write('mods/assets/g.json',{'tiles':[]});self.write('mods/assets/p.json',{'colors':[]})
  self.write('mods/art.json',self.module(room_assets=[{'graphics_source':'assets/g.json','palette_source':'assets/p.json'}]))
  p=self.project(['mods/art.json']);a=compose_project(p)
  self.assertEqual(a['manifest']['room_assets'][0]['graphics_source'],'mods/assets/g.json');self.assertEqual(len(a['report']['assets']),2)
  self.write('mods/assets/g.json',{'tiles':[1]});self.assertNotEqual(a['report']['assets'],compose_project(p)['report']['assets'])
 def test_asset_escape_rejected(self):
  self.write('root.json',{});self.write('mods/art.json',self.module(room_assets=[{'graphics_source':'../root.json','palette_source':'../root.json'}]))
  with self.assertRaisesRegex(PatchError,'escapes'):compose_project(self.project(['mods/art.json']))
 def test_sprite_sources_rebased_and_fingerprinted(self):
  art={'resource':'background-bats','scope':'all_registered_consumers','source':'assets/art.json','expected_page_sha256':'0'*64,'provenance':'Original synthetic pixels'}
  self.write('mods/assets/art.json',{'width':128,'height':32});self.write('mods/assets/p.json',[[0,0,0]]*16)
  self.write('mods/art.json',self.module('art',sprite_assets=[dict(art)]))
  p=self.project(['mods/art.json']);a=compose_project(p)
  self.assertEqual(a['manifest']['sprite_assets'][0]['source'],'mods/assets/art.json');self.assertEqual(len(a['report']['assets']),1)
  self.write('mods/assets/art.json',{'width':128,'height':33});self.assertNotEqual(a['report']['assets'],compose_project(p)['report']['assets'])
  palette=dict(art,palette_source='assets/p.json',expected_palette_sha256='1'*64)
  self.write('mods/art.json',self.module('art',sprite_assets=[palette]))
  self.assertEqual(len(compose_project(p)['report']['assets']),2)
 def test_duplicate_sprite_resource_names_both_modules(self):
  art={'resource':'background-bats','scope':'all_registered_consumers','source':'a.json','expected_page_sha256':'0'*64,'provenance':'x'}
  self.write('a.json',{'width':1});self.write('b.json',{'width':1})
  for name in ('a','b'):self.write(name+'.json',self.module(name,sprite_assets=[dict(art,source=name+'.json')]))
  with self.assertRaisesRegex(PatchError,'Sprite resource conflict background-bats between a and b'):compose_project(self.project(['a.json','b.json']))
 def test_sprite_source_escape_rejected(self):
  self.write('root.json',{});self.write('mods/art.json',self.module(sprite_assets=[{'resource':'r','scope':'s','source':'../root.json','expected_page_sha256':'0'*64,'provenance':'x'}]))
  with self.assertRaisesRegex(PatchError,'escapes'):compose_project(self.project(['mods/art.json']))

@unittest.skipUnless((ROOT/'CastlevaniaAoS.gba').exists(),'private supported host absent')
class NativeImageProjectTests(unittest.TestCase):
 def test_composed_build_matches_flat_manifest(self):
  a=load_image(ROOT/'CastlevaniaAoS.gba');b=load_image(ROOT/'CastlevaniaAoS.gba')
  apply_manifest(a,ROOT/'examples/bridge-project/project.json');apply_manifest(b,ROOT/'examples/bridge-route/mod.json')
  self.assertEqual(a.data,b.data);self.assertEqual(a.ledger,b.ledger);self.assertEqual(a.allocations,b.allocations);self.assertEqual(len(a.project_report['modules']),5)
 def test_composed_sprite_build_matches_flat_manifest(self):
  a=load_image(ROOT/'CastlevaniaAoS.gba');b=load_image(ROOT/'CastlevaniaAoS.gba')
  apply_manifest(a,ROOT/'examples/sky-invaders/project.json');apply_manifest(b,ROOT/'examples/sky-invaders/mod.json')
  self.assertEqual(a.data,b.data);self.assertEqual(a.ledger,b.ledger);self.assertEqual(a.allocations,b.allocations)
  self.assertEqual(len(a.project_report['modules']),1);self.assertEqual(len(a.project_report['assets']),2)
 def test_late_domain_failure_preserves_caller(self):
  r=load_image(ROOT/'CastlevaniaAoS.gba');before=copy.deepcopy(r.__dict__)
  base=json.loads((ROOT/'examples/bridge-route/mod.json').read_text());bad=copy.deepcopy(base['geometry_edits'][-1]);bad['expected_layout_sha256']='0'*64
  with local_temp() as t:
   root=Path(t);(root/'routes.json').write_text(json.dumps(dict(schema_version=1,id='routes',room_edits=base['room_edits'])))
   (root/'bad.json').write_text(json.dumps(dict(schema_version=1,id='bad',geometry_edits=[bad])))
   (root/'project.json').write_text(json.dumps(dict(schema_version=1,kind='tsf-project',id='late-failure',modules=['routes.json','bad.json'])))
   with self.assertRaisesRegex(PatchError,'preimage mismatch'):apply_manifest(r,root/'project.json')
  self.assertEqual(r.__dict__,before)
