import copy,hashlib,io,unittest,wave
from pathlib import Path
from aria.content import decode_pcm_wav
from aria.music import plan_boot_melody,install_boot_melody
from aria.cli import load_image
from aria.core import PatchError
from aria.audio import decode_sample
ROOT=Path(__file__).resolve().parents[1]
def wav(data=b'\x00\x80\xff',channels=1,width=1,rate=8000):
 out=io.BytesIO()
 with wave.open(out,'wb') as w:w.setnchannels(channels);w.setsampwidth(width);w.setframerate(rate);w.writeframes(data)
 return out.getvalue()
def melody():return {'tempo':75,'volume':64,'notes':[{'key':60,'velocity':80,'ticks':24}],'sample':{'source':'triangle.wav','loop_start':0,'provenance':'Original test'}}
class SampleTests(unittest.TestCase):
 def test_pcm_conversion_and_fingerprint(self):
  source=wav();result=decode_pcm_wav(source)
  self.assertEqual(result['pcm'],bytes([128,0,127]));self.assertEqual(result['sample_rate'],8000);self.assertEqual(result['source_sha256'],hashlib.sha256(source).hexdigest())
 def test_formats_and_rates(self):
  for source in (wav(bytes(4),channels=2),wav(bytes(4),width=2),wav(rate=3999),wav(rate=32769)):
   with self.assertRaises(PatchError):decode_pcm_wav(source)
 def test_malformed_truncated_and_source_budget(self):
  for source in (b'invalid',wav()[:-1],bytes(131073),bytearray(wav())):
   with self.assertRaises(PatchError):decode_pcm_wav(source)
 def test_sample_count_budget(self):
  for source in (wav(b''),wav(bytes(32769))):
   with self.assertRaises(PatchError):decode_pcm_wav(source)
 def test_sample_schema(self):
  for field,value in (('provenance',''),('loop_start',True),('loop_start',-1),('source','')):
   data=melody();data['sample'][field]=value
   with self.assertRaises(PatchError):plan_boot_melody(data)
 def test_explicit_loop_policy(self):
  data=melody();del data['sample']['loop_start']
  with self.assertRaises(PatchError):plan_boot_melody(data)
  data=melody();data['sample']['loop_start']=None
  self.assertIsNone(plan_boot_melody(data)['sample_source']['loop_start'])
@unittest.skipUnless((ROOT/'CastlevaniaAoS.gba').exists(),'private host absent')
class NativeSampleTests(unittest.TestCase):
 def test_linked_import_payload_and_loop_modes(self):
  folder=ROOT/'examples/imported-melody';decoded=decode_pcm_wav((folder/'triangle.wav').read_bytes())
  for loop in (0,None):
   rom=load_image(ROOT/'CastlevaniaAoS.gba');data=melody();data['sample']['loop_start']=loop;report=install_boot_melody(rom,data,folder)
   sample=decode_sample(rom.data,report['sample']-rom.base)
   self.assertEqual(sample['freq'],8000*1024);self.assertEqual(sample['status'],0x4000 if loop==0 else 0)
   self.assertEqual(bytes(rom.data[sample['data_offset']:sample['data_end']]),decoded['pcm'])
 def test_loop_bounds_preserve_caller(self):
  rom=load_image(ROOT/'CastlevaniaAoS.gba');before=copy.deepcopy(rom.__dict__);data=melody();data['sample']['loop_start']=40
  with self.assertRaisesRegex(PatchError,'loop must index'):install_boot_melody(rom,data,ROOT/'examples/imported-melody')
  self.assertEqual(rom.__dict__,before)
 def test_source_escape_preserves_caller(self):
  rom=load_image(ROOT/'CastlevaniaAoS.gba');before=copy.deepcopy(rom.__dict__);data=melody();data['sample']['source']='../README.md'
  with self.assertRaisesRegex(PatchError,'escapes'):install_boot_melody(rom,data,ROOT/'examples/imported-melody')
  self.assertEqual(rom.__dict__,before)
