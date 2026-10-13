import unittest
from scripts.emulator import AudioCapture

class CaptureTests(unittest.TestCase):
 def test_stereo_order_and_snapshot(self):
  c=AudioCapture(3);c.append(bytes([1,0,2,0]));a=c.pcm();c.append(bytes([3,0,4,0]))
  self.assertEqual(a,bytes([1,0,2,0]));self.assertEqual(c.pcm(),bytes([1,0,2,0,3,0,4,0]));self.assertFalse(c.overflow)
 def test_overflow_is_bounded_and_explicit(self):
  c=AudioCapture(1);c.append(bytes(8));self.assertEqual(len(c.pcm()),4);self.assertTrue(c.overflow)
  c.append(bytes(4));self.assertEqual(len(c.pcm()),4)
 def test_limits(self):
  for n in (0,-1,True,1.5,10000001):
   with self.assertRaises(ValueError):AudioCapture(n)
 def test_alignment(self):
  c=AudioCapture(1)
  for data in (bytes(3),bytearray(4)):
   with self.assertRaises(ValueError):c.append(data)
