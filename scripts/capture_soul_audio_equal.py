"""Equal-length idle/cast audio windows with a BGM-phase control (private).

Opening room, controller-only, one fresh core: two consecutive 60-frame idle
captures (A, B) then one verified Up+B cast with a 60-frame capture (C). All
windows are the same length at the same position, unlike the exploratory
60-vs-7 windows in scripts/trace_soul_projectile.py. Route and menu sequence
mirror that verified trace exactly.

Verdict logic: A-vs-B measures BGM-phase self-difference; A-vs-C measures
cast difference. A cast-attributed effect needs the cast RMS clearly above
both idle RMS values. Without a lawful BGM mute this is still mixed-output
evidence, not SFX proof.

Read-only: no ROM writes, no authoring. Outputs stay under local/. Original
ROM is never modified.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT))
from aria.soul_projectiles import compare_audio_windows
from emulator import Emulator

FRAMES = 60
EXPECTED_COST = 12


def boot_to_owned_soul(e):
    e.run(1000)
    for key in [3, 8, 8, 8, 3, 3, 8]:
        e.run(1, [key])
        e.run(100)
    for _ in range(60):
        e.run(1, [8])
        e.run(90)
    assert e.read(0x0201331C, 1) == 1, 'first red soul not owned after opening'
    assert e.read(0x02013269, 1) == 1, 'winged skeleton not equipped after opening'


def open_and_close_soul_menu(e):
    e.run(1, [3])
    e.run(30)
    e.run(1, [8])
    e.run(30)
    assert e.read(0x02000064, 1) == 6, 'soul menu did not open'
    for key in [0, 0]:
        e.run(1, [key])
        e.run(30)
    assert e.read(0x02000064, 1) == 1 and e.read(0x020004EE, 1) == 0


def capture(e, frames):
    e.start_audio_capture(120000)
    e.run(frames)
    return e.stop_audio_capture()


def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    e = Emulator(host)
    try:
        boot_to_owned_soul(e)
        open_and_close_soul_menu(e)
        idle_a = capture(e, FRAMES)
        idle_b = capture(e, FRAMES)
        mp_pre = e.read(0x0201327C, 2)
        e.start_audio_capture(120000)
        e.run(1, [4, 0])
        e.run(FRAMES - 1)
        cast_c = e.stop_audio_capture()
        spent = mp_pre - e.read(0x0201327C, 2)
        control = compare_audio_windows(idle_a, idle_b)
        effect = compare_audio_windows(idle_a, cast_c)
        # Net spend allows a small regen bound: MP regenerates during the
        # 60-frame window, so a fired cast can read back as 11, not 12.
        fired = EXPECTED_COST - 2 <= spent <= EXPECTED_COST
        cast_above = (effect['second_peak'] > 1.5 * control['second_peak']
                      and effect['second_rms'] > 1.5 * control['second_rms'])
        report = {
            'route': 'opening room; 60-frame idle A, idle B, then verified cast C',
            'frames_per_window': FRAMES,
            'mp_spent': spent,
            'cast_fired': fired,
            'control_idle_vs_idle': control,
            'effect_idle_vs_cast': effect,
            'verdict': ('cast-attributed audio difference (mixed output, not isolated SFX)'
                        if fired and cast_above
                        else 'BGM-phase dominates or cast fizzled; no SFX isolation'),
            'original_unchanged': host.read_bytes() == original,
            'rom_sha256': hashlib.sha256(original).hexdigest(),
            'limits': ['mixed BGM+SFX output; no mute control; opening room only'],
        }
    finally:
        e.close()
    (ROOT / 'local/soul-audio-equal.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    assert host.read_bytes() == original


if __name__ == '__main__':
    main()
