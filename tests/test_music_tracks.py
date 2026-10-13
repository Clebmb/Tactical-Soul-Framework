import copy,json,unittest
from pathlib import Path
from aria.music import plan_boot_melody,install_boot_melody
from aria.cli import load_image,apply_manifest
from aria.audio import decode_song_header,iter_events
from aria.core import PatchError
ROOT=Path(__file__).resolve().parents[1]
def melody():return json.loads((ROOT/'examples/polyphonic-melody/mod.json').read_text())['boot_melody']
class TrackPlanTests(unittest.TestCase):
 def test_plan_independent_clocks_and_no_mutation(self):
  data=melody();data['tracks'][1]['notes'].insert(0,{'rest':48});data['tracks'][1]['volume']=20
  before=copy.deepcopy(data);plan=plan_boot_melody(data)
  self.assertEqual(data,before);self.assertEqual([t['ticks'] for t in plan['tracks']],[96,144]);self.assertEqual(plan['total_ticks'],144);self.assertEqual(plan['max_gated_notes'],2)
 def test_schema_and_track_count(self):
  for tracks in ([],[melody()['tracks'][0]]*5,None,[{'notes':[] }],[{'notes':melody()['tracks'][0]['notes'],'tempo':60}]):
   data=melody();data['tracks']=tracks
   with self.assertRaises(PatchError):plan_boot_melody(data)
  data=melody();data['notes']=data['tracks'][0]['notes']
  with self.assertRaises(PatchError):plan_boot_melody(data)
 def test_overridden_global_volume_still_validated(self):
  data=melody();data['volume']=101
  for track in data['tracks']:track['volume']=20
  with self.assertRaises(PatchError):plan_boot_melody(data)
 def test_aggregate_tick_budget(self):
  data=melody();data['repeats']=4
  data['tracks']=[{'notes':[{'key':60,'velocity':80,'ticks':96}]*16}]*3
  with self.assertRaisesRegex(PatchError,'aggregate'):plan_boot_melody(data)
 def test_aggregate_step_budget(self):
  data=melody();data['tracks']=[{'notes':[{'key':60,'velocity':80,'ticks':1}]*64}]*3
  with self.assertRaisesRegex(PatchError,'128'):plan_boot_melody(data)
@unittest.skipUnless((ROOT/'CastlevaniaAoS.gba').exists(),'private host absent')
class TrackImageTests(unittest.TestCase):
 def test_shared_bank_and_independent_schedules(self):
  data=melody();data['tracks'][1]['notes'].insert(0,{'rest':48})
  rom=load_image(ROOT/'CastlevaniaAoS.gba');r=install_boot_melody(rom,data);header=decode_song_header(rom.data,r['header']-rom.base)
  self.assertEqual(header['tracks'],2);self.assertEqual(header['voicegroup'],r['voice']);self.assertEqual(len(rom.ledger),6)
  events=[list(iter_events(rom.data,address-rom.base)) for address in r['track_addresses']]
  self.assertIn((0,('note',60,80,0,48)),events[0]);self.assertIn((48,('note',67,80,0,48)),events[1])
  self.assertEqual([e[-1][0] for e in events],[96,144])
 def test_one_track_matches_legacy_payload(self):
  data=melody();data['tracks']=data['tracks'][:1];legacy={k:v for k,v in data.items() if k!='tracks'};legacy['notes']=data['tracks'][0]['notes']
  a=load_image(ROOT/'CastlevaniaAoS.gba');b=load_image(ROOT/'CastlevaniaAoS.gba');install_boot_melody(a,data);install_boot_melody(b,legacy)
  self.assertEqual(a.data,b.data);self.assertEqual(a.ledger,b.ledger)
 def test_project_flat_identity(self):
  a=load_image(ROOT/'CastlevaniaAoS.gba');b=load_image(ROOT/'CastlevaniaAoS.gba')
  apply_manifest(a,ROOT/'examples/polyphonic-melody/mod.json');apply_manifest(b,ROOT/'examples/polyphonic-melody/project.json')
  self.assertEqual(a.data,b.data);self.assertEqual(a.music_report,b.music_report)
 def test_second_track_allocation_failure_is_atomic(self):
  rom=load_image(ROOT/'CastlevaniaAoS.gba');rom.cursors=[int(r['end'],0)-92 for r in rom.profile['allocation_ranges']];before=copy.deepcopy(rom.__dict__)
  with self.assertRaises(PatchError):install_boot_melody(rom,melody())
  self.assertEqual(rom.__dict__,before)
