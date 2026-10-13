import unittest

from aria.audio import iter_events
from aria.audio_synthesis import gate_tied_events


class TieEventsTests(unittest.TestCase):
    def test_tie_wait_release(self):
        self.assertEqual(list(iter_events(bytes([0xCF, 60, 90, 0x86, 0xCE, 60, 0xB1]), 0)),
                         [(0, ('tie', 60, 90, 0)), (6, ('release', 60)), (6, ('end',))])


class TieGateTests(unittest.TestCase):
    def test_polyphonic_releases_preserve_controller_order(self):
        source = [(0, ('tie', 60, 90, 1)), (2, ('vol', 80)),
                  (3, ('tie', 64, 88, 2)), (6, ('release', 60)), (9, ('end',))]
        self.assertEqual(gate_tied_events(source, final_tick=10),
                         ((0, ('note', 60, 90, 1, 6)), (2, ('vol', 80)),
                          (3, ('note', 64, 88, 2, 6)), (9, ('end',))))
        self.assertEqual(source[0][1][0], 'tie')

    def test_newest_active_key_and_expired_note(self):
        source = [(0, ('tie', 60, 90, 1)), (2, ('note', 60, 90, 1, 1)),
                  (3, ('tie', 60, 90, 1)), (4, ('release', 60)),
                  (6, ('release', 60))]
        result = gate_tied_events(source, final_tick=8)
        self.assertEqual([event[1][4] for event in result], [6, 1, 1])

    def test_unclosed_tie_has_explicit_cap(self):
        self.assertEqual(gate_tied_events([(2, ('tie', 60, 90, 0))], final_tick=10),
                         ((2, ('note', 60, 90, 0, 8)),))
        self.assertEqual(gate_tied_events([(0, ('release', 70))], final_tick=1), ())

    def test_tick_and_size_bounds(self):
        for events, end in (([], -1), ([(2, ('end',))], 1),
                            ([(1, ('vol', 1)), (0, ('end',))], 2),
                            ([(0, ('end',))] * 20001, 1)):
            with self.assertRaises(ValueError):
                gate_tied_events(events, final_tick=end)

    def test_omitted_key_and_velocity(self):
        self.assertEqual(list(iter_events(bytes([0xD0, 62, 88, 0xCF, 0x86, 0xCE, 0xB1]), 0)),
                         [(0, ('note', 62, 88, 0, 1)), (0, ('tie', 62, 88, 0)),
                          (6, ('release', 62)), (6, ('end',))])

    def test_running_ties_and_releases(self):
        got = list(iter_events(bytes([0xBD, 4, 0xCF, 60, 90, 0x86, 64,
                                      0x86, 0xCE, 60, 0x86, 64, 0xB1]), 0))
        self.assertEqual(got, [(0, ('tie', 60, 90, 4)), (6, ('tie', 64, 90, 4)),
                               (12, ('release', 60)), (18, ('release', 64)), (18, ('end',))])

    def test_release_updates_key_for_following_omitted_note(self):
        got = list(iter_events(bytes([0xCF, 60, 90, 0xCE, 64, 0xD0, 0xB1]), 0))
        self.assertEqual(got[2], (0, ('note', 64, 90, 0, 1)))

    def test_ties_do_not_advance_time_and_budget_bounds_them(self):
        got = list(iter_events(bytes([0xCF, 60, 90, 64, 0xB1]), 0, budget=2))
        self.assertEqual(got, [(0, ('tie', 60, 90, 0)), (0, ('tie', 64, 90, 0))])

    def test_pattern_retains_tie_state(self):
        rom = bytearray(40)
        rom[:6] = bytes([0xB3]) + (0x08000020).to_bytes(4, 'little') + bytes([0xB1])
        rom[32:39] = bytes([0xCF, 60, 90, 0x86, 0xCE, 0xB4, 0xB1])
        self.assertEqual(list(iter_events(rom, 0)),
                         [(0, ('tie', 60, 90, 0)), (6, ('release', 60)), (6, ('end',))])
