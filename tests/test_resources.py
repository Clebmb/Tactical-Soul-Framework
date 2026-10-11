"""Resource contracts use synthetic ROMs; private-host roundtrips are optional."""
import copy,hashlib,io,json,unittest
from pathlib import Path
from unittest.mock import patch
from contextlib import redirect_stdout,redirect_stderr
from aria.core import RomImage,PatchError
from aria.content import tiles,palette
from aria.resources import descriptor,catalog,export_resource,replace_named,apply_resource_edits,diff_resource

class ResourceTests(unittest.TestCase):
 def image(self):
  raw=bytearray(512);raw[28:32]=b'TILE';raw[32:160]=bytes(range(128));raw[284:288]=b'PALT'
  raw[288:320]=b''.join((i*31).to_bytes(2,'little') for i in range(16))
  def row(a,n,kind,header,w=None,h=None):return {'address':a,'size':n,'format':kind,'header_address':a-4,'header_hex':header.hex(),'original_sha256':hashlib.sha256(raw[a:a+n]).hexdigest(),'width':w,'height':h}
  profile={'size':512,'sha256':hashlib.sha256(raw).hexdigest(),'rom_base':0,'allocation_ranges':[{'start':400,'end':512}],'content_resources':{'sheet':row(32,128,'tiles4',b'TILE',16,16),'colors':row(288,32,'palette_rgb8',b'PALT')}}
  return RomImage(raw,profile)
 def entry(self,rom,name='sheet'):
  return {'resource':name,'expected_sha256':descriptor(rom,name)['original_sha256'],'provenance':'original test art','tiles':[{'index':1,'pixels':[3]*64}]} if name=='sheet' else {'resource':name,'expected_sha256':descriptor(rom,name)['original_sha256'],'provenance':'original colors','colors':[{'index':2,'rgb':[255,0,255]}]}
 def test_tile_export_roundtrip(self):
  r=self.image();self.assertEqual(tiles(export_resource(r,'sheet')),r.read(32,128))
 def test_palette_export_roundtrip(self):
  r=self.image();self.assertEqual(palette(export_resource(r,'colors')),r.read(288,32))
 def test_catalog_current_original_hash(self):
  r=self.image();before=catalog(r);apply_resource_edits(r,[self.entry(r)]);after=catalog(r)
  self.assertEqual(before[0]['original_sha256'],after[0]['original_sha256']);self.assertNotEqual(before[0]['current_sha256'],after[0]['current_sha256'])
 def test_sparse_preserves_neighbors(self):
  r=self.image();apply_resource_edits(r,[self.entry(r),self.entry(r,'colors')]);claimed={i for x in r.ledger for i in range(x['address'],x['end'])}
  self.assertEqual(len(claimed),34);self.assertTrue(all(r.data[i]==r.original[i] for i in range(512) if i not in claimed));self.assertEqual(r.read(64,32),bytes([0x33])*32)
 def test_invalid_batch_no_writes(self):
  for mutate in ['hash','duplicate','bounds','format','boolean','extra','empty']:
   r=self.image();e=self.entry(r)
   if mutate=='hash':e['expected_sha256']='0'*64
   elif mutate=='duplicate':e['tiles']*=2
   elif mutate=='bounds':e['tiles'][0]['index']=4
   elif mutate=='format':e['colors']=[]
   elif mutate=='boolean':e['tiles'][0]['index']=True
   elif mutate=='extra':e['ignored']='no'
   else:e['tiles']=[]
   with self.assertRaises(PatchError):apply_resource_edits(r,[e])
   self.assertEqual(r.data,r.original)
 def test_duplicate_resource(self):
  r=self.image();e=self.entry(r)
  with self.assertRaises(PatchError):apply_resource_edits(r,[e,e])
  self.assertEqual(r.data,r.original)
 def test_header_and_profile_drift(self):
  r=self.image();r.data[28]=0
  with self.assertRaises(PatchError):descriptor(r,'sheet')
  r=self.image();r.profile['content_resources']['sheet']['original_sha256']='0'*64
  with self.assertRaises(PatchError):descriptor(r,'sheet')
 def test_unknown_resource(self):
  with self.assertRaises(PatchError):descriptor(self.image(),'missing')
 def test_named_binding_constraints(self):
  for kind,encoding,data in [('tiles4','lz77',bytes(128)),('palette_rgb8','raw',bytes(128)),('tiles4','raw',bytes(127))]:
   with self.assertRaises(PatchError):replace_named(self.image(),'sheet',kind,encoding,data,'test')
 def test_named_sparse_conflict(self):
  r=self.image();replace_named(r,'sheet','tiles4','raw',bytes(128),'test')
  with self.assertRaises(PatchError):apply_resource_edits(r,[self.entry(r)])
 def test_tile_diff_reconstructs_authored(self):
  r=self.image();art=export_resource(r,'sheet');art['pixels'][10]=15;edit=diff_resource(r,'sheet',art,'my edit');self.assertEqual(len(edit['tiles']),1);apply_resource_edits(r,[edit]);self.assertEqual(r.read(32,128),tiles(art))
 def test_palette_diff_reconstructs_authored(self):
  r=self.image();art=export_resource(r,'colors');art[7]=[255,33,65];edit=diff_resource(r,'colors',art,'my edit');self.assertEqual(edit['colors'][0]['index'],7);apply_resource_edits(r,[edit]);self.assertEqual(r.read(288,32),palette(art))
 def test_empty_diff_and_wrong_dimensions(self):
  r=self.image()
  with self.assertRaises(PatchError):diff_resource(r,'sheet',export_resource(r,'sheet'),'unchanged')
  art=export_resource(r,'sheet');art['width']=8;art['height']=32
  with self.assertRaises(PatchError):diff_resource(r,'sheet',art,'wrong shape')
 def test_export_private_path_guard(self):
  from aria.cli import main
  with patch('aria.cli.load_image',return_value=self.image()),redirect_stderr(io.StringIO()):
   self.assertEqual(main(['export-content','sheet','--out',str(Path(__file__).resolve())]),1)
 def test_real_profile_export_roundtrips(self):
  from aria.cli import load_image,ROOT
  host=ROOT/'CastlevaniaAoS.gba'
  if not host.exists():self.skipTest('private exact host absent')
  r=load_image(host)
  for row in catalog(r):
   data=export_resource(r,row['id']);encoded=tiles(data) if row['format']=='tiles4' else palette(data)
   self.assertEqual(encoded,r.read(row['address'],row['size']))

 def test_export_refuses_private_host_overwrite(self):
  from aria.cli import main,ROOT
  target=ROOT/'local/do-not-create-host.gba'
  with patch('aria.cli.load_image',return_value=self.image()),redirect_stderr(io.StringIO()):
   self.assertEqual(main(['export-content','sheet','--host',str(target),'--out',str(target)]),1)
  self.assertFalse(target.exists())
