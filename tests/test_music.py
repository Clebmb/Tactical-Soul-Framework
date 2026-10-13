import copy,json,unittest
from pathlib import Path
from aria.music import plan_boot_melody,install_boot_melody,BOOT_ENTRY
from aria.cli import load_image
from aria.core import PatchError
from aria.audio import decode_song_header,decode_voice_entry,decode_sample,iter_events
ROOT=Path(__file__).resolve().parents[1]
def melody():return {'tempo':75,'volume':64,'notes':[{'key':60,'velocity':80,'ticks':24}]}
class MelodyTests(unittest.TestCase):
 def test_plan_normalizes_without_mutation(self):
  value=melody();value['tempo']='0x4b';before=copy.deepcopy(value);plan=plan_boot_melody(value)
  self.assertEqual(value,before);self.assertEqual(plan['tempo'],75);self.assertEqual(plan['ticks'],24)
 def test_schema_and_bounds(self):
  for key,value in (('tempo',True),('tempo',29),('volume',101),('notes',[]),('notes',[melody()['notes'][0]]*65)):
   data=melody();data[key]=value
   with self.assertRaises(PatchError):plan_boot_melody(data)
  data=melody();data['loop']=True
  with self.assertRaises(PatchError):plan_boot_melody(data)
 def test_note_and_total_budgets(self):
  for key,value in (('key',47),('key',85),('velocity',0),('ticks',25),('ticks',True)):
   data=melody();data['notes'][0][key]=value
   with self.assertRaises(PatchError):plan_boot_melody(data)
  data=melody();data['notes']=[dict(data['notes'][0],ticks=96)]*17
  with self.assertRaises(PatchError):plan_boot_melody(data)
 def test_repeat_count_and_total_budget(self):
  data=melody();data['repeats']=3
  plan=plan_boot_melody(data);self.assertEqual(plan['total_ticks'],72)
  for count in (0,9,True):
   data['repeats']=count
   with self.assertRaises(PatchError):plan_boot_melody(data)
  data['notes']=[{'key':60,'velocity':80,'ticks':96}]*16;data['repeats']=5
  with self.assertRaises(PatchError):plan_boot_melody(data)
@unittest.skipUnless((ROOT/'CastlevaniaAoS.gba').exists(),'private host absent')
class NativeImageMelodyTests(unittest.TestCase):
 def test_payload_links_and_scheduled_notes(self):
  rom=load_image(ROOT/'CastlevaniaAoS.gba');original=rom.original;report=install_boot_melody(rom,melody())
  header=decode_song_header(rom.data,report['header']-rom.base)
  self.assertEqual(header['tracks'],1);self.assertEqual(header['voicegroup'],report['voice'])
  voice=decode_voice_entry(rom.data,report['voice']-rom.base);self.assertEqual(voice['sample'],report['sample'])
  sample=decode_sample(rom.data,report['sample']-rom.base);self.assertEqual(sample['size'],40)
  events=list(iter_events(rom.data,report['track']-rom.base));self.assertIn((0,('note',60,80,0,24)),events);self.assertEqual(events[-1],(24,('end',)))
  self.assertEqual(rom.original,original);self.assertEqual(len(rom.ledger),5)
 def test_repeated_install_preserves_caller_on_failure(self):
  rom=load_image(ROOT/'CastlevaniaAoS.gba');install_boot_melody(rom,melody());before=copy.deepcopy(rom.__dict__)
  with self.assertRaisesRegex(PatchError,'precondition'):install_boot_melody(rom,melody())
  self.assertEqual(rom.__dict__,before)
 def test_allocation_failure_is_transactional(self):
  rom=load_image(ROOT/'CastlevaniaAoS.gba');rom.cursors=[int(r['end'],0) for r in rom.profile['allocation_ranges']];before=copy.deepcopy(rom.__dict__)
  with self.assertRaisesRegex(PatchError,'Out of declared free space'):install_boot_melody(rom,melody())
  self.assertEqual(rom.__dict__,before)
 def test_ledger_conflict_is_transactional(self):
  rom=load_image(ROOT/'CastlevaniaAoS.gba');rom.write(BOOT_ENTRY,rom.read(BOOT_ENTRY,4),'existing-owner');before=copy.deepcopy(rom.__dict__)
  with self.assertRaisesRegex(PatchError,'Patch conflict'):install_boot_melody(rom,melody())
  self.assertEqual(rom.__dict__,before)
 def test_repeated_schedule_stops_after_exact_pass_count(self):
  data=melody();data['repeats']=3;rom=load_image(ROOT/'CastlevaniaAoS.gba');report=install_boot_melody(rom,data)
  events=list(iter_events(rom.data,report['track']-rom.base))
  self.assertEqual([tick for tick,event in events if event[0]=='note'],[0,24,48])
  self.assertEqual(events[-1],(72,('end',)));self.assertEqual(len(rom.ledger),5)
 def test_default_payload_is_byte_compatible(self):
  a=load_image(ROOT/'CastlevaniaAoS.gba');b=load_image(ROOT/'CastlevaniaAoS.gba');data=melody()
  install_boot_melody(a,data);data['repeats']=1;install_boot_melody(b,data)
  self.assertEqual(a.data,b.data);self.assertEqual(a.ledger,b.ledger)

class PhrasingTests(unittest.TestCase):
 def test_rest_and_gate_plan(self):
  data=melody();data['notes']=[{'rest':48},dict(data['notes'][0],gate_ticks=6)];data['repeats']=2
  before=copy.deepcopy(data);plan=plan_boot_melody(data)
  self.assertEqual(data,before);self.assertEqual(plan['ticks'],72);self.assertEqual(plan['total_ticks'],144)
 def test_invalid_rests_and_gates(self):
  for step in ({'rest':True},{'rest':25},{'rest':24,'key':60},{'key':60,'velocity':80,'ticks':24,'gate_ticks':30},{'key':60,'velocity':80,'ticks':24,'gate_ticks':True}):
   data=melody();data['notes']=[step,melody()['notes'][0]]
   with self.assertRaises(PatchError):plan_boot_melody(data)
 def test_rest_only_and_rest_budget(self):
  for steps in ([{'rest':24}],[{'rest':96}]*16+[melody()['notes'][0]]):
   data=melody();data['notes']=steps
   with self.assertRaises(PatchError):plan_boot_melody(data)
 @unittest.skipUnless((ROOT/'CastlevaniaAoS.gba').exists(),'private host absent')
 def test_compiled_phrasing_schedule(self):
  data=melody();data['notes']=[{'rest':48},dict(data['notes'][0],gate_ticks=6)];data['repeats']=2
  rom=load_image(ROOT/'CastlevaniaAoS.gba');report=install_boot_melody(rom,data)
  events=list(iter_events(rom.data,report['track']-rom.base))
  self.assertEqual([(t,e) for t,e in events if e[0]=='note'],[(48,('note',60,80,0,6)),(120,('note',60,80,0,6))])
  self.assertEqual(events[-1],(144,('end',)))
