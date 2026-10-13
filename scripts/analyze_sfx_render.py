"""Determinism + spectral listening guide for the SFX 0xe4 render (diagnostic).

21st slice rendered the mapped soul-cast voice to local/sfx-0e4-render.wav
but left the ear check open. This probe (1) re-runs scripts/render_sfx_0e4.py
and requires a byte-identical WAV (determinism), (2) characterizes the render
with stdlib-only signal metrics (peak/RMS, crest, zero-crossing rate, onset
and -20 dB decay times, spectral centroid and band energies via a small
radix-2 FFT), and (3) writes a concrete listening guide so the operator's
ear check takes seconds: what to play, what to expect, what confirms or
falsifies the mapping.

Read-only on the ROM. Outputs stay under local/. Original ROM is never
modified. No audio is played by this probe.
"""
import hashlib
import json
import math
import struct
import subprocess
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WAV = ROOT / 'local/sfx-0e4-render.wav'
RENDER_SCRIPT = ROOT / 'scripts/render_sfx_0e4.py'


def fft(values):
    n = len(values)
    if n == 1:
        return values
    even = fft(values[0::2])
    odd = fft(values[1::2])
    return [even[k] + odd[k] * complex(math.cos(-2 * math.pi * k / n),
                                      math.sin(-2 * math.pi * k / n))
            for k in range(n // 2)] + \
           [even[k] - odd[k] * complex(math.cos(-2 * math.pi * k / n),
                                      math.sin(-2 * math.pi * k / n))
            for k in range(n // 2)]


def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    before = hashlib.sha256(WAV.read_bytes()).hexdigest()
    proc = subprocess.run([sys.executable, str(RENDER_SCRIPT)],
                          capture_output=True, text=True, cwd=str(ROOT))
    assert proc.returncode == 0, 'render rerun failed: ' + proc.stderr[-500:]
    after = hashlib.sha256(WAV.read_bytes()).hexdigest()
    deterministic = before == after

    with wave.open(str(WAV), 'rb') as wav:
        rate = wav.getframerate()
        frames = wav.readframes(wav.getnframes())
    samples = [v / 32768 for v in struct.unpack('<%dh' % (len(frames) // 2), frames)]
    duration = len(samples) / rate
    peak = max(abs(v) for v in samples)
    rms = math.sqrt(sum(v * v for v in samples) / len(samples))
    crest = peak / rms if rms > 0 else 0.0
    zc = sum(1 for a, b in zip(samples, samples[1:]) if (a < 0) != (b < 0)) / duration
    env_n = max(1, rate // 100)
    env = [max(abs(v) for v in samples[i:i + env_n]) or 1e-9
           for i in range(0, len(samples), env_n)]
    onset = next((i * env_n / rate for i, e in enumerate(env) if e >= 0.1 * peak), 0.0)
    peak_t = max(range(len(env)), key=lambda i: env[i]) * env_n / rate
    decay = next((i * env_n / rate - peak_t for i in range(len(env))
                  if env[i] <= 0.1 * peak and i * env_n / rate > peak_t), duration - peak_t)
    size = 1
    while size < len(samples):
        size *= 2
    spectrum = [abs(c) for c in fft([complex(v, 0) for v in samples] + [0j] * (size - len(samples)))]
    half = spectrum[:size // 2]
    total = sum(half) or 1e-9
    centroid = sum(i * rate / size * m for i, m in enumerate(half)) / total
    bands = [(0, 500), (500, 2000), (2000, 8000), (8000, rate // 2)]
    band_energy = {('%d-%dHz' % lohi): sum(m for i, m in enumerate(half)
                                           if lo <= i * rate / size < hi) / total
                   for lohi, (lo, hi) in [((lo, hi), (lo, hi)) for lo, hi in bands]}
    brightest = max(band_energy, key=band_energy.get)
    report = {
        'wav': 'local/sfx-0e4-render.wav',
        'wav_sha256': after,
        'deterministic_rerun': deterministic,
        'metrics': {'duration_s': duration, 'peak': peak, 'rms': rms,
                    'crest': crest, 'zero_cross_per_s': zc,
                    'onset_s': onset, 'peak_t_s': peak_t, 'decay_to_m20db_s': decay,
                    'spectral_centroid_hz': centroid, 'band_energy': band_energy,
                    'brightest_band': brightest},
        'listening_guide': {
            'play': 'local/sfx-0e4-render.wav (0.55 s mono 32768 Hz)',
            'expect': 'transient burst starting at ~%.3f s, brightest %s, centroid ~%.0f Hz' % (
                onset, brightest, centroid),
            'confirms_mapping': 'a short percussive whoosh/pop unlike the BGM bed',
            'falsifies_mapping': 'silence, a pure steady tone, or obvious looping clicks',
        },
        'verdict': ('render deterministic and characterized; operator ear check is now a seconds-long listen'
                    if deterministic else 'render NOT deterministic; mapping suspect'),
        'original_unchanged': host.read_bytes() == original,
        'rom_sha256': hashlib.sha256(original).hexdigest(),
        'limits': ['diagnostic renderer metrics, not a mixer/hardware model',
                   'centroid/bands describe the render, not the native mix'],
    }
    (ROOT / 'local/sfx-0e4-listen.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    assert host.read_bytes() == original
    assert deterministic, 'WAV changed across reruns'


if __name__ == '__main__':
    main()
