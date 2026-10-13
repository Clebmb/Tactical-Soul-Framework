"""Trace soul spawn SFX 0xe4 to song, voices and samples (static, private).

Chain (see docs/SOUL-DECOMPILE.md): soul state 0 calls global dispatcher
FUN_080d7910(0xe4); 0xe4 < threshold 0x3FF takes FUN_080d73b8; SFX table at
0x0827CD38 holds 8-byte entries; entry 0xe4 points at song 0x08399BEC.
This probe decodes that song header, its tracks/events, the voicegroup
voices behind the played notes, and the sample rates/durations.

Read-only: no ROM writes, no authoring, no emulation. Outputs stay under
local/. Original ROM is never modified.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aria.audio import (
    ROM_BASE,
    decode_song_header,
    decode_voice_entry,
    decode_sample,
    iter_events,
    parse_track,
    resolve_note_voice,
    sample_c4_duration,
    sample_c4_rate,
)

SFX_ID = 0xE4
SFX_TABLE = 0x0827CD38
SONG_PTR = 0x08399BEC


def to_offset(ptr):
    if not 0x08000000 <= ptr < 0x0A000000:
        raise ValueError('pointer outside ROM image: %s' % hex(ptr))
    return ptr - ROM_BASE


def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    rom = bytes(original)
    table_off = to_offset(SFX_TABLE)
    entry_off = table_off + SFX_ID * 8
    entry_song = int.from_bytes(rom[entry_off:entry_off + 4], 'little')
    entry_chan = int.from_bytes(rom[entry_off + 4:entry_off + 6], 'little')
    assert entry_song == SONG_PTR, (hex(entry_song), hex(SONG_PTR))
    header = decode_song_header(rom, to_offset(SONG_PTR))
    tracks = []
    for track_ptr in header['track_pointers']:
        parsed = parse_track(rom, to_offset(track_ptr))
        events = list(iter_events(rom, to_offset(track_ptr))) if parsed.get('ok') else []
        tracks.append({
            'track_ptr_hex': hex(track_ptr),
            'parse': parsed,
            'event_count': len(events),
            'events': events[:16],
            'truncated': len(events) > 16,
        })
    bank_off = to_offset(header['voicegroup'])
    notes = []
    for track in tracks:
        for tick, payload in track['events']:
            if (isinstance(payload, (list, tuple)) and payload
                    and payload[0] == 'note' and len(payload) == 5):
                notes.append({'tick': tick, 'key': payload[1],
                              'velocity': payload[2], 'voice': payload[3],
                              'gate': payload[4]})
    voices = {}
    for note in notes:
        voice = note['voice']
        if voice not in voices:
            try:
                voices[voice] = {
                    'entry': decode_voice_entry(rom, bank_off + voice * 12),
                    'resolved': resolve_note_voice(
                        rom, bank_off, voice, note['key']),
                }
            except ValueError as exc:
                voices[voice] = {'error': str(exc)}
    samples = {}
    for index, voice in voices.items():
        entry = voice.get('entry', {}) if isinstance(voice, dict) else {}
        if isinstance(entry, dict) and 'sample' in entry:
            voice = entry
            try:
                sample = decode_sample(rom, to_offset(voice['sample']))
                rate = sample_c4_rate(sample['freq'])
                samples[index] = {
                    'sample_ptr_hex': hex(voice['sample']),
                    'voice_kind': voice['kind'],
                    'c4_rate_hz': rate,
                    'duration_s': sample_c4_duration(sample.get('freq'), sample.get('size', 0))
                    if sample.get('freq') and sample.get('size') else None,
                }
            except (ValueError, KeyError) as exc:
                samples[index] = {'error': str(exc)}
    report = {
        'sfx_id_hex': hex(SFX_ID),
        'dispatch': 'FUN_080d7910 -> FUN_080d73b8 (0xe4 < threshold 0x3FF)',
        'sfx_table_hex': hex(SFX_TABLE),
        'entry': {'song_ptr_hex': hex(entry_song), 'channel': entry_chan},
        'song_ptr_hex': hex(SONG_PTR),
        'song_header': {**header,
                        'voicegroup_hex': hex(header['voicegroup']),
                        'track_pointers_hex': [hex(p) for p in header['track_pointers']]},
        'tracks': tracks,
        'notes': notes,
        'voices': {str(k): v for k, v in voices.items()},
        'samples': {str(k): v for k, v in samples.items()},
        'original_unchanged': host.read_bytes() == original,
        'rom_sha256': hashlib.sha256(original).hexdigest(),
        'limits': ['static decode only; no audible render or native play proof'],
    }
    (ROOT / 'local/sfx-0e4.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2)[:3000])
    assert host.read_bytes() == original


if __name__ == '__main__':
    main()
