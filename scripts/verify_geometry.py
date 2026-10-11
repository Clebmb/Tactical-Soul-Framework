"""Native cell-layout collision, reentry and save tests; fixtures declared."""
import sys,json,hashlib,ctypes as C
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aria.cli import load_image,apply_manifest
from aria.geometry import inspect_geometry,verify_roundtrip
from aria.compression import rebuild_aria,decode_lz10
from emulator import Emulator
bridge='--bridge-route' in sys.argv
three_room='--three-room-art' in sys.argv or bridge
two_room='--two-room-art' in sys.argv or three_room
room_art='--room-art' in sys.argv or two_room
lifecycle='--lifecycle' in sys.argv
if lifecycle and not room_art:raise ValueError('--lifecycle requires --room-art')
custom='--custom-terrain' in sys.argv or room_art
mod_id='bridge-route' if bridge else 'three-room-art' if three_room else 'two-room-art' if two_room else 'original-room-art' if room_art else 'custom-terrain-workshop' if custom else 'geometry-workshop'
evidence_prefix='bridge-route-lifecycle' if bridge else 'three-room-art' if three_room else 'two-room-art' if two_room else 'original-room-art' if room_art else 'custom-terrain' if custom else 'geometry'
host=ROOT/'CastlevaniaAoS.gba';original=host.read_bytes();manifest=ROOT/'examples'/mod_id/'mod.json'
r=load_image(host);before=inspect_geometry(r,0,3,full=True);verify_roundtrip(before)
for key in ['visual_resource','collision_resource']:
 expanded,_=decode_lz10(rebuild_aria(before[key],preserve=False));assert expanded[4:].hex()==before[key]['data_hex']
apply_manifest(r,manifest);after=inspect_geometry(r,0,3,full=True)
assert [j for j,(a,b) in enumerate(zip(before['cells'],after['cells'])) if a!=b]==[210]
if custom:
 assert after['metatiles_including_blank']==before['metatiles_including_blank']+1
 for key in ['visual_resource','collision_resource']:
  assert after[key]['data_hex'].startswith(before[key]['data_hex'])
  assert r.read(before[key.replace('_resource','_tileset_address')],before[key]['compressed_bytes']).hex()==before[key]['compressed_hex']
else:
 assert after['visual_resource']==before['visual_resource'] and after['collision_resource']==before['collision_resource']
assert r.read(before['layout_address'],640)==bytes.fromhex(verify_roundtrip(before)['layout_hex'])
assert r.read(0x08116650,64*47*2)==original[0x116650:0x116650+64*47*2]
out=ROOT/'build/mods'/mod_id/(mod_id+'.gba');r.output(out,host)

def press(e,k,wait=40):e.run(1,[k]);e.run(wait)
def boot(e):
 e.run(1000)
 for k in [3,8,8,8,3,3,8]:press(e,k,100)
 for _ in range(60):press(e,8,90)
 for _ in range(150):
  e.run(5,[7])
  if e.read(0x02000088)==0x0850F15C:break
 assert e.read(0x02000088)==0x0850F15C
 e.run(240)
 for _ in range(1200):
  if not (e.read(0x0200042C)&1):break
  e.run(1)
 assert not (e.read(0x0200042C)&1)
def adjacent(e):
 # Controlled equivalent position/velocity fixture beside the new step.
 e.write(0x02000524,(286-e.read(0x0200A09A,2))<<16) # Position is camera-relative; retain settled native Y.
 e.write(0x0200052C,0);e.write(0x02000530,0);e.run(1)

save_checks=[]
def check_save_art(e,stage):
 if not two_room:return
 from aria.rooms import room_address,metadata
 from aria.rendering import read_graphics,read_palettes,render_layer
 import struct
 assert e.read(0x02000088)==room_address(r,0,31)
 m=metadata(r,room_address(r,0,31));g,_=read_graphics(r,m[4]);p,_=read_palettes(r,m[5])
 assert e.bytes(0x0600C000,2048)==g[24]
 assert e.bytes(0x05000100,32)==struct.pack('<16H',*p[8])
 preview=render_layer(r,0,31);cx=e.read(0x0200A09A,2);cy=e.read(0x0200A09E,2);count=0
 for wy in range(100,120):
  for wx in range(164,184):
   off=(wy*preview['width']+wx)*4;c=preview['rgba'][off:off+4]
   if not c[3]:continue
   assert all(a>>3==b>>3 for a,b in zip(e.image.getpixel((wx-cx,wy-cy)),c[:3]))
   count+=1
 assert count>100
 save_checks.append({'stage':stage,'matching_mural_pixels':count})
 e.snap('two-room-art-'+stage+'.png')

gallery_checks={}
gallery_occluded_frames={}
def check_gallery_art(e,stage):
 if not three_room or e.read(0x02000088)!=0x0850F32C:return
 if e.read(0x02000010,1)!=4 or e.read(0x02000064,1)!=1:return
 from aria.rooms import room_address,metadata
 from aria.rendering import read_graphics,read_palettes,render_layer
 import struct
 m=metadata(r,room_address(r,0,6));g,_=read_graphics(r,m[4]);p,_=read_palettes(r,m[5])
 assert e.bytes(0x0600C000,2048)==g[24]
 assert e.bytes(0x05000100,32)==struct.pack('<16H',*p[8])
 cx=e.read(0x0200A09A,2);cy=e.read(0x0200A09E,2)
 if not (0<=324-cx and 344-cx<240 and 0<=100-cy and 120-cy<160):return
 if stage in gallery_checks:return
 preview=render_layer(r,0,6);count=0
 for wy in range(100,120):
  for wx in range(324,344):
   off=(wy*preview['width']+wx)*4;c=preview['rgba'][off:off+4]
   if not c[3]:continue
   if not all(a>>3==b>>3 for a,b in zip(e.image.getpixel((wx-cx,wy-cy)),c[:3])):
    # Keep the full fixed rectangle; retry later while controller traversal
    # clears transient actors/effects. Never filter individual mismatching pixels.
    gallery_occluded_frames[stage]=gallery_occluded_frames.get(stage,0)+1
    return
   count+=1
 assert count>100
 gallery_checks[stage]=count;e.snap('three-room-art-'+stage+'.png')

e=Emulator(host);boot(e);adjacent(e);e.run(30,[7]);base_x=(e.read(0x02000526,2)+e.read(0x0200A09A,2));e.snap('geometry-baseline.png');e.close()
e=Emulator(out);boot(e);adjacent(e);e.run(30,[7]);blocked_x=(e.read(0x02000526,2)+e.read(0x0200A09A,2));e.snap('geometry-step-blocked.png')
print('COLLISION',base_x,blocked_x,flush=True)
assert base_x>320 and blocked_x<320
if custom:
 from aria.rendering import render_layer
 preview=render_layer(r,0,3);cx=e.read(0x0200A09A,2);cy=e.read(0x0200A09E,2);compared=0
 # Right portion of new step, clear of Soma standing against its left edge.
 for wy in range(160,176):
  for wx in range(328,352):
   pos=(wy*preview['width']+wx)*4
   if preview['rgba'][pos+3]!=255:continue
   actual=e.image.getpixel((wx-cx,wy-cy));expected=preview['rgba'][pos:pos+3]
   assert all((a>>3)==(b>>3) for a,b in zip(actual,expected))
   compared+=1
 assert compared>100
 e.snap(evidence_prefix+'-native-step.png')
 print('CUSTOM PIXELS',compared,flush=True)
# Jump across the step using native A jump and Right.
e.run(30,[7,8]);e.run(75,[7]);jump_x=(e.read(0x02000526,2)+e.read(0x0200A09A,2));e.snap('geometry-step-jumped.png')
print('JUMP',jump_x,flush=True);assert jump_x>352
# Reach the existing paired save room through ordinary traversal.
for _ in range(180):
 e.run(20,[7,0]);e.run(1,[7,8]);e.run(15,[7,0])
 check_gallery_art(e,'outbound')
 if e.read(0x02000088)==0x0851021C:break
assert e.read(0x02000088)==0x0851021C
e.run(90)
check_save_art(e,'first-entry')
for _ in range(150):
 x=e.read(0x02000526,2)
 if 112<=x<=124:break
 e.run(1,[7 if x<112 else 6])
e.run(10);press(e,4,30);press(e,6,1);press(e,8,240)
sram=C.string_at(e.lib.retro_get_memory_data(0),e.lib.retro_get_memory_size(0));e.snap('geometry-save.png');e.close()
e=Emulator(out);C.memmove(e.lib.retro_get_memory_data(0),sram,len(sram));e.run(1000)
for k in [3,8,8,8]:press(e,k,160)
assert e.read(0x02000088)==0x0851021C
e.run(30);check_save_art(e,'fresh-continue')
# Return through the paired doorway and inspect the edited room again.
for _ in range(160):
 e.run(10,[6])
 check_gallery_art(e,'fresh-continue-return')
 if e.read(0x02000088)==0x0850F15C:break
assert e.read(0x02000088)==0x0850F15C
e.run(60)
for _ in range(160):
 e.run(10,[6])
 if e.read(0x02000526,2)+e.read(0x0200A09A,2)<400:break
e.run(60,[6]);return_x=e.read(0x02000526,2)+e.read(0x0200A09A,2)
print('RETURN',return_x,flush=True);assert 352<=return_x<400
if room_art:
 from aria.rendering import read_graphics,read_palettes
 from aria.rooms import metadata,room_address
 m=metadata(r,room_address(r,0,3));chunks,_=read_graphics(r,m[4]);banks,_=read_palettes(r,m[5])
 assert e.bytes(0x0600C000,2048)==chunks[24]
 assert e.bytes(0x05000100,32)==__import__('struct').pack('<16H',*banks[8])
 e.snap('original-room-art-native-return.png')
if lifecycle:
 press(e,3,40);assert e.read(0x02000064,1)==6
 e.snap('original-room-art-paused.png');e.run(200) # Let the native menu settle before B cancellation.
 press(e,0,90);print('RESUME',e.read(0x02000010,1),e.read(0x02000064,1),flush=True);assert e.read(0x02000010,1)==4 and e.read(0x02000064,1)==1
 assert e.bytes(0x0600C000,2048)==chunks[24]
 assert e.bytes(0x05000100,32)==__import__('struct').pack('<16H',*banks[8])
 e.snap('original-room-art-resumed.png')
 # Explicit death fixture: HP only. Native engine handles death/game-over.
 e.write(0x0201327A,0,2);e.run(180)
 assert e.read(0x0201327A,2)==0
 print('DEATH',e.read(0x02000010,1),e.read(0x02000064,1),e.read(0x020004EE,1),flush=True)
 assert e.read(0x020004EE,1)==16
 e.snap('original-room-art-death.png');e.run(900)
 print('GAMEOVER',e.read(0x02000010,1),e.read(0x02000064,1),flush=True)
 assert e.read(0x02000010,1)==5
 e.snap('original-room-art-gameover.png')
 death_sram=C.string_at(e.lib.retro_get_memory_data(0),e.lib.retro_get_memory_size(0))
 e.close();e=Emulator(out)
 C.memmove(e.lib.retro_get_memory_data(0),death_sram,len(death_sram));e.run(1000)
 for k in [3,8,8,8]:press(e,k,160)
 assert e.read(0x02000088)==0x0851021C and e.read(0x0201327A,2)>0
 e.run(30);check_save_art(e,'post-death-continue')
 for _ in range(160):
  e.run(10,[6])
  check_gallery_art(e,'post-death-return')
  if e.read(0x02000088)==0x0850F15C:break
 assert e.read(0x02000088)==0x0850F15C
 e.run(60)
 for _ in range(160):
  e.run(10,[6])
  if e.read(0x02000526,2)+e.read(0x0200A09A,2)<400:break
 e.run(60,[6]);assert 352<=e.read(0x02000526,2)+e.read(0x0200A09A,2)<400
 assert e.bytes(0x0600C000,2048)==chunks[24]
 assert e.bytes(0x05000100,32)==__import__('struct').pack('<16H',*banks[8])
 e.snap('original-room-art-post-death-return.png')
e.snap('geometry-continue-return.png');e.close();assert host.read_bytes()==original
report={'passed':['type-2 layer metadata/layout/compressed resources reconstruct exactly','literal recompression decodes to identical visual/collision data','one selected cell changes; original shared layout/resources and castle map preserved','native movement crosses baseline and is blocked by new stone step','native A jump crosses new step','natural traversal reaches paired native save room','fresh native continue returns through paired door and retains collision edit','original ROM unchanged'],'baseline_x':base_x,'blocked_x':blocked_x,'jump_x':jump_x,'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'fixtures':['identical camera-relative player X and zero velocity beside the step for initial comparisons; settled native Y retained; return collision tested by natural walking','existing paired-door save-route example; no terrain/collision RAM writes'],'limitations':['existing metatile reuse only; no new graphics or collision definitions','first-hallway main layer only for writes; no room resizing','death/hardware/all campaign interactions not certified','shared resources preserved; no general VRAM allocator or map compiler']}
if custom:
 report['custom_metatiles_added']=1;report['native_new_metatile_pixels_compared']=compared
 report['passed'].append('isolated appended visual/collision definitions render natively with exact sampled pixels')
 report['limitations'][0]='new arrangements of existing characters only; collision bytes 0/3 only; no imported graphics or VRAM allocation'
if room_art:
 report['room_assets']=r.room_asset_report
 report['passed'].append('original imported characters and palette load again after fresh continue and return')
 report['limitations'][0]='one registered 2KB character chunk and one palette bank; no general VRAM allocator or animation'
if lifecycle:
 report['passed'].extend(['pause/resume restores imported characters/palette','native death/game-over followed by fresh continue from post-death SRAM retains save and imported art on return'])
 report['fixtures'].append('HP set to zero to trigger native death; no graphics/palette/terrain RAM writes; fresh continue uses SRAM copied after game-over')
 report['limitations'][2]='one forced-HP death fixture; same-session game-over-menu continue, other events, hardware and full campaign unverified'
if two_room:
 assert len(save_checks)==(3 if lifecycle else 2)
 report['save_room_art_checks']=save_checks
 report['passed'].append('contrasting save-room graphics/palette and native mural pixels match at reported stages')
 report['limitations'][0]='two registered room-local 2KB character loads and palette banks; no general VRAM allocator or animation'
 report['limitations'][1]='registered hallway and save-room main layers only; dimensions preserved'
if three_room:
 assert set(gallery_checks)==({'outbound','fresh-continue-return','post-death-return'} if lifecycle else {'outbound','fresh-continue-return'})
 report['gallery_art_checks']=gallery_checks
 report['gallery_unmatched_capture_attempts']=gallery_occluded_frames
 report['limitations'][0]='three registered room-local character loads/palette banks; no general VRAM allocator'
 report['limitations'][1]='registered hallway/gallery/save main layers only; unchanged dimensions; not a repaired campaign graph'
if bridge:
 report['limitations'][1]='four registered terrain rooms; neighbor bridge traversed separately; campaign event access unverified'
 report['passed'].append('separate bridge-route build retains three-room main-route lifecycle')
(ROOT/'local'/(evidence_prefix+'-verification.json')).write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

