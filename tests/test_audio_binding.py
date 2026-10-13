import struct,unittest
from aria.audio_binding import match_song_headers
class BindingTests(unittest.TestCase):
 def test_aliases_and_locations(self):
  data=struct.pack('<III',0,0x08000100,0x08000100)
  result=match_song_headers(data,0x03000000,[('a',0x08000100),('b',0x08000100)])
  self.assertEqual([x['identity'] for x in result],['a','b','a','b']);self.assertEqual(result[-1]['memory_address'],0x03000008)
 def test_no_match_and_empty(self):
  self.assertEqual(match_song_headers(bytes(4),0,[('a',0x08000100)]),())
  self.assertEqual(match_song_headers(b'',0,[]),())
 def test_memory_bounds(self):
  for data,base in ((bytearray(4),0),(bytes(3),0),(bytes(4),True),(bytes(4),1),(bytes(8),0xfffffffc),(bytes(0x100004),0)):
   with self.assertRaises(ValueError):match_song_headers(data,base,[])
 def test_catalog_bounds(self):
  for cat in ([('a',True)],[('',4)],[('a',3)],[('a',0)],[('a',4)]*4097,[('a',)]):
   with self.assertRaises(ValueError):match_song_headers(b'',0,cat)
 def test_match_output_budget(self):
  with self.assertRaisesRegex(ValueError,'match budget'):
   match_song_headers(struct.pack('<I',4)*5,0,[('alias',4)]*4096)
