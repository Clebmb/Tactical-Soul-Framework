"""Renderer format/orientation contracts independent of copyrighted fixtures."""
import hashlib,struct,unittest,zlib
from pathlib import Path
from aria.core import RomImage,PatchError
from aria.rendering import minitile,transform,rgb555,png_rgba,read_graphics,read_palettes,render_layer,graphics_chunk_modes

class RenderingTests(unittest.TestCase):
    def image(self):
        raw=bytearray(8192);b=0x08000000
        struct.pack_into('<IBBBB',raw,0,b+256,2,0,1,0)
        raw[256:260]=bytes([0,4,0,4]);raw[260:2308]=bytes([0x21])*2048
        struct.pack_into('<IBBBB',raw,32,b+4096,3,1,1,0)
        raw[4096:4100]=bytes([0,0,2,0]);struct.pack_into('<16H',raw,4132,*range(16))
        return RomImage(raw,{'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'rom_base':b,'allocation_ranges':[]})
    def test_rgb555_and_transparency(self):
        self.assertEqual(rgb555(0x7FFF),bytes([255,255,255,255]))
        self.assertEqual(rgb555(31,True),bytes([255,0,0,0]))
    def test_nibble_order_palette_and_local_flip(self):
        chunks={0:bytes([0x21])+bytes(2047)};palettes={3:[0,31,0x3E0]+[0]*13}
        pixels=minitile(3<<12,0,chunks,palettes)
        self.assertEqual(pixels[:8],bytes([255,0,0,255,0,255,0,255]))
        self.assertEqual(pixels[11],0)
        self.assertEqual(minitile((3<<12)|0xC00,0,chunks,palettes),transform(pixels,8,8,True,True))
    def test_character_base_and_page_mapping(self):
        tile=minitile(0x140,2,{21:bytes([0x11])*2048},{0:[0,31]+[0]*14})
        self.assertEqual(tile,bytes([255,0,0,255])*64)
    def test_missing_resources_rejected(self):
        for chunks,palettes in [({},{}),({0:bytes(2048)},{}),({0:b''},{0:[0]*16})]:
            with self.assertRaises(PatchError):minitile(0,0,chunks,palettes)
    def test_whole_rectangle_flips(self):
        pixels=bytes([1,0,0,255,2,0,0,255,3,0,0,255,4,0,0,255])
        self.assertEqual(transform(pixels,2,2,True,True)[::4],bytes([4,3,2,1]))
        with self.assertRaises(PatchError):transform(b'',2,2)
    def test_raw_graphics_chunks(self):
        chunks,records=read_graphics(self.image(),0x08000000)
        self.assertEqual(chunks,{2:bytes([0x21])*2048});self.assertFalse(records[0]['compressed'])
    def test_raw_and_compressed_8bpp_preserve_physical_chunks(self):
        from aria.content import lz77
        for compressed in (False,True):
            r=self.image();r.data[257]=8
            payload=bytes([0x21])*2048
            if compressed:
                r.data[256]=1;struct.pack_into('<I',r.data,260,r.base+512)
                stream=lz77(((len(payload)+4)<<8).to_bytes(4,'little')+payload)
                r.data[512:512+len(stream)]=stream
            chunks,records=read_graphics(r,r.base)
            self.assertEqual(chunks,{2:payload});self.assertEqual(records[0]['bpp'],8)
            self.assertEqual(graphics_chunk_modes(records),{2:8})
    def test_ordered_mode_overwrite_and_render_guard(self):
        records=[{'target_chunk':0,'chunk_count':2,'bpp':8},
                 {'target_chunk':1,'chunk_count':1,'bpp':4}]
        modes=graphics_chunk_modes(records);self.assertEqual(modes,{0:8,1:4})
        chunks={0:bytes(2048),1:bytes(2048)};banks={0:[0]*16}
        with self.assertRaisesRegex(PatchError,'not compatible 4bpp'):minitile(0,0,chunks,banks,modes)
        self.assertEqual(len(minitile(64,0,chunks,banks,modes)),256)
    def test_palette_source_and_destination_offsets(self):
        banks,records=read_palettes(self.image(),0x08000020)
        self.assertEqual(banks,{3:list(range(16))});self.assertEqual(records[0]['first_bank'],1)
    def test_invalid_wrappers_and_inheritance(self):
        for offset,value,reader,pointer in [(257,16,read_graphics,0),(6,5,read_graphics,0),(5,4,read_graphics,0),(36,16,read_palettes,32),(4096,1,read_palettes,32)]:
            r=self.image();r.data[offset]=value
            with self.assertRaises(PatchError):reader(r,r.base+pointer)
        r=self.image()
        with self.assertRaises(PatchError):read_graphics(r,r.base+64)
        with self.assertRaises(PatchError):read_palettes(r,r.base+64)
    def test_png_crc_and_roundtrip(self):
        pixels=bytes([255,0,0,255])*4;png=png_rgba(2,2,pixels);offset=8;payload=b''
        self.assertEqual(png[:8],b'\x89PNG\r\n\x1a\n')
        while offset<len(png):
            size=struct.unpack('>I',png[offset:offset+4])[0];kind=png[offset+4:offset+8];data=png[offset+8:offset+8+size]
            self.assertEqual(struct.unpack('>I',png[offset+8+size:offset+12+size])[0],zlib.crc32(kind+data)&0xFFFFFFFF)
            if kind==b'IDAT':payload+=data
            offset+=12+size
        self.assertEqual(zlib.decompress(payload),b'\0'+pixels[:8]+b'\0'+pixels[8:])
        with self.assertRaises(PatchError):png_rgba(0,2,b'')

class PrivateRenderingTests(unittest.TestCase):
    def test_native_room_and_isolated_step_pixels(self):
        root=Path(__file__).resolve().parents[1];host=root/'CastlevaniaAoS.gba'
        if not host.exists():self.skipTest('Private original not present')
        from aria.cli import load_image,apply_manifest
        r=load_image(host);original=bytes(r.data);before=render_layer(r,0,3)
        self.assertEqual(bytes(r.data),original);self.assertFalse(r.ledger)
        apply_manifest(r,root/'examples/geometry-workshop/mod.json');after=render_layer(r,0,3)
        self.assertEqual((before['width'],before['height']),(1280,256))
        different=[]
        for n in range(1280*256):
            if before['rgba'][n*4:n*4+4]!=after['rgba'][n*4:n*4+4]:different.append((n%1280,n//1280))
        self.assertTrue(different)
        self.assertTrue(all(320<=x<352 and 160<=y<192 for x,y in different))
