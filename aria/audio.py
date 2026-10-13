"""Native audio reconnaissance: MusicPlayer2000 (Sappy) structures.

Read-only, pure helpers over ROM bytes. Command semantics follow the
VGMDocs 'Summary of GBA standard sound driver' reference (Bregalad/ipatix):
waits W00-W96, FINE/GOTO/PATT/PEND/REPT, MEMACC, TEMPO/KEYSH/VOICE/VOL/PAN
controllers, TIE/EOT and variable-length notes with running status.

One engine behavior is an explicit assumption, not reference text:
a top-level PEND (empty pattern stack) is treated as a no-op separator.
It is pervasive in this ROM (136 of 366 song tracks hit one) and the
shipped game plays those songs, so whatever the engine does there is
non-fatal by construction. Native driver-trace confirmation is pending.

Native evidence (private): six song tables, all fully decoded (400 songs,
578 tracks, 0 failures); five voicegroups with a typed census (535 sampled
voices, 59 square, 1 wave, 2 rhythm, 2 noise-alt); 360 distinct WaveData
samples (2.3 MB of 8-bit PCM) with validated headers. See
docs/AUDIO-RECON.md. Narrow original boot melody writing lives in aria.music.
"""

ROM_BASE = 0x08000000

NOTE_MIN, NOTE_MAX = 0xD0, 0xFF

# Repeatable commands and their maximum trailing-argument counts. A bare
# byte (< 0x80) replays the most recent repeatable command with the byte
# as its first argument; running status survives waits and flow commands.
REPEATABLE_MAXARGS = {
    0xBD: 1,  # VOICE
    0xBE: 1,  # VOL
    0xBF: 1,  # PAN
    0xC0: 1,  # BEND
    0xC1: 1,  # BENDR
    0xC4: 1,  # MOD depth
    0xC8: 1,  # TUNE
    0xCE: 1,  # EOT [key]
    0xCF: 2,  # TIE [key[,velo]]
}

# Fixed one-argument, non-repeatable controllers.
FIXED_ONE_ARG = {0xBA, 0xBB, 0xBC, 0xC2, 0xC3, 0xC5}  # PRIO T TEMPO KEYSH LFOS LFODL MODT


def _u32(rom, off):
    return int.from_bytes(rom[off:off + 4], "little")


def decode_song_header(rom, offset):
    """Decode an MP2k song header: track count, voicegroup, track pointers."""
    n_tracks = rom[offset]
    voicegroup = _u32(rom, offset + 4)
    tracks = [_u32(rom, offset + 8 + 4 * i) for i in range(n_tracks)]
    return {"tracks": n_tracks, "voicegroup": voicegroup,
            "track_pointers": tracks}


# Voicegroup ToneData: every entry is 12 bytes regardless of voice type
# (pret m4a_internal.h / music_voice.inc via web research). Sampled types
# carry a sample pointer; PSG types carry duty/wave/period payloads in the
# same word; key-split types carry sub-table pointers.
VOICE_KINDS = {
    0x00: "sampled", 0x08: "sampled-no-resample",
    0x01: "square1", 0x02: "square2", 0x09: "square1-alt",
    0x0A: "square2-alt", 0x03: "wave", 0x0B: "wave-alt",
    0x04: "noise", 0x0C: "noise-alt",
    0x40: "key-split", 0x80: "rhythm",
}
VOICE_SIZE = 12


def decode_voice_entry(rom, offset):
    """Decode one 12-byte voicegroup entry of any known voice type.

    Returns type/key plus kind-specific payloads: sampled/wave voices give
    a sample/wave pointer and ADSR; square/noise voices give duty/period
    bytes and ADSR; key-split/rhythm voices give sub-table pointers.
    Raises ValueError only for unknown leading type bytes.
    """
    kind = rom[offset]
    if kind not in VOICE_KINDS:
        raise ValueError("unknown voice type 0x%02X" % kind)
    entry = {"type": kind, "kind": VOICE_KINDS[kind],
             "key": rom[offset + 1]}
    word = _u32(rom, offset + 4)
    if kind in (0x00, 0x08, 0x03, 0x0B):
        entry["sample" if kind in (0x00, 0x08) else "wave"] = word
        entry.update({"attack": rom[offset + 8], "decay": rom[offset + 9],
                      "sustain": rom[offset + 10],
                      "release": rom[offset + 11]})
    elif kind in (0x01, 0x02, 0x09, 0x0A, 0x04, 0x0C):
        entry["duty_period"] = rom[offset + 4]
        entry.update({"attack": rom[offset + 8], "decay": rom[offset + 9],
                      "sustain": rom[offset + 10],
                      "release": rom[offset + 11]})
    else:  # 0x40 key-split / 0x80 rhythm: two table pointers
        entry["table_a"] = word
        entry["table_b"] = _u32(rom, offset + 8)
    return entry


def iter_voices(rom, offset, count=128):
    """Yield (index, entry) over a voicegroup with uniform 12-byte stride."""
    for i in range(count):
        yield i, decode_voice_entry(rom, offset + VOICE_SIZE * i)


def resolve_note_voice(rom, bank_offset, voice_index, note_key, rom_base=ROM_BASE):
    """Resolve direct/rhythm ToneData with checked, one-level table access.

    Returns voice, selected file offset, playback_key and rhythm_pan. Rhythm
    uses the note key as a 12-byte child index and the child's key for pitch;
    direct instruments retain the note key. rhythm_pan is signed -128..126
    or None when not forced. No recursive banks or key-splits are supported.
    This source-derived lookup is not native consumer or audio-write proof.
    """
    for value in (voice_index, note_key):
        if type(value) is not int or not 0 <= value <= 127:
            raise ValueError("voice index and note key must be MIDI bytes")
    if type(bank_offset) is not int or bank_offset < 0:
        raise ValueError("bank offset must be a nonnegative file offset")

    def checked(offset):
        if not 0 <= offset <= len(rom) - VOICE_SIZE:
            raise ValueError("voice entry outside image")
        return decode_voice_entry(rom, offset)

    offset = bank_offset + voice_index * VOICE_SIZE
    voice = checked(offset)
    playback_key, pan = note_key, None
    if voice["kind"] == "key-split":
        raise ValueError("key-split resolution is unsupported")
    if voice["kind"] == "rhythm":
        table = voice["table_a"] - rom_base
        if not 0 <= table <= len(rom) - VOICE_SIZE:
            raise ValueError("rhythm bank pointer outside image")
        offset = table + note_key * VOICE_SIZE
        voice = checked(offset)
        if voice["kind"] in ("key-split", "rhythm"):
            raise ValueError("nested instrument bank is unsupported")
        playback_key = voice["key"]
        if not 0 <= playback_key <= 127:
            raise ValueError("rhythm playback key is not a MIDI byte")
        raw_pan = rom[offset + 3]
        if raw_pan & 0x80:
            pan = (raw_pan - 0xC0) * 2
    return {"voice": voice, "offset": offset, "playback_key": playback_key,
            "rhythm_pan": pan}


SAMPLE_HEADER_SIZE = 16
SAMPLE_STATUSES = (0x0000, 0x4000)  # one-shot, looped

# WaveData.freq is 1024x the C4 (MIDI key 60) playback rate in Hz
# (Bregalad's Sappy notes; GBATEK MidiKey2Freq). 0x00A44000 decodes to
# exactly 10512 Hz and 0x00D10C00 to exactly 13379 Hz, both standard
# MP2K mixer rates. Per-key playback scales by 2^((key-60)/12).
FREQ_SCALE = 1024


def decode_sample(rom, offset):
    """Decode one 16-byte WaveData header plus its 8-bit PCM payload range.

    Layout: u16 type (0), u16 status (0 one-shot / 0x4000 looped),
    u32 freq (engine fixed-point rate word), u32 loop start, u32 size.
    Returns type/status/freq/loop/size and the payload file range
    (data_offset, data_end). Raises ValueError unless every field is
    in bounds (loop <= size, payload inside the image). Pure.
    """
    stype = int.from_bytes(rom[offset:offset + 2], "little")
    status = int.from_bytes(rom[offset + 2:offset + 4], "little")
    freq = _u32(rom, offset + 4)
    loop = _u32(rom, offset + 8)
    size = _u32(rom, offset + 12)
    data = offset + SAMPLE_HEADER_SIZE
    if (stype != 0 or status not in SAMPLE_STATUSES
            or not 0x1000 <= freq <= 0xFFFFFF
            or loop > size or data + size > len(rom)):
        raise ValueError("not a WaveData header at offset %d" % offset)
    return {"type": stype, "status": status, "freq": freq, "loop": loop,
            "size": size, "data_offset": data, "data_end": data + size}


def sample_c4_rate(freq):
    """Playback rate in Hz of a WaveData freq word at MIDI C4 (key 60)."""
    return freq / FREQ_SCALE


def sample_c4_duration(freq, size):
    """Seconds of 8-bit PCM `size` bytes long at the word's C4 rate."""
    return size / sample_c4_rate(freq)


# Note/wait lengths in ticks, indexed by command (D0-FF notes, 80-B0 waits).
# VGMDocs reference table (48 entries, 1..96 ticks); indices clamp at the end.
NOTE_LENGTHS = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
                 17, 18, 19, 20, 21, 22, 23, 24, 28, 30, 32, 36, 40, 42,
                 44, 48, 52, 54, 56, 60, 64, 66, 68, 72, 76, 78, 80, 84,
                 88, 90, 92, 96)

# Ticks are engine frames scaled by tempo: 1 tick = 1 frame at tempo 75.
TICKS_REFERENCE_TEMPO = 75
FRAME_SECONDS = 1 / 60


def ticks_to_seconds(ticks, tempo):
    """Convert tick counts to seconds at an MP2k TEMPO value (BPM/2)."""
    return ticks * TICKS_REFERENCE_TEMPO / tempo * FRAME_SECONDS


def iter_events(rom, start, rom_base=ROM_BASE, budget=20000, loop_passes=1):
    """Schedule one track as (tick, event) tuples in execution order.

    Events: ("note", key, velocity, voice, length) with the voice/tempo
    state at strike time, ("tempo", value), ("vol", value),
    ("tie", key, velocity, voice), ("release", key), ("end",) and ("loop",).
    Only waits advance time; notes set independent gates (including the
    optional third-argument extension). W00 is zero ticks. Running status, PATT
    subroutines (max depth 4) and top-level-PEND-as-no-op match
    parse_track. Backward GOTOs unroll `loop_passes` extra times, then
    emit ("loop",) and stop; FINE emits ("end",). Velocities default
    to 64 when omitted (engine running value; exact default untraced).
    Pure.
    """
    end = min(start + 4096, len(rom))
    pos = start
    tick = 0
    last_rep = None
    stack = []
    loops = {}
    voice = 0
    velocity = 64
    key = 0
    steps = 0

    def args(need):
        nonlocal pos
        out = []
        while len(out) < need and pos < end and rom[pos] < 0x80:
            out.append(rom[pos])
            pos += 1
        return out

    def note_len(cmd):
        return NOTE_LENGTHS[cmd - NOTE_MIN]

    def strike(code, values):
        nonlocal key, velocity
        if values:
            key = values[0]
        if len(values) > 1:
            velocity = values[1]
        if code == 0xCF:
            return ("tie", key, velocity, voice)
        gate = (note_len(code) + (values[2] if len(values) > 2 else 0)) & 0xFF
        return ("note", key, velocity, voice, gate)

    def release(values):
        nonlocal key
        if values:
            key = values[0]
        return ("release", key)

    while steps < budget:
        steps += 1
        if not (0 <= pos < len(rom) and start <= pos < end):
            return
        cmd = rom[pos]
        if cmd < 0x80:
            if last_rep is None:
                return
            code, need = last_rep
            first = cmd
            pos += 1
            rest = args(need - 1)
            full = [first] + rest
            if code == 0xBE:
                yield (tick, ("vol", first))
            elif code == 0xBD:
                voice = first
            elif code >= NOTE_MIN:
                yield (tick, strike(code, full))
            elif code == 0xCF:
                yield (tick, strike(code, full))
            elif code == 0xCE:
                yield (tick, release(full))
            continue
        if 0x80 <= cmd <= 0xB0:
            tick += ((0,) + NOTE_LENGTHS)[cmd - 0x80]
            pos += 1
            continue
        if NOTE_MIN <= cmd <= NOTE_MAX:
            pos += 1
            got = args(3)
            last_rep = (cmd, 3)
            yield (tick, strike(cmd, got))
            continue
        if cmd == 0xB1:
            yield (tick, ("end",))
            return
        if cmd in (0xB2, 0xB3):
            if pos + 5 > end:
                return
            dest = _u32(rom, pos + 1) - rom_base
            if not (0 <= dest < len(rom)):
                return
            if cmd == 0xB3:
                if len(stack) >= 4:
                    return
                stack.append(pos + 5)
                pos = dest
                continue
            seen = loops.get(dest, 0)
            if dest <= pos and seen >= loop_passes:
                yield (tick, ("loop",))
                return
            loops[dest] = seen + 1
            pos = dest
            continue
        if cmd == 0xB4:
            pos = stack.pop() if stack else pos + 1
            continue
        if cmd == 0xB5:
            pos += 6
            continue
        if cmd == 0xB9:
            pos += 8 if pos + 1 < end and rom[pos + 1] >= 6 else 4
            continue
        if cmd in FIXED_ONE_ARG:
            if cmd == 0xBB and pos + 1 < end:
                yield (tick, ("tempo", rom[pos + 1]))
            pos += 2
            continue
        if cmd in REPEATABLE_MAXARGS and cmd not in (0xCE, 0xCF):
            if pos + 1 < end and rom[pos + 1] < 0x80:
                if cmd == 0xBD:
                    voice = rom[pos + 1]
                elif cmd == 0xBE:
                    yield (tick, ("vol", rom[pos + 1]))
                last_rep = (cmd, REPEATABLE_MAXARGS[cmd])
            pos += 2
            continue
        if cmd in (0xCE, 0xCF):
            pos += 1
            got = args(REPEATABLE_MAXARGS[cmd])
            yield (tick, strike(cmd, got) if cmd == 0xCF else release(got))
            last_rep = (cmd, REPEATABLE_MAXARGS[cmd])
            continue
        if cmd == 0xCD:
            pos += 3
            continue
        return


# PSG reconstruction aids (approximate engine behavior; see AUDIO-RECON.md).
# Duty patterns are the exact GBA 8-step hardware patterns, time-ordered
# (GbdevWiki; Bregalad's Sappy notes). Pitch uses equal temperament from
# A4 = 440 Hz, matching the documented C4 = 261.6 Hz mapping point.
DUTY_PATTERNS = (
    (0, 0, 0, 0, 0, 0, 0, 1),  # 12.5%
    (1, 0, 0, 0, 0, 0, 0, 1),  # 25%
    (1, 0, 0, 0, 0, 1, 1, 1),  # 50%
    (0, 1, 1, 1, 1, 1, 1, 0),  # 75%
)


def psg_tone_freq(midi_key, wave_channel=False):
    """Approximate PSG tone in Hz for a MIDI note key (equal temperament).

    The engine maps keys through MidiKeyToCgbFreq tables; this matches its
    documented C4 calibration (261.6 Hz square, one octave down on wave).
    """
    freq = 440.0 * 2 ** ((midi_key - 69) / 12)
    return freq / 2 if wave_channel else freq


def sampled_envelope(attack, decay, sustain, release, frames):
    """Approximate per-frame gain for sampled-voice ADSR bytes.

    Reference endpoints (Bregalad): attack 0xFF = instant, 0x01 longest;
    decay 0 = none; sustain scales silence..full; release 0 = hard cut.
    Attack ramps linearly, decay/release fall multiplicatively toward the
    sustain floor, all scaled to the note length. The raw preset
    (0xFF, 0, 0xFF, 0) yields unity gain. Engine integer timing is not
    reproduced; this is a reconstruction aid, not a cycle proof.
    """
    if frames <= 0:
        return []
    floor = sustain / 255
    attack_len = int(frames * (0xFF - attack) / 0xFF * 0.5)
    release_len = int(frames * release / 0xFF * 0.5)
    body = max(0, frames - attack_len - release_len)
    decay_rate = 0.0 if decay == 0 else decay / 0xFF
    gains = [(i + 1) / attack_len for i in range(attack_len)]
    level = gains[-1] if gains else 1.0
    for _ in range(body):
        level = floor + (level - floor) * (1.0 - decay_rate * 0.25)
        gains.append(level)
    for i in range(release_len):
        tail = gains[-1] if gains else level
        gains.append(tail * (1.0 - (i + 1) / release_len))
    return gains[:frames] + [gains[-1]] * max(0, frames - len(gains))


def iter_songs(rom, table_offset, count, rom_base=ROM_BASE):
    """Yield (index, song header) over a song table of 8-byte entries,
    dereferencing each entry's song pointer."""
    for i in range(count):
        song = _u32(rom, table_offset + 8 * i) - rom_base
        yield i, decode_song_header(rom, song)


def parse_track(rom, start, rom_base=ROM_BASE, budget=20000):
    """Structurally parse one MP2k track.

    Returns {"ok": True, "fine": bool} when the byte stream is a valid
    command sequence ending in FINE (fine True) or a bounded control loop
    (fine False). Returns {"ok": False, "why": str, "at": int} otherwise.
    Pure: reads only, never mutates.
    """
    size = len(rom)
    end = min(start + 4096, size)
    pos = start
    last_rep = None
    stack = []
    seen = set()
    steps = 0
    while steps < budget:
        steps += 1
        if not (0 <= pos < len(rom) and start <= pos < end):
            return {"ok": False, "why": "oob", "at": pos}
        key = (pos, len(stack), last_rep[0] if last_rep else -1)
        if key in seen:
            return {"ok": True, "fine": False}
        seen.add(key)
        cmd = rom[pos]
        if cmd < 0x80:
            if last_rep is None:
                return {"ok": False, "why": "bare-no-status", "at": pos}
            _, need = last_rep
            nxt = pos + 1
            for _ in range(need - 1):
                if nxt < end and rom[nxt] < 0x80:
                    nxt += 1
                else:
                    break
            pos = nxt
            continue
        if 0x80 <= cmd <= 0xB0:  # W00-W96 waits
            pos += 1
            continue
        if NOTE_MIN <= cmd <= NOTE_MAX:  # notes, 0-3 trailing args
            nxt = pos + 1
            taken = 0
            while taken < 3 and nxt < end and rom[nxt] < 0x80:
                nxt += 1
                taken += 1
            last_rep = (cmd, 3)
            pos = nxt
            continue
        if cmd == 0xB1:  # FINE
            return {"ok": True, "fine": True}
        if cmd in (0xB2, 0xB3):  # GOTO / PATT
            if pos + 5 > end:
                return {"ok": False, "why": "trunc-addr", "at": pos}
            dest = _u32(rom, pos + 1) - rom_base
            if not (0 <= dest < size):
                return {"ok": False, "why": "bad-addr", "at": pos}
            if cmd == 0xB3:
                if len(stack) >= 4:
                    return {"ok": False, "why": "deep-patt", "at": pos}
                stack.append(pos + 5)
            pos = dest
            continue
        if cmd == 0xB4:  # PEND: pop, or assumed no-op at top level
            if not stack:
                pos += 1
                continue
            pos = stack.pop()
            continue
        if cmd == 0xB5:  # REPT count + address
            if pos + 6 > end or rom[pos + 1] >= 0x80:
                return {"ok": False, "why": "bad-rept", "at": pos}
            dest = _u32(rom, pos + 2) - rom_base
            if not (0 <= dest < size):
                return {"ok": False, "why": "bad-addr", "at": pos}
            pos += 6
            continue
        if cmd == 0xB9:  # MEMACC
            if pos + 4 > end or any(rom[pos + i] >= 0x80 for i in (1, 2, 3)):
                return {"ok": False, "why": "bad-memacc", "at": pos}
            if rom[pos + 1] > 17:
                return {"ok": False, "why": "bad-memacc", "at": pos}
            if rom[pos + 1] >= 6:
                if pos + 8 > end:
                    return {"ok": False, "why": "trunc-addr", "at": pos}
                dest = _u32(rom, pos + 4) - rom_base
                if not (0 <= dest < size):
                    return {"ok": False, "why": "bad-addr", "at": pos}
                pos += 8
            else:
                pos += 4
            continue
        if cmd in FIXED_ONE_ARG:
            if pos + 2 > end or rom[pos + 1] >= 0x80:
                return {"ok": False, "why": "bad-arg", "at": pos}
            pos += 2
            continue
        if cmd in REPEATABLE_MAXARGS and cmd not in (0xCE, 0xCF):
            if pos + 2 > end or rom[pos + 1] >= 0x80:
                return {"ok": False, "why": "bad-arg", "at": pos}
            last_rep = (cmd, REPEATABLE_MAXARGS[cmd])
            pos += 2
            continue
        if cmd in (0xCE, 0xCF):  # EOT / TIE, optional args
            need = REPEATABLE_MAXARGS[cmd]
            nxt = pos + 1
            taken = 0
            while taken < need and nxt < end and rom[nxt] < 0x80:
                nxt += 1
                taken += 1
            last_rep = (cmd, need)
            pos = nxt
            continue
        if cmd == 0xCD:  # XCMD sub-command + argument
            if pos + 3 > end or rom[pos + 1] >= 0x80 or rom[pos + 2] >= 0x80:
                return {"ok": False, "why": "bad-xcmd", "at": pos}
            pos += 3
            continue
        return {"ok": False, "why": "undef-%02X" % cmd, "at": pos}
    return {"ok": False, "why": "steps", "at": pos}
