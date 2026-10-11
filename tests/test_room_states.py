import hashlib,struct,unittest
from unittest.mock import patch
from aria.core import RomImage,PatchError
from aria.room_states import inspect_room_states

class RoomStateTests(unittest.TestCase):
    def image(self):
        raw=bytearray(512);b=0x08000000
        for address,next_state in [(32,b+96),(96,0)]:
            struct.pack_into('<HH8I',raw,address,0,7,next_state,b+160,0,0,0,0,0,0)
        return RomImage(raw,{'id':'test','size':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'rom_base':b,'allocation_ranges':[]})
    def inspect(self,r,**kw):
        with patch('aria.room_states.room_address',return_value=r.base+32):return inspect_room_states(r,0,0,**kw)
    def test_chain_identity_and_explicit_inheritance(self):
        r=self.image();before=bytes(r.data);a=self.inspect(r)
        self.assertTrue(a['chain_complete']);self.assertEqual(len(a['states']),2)
        self.assertEqual(a['states'][1]['id'],'test:s00:r000:alternate:01')
        self.assertEqual(a['states'][0]['loads']['graphics']['status'],'inherited_or_empty')
        self.assertFalse(a['states'][1]['write_registered']);self.assertEqual(bytes(r.data),before);self.assertFalse(r.ledger)
    def test_cycle_and_limit(self):
        r=self.image();struct.pack_into('<I',r.data,100,r.base+32)
        a=self.inspect(r);self.assertEqual(a['diagnostics'][0]['code'],'state_cycle');self.assertEqual(len(a['states']),2)
        a=self.inspect(r,max_states=1);self.assertEqual(a['diagnostics'][0]['code'],'state_limit')
    def test_invalid_pointer_and_independent_load_failure(self):
        r=self.image();struct.pack_into('<I',r.data,36,0xDEADBEEF)
        a=self.inspect(r);self.assertFalse(a['chain_complete']);self.assertEqual(len(a['states']),1)
        struct.pack_into('<I',r.data,44,0xDEADBEEF)
        a=self.inspect(r);self.assertEqual(a['states'][0]['loads']['graphics']['status'],'unavailable')
        self.assertEqual(a['states'][0]['loads']['palettes']['status'],'inherited_or_empty')
    def test_invalid_bound(self):
        for value in (0,65,True):
            with self.assertRaises(PatchError):self.inspect(self.image(),max_states=value)
