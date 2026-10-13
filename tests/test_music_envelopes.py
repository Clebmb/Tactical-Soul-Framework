import copy,json,unittest
from pathlib import Path
from aria.music import plan_boot_melody,plan_envelope,install_boot_melody,DEFAULT_ENVELOPE
from aria.cli import load_image,apply_manifest
from aria.core import PatchError
ROOT=Path(__file__).resolve().parents[1]
def melody():return json.loads((ROOT/'examples/envelope-melody/mod.json').read_text())['boot_melody']
class EnvelopePlanTests(unittest.TestCase):
 def test_complete_schema_and_bounds(self):
  for value in (None,{},dict(DEFAULT_ENVELOPE,extra=1)):
   with self.assertRaises(PatchError):plan_envelope(value)
  for field,value in (('attack',0),('attack',256),('decay',-1),('sustain',256),('release',255),('attack',True)):
   with self.assertRaises(PatchError):plan_envelope(dict(DEFAULT_ENVELOPE,**{field:value}))
 def test_extremes_and_normalization(self):
  self.assertEqual(plan_envelope({'attack':'0xff','decay':0,'sustain':255,'release':0}),{'attack':255,'decay':0,'sustain':255,'release':0})
 def test_no_mutation_and_multitrack_inheritance(self):
  value=melody();value['tracks']=[{'notes':value.pop('notes')}]*2;before=copy.deepcopy(value)
  self.assertEqual(plan_boot_melody(value)['envelope'],value['envelope']);self.assertEqual(value,before)
@unittest.skipUnless((ROOT/'CastlevaniaAoS.gba').exists(),'private host absent')
class EnvelopeImageTests(unittest.TestCase):
 def test_default_bytes_unchanged(self):
  value=melody();del value['envelope'];a=load_image(ROOT/'CastlevaniaAoS.gba');b=load_image(ROOT/'CastlevaniaAoS.gba')
  install_boot_melody(a,value);value['envelope']=dict(DEFAULT_ENVELOPE);install_boot_melody(b,value)
  self.assertEqual(a.data,b.data);self.assertEqual(a.ledger,b.ledger)
 def test_bank_override_and_shared_default(self):
  value=json.loads((ROOT/'examples/instrument-melody/mod.json').read_text())['boot_melody'];value['envelope']=melody()['envelope'];value['instruments'][1]['envelope']=dict(DEFAULT_ENVELOPE,release=0)
  rom=load_image(ROOT/'CastlevaniaAoS.gba');r=install_boot_melody(rom,value,ROOT/'examples/instrument-melody')
  for index,expected in enumerate((value['envelope'],value['instruments'][1]['envelope'])):
   self.assertEqual(rom.read(r['voice']+12*index+8,4),bytes(expected[k] for k in DEFAULT_ENVELOPE));self.assertEqual(r['instrument_bank'][index]['envelope'],expected)
 def test_late_invalid_bank_envelope_preserves_caller(self):
  value=json.loads((ROOT/'examples/instrument-melody/mod.json').read_text())['boot_melody'];value['instruments'][1]['envelope']=dict(DEFAULT_ENVELOPE,release=255)
  rom=load_image(ROOT/'CastlevaniaAoS.gba');before=copy.deepcopy(rom.__dict__)
  with self.assertRaises(PatchError):install_boot_melody(rom,value,ROOT/'examples/instrument-melody')
  self.assertEqual(rom.__dict__,before)
 def test_project_matches_flat(self):
  a=load_image(ROOT/'CastlevaniaAoS.gba');b=load_image(ROOT/'CastlevaniaAoS.gba');apply_manifest(a,ROOT/'examples/envelope-melody/mod.json');apply_manifest(b,ROOT/'examples/envelope-melody/project.json')
  self.assertEqual(a.data,b.data);self.assertEqual(a.music_report,b.music_report)
