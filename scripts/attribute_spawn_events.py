"""Private spawn-anchored twin attribution for walker art page 0x08635990.

Kill-then-respawn protocol with no OAM-map dependence: boots the hallway,
HP-zeroes observed Zombie slots (declared fixture, same class as prior
harnesses), waits for a respawn (first live Zombie slot reappearance via
EWRAM only), and captures snapshot windows before/after the spawn frame.
Runs original/original (control determinism) and original/magenta-diagnostic
(twin) pairs; only rendered consumers can differ.

Builds the diagnostic by importing trace_sprite_consumers.build_diagnostic
(all three page copies repointed + palette magenta). Outputs stay under
local/; nothing here ships as a production writer entry.
"""
import hashlib
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
from aria.cli import load_image
from aria.sprite_attribution import diff_scenes
from aria.tables import read_record
from emulator import Emulator
from probe_actor_binding import boot, zombie_slots
from trace_sprite_consumers import build_diagnostic

PRE_KEEP = 10
POST_FRAMES = 20
POST_STEP = 3
RESPAWN_BUDGET = 900


def live_slots(e, update):
    return [s for s in zombie_slots(e, update) if e.read(s + 0x34, 2) > 0]


def world_x(e):
    return (e.read(0x02000526, 2) + e.read(0x0200A09A, 2)) & 0xFFFF


def run_spawn_capture(path, update):
    e = Emulator(path)
    try:
        boot(e)
        assert e.read(0x02000088) == 0x0850F15C
        for _ in range(40):
            for s in zombie_slots(e, update):
                e.write(s + 0x34, 0, 2)
            e.run(10)
            if not live_slots(e, update):
                break
        assert not live_slots(e, update), 'Kill fixture did not clear live slots'
        ring = []
        spawn_frame = None
        for frame in range(RESPAWN_BUDGET):
            e.run(1)
            if frame % 3 == 0:
                ring.append(e.image.tobytes())
                if len(ring) > PRE_KEEP:
                    ring.pop(0)
            if live_slots(e, update):
                spawn_frame = frame
                break
        assert spawn_frame is not None, 'No respawn within budget'
        pre = list(ring)
        post = []
        for _ in range(POST_FRAMES):
            e.run(POST_STEP)
            post.append(e.image.tobytes())
        return {
            'spawn_frame': spawn_frame,
            'pre': pre,
            'post': post,
            'world_x': world_x(e),
            'live_count': len(live_slots(e, update)),
        }
    finally:
        e.close()


def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    rom = load_image(host)
    update = read_record(rom, 'enemies', 1)['update_code']
    diag, build = build_diagnostic(host)
    a = run_spawn_capture(host, update)
    b = run_spawn_capture(host, update)
    control = diff_scenes({'spawn_pre': a['pre'], 'spawn_post': a['post']},
                          {'spawn_pre': b['pre'], 'spawn_post': b['post']})
    control_deterministic = (
        all(v['differing_frames'] == 0 for v in control.values())
        and a['spawn_frame'] == b['spawn_frame'])
    t = run_spawn_capture(diag, update)
    assert len(t['pre']) == len(a['pre']) and len(t['post']) == len(a['post'])
    twin = diff_scenes({'spawn_pre': a['pre'], 'spawn_post': a['post']},
                       {'spawn_pre': t['pre'], 'spawn_post': t['post']})
    assert host.read_bytes() == original
    report = dict(
        status='spawn_anchored_attribution_complete',
        host_sha256=hashlib.sha256(original).hexdigest(),
        diagnostic_sha256=hashlib.sha256(diag.read_bytes()).hexdigest(),
        build=build,
        spawn_frames=dict(control_a=a['spawn_frame'], control_b=b['spawn_frame'], test=t['spawn_frame']),
        world_x=dict(control_a=a['world_x'], control_b=b['world_x'], test=t['world_x']),
        control_deterministic=bool(control_deterministic),
        control=control,
        twin=twin,
        fixtures=['HP zeroed in observed Zombie slots, then waited for EWRAM-observed respawn; no graphics/OAM/palette/tile writes'],
        limitations=['One hallway spawner and respawn path only; other rooms/actors unproven',
                     'Sibling-page tiles, shared lists and palette-copy users outside this window stay unproven'])
    (ROOT / 'local/spawn-attribution.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
