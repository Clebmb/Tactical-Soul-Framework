import copy,hashlib,struct,unittest
from unittest.mock import patch
from aria.core import RomImage,PatchError
from aria.content import lz77
from aria.compression import decode_lz10,read_aria,rebuild_aria
from aria.geometry import inspect_geometry,verify_roundtrip,apply_geometry_edits

class CompressionTests(unittest.TestCase):
 def test_backreference(self):
  data,n=decode_lz10(bytes.fromhex('10090000106162633002'));self.assertEqual(data,b'abcabcabc');self.assertEqual(n,10)
 def test_overlapping_reference(self):self.assertEqual(decode_lz10(bytes.fromhex('1006000040412000'))[0],b'AAAAAA')
 def test_literal_roundtrip(self):
  data=bytes(range(256))*5;self.assertEqual(decode_lz10(lz77(data))[0],data)
 def test_invalid_streams(self):
  for raw in [b'',bytes.fromhex('110100000000'),bytes.fromhex('10000000'),bytes.fromhex('10010000'),bytes.fromhex('10030000800000'),bytes.fromhex('1002000040410000')]:
   with self.assertRaises(PatchError):decode_lz10(raw)
 def test_size_bound(self):
  with self.assertRaises(PatchError):decode_lz10(lz77(bytes(32)),max_output=16)

class GeometryTests(unittest.TestCase):
 def setUp(self):
  self.room_patch=patch('aria.geometry.room_address',return_value=0x08000020);self.room_patch.start();self.addCleanup(self.room_patch.stop)
 def image(self):
  raw=bytearray(4096);base=0x08000000
  struct.pack_into('<HH8I',raw,32,0,0,0,base+96,0,0,0,0,0,0)
  struct.pack_into('<BBHHHI',raw,96,22,1,7496,256,256,base+144)
  struct.pack_into('<BBHIII',raw,144,1,1,2,base+512,base+768,base+176)
  for address,payload in [(512,bytes(range(32))),(768,bytes([3])*16)]:
   block=lz77(struct.pack('<I',(len(payload)+4)<<8)+payload);raw[address:address+len(block)]=block
  profile={'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'rom_base':base,'allocation_ranges':[{'start':base+2048,'end':base+4096}],'geometry_edit_rooms':[[0,3]]}
  return RomImage(raw,profile)
 def edit(self,r):
  b=inspect_geometry(r,0,3)
  return {'room':{'sector':0,'room':3},'layer':0,'expected_layout_sha256':b['layout_sha256'],'cells':[{'x':3,'y':4,'expect':0,'value':1}]}
 def test_read_and_lossless_rebuild(self):
  r=self.image();b=inspect_geometry(r,0,3,full=True);v=verify_roundtrip(b)
  self.assertEqual(bytes.fromhex(v['layout_hex']),r.read(0x080000B0,128));self.assertEqual(b['metatiles_including_blank'],2)
 def test_inner_header_preserved_and_recompression(self):
  r=self.image();resource=read_aria(r,0x08000200)
  self.assertEqual(bytes.fromhex(resource['inner_header_hex'])[0],0)
  self.assertEqual(decode_lz10(rebuild_aria(resource,preserve=False))[0][4:],bytes(range(32)))
  resource['data_hex']='ff'+resource['data_hex'][2:]
  with self.assertRaises(PatchError):rebuild_aria(resource,preserve=True)
 def test_isolated_copy_and_pointer_chain(self):
  r=self.image();before=inspect_geometry(r,0,3,full=True);apply_geometry_edits(r,[self.edit(r)]);after=inspect_geometry(r,0,3,full=True)
  self.assertEqual(after['cells'][35],1);self.assertEqual(sum(a!=b for a,b in zip(before['cells'],after['cells'])),1)
  self.assertNotEqual(before['layout_address'],after['layout_address']);self.assertNotEqual(before['layer_list_address'],after['layer_list_address'])
  for address,size in [(96,36),(144,16),(176,128),(512,64),(768,64)]:self.assertEqual(r.read(0x08000000+address,size),r.original[address:address+size])
 def test_rejections_before_writes(self):
  for key in ['hash','room','layer','duplicate','coordinate','metatile','expected','noop','boolean','extra']:
   r=self.image();e=self.edit(r)
   if key=='hash':e['expected_layout_sha256']='0'*64
   elif key=='room':e['room']['room']=6
   elif key=='layer':e['layer']=1
   elif key=='duplicate':e['cells']*=2
   elif key=='coordinate':e['cells'][0]['x']=8
   elif key=='metatile':e['cells'][0]['value']=2
   elif key=='expected':e['cells'][0]['expect']=1
   elif key=='noop':e['cells'][0]['value']=0
   elif key=='boolean':e['cells'][0]['x']=True
   else:e['unsupported']=True
   with self.assertRaises(PatchError):apply_geometry_edits(r,[e])
   self.assertEqual(r.data,r.original)
 def test_invalid_geometry_records(self):
  for address,payload in [(144,b'\x10'),(146,b'\x01\x00'),(176,b'\xff\x3f')]:
   r=self.image();r.data[address:address+len(payload)]=payload
   with self.assertRaises(PatchError):inspect_geometry(r,0,3)
 def test_export_metadata_drift(self):
  b=inspect_geometry(self.image(),0,3,full=True);b['bg_control']=0
  with self.assertRaises(PatchError):verify_roundtrip(b)
 def test_real_room_roundtrips(self):
  self.room_patch.stop()
  from aria.cli import load_image,ROOT
  host=ROOT/'CastlevaniaAoS.gba'
  if not host.exists():self.skipTest('private exact host absent')
  r=load_image(host)
  for room in [0,3,6,31]:
   for layer in range(3):
    b=inspect_geometry(r,0,room,layer,full=True);verify_roundtrip(b)
