import unittest,tempfile,json,hashlib,wave
from pathlib import Path
from aria.content import palette,tiles,lz77,encode,install_content
from aria.core import RomImage,PatchError
TMP=Path(__file__).resolve().parents[1]/"local/content-tests"
TMP.mkdir(parents=True,exist_ok=True)
class ContentTests(unittest.TestCase):
 def test_palette(self):self.assertEqual(palette([[255,0,0],[0,255,0],[0,0,255]]),bytes.fromhex('1f00e003007c'))
 def test_palette_bad(self):
  for c in [[],[[256,0,0]],[[True,0,0]],[[0,0]]]:
   with self.assertRaises((PatchError,ValueError)):palette(c)
 def test_tiles_order(self):
  p=[x%16 for y in range(8) for x in range(16)];self.assertEqual(tiles({'width':16,'height':8,'pixels':p}),bytes.fromhex('10325476')*8+bytes.fromhex('98badcfe')*8)
 def test_tiles_invalid(self):
  for s in [{'width':9,'height':8,'pixels':[0]*72},{'width':8,'height':8,'pixels':[16]*64},{'width':8,'height':8,'pixels':[]}]:
   with self.assertRaises(PatchError):tiles(s)
 def test_lz_literals(self):
  data=bytes(range(19));b=lz77(data);self.assertEqual(b[:4],bytes.fromhex('10130000'));self.assertEqual(b[4],0);self.assertEqual(b[5:13],data[:8]);self.assertEqual(len(b)%4,0)
 def test_pcm(self):
  with tempfile.TemporaryDirectory(dir=TMP) as d:
   p=Path(d)/'a.wav'
   with wave.open(str(p),'wb') as w:w.setparams((1,1,8192,0,'NONE','not compressed'));w.writeframes(bytes([0,128,255]))
   self.assertEqual(encode('pcm_s8',p),bytes([128,0,127]))
 def test_install_and_guards(self):
  raw=bytes(512);profile={'size':512,'sha256':hashlib.sha256(raw).hexdigest(),'rom_base':0x8000000,'allocation_ranges':[{'start':0x8000100,'end':0x8000200}]}
  with tempfile.TemporaryDirectory(dir=TMP) as d:
   folder=Path(d);(folder/'p.json').write_text('[[255,0,0]]');a={'id':'test','format':'palette_rgb8','source':'p.json','provenance':'original','replace':{'address':0x8000000,'size':2,'expected_sha256':hashlib.sha256(bytes(2)).hexdigest()}}
   rom=RomImage(raw,profile);install_content(rom,[a],folder);self.assertEqual(rom.read(0x8000000,2),b'\x1f\x00')
   with self.assertRaises(PatchError):install_content(rom,[a],folder)
   a['source']='../p.json'
   with self.assertRaises(PatchError):install_content(RomImage(raw,profile),[a],folder)
 def test_pointer_binding(self):
  raw=bytes(512);profile={'size':512,'sha256':hashlib.sha256(raw).hexdigest(),'rom_base':0x8000000,'allocation_ranges':[{'start':0x8000100,'end':0x8000200}]}
  with tempfile.TemporaryDirectory(dir=TMP) as d:
   folder=Path(d);(folder/'p.json').write_text('[[255,0,0]]');a={'id':'test','format':'palette_rgb8','source':'p.json','provenance':'original','pointers':[{'address':0x8000000,'expected':0}]};rom=RomImage(raw,profile);r=install_content(rom,[a],folder);self.assertEqual(rom.integer(0x8000000),r[0]['address'])
   with self.assertRaises(PatchError):install_content(RomImage(raw,profile),[a,a],folder)

 def test_pcm_rejects_stereo(self):
  with tempfile.TemporaryDirectory(dir=TMP) as d:
   p=Path(d)/'bad.wav'
   with wave.open(str(p),'wb') as w:w.setparams((2,1,8192,0,'NONE','not compressed'));w.writeframes(bytes(8))
   with self.assertRaises(PatchError):encode('pcm_s8',p)
 def test_lz_roundtrip(self):
  data=bytes(range(256))*3;b=lz77(data);size=int.from_bytes(b[1:4],'little');i=4;decoded=bytearray()
  while len(decoded)<size:
   flags=b[i];i+=1
   for bit in range(7,-1,-1):
    if len(decoded)==size:break
    self.assertEqual(flags&(1<<bit),0);decoded.append(b[i]);i+=1
  self.assertEqual(bytes(decoded),data)
