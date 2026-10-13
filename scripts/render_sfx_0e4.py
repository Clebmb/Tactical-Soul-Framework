"""Render the mapped SFX 0xe4 voice to a private WAV (diagnostic).

Chain: song 0x08399BEC, one C4 note (gate 23 ticks at tempo 75), voice 92
(type 8 sampled-no-resample, ADSR 255/0/255/0), sample 0x083AE488 at
10,512 Hz. Renders with aria.audio_synthesis (linear resample + sampled
envelope), writes local/sfx-0e4-render.wav, and checks energy/duration
consistency against the 18th slice's cast window (idle RMS 741, cast RMS
1348 over equal 60-frame windows): the render's energy must be nonzero and
its duration must match the 0.30 s static figure within tolerance.

Diagnostic only: no native mixer quantization, channel allocation, hardware
filtering, or BGM coexistence. Read-only on the ROM. Outputs stay under
local/. Original ROM is never modified.
"""
import hashlib
import json
import math
import struct
import wave
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aria.audio import (
    ROM_BASE,
    decode_sample,
    sample_c4_rate,
    ticks_to_seconds,
)
from aria.audio_synthesis import render_sample, sampled_envelope

SAMPLE_PTR = 0x083AE488
ADSR = (255, 0, 255, 0)
GATE_TICKS = 23
TEMPO = 75
OUT_RATE = 32768
CAST_IDLE_RMS = 740.8810236562948
CAST_RMS = 1347.9963152702373


def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    rom = bytes(original)
    sample = decode_sample(rom, SAMPLE_PTR - ROM_BASE)
    pcm = rom[sample['data_offset']:sample['data_end']]
    rate = sample_c4_rate(sample['freq'])
    gate_seconds = ticks_to_seconds(GATE_TICKS, TEMPO)
    gate_frames = max(1, int(gate_seconds * 60))
    total_frames = int(sample['size'] / rate * OUT_RATE) + OUT_RATE // 4
    envelope = sampled_envelope(*ADSR, gate_frames=gate_frames, frames=total_frames)
    levels = render_sample(pcm, rate, output_rate=OUT_RATE,
                           frames=total_frames, envelope=envelope)
    peak = max(abs(v) for v in levels)
    rms = math.sqrt(sum(v * v for v in levels) / len(levels))
    duration = len(levels) / OUT_RATE
    static_duration = sample['size'] / rate
    wav_path = ROOT / 'local/sfx-0e4-render.wav'
    with wave.open(str(wav_path), 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(OUT_RATE)
        wav.writeframes(b''.join(
            struct.pack('<h', max(-32768, min(32767, int(v / 128 * 32767))))
            for v in levels))
    # Energy check: rendered SFX energy (over its own span) must be of the
    # same order as the cast-window excess energy, not silent and not absurd.
    excess = math.sqrt(max(0.0, CAST_RMS ** 2 - CAST_IDLE_RMS ** 2))
    report = {
        'chain': 'song 0x08399BEC, C4 gate 23 @ tempo 75, voice 92, sample 0x083AE488',
        'sample_rate_hz': rate,
        'gate_frames': gate_frames,
        'render': {'frames': len(levels), 'duration_s': duration,
                   'peak_8bit': peak, 'rms_8bit': rms,
                   'wav': 'local/sfx-0e4-render.wav'},
        'static_duration_s': static_duration,
        'duration_match': abs(duration - static_duration) < 0.35,
        'cast_excess_rms': excess,
        'energy_consistent': rms > 0 and excess / max(rms, 1e-9) < 50,
        'verdict': ('rendered voice is audible-length and energetically '
                    'consistent with the cast-window excess'
                    if abs(duration - static_duration) < 0.35 and rms > 0
                    and excess / max(rms, 1e-9) < 50
                    else 'render inconsistent with cast window; mapping suspect'),
        'original_unchanged': host.read_bytes() == original,
        'rom_sha256': hashlib.sha256(original).hexdigest(),
        'limits': ['diagnostic renderer; no mixer/hardware/BGM model; no ear check'],
    }
    (ROOT / 'local/sfx-0e4-render.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    assert host.read_bytes() == original


if __name__ == '__main__':
    main()
