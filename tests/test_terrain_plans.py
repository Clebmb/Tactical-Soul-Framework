import copy,json,unittest
from pathlib import Path
from aria.core import PatchError
from aria.cli import load_image
from aria.terrain_plans import plan_terrain
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless((ROOT/'CastlevaniaAoS.gba').exists(),'private supported host absent')
class TerrainPlanTests(unittest.TestCase):
 def setUp(self):
  self.r=load_image(ROOT/'CastlevaniaAoS.gba');self.spec=json.loads((ROOT/'examples/bridge-route/terrain-plan.json').read_text())
 def test_paint_matches_checked_example(self):
  original=copy.deepcopy(self.r.__dict__);spec=copy.deepcopy(self.spec);p=plan_terrain(self.r,self.spec)
  self.assertEqual(p['changed_cells'],22);self.assertEqual(p['painted_cells'],36)
  example=json.loads((ROOT/'examples/bridge-route/mod.json').read_text())
  self.assertEqual(p['geometry_edit'],example['geometry_edits'][-1]);self.assertEqual(self.r.__dict__,original);self.assertEqual(self.spec,spec)
 def test_rejected_plans_preserve_allocation_state(self):
  for problem in ('image','layout','overlap','bounds','missing','boolean','unregistered'):
   s=copy.deepcopy(self.spec)
   if problem=='image':s['expected_image_sha256']='0'*64
   elif problem=='layout':s['expected_layout_sha256']='0'*64
   elif problem=='overlap':s['rectangles']*=2
   elif problem=='bounds':s['rectangles'][0]['width']=16
   elif problem=='missing':s['rectangles'][0]['value']=4095
   elif problem=='boolean':s['rectangles'][0]['x']=True
   else:
    self.r.profile['geometry_edit_rooms']=[]
   original=copy.deepcopy(self.r.__dict__)
   with self.assertRaises(PatchError):plan_terrain(self.r,s)
   self.assertEqual(self.r.__dict__,original)
 def test_noop_and_schema_rejected(self):
  for s in ({},dict(self.spec,schema_version=True),dict(self.spec,rectangles=[]),dict(self.spec,rectangles=[{'x':0,'y':0,'width':1,'height':1,'value':0}])):
   with self.assertRaises(PatchError):plan_terrain(self.r,s)
 def test_deterministic(self):self.assertEqual(plan_terrain(self.r,self.spec),plan_terrain(self.r,self.spec))
