import unittest

from aria.audio import iter_events, NOTE_LENGTHS
from aria.audio_synthesis import sampled_envelope, render_sample


class TimingTests(unittest.TestCase):
    def test_chord_and_independent_gate(self):
        events = list(iter_events(bytes([0xD0, 60, 90, 4, 0xD0, 64,
                                        0x80, 0x86, 0xD0, 0xB1]), 0))
        self.assertEqual(events, [(0, ("note", 60, 90, 0, 5)),
                                  (0, ("note", 64, 90, 0, 1)),
                                  (6, ("note", 64, 90, 0, 1)),
                                  (6, ("end",))])

    def test_every_wait_opcode(self):
        for opcode, ticks in enumerate((0,) + NOTE_LENGTHS, 0x80):
            self.assertEqual(list(iter_events(bytes([opcode, 0xB1]), 0)),
                             [(ticks, ("end",))])

    def test_running_voice_selection(self):
        events = list(iter_events(bytes([0xBD, 2, 3, 0xD0, 60, 0xB1]), 0))
        self.assertEqual(events[0][1][3], 3)


class EnvelopeTests(unittest.TestCase):
    def test_integer_attack_decay_sustain_release(self):
        self.assertEqual(sampled_envelope(128, 128, 64, 128,
                                         gate_frames=5, frames=9),
                         (128, 255, 127, 64, 64, 32, 16, 8, 4))

    def test_release_interrupts_attack(self):
        self.assertEqual(sampled_envelope(10, 255, 255, 0,
                                         gate_frames=2, frames=4), (10, 20, 0, 0))

    def test_zero_gate_and_zero_attack(self):
        self.assertEqual(sampled_envelope(255, 255, 255, 255,
                                         gate_frames=0, frames=3), (0, 0, 0))
        self.assertEqual(sampled_envelope(0, 0, 0, 0,
                                         gate_frames=3, frames=3), (0, 0, 0))

    def test_bounds(self):
        for value in (-1, 256, 1.5, True):
            with self.assertRaises(ValueError):
                sampled_envelope(value, 0, 0, 0, gate_frames=1, frames=2)
        with self.assertRaises(ValueError):
            sampled_envelope(0, 0, 0, 0, gate_frames=1, frames=1000001)


class SampleRenderTests(unittest.TestCase):
    def test_signed_pcm_and_exhaustion(self):
        self.assertEqual(render_sample(bytes([0, 127, 128, 255]), 4,
                                       output_rate=4, frames=6),
                         (0, 127, -128, -1, 0, 0))

    def test_fractional_loop_seam_and_many_passes(self):
        self.assertEqual(render_sample(bytes([0, 40, 80]), 1,
                                       output_rate=2, frames=13, loop_start=1),
                         (0, 20, 40, 60, 80, 60, 40, 60, 80, 60, 40, 60, 80))

    def test_one_sample_loop_and_large_step(self):
        self.assertEqual(render_sample(bytes([255]), 100,
                                       output_rate=1, frames=4, loop_start=0),
                         (-1, -1, -1, -1))

    def test_envelope_clock_is_independent_of_output_rate(self):
        self.assertEqual(render_sample(bytes([100]), 1, output_rate=4,
                                       frames=6, loop_start=0, envelope=(255, 0),
                                       envelope_rate=2), (100, 100, 0, 0, 0, 0))

    def test_validation(self):
        for rate in (0, -1, float('inf'), float('nan'), True):
            with self.assertRaises(ValueError):
                render_sample(b'\x00', rate, output_rate=1, frames=1)
        for loop in (-1, 1, True):
            with self.assertRaises(ValueError):
                render_sample(b'\x00', 1, output_rate=1, frames=1, loop_start=loop)
        with self.assertRaises(ValueError):
            render_sample(b'', 1, output_rate=1, frames=1)
        with self.assertRaises(ValueError):
            render_sample(b'\x00', 1, output_rate=1, frames=1000001)
        with self.assertRaises(ValueError):
            render_sample(b'\x00', 1, output_rate=1, frames=1, envelope=(256,))
        with self.assertRaises(ValueError):
            render_sample(b'\x00', 1, output_rate=1, frames=10,
                          envelope_rate=1e308)


class TempoMapTests(unittest.TestCase):
    def test_cross_tempo_duration(self):
        from aria.audio_synthesis import TempoMap
        from aria.audio import ticks_to_seconds
        clock=TempoMap([[(10, ('tempo',150))]])
        self.assertAlmostEqual(clock.duration(5,15),ticks_to_seconds(5,75)+ticks_to_seconds(5,150))
        self.assertEqual(clock.duration(10,10),0)
    def test_shared_same_tick_order(self):
        from aria.audio_synthesis import TempoMap
        from aria.audio import ticks_to_seconds
        tracks=[[(0,('tempo',100)),(0,('tempo',120))],[(0,('tempo',150))]]
        clock=TempoMap(tracks);tracks[1].clear()
        self.assertEqual(clock.seconds_at(20),ticks_to_seconds(20,150))
    def test_empty_and_extrapolated_clock(self):
        from aria.audio_synthesis import TempoMap
        from aria.audio import ticks_to_seconds
        clock=TempoMap([],initial_tempo=100)
        self.assertEqual(clock.seconds_at(1000000000),ticks_to_seconds(1000000000,100))
    def test_invalid_schedules_and_tempos(self):
        from aria.audio_synthesis import TempoMap
        for tracks in ([[(0,('tempo',0))]],[[(2,('end',)),(1,('end',))]],
                       [[(True,('end',))]],[[(0,())]],[[]]*17,[[(0,('end',))]*20001]):
            with self.assertRaises(ValueError):TempoMap(tracks)
        with self.assertRaises(ValueError):TempoMap([],initial_tempo=True)
    def test_invalid_queries(self):
        from aria.audio_synthesis import TempoMap
        clock=TempoMap([])
        for tick in (-1,True,1.5,1000000001):
            with self.assertRaises(ValueError):clock.seconds_at(tick)
        with self.assertRaises(ValueError):clock.duration(2,1)


class TempoClockTests(unittest.TestCase):
    def test_explicit_clock_scales_all_segments_and_gates(self):
        from aria.audio_synthesis import TempoMap
        tracks=[[(10,('tempo',150)),(20,('tempo',100))]]
        default=TempoMap(tracks);custom=TempoMap(tracks,frame_rate=50)
        for tick in (0,5,10,15,20,30):
            self.assertAlmostEqual(custom.seconds_at(tick),default.seconds_at(tick)*1.2)
        self.assertAlmostEqual(custom.duration(5,25),default.duration(5,25)*1.2)
    def test_default_clock_is_compatible(self):
        from aria.audio_synthesis import TempoMap
        tracks=[[(10,('tempo',150))]]
        self.assertEqual(TempoMap(tracks).seconds_at(100),TempoMap(tracks,frame_rate=60).seconds_at(100))
    def test_invalid_clocks(self):
        from aria.audio_synthesis import TempoMap
        for value in (0,-1,True,0.5,1001,float('inf'),float('nan'),'60'):
            with self.assertRaises(ValueError):TempoMap([],frame_rate=value)
