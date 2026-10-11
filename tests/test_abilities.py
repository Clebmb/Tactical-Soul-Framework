"""No-ROM configuration, RAM ownership and compiler fingerprint contracts."""
import copy,json,tempfile,hashlib,unittest
from pathlib import Path
from aria.abilities import plan_abilities
from aria.compiler import ensure_callback
from aria.core import PatchError
ROOT=Path(__file__).resolve().parents[1]
PROFILE=json.loads((ROOT/'framework/aos-usa-r0.json').read_text())
class AbilityContracts(unittest.TestCase):
 def spec(self):return {'features':[{'id':'still_regen'},{'id':'focus_heal'}]}
 def test_config_defaults_and_size(self):
  payload,report=plan_abilities(self.spec(),PROFILE)
  self.assertEqual(len(payload),40);self.assertEqual(report['features']['focus_heal']['mana_cost'],3)
  self.assertEqual(len(report['ram_claims']),3)
 def test_order_independent_config(self):
  spec=self.spec();a=plan_abilities(spec,PROFILE)[0];spec['features'].reverse()
  self.assertEqual(a,plan_abilities(spec,PROFILE)[0])
 def test_feature_masks(self):
  for feature,mask in [('still_regen',1),('focus_heal',2)]:
   payload,_=plan_abilities({'features':[{'id':feature}]},PROFILE)
   self.assertEqual(int.from_bytes(payload[8:12],'little'),mask)
 def test_unknown_or_duplicate_feature(self):
  for features in [[{'id':'missing'}],[{'id':'still_regen'},{'id':'still_regen'}]]:
   with self.assertRaises(PatchError):plan_abilities({'features':features},PROFILE)
 def test_ranges_and_booleans(self):
  for field,value in [('interval',0),('interval',36001),('amount',1000),('amount',True)]:
   with self.assertRaises(PatchError):plan_abilities({'features':[{'id':'still_regen',field:value}]},PROFILE)
 def test_unknown_parameter(self):
  with self.assertRaises(PatchError):plan_abilities({'features':[{'id':'focus_heal','speed':3}]},PROFILE)
 def test_empty_and_unknown_spec(self):
  for spec in [{'features':[]},{'features':[{'id':'still_regen'}],'typo':1}]:
   with self.assertRaises(PatchError):plan_abilities(spec,PROFILE)
 def test_profile_abi_drift(self):
  profile=copy.deepcopy(PROFILE);profile["ability_runtime"]["abi_version"]=2
  with self.assertRaises(PatchError):plan_abilities(self.spec(),profile)
 def test_extra_ram_claim(self):
  spec=self.spec();spec['ram_claims']=[{'id':'future-feature','start':'0x0203D060','size':16}]
  self.assertEqual(len(plan_abilities(spec,PROFILE)[1]['ram_claims']),4)
 def test_ram_collisions_and_bounds(self):
  for address,size in [(0x0203D000,4),(0x0203D044,4),(0x0203D050,4),(0x0203D3FC,8),(0x0203D061,4),(0x0203CFFC,4),(0x0203D060,0)]:
   spec=self.spec();spec['ram_claims']=[{'id':'bad','start':address,'size':size}]
   with self.assertRaises(PatchError):plan_abilities(spec,PROFILE)
 def test_duplicate_claim(self):
  spec=self.spec();spec['ram_claims']=[{'id':'dispatcher','start':0x0203D060,'size':4}]
  with self.assertRaises(PatchError):plan_abilities(spec,PROFILE)
 def test_config_tag_changes(self):
  spec=self.spec();before=plan_abilities(spec,PROFILE)[1]['config_tag'];spec['features'][0]['amount']=2
  self.assertNotEqual(before,plan_abilities(spec,PROFILE)[1]['config_tag'])
 def test_header_fingerprint_and_path_guard(self):
  directory=ROOT/'local/framework-tests';directory.mkdir(parents=True,exist_ok=True)
  with tempfile.TemporaryDirectory(dir=directory) as temp:
   folder=Path(temp);names=['runtime.c','link.ld','runtime.bin','api.h']
   for name in names:(folder/name).write_bytes(b'original '+name.encode())
   (folder/'runtime.build.json').write_text(json.dumps({n:hashlib.sha256((folder/n).read_bytes()).hexdigest() for n in names}))
   spec={'source':'runtime.c','linker':'link.ld','file':'runtime.bin','dependencies':['api.h']}
   ensure_callback(folder,spec)
   (folder/'api.h').write_text('changed header')
   with self.assertRaises(PatchError):ensure_callback(folder,spec)
   spec['dependencies']=['../escape.h']
   with self.assertRaises(PatchError):ensure_callback(folder,spec)
if __name__=='__main__':unittest.main()
