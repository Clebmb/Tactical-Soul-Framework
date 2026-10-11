"""Synthetic format boundaries; no commercial ROM needed."""
import struct
import unittest
from pathlib import Path
from aria.core import PatchError
from aria.sprites import inspect_sprite, SPRITES

class Memory:
    def __init__(self):
        self.data=bytearray(2048)
        self.put(16,'<HHIII',1,3,64,256,128)
        self.put(64,'<IBBHII',123,1,1,456,192,208)
        self.put(192,'<bbBB',-2,-3,8,9)
        self.put(208,'<bbH8B',-4,5,789,0,0,8,8,0,0,3,99)
        self.put(128,'<III',256,256,0)
        self.put(256,'<HHBBH',1,1,0,7,999)
    def put(self,address,fmt,*values):struct.pack_into(fmt,self.data,address,*values)
    def read(self,address,size):
        if address<0 or address+size>len(self.data):raise PatchError('Out of bounds')
        return bytes(self.data[address:address+size])

class SpriteTests(unittest.TestCase):
    def test_lossless_unknowns_alias_and_null(self):
        rom=Memory();before=bytes(rom.data);result=inspect_sprite(rom,16)
        self.assertEqual(bytes(rom.data),before)
        self.assertEqual(result['frames'][0]['parts'][0]['unknown16'],789)
        self.assertEqual(result['frames'][0]['hitboxes'],[[-2,-3,8,9]])
        self.assertEqual(result['animations'][1]['alias_of'],0)
        self.assertEqual(result['animations'][2]['status'],'null')
        self.assertEqual(result['animations'][0]['steps'],[[0,7,999]])
    def test_unknown_animation_is_local_diagnostic(self):
        rom=Memory();rom.put(256,'<HH',65535,0)
        result=inspect_sprite(rom,16)
        self.assertEqual(result['animations'][0]['status'],'unsupported_function')
        self.assertEqual(len(result['frames']),1)
    def test_missing_frame_rejected(self):
        rom=Memory();rom.put(260,'<BBH',1,7,0)
        with self.assertRaisesRegex(PatchError,'missing frame'):inspect_sprite(rom,16)
    def test_count_pointer_and_alignment_guards(self):
        for offset,fmt,value in [(16,'<H',1025),(20,'<I',2048),(20,'<I',65)]:
            rom=Memory();rom.put(offset,fmt,value)
            with self.assertRaises(PatchError):inspect_sprite(rom,16)
    def test_inline_hitbox_step_formats(self):
        for function,fmt,values in [(2,'<HHbbBB',(0,9,-1,-2,3,4)),(3,'<HHbbBBbbBB',(0,9,-1,-2,3,4,-5,-6,7,8))]:
            rom=Memory();rom.put(256,'<HH',1,function);rom.put(260,fmt,*values)
            self.assertEqual(inspect_sprite(rom,16)['animations'][0]['steps'],[list(values)])
    def test_part_budget(self):
        rom=Memory();rom.put(69,'<B',129)
        with self.assertRaisesRegex(PatchError,'part/hitbox'):inspect_sprite(rom,16)

class NativeSpriteTests(unittest.TestCase):
    @unittest.skipUnless((Path(__file__).resolve().parents[1]/'CastlevaniaAoS.gba').exists(),'Private host unavailable')
    def test_registered_host_resources(self):
        from aria.cli import load_image
        rom=load_image(Path(__file__).resolve().parents[1]/'CastlevaniaAoS.gba')
        before=bytes(rom.data)
        for name,counts in [('common',(126,23)),('julius',(75,31)),('background-bats',(15,4))]:
            result=inspect_sprite(rom,SPRITES[name])
            self.assertEqual((result['frame_count'],result['animation_count']),counts)
            self.assertEqual(result['diagnostics'],[])
        self.assertEqual(bytes(rom.data),before);self.assertEqual(rom.ledger,[])

if __name__=='__main__':unittest.main()
