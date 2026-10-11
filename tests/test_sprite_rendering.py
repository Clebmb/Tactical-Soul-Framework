"""Pixel-level tests for static sprite composition, formats and output guards."""
import contextlib
import io
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
from aria.core import PatchError
from aria.sprite_rendering import read_sprite_page, resolve_sprite_resources, render_sprite_frame, preview_sprite
from aria.sprites import SPRITES, inspect_sprite
from aria.rendering import rgb555

ROOT=Path(__file__).resolve().parents[1]

class Memory:
    def __init__(self):self.data=bytearray(20000)
    def read(self,address,size):
        if address<0 or address+size>len(self.data):raise PatchError('Out of bounds')
        return bytes(self.data[address:address+size])
    def integer(self,address):return int.from_bytes(self.read(address,4),'little')
    def offset(self,address,size=1):self.read(address,size);return address

def part(**fields):
    result=dict(x=-2,y=-3,width=8,height=8,object_dimensions=[8,8],gfx_page=0,gfx_x=0,gfx_y=0,flip_bits=0)
    result.update(fields);return result

def resources():return dict(pages=[bytes(512)],palette=[0,31,31<<5,31<<10]+[0]*12)

def pixel(image,x,y):
    pos=(y*image['width']+x)*4;return image['pixels'][pos:pos+4]

class SpriteRenderingTests(unittest.TestCase):
    def test_raw_page_dimensions_and_provenance(self):
        rom=Memory();rom.data[16:20]=bytes([0,4,99,1])
        data,record=read_sprite_page(rom,16)
        self.assertEqual(len(data),512);self.assertEqual(record['height'],8)
        self.assertEqual(record['data_address'],20);self.assertEqual(record['reserved'],99)

    def test_compressed_page_uses_validated_inner_header(self):
        from aria.content import lz77
        rom=Memory();rom.data[16:20]=bytes([1,4,16,1]);struct.pack_into('<I',rom.data,20,64)
        payload=bytes([0x21])*512
        expanded=((len(payload)+4)<<8).to_bytes(4,'little')+payload
        compressed=lz77(expanded);rom.data[64:64+len(compressed)]=compressed
        data,record=read_sprite_page(rom,16)
        self.assertEqual(data,payload);self.assertEqual(record['encoding'],'aria-lz10')

    def test_invalid_wrapper_and_page_bounds(self):
        for header in ([0,8,0,1],[2,4,0,1],[0,4,0,0],[0,4,0,17]):
            rom=Memory();rom.data[16:20]=bytes(header)
            with self.assertRaises(PatchError):read_sprite_page(rom,16)
        with self.assertRaisesRegex(PatchError,'Unaligned'):read_sprite_page(Memory(),17)

    def test_palette_header_bank_and_bounds(self):
        rom=Memory();rom.data[32:36]=bytes([0,4,1,0])
        rom.data[64:68]=bytes([0,4,0,1])
        registration={'test':dict(pages=[64],palette=32,bank=0)}
        with patch('aria.sprite_rendering.SPRITE_RESOURCES',registration):
            self.assertEqual(len(resolve_sprite_resources(rom,'test')['palette']),16)
            for bank in (-1,1,True):
                with self.assertRaisesRegex(PatchError,'bank'):resolve_sprite_resources(rom,'test',bank)
            rom.data[33]=8
            with self.assertRaisesRegex(PatchError,'header'):resolve_sprite_resources(rom,'test')

    def test_tile_rows_nibbles_transparency_origin(self):
        r=resources();page=bytearray(512);page[0]=0x21;page[4]=3;r['pages']=[bytes(page)]
        image=render_sprite_frame({'parts':[part()]},r)
        self.assertEqual(image['origin'],[-2,-3]);self.assertEqual((image['width'],image['height']),(8,8))
        self.assertEqual(pixel(image,0,0),rgb555(31));self.assertEqual(pixel(image,1,0),rgb555(31<<5))
        self.assertEqual(pixel(image,0,1),rgb555(31<<10));self.assertEqual(pixel(image,2,0),bytes(4))

    def test_whole_part_flips(self):
        r=resources();page=bytearray(512);page[0]=1;r['pages']=[bytes(page)]
        for flags,x,y in [(0,0,0),(1,0,7),(2,7,0),(3,7,7)]:
            image=render_sprite_frame({'parts':[part(flip_bits=flags)]},r)
            self.assertEqual(pixel(image,x,y),rgb555(31))
            self.assertEqual(sum(image['pixels'][3::4]),255)

    def test_cross_tile_addressing_not_linear_scanlines(self):
        r=resources();page=bytearray(1024)
        page[0]=1;page[32]=2;page[512]=3;page[544]=1
        r['pages']=[bytes(page)]
        image=render_sprite_frame({'parts':[part(width=16,height=16,object_dimensions=[16,16])]},r)
        for x,y,color in [(0,0,31),(8,0,31<<5),(0,8,31<<10),(8,8,31)]:
            self.assertEqual(pixel(image,x,y),rgb555(color))
        self.assertEqual(pixel(image,0,1),bytes(4))

    def test_reverse_order_and_transparent_overlay(self):
        r=resources();page=bytearray(512);page[0]=1;page[32]=0x22;r['pages']=[bytes(page)]
        image=render_sprite_frame({'parts':[part(),part(gfx_x=8)]},r)
        self.assertEqual(pixel(image,0,0),rgb555(31))
        self.assertEqual(pixel(image,1,0),rgb555(31<<5))

    def test_source_offsets_snap_to_eight_pixels(self):
        r=resources();page=bytearray(1024);page[512+32]=1;r['pages']=[bytes(page)]
        image=render_sprite_frame({'parts':[part(gfx_x=15,gfx_y=15)]},r)
        self.assertEqual(pixel(image,0,0),rgb555(31))

    def test_missing_pages_flags_dimensions_crops_and_canvas_fail(self):
        for p in [part(gfx_page=1),part(flip_bits=4),part(width=16),part(gfx_x=128),part(gfx_y=8),part(width=0)]:
            with self.assertRaises(PatchError):render_sprite_frame({'parts':[p]},resources())
        with self.assertRaisesRegex(PatchError,'canvas'):
            render_sprite_frame({'parts':[part(x=0),part(x=600)]},resources())

    def test_empty_frame(self):
        image=render_sprite_frame({'parts':[]},resources())
        self.assertEqual((image['width'],image['height'],image['pixels']),(1,1,bytes(4)))

class NativeSpritePreviewTests(unittest.TestCase):
    @unittest.skipUnless((ROOT/'CastlevaniaAoS.gba').exists(),'Private host unavailable')
    def test_all_272_registered_frames_render_without_mutation(self):
        from aria.cli import load_image
        rom=load_image(ROOT/'CastlevaniaAoS.gba');before=bytes(rom.data);count=0
        for name in SPRITES:
            resources_=resolve_sprite_resources(rom,name)
            for frame in inspect_sprite(rom,SPRITES[name])['frames']:
                image=render_sprite_frame(frame,resources_);count+=1
                self.assertEqual(len(image['pixels']),image['width']*image['height']*4)
            self.assertEqual(preview_sprite(rom,name)['report']['status'],'static_source_preview')
        self.assertEqual(count,272);self.assertEqual(bytes(rom.data),before);self.assertEqual(rom.ledger,[])
        unknown=inspect_sprite(rom,SPRITES['unknown-actor'])
        self.assertEqual((unknown['frame_count'],unknown['animation_count'],unknown['diagnostics']),(21,9,[]))
        unknown2=inspect_sprite(rom,SPRITES['unknown-actor-2'])
        self.assertEqual((unknown2['frame_count'],unknown2['animation_count'],unknown2['diagnostics']),(35,10,[]))
        resources_=resolve_sprite_resources(rom,'unknown-actor')
        self.assertEqual(len(resources_['pages'][0]),4096);self.assertEqual(len(resources_['palette']),16)
        for frame in (-1,999,True):
            with self.assertRaisesRegex(PatchError,'frame index'):preview_sprite(rom,'common',frame)

    def test_cli_output_guard_and_png_with_synthetic_host_loader(self):
        from aria.cli import main
        root=ROOT/'local/sprite-tests';root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as temp:
            path=Path(temp)/'frame.png'
            result=dict(width=1,height=1,pixels=bytes(4),report=dict(status='static_source_preview'))
            with patch('aria.cli.load_image',return_value=object()),patch('aria.cli.preview_sprite',return_value=result),contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(['preview-sprite','common','--out',str(path)]),0)
                self.assertEqual(path.read_bytes()[:8],b'\x89PNG\r\n\x1a\n')
                for out in [ROOT/'frame.png',path.with_suffix('.json')]:
                    self.assertNotEqual(main(['preview-sprite','common','--out',str(out)]),0)
                before=path.read_bytes()
                self.assertNotEqual(main(['preview-sprite','common','--host',str(path),'--out',str(path)]),0)
                self.assertEqual(path.read_bytes(),before)
                mod=Path(temp)/'mod.json'
                mod.write_text('{}')
                with patch('aria.cli.apply_manifest',return_value={'content':[{'source':'frame.png'}]}):
                    self.assertNotEqual(main(['preview-sprite','common','--mod',str(mod),'--out',str(path)]),0)
                self.assertEqual(path.read_bytes(),before)

if __name__=='__main__':unittest.main()
