import copy,unittest
from aria.core import PatchError
from aria.input_routes import validate_input_route,replay_input_route

class FakeEmulator:
 def __init__(self):self.calls=[]
 def run(self,frames,keys):self.calls.append((frames,list(keys)))

class InputRouteTests(unittest.TestCase):
 def route(self):return {'schema_version':1,'id':'test','segments':[{'label':'walk','frames':12,'keys':[7],'expect':{'world_x':[10,20]}}]}
 def test_success_and_input_preserved(self):
  spec=self.route();before=copy.deepcopy(spec);e=FakeEmulator()
  report=replay_input_route(e,spec,lambda e:{'world_x':15})
  self.assertEqual(report['status'],'passed');self.assertEqual(e.calls,[(12,[7])]);self.assertEqual(spec,before)
 def test_failure_stops_subsequent_input(self):
  spec=self.route();spec['segments'].append({'label':'later','frames':3,'keys':[]})
  e=FakeEmulator();r=replay_input_route(e,spec,lambda e:{'world_x':9})
  self.assertEqual(r['status'],'failed');self.assertEqual(len(e.calls),1)
  self.assertEqual(r['samples'][0]['failures'][0]['actual'],9)
 def test_invalid_descriptor_rejected_before_input(self):
  variants=[]
  for field,value in [('frames',True),('frames',0),('frames',3601),('keys',[7,7]),('keys',[False]),('keys',[16]),('expect',{'unknown':1}),('expect',{'hp':[2,1]}),('expect',{'hp':True})]:
   s=self.route();s['segments'][0][field]=value;variants.append(s)
  variants.extend([dict(self.route(),schema_version=True),dict(self.route(),extra=1),dict(self.route(),segments=[])])
  for spec in variants:
   e=FakeEmulator()
   with self.assertRaises(PatchError):replay_input_route(e,spec,lambda e:{})
   self.assertEqual(e.calls,[])
 def test_duplicate_labels_and_total_budget(self):
  spec=self.route();spec['segments']*=2
  with self.assertRaises(PatchError):validate_input_route(spec)
  spec['segments']=[{'label':str(i),'frames':3600,'keys':[]} for i in range(11)]
  with self.assertRaises(PatchError):validate_input_route(spec)
 def test_missing_observation_fails(self):
  e=FakeEmulator();self.assertEqual(replay_input_route(e,self.route(),lambda e:{})['status'],'failed')
 def test_copy_is_isolated(self):
  s=self.route();v=validate_input_route(s);v['segments'][0]['keys'].append(8);self.assertEqual(s['segments'][0]['keys'],[7])
