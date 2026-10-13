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
 def boot_melody(self):return {'tempo':75,'volume':64,'notes':[{'key':60,'velocity':80,'ticks':24}]}
 def test_melody_single_owner_conflict(self):
  for name in ('a','b'):self.write(name+'.json',self.module(name,boot_melody=self.boot_melody()))
  for paths in (['a.json','b.json'],['b.json','a.json']):
   with self.assertRaisesRegex(PatchError,'Boot melody conflict between '+paths[0][0]+' and '+paths[1][0]):compose_project(self.project(paths))
 def test_melody_source_rebased_and_fingerprinted(self):
  source=self.root/'modules/assets/tone.wav';source.parent.mkdir(parents=True);source.write_bytes(b'first source')
  data=self.boot_melody();data['sample']={'source':'assets/tone.wav','provenance':'Original test','loop_start':0}
  self.write('modules/music.json',self.module('music',boot_melody=data));p=self.project(['modules/music.json']);a=compose_project(p)
  self.assertEqual(a['manifest']['boot_melody']['sample']['source'],'modules/assets/tone.wav')
  self.assertEqual(a['report']['boot_melody_owner'],'music');self.assertEqual(len(a['report']['assets']),1)
  source.write_bytes(b'changed source');self.assertNotEqual(a['report']['assets'],compose_project(p)['report']['assets'])
 def test_melody_source_size_budget(self):
  source=self.root/'tone.wav';source.write_bytes(bytes(131073));data=self.boot_melody()
  data['sample']={'source':'tone.wav','provenance':'Original test','loop_start':0}
  self.write('music.json',self.module('music',boot_melody=data))
  with self.assertRaisesRegex(PatchError,'exceeds128KiB'):compose_project(self.project(['music.json']))
 def test_melody_source_escape_rejected(self):
  self.write('root.json',{});data=self.boot_melody();data['sample']={'source':'../root.json','provenance':'Original','loop_start':0}
  self.write('modules/music.json',self.module('music',boot_melody=data))
  with self.assertRaisesRegex(PatchError,'escapes'):compose_project(self.project(['modules/music.json']))
 def test_melody_invalid_settings_rejected_without_rom(self):
  data=self.boot_melody();data['repeats']=0;self.write('a.json',self.module('a',boot_melody=data))
  with self.assertRaises(PatchError):compose_project(self.project(['a.json']))
 def test_generated_melody_needs_no_assets(self):
  self.write('a.json',self.module('a',boot_melody=self.boot_melody()));a=compose_project(self.project(['a.json']))
  self.assertEqual(a['report']['assets'],[]);self.assertEqual(a['manifest']['boot_melody'],self.boot_melody())
 def test_soul_module_composes_and_fingerprints(self):
  edit={'soul':'winged-skeleton','expect':{'mana_cost':12},'fields':{'mana_cost':6}}
  self.write('a.json',self.module('a',soul_edits=[edit]));p=self.project(['a.json'])
  a=compose_project(p);self.assertEqual(a['manifest']['soul_edits'],[edit]);self.assertEqual(a['report']['soul_targets'],1)
  edit['fields']['mana_cost']=7;self.write('a.json',self.module('a',soul_edits=[edit]))
  self.assertNotEqual(a['report']['modules'],compose_project(p)['report']['modules'])
 def test_soul_ownership_names_both_modules(self):
  edit={'soul':'winged-skeleton','expect':{'mana_cost':12},'fields':{'mana_cost':6}}
  for name in ('a','b'):self.write(name+'.json',self.module(name,soul_edits=[edit]))
  with self.assertRaisesRegex(PatchError,'Soul edit conflict winged-skeleton between a and b'):compose_project(self.project(['a.json','b.json']))
  self.write('a.json',self.module('a',soul_edits=[edit,edit]))
  with self.assertRaisesRegex(PatchError,'between a and a'):compose_project(self.project(['a.json']))
 def test_soul_module_validates_before_rom_loading(self):
  for edit in ({'soul':'unknown','expect':{'mana_cost':12},'fields':{'mana_cost':6}},
               {'soul':'winged-skeleton','expect':{'mana_cost':12},'fields':{'mana_cost':0}}):
   self.write('a.json',self.module('a',soul_edits=[edit]))
   with self.assertRaises(PatchError):compose_project(self.project(['a.json']))
 def test_soul_table_conflicts_in_either_module_order(self):
  edit={'soul':'winged-skeleton','expect':{'mana_cost':12},'fields':{'mana_cost':6}}
  self.write('named.json',self.module('named',soul_edits=[edit]))
  for fields in ({'mana_cost':6},{'damage_multiplier':2}):
   self.write('raw.json',self.module('raw',table_edits=[{'table':'red_souls','index':'0x1','fields':fields}]))
   for paths in (['named.json','raw.json'],['raw.json','named.json']):
    with self.assertRaisesRegex(PatchError,'Soul/table record conflict winged-skeleton.*between named and raw'):compose_project(self.project(paths))
 def test_soul_table_conflict_within_one_module(self):
  edit={'soul':'winged-skeleton','expect':{'mana_cost':12},'fields':{'mana_cost':6}}
  self.write('a.json',self.module('a',soul_edits=[edit],table_edits=[{'table':'red_souls','index':1,'fields':{'mana_cost':6}}]))
  with self.assertRaisesRegex(PatchError,'between a and a'):compose_project(self.project(['a.json']))
 def test_unrelated_soul_table_records_still_compose(self):
  edit={'soul':'winged-skeleton','expect':{'mana_cost':12},'fields':{'mana_cost':6}}
  raw={'table':'red_souls','index':2,'fields':{'mana_cost':8}}
  self.write('a.json',self.module('a',soul_edits=[edit],table_edits=[raw]))
  result=compose_project(self.project(['a.json']))
  self.assertEqual(result['manifest']['table_edits'],[raw]);self.assertEqual(result['report']['soul_targets'],1)
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
 def test_new_game_start_singleton(self):
  start={'sector':0,'room':31,'position':[128,141]}
  self.write('a.json',self.module('a',new_game_start=start))
  self.write('b.json',self.module('b',new_game_start=start))
  with self.assertRaisesRegex(PatchError,'New-game start conflict between a and b'):compose_project(self.project(['a.json','b.json']))
  alone=compose_project(self.project(['a.json']))
  self.assertEqual(alone['manifest']['new_game_start'],start)
  self.write('c.json',self.module('c',new_game_start=True))
  with self.assertRaisesRegex(PatchError,'must be an object'):compose_project(self.project(['c.json']))
 def test_palette_tint_target_conflict(self):
  tint={'target':'zombie','style':'blood','scope':'shared-native-palette'}
  for name in ('a','b'):self.write(name+'.json',self.module(name,palette_tints=[tint]))
  with self.assertRaisesRegex(PatchError,'Palette tint conflict zombie between a and b'):compose_project(self.project(['a.json','b.json']))
  self.write('a.json',self.module('a',palette_tints=[tint]))
  self.write('b.json',self.module('b',palette_tints=[dict(tint,target='save-flame')]))
  merged=compose_project(self.project(['a.json','b.json']))
  self.assertEqual([e['target'] for e in merged['manifest']['palette_tints']],['zombie','save-flame'])
 def test_geometry_replacements_compose(self):
  base=self.geometry();base['metatile_replacements']=[{'id':1,'minitiles':[0]*16,'collision':[0]*16}]
  other=self.geometry(2);other['metatile_replacements']=[{'id':2,'minitiles':[0]*16,'collision':[0]*16}]
  self.write('a.json',self.module('a',geometry_edits=[base]));self.write('b.json',self.module('b',geometry_edits=[other]))
  with self.assertRaisesRegex(PatchError,'Multiple custom metatile providers'):compose_project(self.project(['a.json','b.json']))
  cells=self.geometry(2)
  self.write('b.json',self.module('b',geometry_edits=[cells]))
  merged=compose_project(self.project(['a.json','b.json']))
  self.assertEqual(merged['manifest']['geometry_edits'][0]['metatile_replacements'],base['metatile_replacements'])
  self.assertEqual([c['x'] for c in merged['manifest']['geometry_edits'][0]['cells']],[1,2])
  both=self.geometry();both['metatiles']=[];both['metatile_replacements']=[]
  self.write('a.json',self.module('a',geometry_edits=[both]))
  with self.assertRaisesRegex(PatchError,'not both'):compose_project(self.project(['a.json']))
 def test_duplicate_door_endpoint(self):
  connection={'a':{'room':{'sector':0,'room':3},'door':2,'spawn':[0,0]},'b':{'room':{'sector':0,'room':6},'door':0,'spawn':[0,0]}}
  for name in ('a','b'):self.write(name+'.json',self.module(name,room_edits={'connections':[connection]}))
  with self.assertRaisesRegex(PatchError,'Door endpoint conflict'):compose_project(self.project(['a.json','b.json']))
 def test_duplicate_entity_move(self):
  move={'room':{'sector':0,'room':3},'entity_id':1,'from':[0,0],'to':[1,1]}
  for name in ('a','b'):self.write(name+'.json',self.module(name,room_edits={'moves':[move]}))
  with self.assertRaisesRegex(PatchError,'Entity move conflict'):compose_project(self.project(['a.json','b.json']))
 def test_full_list_room_conflicts_name_both_modules(self):
  entities=[{'x':1,'y':2,'unique_id':3,'type':4,'subtype':5,'byte_8':0,'var_a':0,'var_b':0}]
  doors=[{'x':1,'y':2,'destination':3,'dest_x':0,'dest_y':0,'dest_x_2':0,'dest_y_2':0,'unused':0}]
  for name in ('a','b'):self.write(name+'.json',self.module(name,entity_lists=[{'sector':0,'room':3,'entities':entities}]))
  with self.assertRaisesRegex(PatchError,r'Entity list conflict \(0, 3\) between a and b'):compose_project(self.project(['a.json','b.json']))
  for name in ('a','b'):self.write(name+'.json',self.module(name,door_lists=[{'sector':0,'room':3,'doors':doors}]))
  with self.assertRaisesRegex(PatchError,r'Door list conflict \(0, 3\) between a and b'):compose_project(self.project(['a.json','b.json']))
  self.write('a.json',self.module('a',entity_lists=[{'sector':0,'room':3,'entities':entities}]))
  self.write('b.json',self.module('b',entity_lists=[{'sector':0,'room':31,'entities':entities}]))
  merged=compose_project(self.project(['a.json','b.json']))
  self.assertEqual(len(merged['manifest']['entity_lists']),2);self.assertEqual(merged['report']['full_list_rooms'],2)
 def test_full_lists_reject_staged_edits(self):
  entities=[{'x':1,'y':2,'unique_id':3,'type':4,'subtype':5,'byte_8':0,'var_a':0,'var_b':0}]
  move={'room':{'sector':0,'room':3},'entity_id':1,'from':[0,0],'to':[1,1]}
  connection={'a':{'room':{'sector':0,'room':3},'door':2,'spawn':[0,0]},'b':{'room':{'sector':0,'room':6},'door':0,'spawn':[0,0]}}
  self.write('full.json',self.module('full',entity_lists=[{'sector':0,'room':3,'entities':entities}]))
  self.write('moves.json',self.module('moves',room_edits={'moves':[move]}))
  with self.assertRaisesRegex(PatchError,'Full entity/door lists conflict with staged room edits between full and moves'):compose_project(self.project(['full.json','moves.json']))
  self.write('conns.json',self.module('conns',room_edits={'connections':[connection]}))
  with self.assertRaisesRegex(PatchError,'staged room edits'):compose_project(self.project(['full.json','conns.json']))
  self.write('encs.json',self.module('encs',enemy_encounters=[{'room':{'sector':0,'room':6},'clone':{}}]))
  with self.assertRaisesRegex(PatchError,'staged room edits'):compose_project(self.project(['full.json','encs.json']))
  self.write('both.json',self.module('both',entity_lists=[{'sector':0,'room':3,'entities':entities}],room_edits={'moves':[move]}))
  with self.assertRaisesRegex(PatchError,'staged room edits'):compose_project(self.project(['both.json']))
  self.write('empty.json',self.module('empty',entity_lists=[]))
  merged=compose_project(self.project(['empty.json','moves.json']))
  self.assertEqual(merged['report']['full_list_rooms'],0)
 def test_full_list_shapes_rejected(self):
  self.write('a.json',self.module('a',entity_lists=[{'sector':0,'room':300,'entities':[{}]}]))
  with self.assertRaises(PatchError):compose_project(self.project(['a.json']))
  self.write('a.json',self.module('a',door_lists=[{'sector':0,'room':3,'doors':[]}] ))
  with self.assertRaisesRegex(PatchError,'rows'):compose_project(self.project(['a.json']))
  self.write('a.json',self.module('a',entity_lists=[{'sector':0,'room':3}]))
  with self.assertRaisesRegex(PatchError,'rows'):compose_project(self.project(['a.json']))
  self.write('a.json',self.module('a',entity_lists=[{'sector':0,'room':3,'entities':[],'extra':1}]))
  with self.assertRaisesRegex(PatchError,'Invalid entity_lists entry'):compose_project(self.project(['a.json']))
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
 def test_composed_imported_melody_matches_flat(self):
  a=load_image(ROOT/'CastlevaniaAoS.gba');b=load_image(ROOT/'CastlevaniaAoS.gba')
  apply_manifest(a,ROOT/'examples/imported-melody/project.json');apply_manifest(b,ROOT/'examples/imported-melody/mod.json')
  self.assertEqual(a.data,b.data);self.assertEqual(a.ledger,b.ledger);self.assertEqual(a.allocations,b.allocations);self.assertEqual(a.music_report,b.music_report)
  self.assertEqual(a.project_report['boot_melody_owner'],'original-music');self.assertEqual(len(a.project_report['assets']),1)
 def test_composed_soul_cost_matches_flat(self):
  a=load_image(ROOT/'CastlevaniaAoS.gba');b=load_image(ROOT/'CastlevaniaAoS.gba')
  apply_manifest(a,ROOT/'examples/soul-cost/project.json');apply_manifest(b,ROOT/'examples/soul-cost/mod.json')
  self.assertEqual(a.data,b.data);self.assertEqual(a.ledger,b.ledger);self.assertEqual(a.allocations,b.allocations)
  self.assertEqual(a.soul_report,b.soul_report);self.assertEqual(a.project_report['soul_targets'],1)
 def test_composed_build_matches_flat_manifest(self):
  a=load_image(ROOT/'CastlevaniaAoS.gba');b=load_image(ROOT/'CastlevaniaAoS.gba')
  apply_manifest(a,ROOT/'examples/bridge-project/project.json');apply_manifest(b,ROOT/'examples/bridge-route/mod.json')
  self.assertEqual(a.data,b.data);self.assertEqual(a.ledger,b.ledger);self.assertEqual(a.allocations,b.allocations);self.assertEqual(len(a.project_report['modules']),5)
 def test_composed_sprite_build_matches_flat_manifest(self):
  a=load_image(ROOT/'CastlevaniaAoS.gba');b=load_image(ROOT/'CastlevaniaAoS.gba')
  apply_manifest(a,ROOT/'examples/sky-invaders/project.json');apply_manifest(b,ROOT/'examples/sky-invaders/mod.json')
  self.assertEqual(a.data,b.data);self.assertEqual(a.ledger,b.ledger);self.assertEqual(a.allocations,b.allocations)
  self.assertEqual(len(a.project_report['modules']),1);self.assertEqual(len(a.project_report['assets']),2)
 def test_composed_new_sections_match_flat_manifest(self):
  source=json.loads((ROOT/'examples/custom_room/mod.json').read_text())
  with local_temp() as t:
   root=Path(t)
   for name in ('flesh-tiles.json','flesh-palette.json'):
    (root/name).write_bytes((ROOT/'examples/custom_room'/name).read_bytes())
   arts=[dict(a,graphics_source='flesh-tiles.json',palette_source='flesh-palette.json') for a in source['room_assets']]
   flat=dict(schema_version=1,id='full-custom',new_game_start=source['new_game_start'],
             palette_tints=source['palette_tints'],room_assets=arts,geometry_edits=source['geometry_edits'],
             entity_lists=source['entity_lists'],door_lists=source['door_lists'])
   modules={'start':dict(new_game_start=source['new_game_start']),'tints':dict(palette_tints=source['palette_tints']),
            'art':dict(room_assets=arts),'terrain':dict(geometry_edits=source['geometry_edits']),
            'entities':dict(entity_lists=source['entity_lists']),'doors':dict(door_lists=source['door_lists'])}
   for name,fields in modules.items():
    (root/(name+'.json')).write_text(json.dumps(dict(schema_version=1,id=name,**fields)))
   (root/'project.json').write_text(json.dumps(dict(schema_version=1,kind='tsf-project',id='custom-full',modules=[n+'.json' for n in modules])))
   a=load_image(ROOT/'CastlevaniaAoS.gba');b=load_image(ROOT/'CastlevaniaAoS.gba')
   from aria.cli import apply_manifest_data
   apply_manifest(a,root/'project.json');apply_manifest_data(b,flat,root)
   self.assertEqual(a.data,b.data);self.assertEqual(a.ledger,b.ledger);self.assertEqual(a.allocations,b.allocations)
   self.assertEqual(len(a.project_report['modules']),6);self.assertEqual(a.project_report['full_list_rooms'],3)
 def test_late_domain_failure_preserves_caller(self):
  r=load_image(ROOT/'CastlevaniaAoS.gba');before=copy.deepcopy(r.__dict__)
  base=json.loads((ROOT/'examples/bridge-route/mod.json').read_text());bad=copy.deepcopy(base['geometry_edits'][-1]);bad['expected_layout_sha256']='0'*64
  with local_temp() as t:
   root=Path(t);(root/'routes.json').write_text(json.dumps(dict(schema_version=1,id='routes',room_edits=base['room_edits'])))
   (root/'bad.json').write_text(json.dumps(dict(schema_version=1,id='bad',geometry_edits=[bad])))
   (root/'project.json').write_text(json.dumps(dict(schema_version=1,kind='tsf-project',id='late-failure',modules=['routes.json','bad.json'])))
   with self.assertRaisesRegex(PatchError,'preimage mismatch'):apply_manifest(r,root/'project.json')
  self.assertEqual(r.__dict__,before)
