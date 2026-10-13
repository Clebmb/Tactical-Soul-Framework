"""Synthetic tests for aria.audio. No ROM bytes; all streams are hand-built."""
import unittest

from aria.audio import decode_song_header, decode_voice_entry, parse_track

BASE = 0x08000000


def blob(*chunks):
    size = 0x200
    rom = bytearray([0x80] * size)  # default waits keep streams open-ended
    for off, data in chunks:
        rom[off:off + len(data)] = data
    return bytes(rom)


def ptr(off):
    return (BASE + off).to_bytes(4, "little")


class AudioParserTests(unittest.TestCase):
    def test_minimal_fine_track(self):
        rom = blob(((0x10, bytes([0xBC, 0x00, 0xB1]))))
        self.assertEqual(parse_track(rom, 0x10), {"ok": True, "fine": True})

    def test_running_status_survives_waits(self):
        # NOTE key/velo, wait, then bare bytes replay the note across waits.
        rom = blob(((0x10, bytes([0xD0, 0x3C, 0x50, 0x86, 0x3E, 0x86, 0xB1]))))
        self.assertEqual(parse_track(rom, 0x10), {"ok": True, "fine": True})

    def test_bare_byte_with_no_status_fails(self):
        rom = blob(((0x10, bytes([0x3C, 0xB1]))))
        bad = parse_track(rom, 0x10)
        self.assertFalse(bad["ok"])
        self.assertEqual(bad["why"], "bare-no-status")

    def test_goto_loop_is_ok_not_fine(self):
        loop = 0x10
        rom = blob(((loop, bytes([0xD0, 0x3C, 0xB2]) + ptr(loop),)))
        good = parse_track(rom, loop)
        self.assertTrue(good["ok"])
        self.assertFalse(good["fine"])

    def test_pattern_call_and_return(self):
        # PATT to a subroutine closed by PEND, then FINE.
        sub = 0x40
        rom = blob((0x10, bytes([0xB3]) + ptr(sub) + bytes([0xB1])),
                   (sub, bytes([0xD0, 0x3C, 0xB4])))
        self.assertEqual(parse_track(rom, 0x10), {"ok": True, "fine": True})

    def test_top_level_pend_is_noop_separator(self):
        rom = blob(((0x10, bytes([0xD0, 0x3C, 0xB4, 0xBD, 0x2E, 0xB1]))))
        self.assertEqual(parse_track(rom, 0x10), {"ok": True, "fine": True})

    def test_undefined_command_fails(self):
        rom = blob(((0x10, bytes([0xC6, 0x00, 0xB1]))))
        bad = parse_track(rom, 0x10)
        self.assertFalse(bad["ok"])
        self.assertEqual(bad["why"], "undef-C6")

    def test_prologue_decodes(self):
        # KEYSH 0, TEMPO 53 (106 BPM), VOICE 0, VOL 45, then FINE.
        rom = blob(((0x10, bytes([0xBC, 0x00, 0xBB, 0x35, 0xBD, 0x00,
                                  0xBE, 0x2D, 0xB1]))))
        self.assertEqual(parse_track(rom, 0x10), {"ok": True, "fine": True})


class AudioStructTests(unittest.TestCase):
    def test_song_header(self):
        rom = blob(((0x20, bytes([0x02, 0x00, 0x00, 0x00]) + ptr(0x60)
                      + ptr(0x10) + ptr(0x18),)))
        hdr = decode_song_header(rom, 0x20)
        self.assertEqual(hdr["tracks"], 2)
        self.assertEqual(hdr["voicegroup"], BASE + 0x60)
        self.assertEqual(hdr["track_pointers"], [BASE + 0x10, BASE + 0x18])

    def test_sampled_voice_entry(self):
        rom = blob(((0x30, bytes([0x08, 0x3C, 0x00, 0x00]) + ptr(0x100)
                      + bytes([0xFF, 0x00, 0xFF, 0x00]),)))
        voice = decode_voice_entry(rom, 0x30)
        self.assertEqual((voice["type"], voice["key"]), (0x08, 0x3C))
        self.assertEqual(voice["sample"], BASE + 0x100)
        self.assertEqual((voice["attack"], voice["release"]), (0xFF, 0x00))

    def test_unknown_voice_rejected(self):
        rom = blob(((0x30, bytes([0xFF] + [0] * 11),)))
        with self.assertRaises(ValueError):
            decode_voice_entry(rom, 0x30)

    def test_square_voice_entry(self):
        rom = blob(((0x30, bytes([0x01, 0x3C, 0x00, 0x00, 0x02, 0, 0, 0,
                                  0xFF, 0x00, 0xFF, 0x00]),)))
        voice = decode_voice_entry(rom, 0x30)
        self.assertEqual(voice["kind"], "square1")
        self.assertEqual(voice["duty_period"], 0x02)
        self.assertEqual(voice["attack"], 0xFF)

    def test_key_split_voice_entry(self):
        rom = blob(((0x30, bytes([0x40, 0, 0, 0]) + ptr(0x100)
                      + ptr(0x120),)))
        voice = decode_voice_entry(rom, 0x30)
        self.assertEqual(voice["kind"], "key-split")
        self.assertEqual((voice["table_a"], voice["table_b"]),
                         (BASE + 0x100, BASE + 0x120))

    def test_iter_voices_uniform_stride(self):
        ent = (bytes([0x08, 0x3C, 0, 0]) + ptr(0x100)
               + bytes([0xFF, 0, 0xFF, 0]))
        rom = blob((0x30, ent + ent))
        from aria.audio import iter_voices
        got = list(iter_voices(rom, 0x30, count=2))
        self.assertEqual([i for i, _ in got], [0, 1])
        self.assertTrue(all(e["kind"] == "sampled-no-resample"
                            for _, e in got))

    def test_looped_sample_header(self):
        from aria.audio import decode_sample
        body = bytes([0x80]) * 32
        rom = blob((0x40, bytes([0x00, 0x00, 0x00, 0x40,
                                 0x00, 0x40, 0xA4, 0x00,
                                 0x10, 0x00, 0x00, 0x00,
                                 0x20, 0x00, 0x00, 0x00]) + body))
        got = decode_sample(rom, 0x40)
        self.assertEqual((got["status"], got["freq"]), (0x4000, 0xA44000))
        self.assertEqual((got["loop"], got["size"]), (0x10, 0x20))
        self.assertEqual((got["data_offset"], got["data_end"]),
                         (0x50, 0x70))

    def test_one_shot_sample_header(self):
        from aria.audio import decode_sample
        rom = blob(((0x40, bytes([0x00, 0x00, 0x00, 0x00,
                                  0x00, 0x40, 0xA4, 0x00,
                                  0x00, 0x00, 0x00, 0x00,
                                  0x08, 0x00, 0x00, 0x00])
                      + bytes(8),)))
        got = decode_sample(rom, 0x40)
        self.assertEqual(got["status"], 0)
        self.assertEqual(got["size"], 8)

    def test_bad_sample_rejected(self):
        from aria.audio import decode_sample
        rom = blob(((0x40, bytes([0x01, 0x00, 0x00, 0x40,
                                  0x00, 0x40, 0xA4, 0x00,
                                  0x20, 0x00, 0x00, 0x00,
                                  0x10, 0x00, 0x00, 0x00]),)))
        with self.assertRaises(ValueError):
            decode_sample(rom, 0x40)

    def test_c4_rates_match_documented_mixer_rates(self):
        from aria.audio import sample_c4_rate, sample_c4_duration
        self.assertEqual(sample_c4_rate(0x00A44000), 10512)
        self.assertEqual(sample_c4_rate(0x00D10C00), 13379)
        self.assertAlmostEqual(sample_c4_duration(0x00A44000, 10512), 1.0)

    def test_event_schedule_with_waits_and_tempo(self):
        from aria.audio import iter_events, ticks_to_seconds
        rom = blob((0x10, bytes([0xBB, 0x35, 0xD0, 0x3C, 0x50,
                                  0x86, 0x3E, 0xB1])))
        got = list(iter_events(rom, 0x10))
        self.assertEqual(got[0], (0, ("tempo", 0x35)))
        # D0 sets a one-tick gate; W06 advances six ticks.
        self.assertEqual(got[1][1][:4], ("note", 0x3C, 0x50, 0))
        self.assertEqual(got[2][0], 6)
        self.assertEqual(got[2][1][:3], ("note", 0x3E, 0x50))
        self.assertEqual(got[3][1], ("end",))
        self.assertAlmostEqual(ticks_to_seconds(53, 53), 75 / 60.0)

    def test_event_loop_unrolls_once(self):
        from aria.audio import iter_events
        loop = 0x10
        rom = blob((loop, bytes([0xD0, 0x3C, 0xB2]) + ptr(loop)))
        got = list(iter_events(rom, loop))
        kinds = [e[1][0] for e in got]
        self.assertEqual(kinds, ["note", "note", "loop"])
        self.assertEqual(got[1][0], got[0][0])

    def test_event_vol_emitted(self):
        from aria.audio import iter_events
        rom = blob((0x10, bytes([0xBE, 0x40, 0x40, 0xD0, 0x3C, 0xB1])))
        kinds = [e[1][0] for e in iter_events(rom, 0x10)]
        self.assertEqual(kinds, ["vol", "vol", "note", "end"])

    def test_duty_patterns_and_psg_pitch(self):
        from aria.audio import DUTY_PATTERNS, psg_tone_freq
        self.assertEqual([sum(p) for p in DUTY_PATTERNS], [1, 2, 4, 6])
        self.assertTrue(all(len(p) == 8 for p in DUTY_PATTERNS))
        self.assertAlmostEqual(psg_tone_freq(69), 440.0)
        self.assertAlmostEqual(psg_tone_freq(60), 261.63, places=1)
        self.assertAlmostEqual(psg_tone_freq(60, wave_channel=True),
                               261.63 / 2, places=1)

    def test_sampled_envelope_raw_preset_is_unity(self):
        from aria.audio import sampled_envelope
        gains = sampled_envelope(0xFF, 0, 0xFF, 0, 64)
        self.assertEqual(len(gains), 64)
        self.assertTrue(all(g == 1.0 for g in gains))

    def test_sampled_envelope_release_cuts(self):
        from aria.audio import sampled_envelope
        gains = sampled_envelope(0xFF, 0, 0xFF, 0xFF, 64)
        self.assertEqual(len(gains), 64)
        self.assertAlmostEqual(gains[-1], 0.0)
        self.assertTrue(all(0.0 <= g <= 1.0 for g in gains))

    def test_event_garbage_start_terminates(self):
        from aria.audio import iter_events
        self.assertEqual(list(iter_events(bytes([0x80] * 64), 0x50005)), [])
        self.assertEqual(list(iter_events(bytes([0x80] * 64), -4)), [])

    def test_event_voice_state_tracked(self):
        from aria.audio import iter_events
        rom = blob((0x10, bytes([0xBD, 0x05, 0xD0, 0x3C, 0xB1])))
        got = list(iter_events(rom, 0x10))
        self.assertEqual(got[0][1], ("note", 0x3C, 64, 5, 1))

    def test_iter_songs_dereferences_table(self):
        from aria.audio import iter_songs
        hdr = bytes([0x01, 0, 0, 0]) + ptr(0x90) + ptr(0x10)
        rom = blob((0x20, ptr(0x60) + bytes(4)), (0x60, hdr))
        got = list(iter_songs(rom, 0x20, 1))
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0][1]["track_pointers"], [BASE + 0x10])


if __name__ == "__main__":
    unittest.main()
