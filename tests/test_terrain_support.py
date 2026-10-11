import copy,unittest
from pathlib import Path
from unittest.mock import patch
from aria.cli import load_image
from aria.core import PatchError
from aria.terrain_support import assess_terrain_support,catalog_terrain_support
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless((ROOT/'CastlevaniaAoS.gba').exists(),'private supported host absent')
class TerrainSupportTests(unittest.TestCase):
 def setUp(self):self.r=load_image(ROOT/'CastlevaniaAoS.gba')
 def test_registered_readonly(self):
  before=copy.deepcopy(self.r.__dict__);a=assess_terrain_support(self.r,0,5)
  self.assertEqual(a['status'],'registered');self.assertTrue(a['write_enabled']);self.assertIn(6,a['available_metatile_ids']);self.assertTrue(a['roundtrip_verified']);self.assertEqual(self.r.__dict__,before)
 def test_candidate_is_not_authorization(self):
  self.r.profile['geometry_edit_rooms']=[];a=assess_terrain_support(self.r,0,5)
  self.assertEqual(a['status'],'static_candidate');self.assertFalse(a['write_enabled']);self.assertIn('registration_required',a);self.assertEqual(self.r.profile['geometry_edit_rooms'],[])
 def test_resource_failure_blocks_registered_room(self):
  with patch('aria.terrain_support.audit_room_resources',side_effect=PatchError('bad load')):a=assess_terrain_support(self.r,0,5)
  self.assertEqual(a['status'],'blocked');self.assertFalse(a['write_enabled']);self.assertEqual(a['diagnostics'][-1]['code'],'invalid_terrain_data')
 def test_alternate_state_blocks_narrow_assessment(self):
  from aria.rooms import room_address
  offset=room_address(self.r,0,5)-self.r.base+4;self.r.data[offset:offset+4]=(0x0850F294).to_bytes(4,'little')
  a=assess_terrain_support(self.r,0,5);self.assertFalse(a['write_enabled']);self.assertIn('alternate_states_unverified',[d['code'] for d in a['diagnostics']])
 def test_pagination_and_invalid_options(self):
  a=catalog_terrain_support(self.r,sector=0,offset=3,limit=3)
  self.assertEqual([r['room'] for r in a['rooms']],[3,4,5]);self.assertEqual(a['next_offset'],6)
  self.assertEqual(sum(a['page_summary'].values()),3)
  for kwargs in ({'limit':129},{'limit':True},{'sector':12},{'offset':-1}):
   with self.assertRaises(PatchError):catalog_terrain_support(self.r,**kwargs)
 def test_local_room_error_does_not_abort_page(self):
  from aria.rooms import sector_span
  table,count=sector_span(self.r,0);offset=table-self.r.base+4*4;self.r.data[offset:offset+4]=bytes(4)
  a=catalog_terrain_support(self.r,sector=0,offset=3,limit=3)
  self.assertEqual(a['rooms'][1]['status'],'blocked');self.assertEqual(a['rooms'][2]['status'],'registered')
