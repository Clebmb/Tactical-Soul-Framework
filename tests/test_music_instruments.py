import copy,json,tempfile,unittest
from pathlib import Path
from aria.music import plan_boot_melody,install_boot_melody
from aria.cli import load_image,apply_manifest
from aria.audio import iter_events,decode_voice_entry
from aria.core import PatchError
from tests.test_music_samples import wav
ROOT=Path(__file__).resolve().parents[1]
def melody():return json.loads((ROOT/'examples/instrument-melody/mod.json').read_text())['boot_melody']
class InstrumentsTests(unittest.TestCase):
 def test_bank_and_selection_bounds(self):
  for bank in ([],[melody()['instruments'][0]]*9,{},None):
   data=melody();data['instruments']=bank
   with self.assertRaises(PatchError):plan_boot_melody(data)
  for index in (-1,2,True):
   data=melody();data['notes'][0]['instrument']=index
   with self.assertRaises(PatchError):plan_boot_melody(data)
 def test_exclusive_legacy_sample(self):
  data=melody();data['sample']=data['instruments'][0]
  with self.assertRaises(PatchError):plan_boot_melody(data)
 def test_plan_preserves_inputs(self):
  data=melody();before=copy.deepcopy(data);plan=plan_boot_melody(data)
  self.assertEqual(data,before);self.assertEqual(len(plan['instruments']),2)
@unittest.skipUnless((ROOT/'CastlevaniaAoS.gba').exists(),'private host absent')
class InstrumentImageTests(unittest.TestCase):
 def test_voice_linkage_and_repeated_selection(self):
  rom=load_image(ROOT/'CastlevaniaAoS.gba');r=install_boot_melody(rom,melody(),ROOT/'examples/instrument-melody')
  for index,sample in enumerate(r['instrument_bank']):
   self.assertEqual(decode_voice_entry(rom.data,r['voice']-rom.base+12*index)['sample'],sample['sample'])
  notes=[(t,e[4],e[3]) for t,e in iter_events(rom.data,r['track']-rom.base) if e[0]=='note']
  self.assertEqual(notes,[(i*48,24,v) for i,v in enumerate((0,1,0,0,1,0))])
 def test_project_matches_flat_and_fingerprints_all_assets(self):
  a=load_image(ROOT/'CastlevaniaAoS.gba');b=load_image(ROOT/'CastlevaniaAoS.gba')
  apply_manifest(a,ROOT/'examples/instrument-melody/mod.json');apply_manifest(b,ROOT/'examples/instrument-melody/project.json')
  self.assertEqual(a.data,b.data);self.assertEqual(a.music_report,b.music_report);self.assertEqual(len(b.project_report['assets']),2)
 def test_late_bad_sample_rolls_back(self):
  data=melody();data['instruments'][1]['loop_start']=100
  rom=load_image(ROOT/'CastlevaniaAoS.gba');before=copy.deepcopy(rom.__dict__)
  with self.assertRaises(PatchError):install_boot_melody(rom,data,ROOT/'examples/instrument-melody')
  self.assertEqual(rom.__dict__,before)
 def test_combined_pcm_budget_rolls_back(self):
  with tempfile.TemporaryDirectory(dir=ROOT/'local') as directory:
   folder=Path(directory);(folder/'large.wav').write_bytes(wav(bytes(32768)))
   data=melody();data['instruments']=[{'source':'large.wav','provenance':'Original test','loop_start':0}]*3
   rom=load_image(ROOT/'CastlevaniaAoS.gba');before=copy.deepcopy(rom.__dict__)
   with self.assertRaisesRegex(PatchError,'65536'):install_boot_melody(rom,data,folder)
   self.assertEqual(rom.__dict__,before)

 def test_omitted_selection_returns_to_instrument_zero(self):
  data=melody();data['notes'][0]['instrument']=1;del data['notes'][1]['instrument']
  rom=load_image(ROOT/'CastlevaniaAoS.gba');r=install_boot_melody(rom,data,ROOT/'examples/instrument-melody')
  voices=[e[3] for t,e in iter_events(rom.data,r['track']-rom.base) if e[0]=='note']
  self.assertEqual(voices,[1,0,0,1,0,0])
 def test_late_path_escape_rolls_back(self):
  data=melody();data['instruments'][1]['source']='../imported-melody/triangle.wav'
  rom=load_image(ROOT/'CastlevaniaAoS.gba');before=copy.deepcopy(rom.__dict__)
  with self.assertRaises(PatchError):install_boot_melody(rom,data,ROOT/'examples/instrument-melody')
  self.assertEqual(rom.__dict__,before)
