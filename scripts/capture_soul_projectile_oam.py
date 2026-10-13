"""Native OAM + OBJ-palette capture for the Winged Skeleton cast (private).

One fresh-core run repeats the verified opening + menu + one Up+B cast, then
captures OAM (0x07000000, 1 KB) and OBJ palette (0x05000200, 512 B) at baseline,
mid-flight (slots 2–3 live) and post-despawn (both code words clear). Bytes
that change mid-flight and revert post-despawn are projectile-render
candidates; bytes that stay changed are other scene churn (e.g. Soma idle).

Read-only: no ROM writes, no authoring. Candidates are not proven OAM/palette
ownership — entry-to-actor binding stays open. Outputs stay under local/.
Original ROM is never modified.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aria.soul_projectiles import diff_bytes, snapshot_actor_window
from emulator import Emulator

EXPECTED_COST = 12
OAM_ADDRESS = 0x07000000
OAM_SIZE = 1024
OBJ_PALETTE_ADDRESS = 0x05000200
OBJ_PALETTE_SIZE = 512


def entries_changed(before, after):
    """Return OAM entry indices (8 bytes each) with any changed byte."""
    return [entry for entry in range(OAM_SIZE // 8)
            if before[entry * 8:(entry + 1) * 8] != after[entry * 8:(entry + 1) * 8]]


def main():
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    e = Emulator(host)
    try:
        e.run(1000)
        for key in [3, 8, 8, 8, 3, 3, 8]:
            e.run(1, [key])
            e.run(100)
        for _ in range(60):
            e.run(1, [8])
            e.run(90)
        assert e.read(0x0201331C, 1) == 1 and e.read(0x02013269, 1) == 1
        e.run(1, [3])
        e.run(30)
        e.run(1, [8])
        e.run(30)
        assert e.read(0x02000064, 1) == 6
        for key in [0, 0]:
            e.run(1, [key])
            e.run(30)
        assert e.read(0x02000064, 1) == 1 and e.read(0x020004EE, 1) == 0
        mp_pre = e.read(0x0201327C, 2)
        base_oam = e.bytes(OAM_ADDRESS, OAM_SIZE)
        base_pal = e.bytes(OBJ_PALETTE_ADDRESS, OBJ_PALETTE_SIZE)
        e.run(30)
        ctrl_oam = e.bytes(OAM_ADDRESS, OAM_SIZE)
        ctrl_pal = e.bytes(OBJ_PALETTE_ADDRESS, OBJ_PALETTE_SIZE)
        e.run(1, [4, 0])
        e.run(6)
        assert mp_pre - e.read(0x0201327C, 2) == EXPECTED_COST
        e.run(1)
        e.run(22)
        mid_snap = snapshot_actor_window(e.read)
        assert 2 in mid_snap and 3 in mid_snap, 'projectile slots not live at mid-flight'
        mid_oam = e.bytes(OAM_ADDRESS, OAM_SIZE)
        mid_pal = e.bytes(OBJ_PALETTE_ADDRESS, OBJ_PALETTE_SIZE)
        post_oam = post_pal = None
        for _ in range(40):
            e.run(2)
            snap = snapshot_actor_window(e.read)
            if 2 not in snap and 3 not in snap:
                post_oam = e.bytes(OAM_ADDRESS, OAM_SIZE)
                post_pal = e.bytes(OBJ_PALETTE_ADDRESS, OBJ_PALETTE_SIZE)
                break
        assert post_oam is not None, 'projectile slots never cleared'
        oam_mid = diff_bytes(base_oam, mid_oam)
        oam_post = diff_bytes(base_oam, post_oam)
        oam_ctrl = diff_bytes(base_oam, ctrl_oam)
        pal_mid = diff_bytes(base_pal, mid_pal)
        pal_post = diff_bytes(base_pal, post_pal)
        pal_ctrl = diff_bytes(base_pal, ctrl_pal)
        ctrl_set = set(oam_ctrl['changed'])
        cast_specific = sorted(set(oam_mid['changed']) - ctrl_set)
        pal_cast_specific = sorted(set(pal_mid['changed']) - set(pal_ctrl['changed']))
        mid_set, post_set = set(oam_mid['changed']), set(oam_post['changed'])
        reverted = sorted(mid_set - post_set)
        persistent = sorted(mid_set & post_set)
        reverted_ranges = []
        for offset in reverted:
            if reverted_ranges and offset == reverted_ranges[-1]['start'] + reverted_ranges[-1]['length']:
                reverted_ranges[-1]['length'] += 1
            else:
                reverted_ranges.append({'start': offset, 'length': 1})
        pal_mid_set, pal_post_set = set(pal_mid['changed']), set(pal_post['changed'])
        pal_reverted = sorted(pal_mid_set - pal_post_set)
        report = {
            'route': 'verified opening + soul menu open/close + one Up+B cast; OAM/palette at baseline/mid/post',
            'oam': {
                'sha256': {'baseline': hashlib.sha256(base_oam).hexdigest(),
                           'mid': hashlib.sha256(mid_oam).hexdigest(),
                           'post': hashlib.sha256(post_oam).hexdigest()},
                'changed_mid_count': oam_mid['count'],
                'changed_post_count': oam_post['count'],
                'mid_changed_entries': entries_changed(base_oam, mid_oam),
                'reverted_entry_candidates': entries_changed(base_oam, mid_oam)
                if post_oam == base_oam else [entry for entry in entries_changed(base_oam, mid_oam)
                                              if entry not in entries_changed(base_oam, post_oam)],
                'reverted_byte_count': len(reverted),
                'persistent_byte_count': len(persistent),
                'reverted_ranges': reverted_ranges,
                'control_changed_count': oam_ctrl['count'],
                'control_changed_entries': entries_changed(base_oam, ctrl_oam),
                'cast_specific_byte_count': len(cast_specific),
                'cast_specific_entries': sorted({offset // 8 for offset in cast_specific}),
            },
            'obj_palette': {
                'sha256': {'baseline': hashlib.sha256(base_pal).hexdigest(),
                           'mid': hashlib.sha256(mid_pal).hexdigest(),
                           'post': hashlib.sha256(post_pal).hexdigest()},
                'changed_mid_count': pal_mid['count'],
                'changed_post_count': pal_post['count'],
                'control_changed_count': pal_ctrl['count'],
                'cast_specific_count': len(pal_cast_specific),
                'cast_specific_offsets': pal_cast_specific[:64],
                'cast_specific_truncated': len(pal_cast_specific) > 64,
                'reverted_byte_count': len(pal_reverted),
                'reverted_offsets': pal_reverted[:64],
                'reverted_truncated': len(pal_reverted) > 64,
            },
            'scope': ('a 30-frame no-cast control isolates cast-caused bytes; nothing '
                      'reverts post-despawn, so candidates rest on the control, not on unloading'),
            'original_unchanged': host.read_bytes() == original,
            'rom_sha256': hashlib.sha256(original).hexdigest(),
            'limits': [
                'one cast, one room, one direction, one run',
                'stale OAM/palette persist after despawn: no unload observed, binding by control only',
                'no tile/VRAM-art, priority/affine semantic or actor-to-entry proof',
            ],
        }
        (ROOT / 'local/soul-projectile-oam.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps({k: report[k] for k in ('oam', 'obj_palette', 'scope', 'limits')}, indent=2))
    finally:
        e.close()
        assert host.read_bytes() == original


if __name__ == '__main__':
    main()
