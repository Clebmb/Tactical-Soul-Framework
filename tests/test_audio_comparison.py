import math,unittest
from aria.audio_comparison import rms_windows,align_envelopes
class ComparisonTests(unittest.TestCase):
 def test_rms_shared_grid_and_partial_tail(self):
  self.assertEqual(rms_windows([3,4,0,0,99],4,window_seconds=0.5),(math.sqrt(12.5),0))
  self.assertEqual(rms_windows([2]*10,5,window_seconds=0.3),(2,)*6)
 def test_offset_and_gain_independence(self):
  result=align_envelopes([8,8,1,3,2,7],[2,6,4,14],max_offset_bins=2)
  self.assertEqual(result['offset_bins'],2);self.assertAlmostEqual(result['correlation'],1)
 def test_ties_use_earliest_offset(self):
  result=align_envelopes([1,3,2,1,3,2],[1,3,2],max_offset_bins=3)
  self.assertEqual(result['offset_bins'],0);self.assertEqual(result['runner_up_correlation'],1)
 def test_constant_and_short_inputs(self):
  for ref,obs in (([1]*3,[1]*3),([1]*4,[1,2,3]),([1,2,3],[1,2,3,4]),([1,2],[1,2])):
   with self.assertRaises(ValueError):align_envelopes(ref,obs,max_offset_bins=2)
 def test_validation_and_work_budgets(self):
  for rate,window in ((True,0.02),(0,0.02),(100,0.0001),(1,0.02),(float('inf'),1)):
   with self.assertRaises(ValueError):rms_windows([1,2,3],rate,window_seconds=window)
  with self.assertRaises(ValueError):rms_windows([float('nan')],100)
  with self.assertRaises(ValueError):align_envelopes([1,2,3],[1,2,3],max_offset_bins=True)
  with self.assertRaises(ValueError):align_envelopes([1,2]*10000,[1,2]*1000,max_offset_bins=2000)
