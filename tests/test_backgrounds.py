import copy,hashlib,struct,unittest
from pathlib import Path
from unittest.mock import patch
from aria.core import RomImage,PatchError
from aria.content import lz77
from aria.backgrounds import inspect_background,verify_background_roundtrip,expand_background_map,minitile_8bpp

class BackgroundTests(unittest.TestCase):
    def test_8bpp_character_stride_palette_and_transparency(self):
        chunks={8:bytes(2048),9:bytes([17,0])+bytes([18])*2046}
        banks={1:[0,31,0x3E0]+[0]*13};modes={8:8,9:8}
        pixels=minitile_8bpp(32,1,chunks,banks,modes)
        self.assertEqual(pixels[:12],bytes([255,0,0,255,0,0,0,0,0,255,0,255]))
        self.assertEqual(minitile_8bpp(33,1,chunks,banks,modes),bytes([0,255,0,255])*64)
    def test_8bpp_missing_or_wrong_resources(self):
        for chunks,banks,modes in [({}, {}, {}),({0:bytes(2048)}, {}, {0:4}),({0:b''},{},{0:8}),({0:bytes([17])*2048},{},{0:8})]:
            with self.assertRaises(PatchError):minitile_8bpp(0,0,chunks,banks,modes)
    def test_expanded_map_and_unverified_flags(self):
        r=self.image(3)
        with self.assertRaisesRegex(PatchError,'native flip'):expand_background_map(self.inspect(r))
        struct.pack_into('<H',r.data,176,1)
        width,height,data=expand_background_map(self.inspect(r))
        self.assertEqual((width,height),(32,32))
        self.assertEqual(data[:4],bytes(range(4)));self.assertEqual(data[32:36],bytes(range(4,8)))
        self.assertEqual(data[4:32],bytes(28))
    def image(self,kind):
        raw=bytearray(8192);b=0x08000000
        struct.pack_into('<HH8I',raw,32,0,0,0,b+96,0,0,0,0,0,0)
        struct.pack_into('<BBHHHI',raw,108,1,0,0x7EC0,256,256,b+144)
        struct.pack_into('<BBHIII',raw,144,1,1,kind,b+512,0,b+176)
        data=bytes(range(256))*16 if kind==1 else bytes(range(16))
        source=data if kind==1 else lz77(((len(data)+4)<<8).to_bytes(4,'little')+data)
        raw[512:512+len(source)]=source;struct.pack_into('<H',raw,176,0xC001)
        return RomImage(raw,{'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'rom_base':b,'allocation_ranges':[]})
    def inspect(self,r):
        with patch('aria.backgrounds.room_address',return_value=r.base+32):return inspect_background(r,0,0,1,True)
    def test_raw_and_compressed_lossless_nonmutation(self):
        for kind,count in [(1,257),(3,2)]:
            r=self.image(kind);before=bytes(r.data);bundle=self.inspect(r)
            rebuilt=verify_background_roundtrip(bundle)
            self.assertEqual(bundle['metatiles_including_blank'],count)
            self.assertEqual(bundle['referenced_metatile_ids'],[0,1])
            self.assertEqual(bytes.fromhex(rebuilt['layout_hex']),r.read(r.base+176,128))
            source=bytes.fromhex(rebuilt['visual_source_hex'])
            self.assertEqual(source,r.read(r.base+512,len(source)))
            self.assertEqual(bytes(r.data),before);self.assertFalse(r.ledger)
    def test_invalid_dimensions_format_reference_and_payload(self):
        for address,data in [(144,b'\0'),(146,b'\2\0'),(176,b'\xff\x3f'),(512,b'\x11')]:
            r=self.image(3);r.data[address:address+len(data)]=data
            with self.assertRaises(PatchError):self.inspect(r)
    def test_export_tampering(self):
        baseline=self.inspect(self.image(3))
        for field,value in [('layout_sha256','0'*64),('visual_sha256','0'*64),('metatiles_including_blank',3),('layer_metadata_hex','00'*16)]:
            b=copy.deepcopy(baseline);b[field]=value
            with self.assertRaises(PatchError):verify_background_roundtrip(b)

class PrivateBackgroundTests(unittest.TestCase):
    def test_static_8bpp_source_raster_nonmutation(self):
        root=Path(__file__).resolve().parents[1]
        if not (root/'CastlevaniaAoS.gba').exists():self.skipTest('Private host absent')
        from aria.cli import load_image
        from aria.backgrounds import render_background
        r=load_image(root/'CastlevaniaAoS.gba');before=bytes(r.data)
        p=render_background(r,4,0,1)
        self.assertEqual((p['width'],p['height']),(256,256))
        self.assertEqual(p['report']['rgba_sha256'],'bb6391f2a63b8aea7e46634e330feea74d2dd5369cec1a9ec09ea8b20f82e259')
        self.assertEqual(bytes(r.data),before);self.assertFalse(r.ledger)
    def test_all_base_state_byte_index_layers(self):
        root=Path(__file__).resolve().parents[1]
        if not (root/'CastlevaniaAoS.gba').exists():self.skipTest('Private host absent')
        from aria.cli import load_image
        from aria.rooms import sector_span,room_address,metadata
        r=load_image(root/'CastlevaniaAoS.gba');before=bytes(r.data);counts={1:0,3:0}
        for s in range(12):
            _,count=sector_span(r,s)
            for i in range(count):
                listing=metadata(r,room_address(r,s,i))[3]
                for layer in range(3):
                    address=r.integer(listing+layer*12+8)
                    if not address:continue
                    kind=r.integer(address+2,2)
                    if kind not in counts:continue
                    b=inspect_background(r,s,i,layer,True);v=verify_background_roundtrip(b)
                    source=bytes.fromhex(v['visual_source_hex'])
                    self.assertEqual(source,r.read(b['visual_tileset_address'],len(source)))
                    counts[kind]+=1
        self.assertEqual(counts,{1:11,3:13})
        self.assertEqual(bytes(r.data),before);self.assertFalse(r.ledger);self.assertFalse(r.allocations)
