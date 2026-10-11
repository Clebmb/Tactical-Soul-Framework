"""Safety contracts tested on synthetic bytes, never on distributed ROM data."""
import hashlib,tempfile,unittest
from pathlib import Path
from aria.core import RomImage,PatchError

class PatchContracts(unittest.TestCase):
    def image(self):
        original=bytes(64)
        return RomImage(original,{"id":"synthetic","sha256":hashlib.sha256(original).hexdigest(),"size":64,"rom_base":0x08000000,"allocation_ranges":[{"start":0x08000020,"end":0x08000040}]})
    def test_wrong_rom_rejected(self):
        image=self.image()
        with self.assertRaises(PatchError):RomImage(bytes([1])*64,image.profile)
    def test_bad_preimage_does_not_mutate(self):
        image=self.image()
        with self.assertRaises(PatchError):image.write(0x08000000,b"A","wrong",b"B")
        self.assertEqual(image.read(0x08000000,1),b"\0")
    def test_overlap_is_rejected(self):
        image=self.image();image.write(0x08000000,b"AB","first")
        with self.assertRaises(PatchError):image.write(0x08000001,b"C","conflict")
    def test_allocation_skips_reserved_patch(self):
        image=self.image();image.write(0x08000020,b"12345","reserved")
        self.assertEqual(image.allocate("aligned",b"xyz",4),0x08000028)
    def test_allocation_exhaustion_and_duplicate_name(self):
        image=self.image();image.allocate("full",bytes(32))
        with self.assertRaises(PatchError):image.allocate("overflow",b"x")
        with self.assertRaises(PatchError):image.allocate("full",b"x")
    def test_bounds_and_alignment(self):
        image=self.image()
        with self.assertRaises(PatchError):image.write(0x07FFFFFF,b"x","bad")
        with self.assertRaises(PatchError):image.allocate("bad",b"x",3)
    def test_output_cannot_overwrite_input(self):
        path=Path(__file__).resolve().parents[1]/"local/framework-tests/original.bin"
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(bytes(64))
        image=self.image();image.write(0x08000000,b"A","change")
        with self.assertRaises(PatchError):image.output(path,path)
        self.assertEqual(path.read_bytes(),bytes(64))
    def test_original_bytes_remain_immutable(self):
        image=self.image();image.write(0x08000000,b"A","change")
        self.assertEqual(image.original,bytes(64))

if __name__=="__main__":unittest.main()
