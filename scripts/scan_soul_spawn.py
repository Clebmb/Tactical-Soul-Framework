"""Diagnostic actor-table scan for soul-crystal spawns while killing hallway zombies.

Builds a throwaway probe ROM (zombie soul rarity set, item drops disabled),
walks to the zombie room with controller input only, records calm-phase actor
codes, then kill-loops while logging kill-aligned novel codes. Reports whether
any novel code first appears at a kill transition and persists.

Established boundary (2026-10-11, two rarities): the only attack-correlated
code is Soma's slash effect 0x80221cd (absent without attack input); kills
produce no kill-correlated persistent novel actor. Soul-crystal spawns are not
observable in this enemy actor window, and collection/grant remains uncertified:
no soul-inventory RAM address or menu proof exists. No graphics, palette,
position, HP or RNG writes; the original ROM is unchanged.
"""
import argparse, sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aria.cli import load_image
from aria.cli import apply_manifest_data
from aria.enemies import resolve as resolve_enemy
from emulator import Emulator

BASE = 0x020004E4
STRIDE = 0x84
SLOTS = 224
VICTIMS = {
    'zombie': {'room': 0x0850F15C, 'route': 'natural'},
    'skeleton': {'room': 0x0850F32C, 'route': 'workshop-shortcut'},
}
VICTIM_EDITS = {
    'zombie': [{'enemy': 'zombie',
                'expect': {'soul_rarity': 180, 'item_1': 93, 'item_1_rarity': 20,
                           'item_2': 34, 'item_2_rarity': 30}}],
    'skeleton': [{'enemy': 'skeleton',
                  'expect': {'soul_rarity': 8, 'item_1': 0, 'item_1_rarity': 10,
                             'item_2': 0, 'item_2_rarity': 30}},
                 {'enemy': 'zombie',
                  'expect': {'item_1': 93, 'item_1_rarity': 20,
                             'item_2': 34, 'item_2_rarity': 30}}],
}


def snapshot(e):
    out = {}
    for j in range(SLOTS):
        c = e.read(BASE + j * STRIDE)
        if c:
            out.setdefault(hex(c), []).append(j)
    return out


def main():
    args = argparse.ArgumentParser(description='Scan for soul-spawn actor codes')
    args.add_argument('--rarity', type=int, default=255)
    args.add_argument('--rolls', type=int, default=150)
    args.add_argument('--enemy', choices=sorted(VICTIMS), default='zombie')
    args.add_argument('--out', type=Path, default=ROOT / 'local/soul-scan.json')
    opts = args.parse_args()
    if not 0 <= opts.rarity <= 255:
        raise SystemExit('rarity must be 0..255')
    if not 1 <= opts.rolls <= 1000:
        raise SystemExit('rolls must be 1..1000')
    host = ROOT / 'CastlevaniaAoS.gba'
    original = host.read_bytes()
    workspace = ROOT / 'local/soul-scan'
    workspace.mkdir(parents=True, exist_ok=True)
    victim = VICTIMS[opts.enemy]
    rom = load_image(host)
    import copy
    edits = []
    for base in VICTIM_EDITS[opts.enemy]:
        edit = copy.deepcopy(base)
        if edit['enemy'] == opts.enemy:
            edit['expect'] = dict(edit['expect'], soul_rarity={
                'zombie': 180, 'skeleton': 8}[opts.enemy])
            edit['fields'] = {'soul_rarity': opts.rarity}
        edit['drops'] = {'item_1': {'item': None, 'rarity': 0},
                         'item_2': {'item': None, 'rarity': 0}}
        edits.append(edit)
    mod = {'schema_version': 1, 'id': 'soul-scan', 'enemy_edits': edits}
    if victim['route'] == 'workshop-shortcut':
        workshop = json.loads((ROOT / 'examples/enemy-workshop/mod.json').read_text())
        mod['room_edits'] = workshop['room_edits']
        mod['enemy_encounters'] = workshop['enemy_encounters']
    apply_manifest_data(rom, mod, workspace)
    image = workspace / 'probe.gba'
    rom.output(image, host)
    e = Emulator(image)
    try:
        e.run(1000)
        for k in [3, 8, 8, 8, 3, 3, 8]:
            e.run(1, [k])
            e.run(100)
        for _ in range(60):
            e.run(1, [8])
            e.run(90)
        for _ in range(600):
            e.run(1, [7])
            if e.read(0x02000088) == victim['room']:
                break
        for _ in range(180):
            if e.read(0x02000088) == victim['room']:
                break
            e.run(20, [7, 0])
            e.run(1, [7, 8])
            e.run(15, [7, 0])
        assert e.read(0x02000088) == victim['room'], 'did not reach victim room'
        e.run(70, [7])
        e.run(120)
        calm = {}
        for i in range(60):
            e.run(12, [7] if (i // 10) % 2 == 0 else [6])
            for code in snapshot(e):
                calm[code] = calm.get(code, 0) + 1
        known = set(calm)
        log = []
        last_exp = e.read(0x0201328c)
        for roll in range(opts.rolls):
            direction = 7 if (roll // 10) % 2 == 0 else 6
            e.run(1, [0, direction])
            e.run(12, [direction])
            e.run(1)
            e.run(12)
            exp = e.read(0x0201328c)
            novel = sorted(c for c in snapshot(e) if c not in known)
            if novel:
                log.append({'roll': roll, 'exp': exp,
                            'killed': exp != last_exp, 'novel': novel})
            last_exp = exp
        e.snap('soul-scan.png')
        sightings = {}
        first_seen = {}
        for entry in log:
            for code in entry['novel']:
                sightings[code] = sightings.get(code, 0) + 1
                first_seen.setdefault(code, entry['roll'])
        kill_rolls = {entry['roll'] for entry in log if entry['killed']}
        candidates = [code for code in sightings
                      if sightings[code] >= 5 and
                      any(abs(first_seen[code] - k) <= 2 for k in kill_rolls)]
        codes = resolve_enemy(rom, opts.enemy)['fields']
        pages = {codes['update_code'] & 0xFFFF0000, codes['create_code'] & 0xFFFF0000}
        same_page = [c for c in candidates if int(c, 16) & 0xFFFF0000 in pages]
        pickup_like = [c for c in candidates if c not in same_page]
        attack_only = sorted(set(sightings) - set(calm))
        findings = ['attack-correlated codes (never calm, seen while attacking): ' +
                    (', '.join(attack_only) if attack_only else 'none')]
        findings.append('kill-correlated persistent candidates: ' +
                        (', '.join(candidates) if candidates else 'none found'))
        findings.append('same code page as victim update/create (likely death-state, not pickup): ' +
                        (', '.join(same_page) if same_page else 'none'))
        findings.append('off-page kill-correlated codes (unattributed; burst, numbers or other effects possible): ' +
                        (', '.join(pickup_like) if pickup_like else 'none'))
        report = {'enemy': opts.enemy, 'rarity': opts.rarity, 'rolls': opts.rolls,
                  'calm_codes': calm, 'novel_rolls': log,
                  'sightings': sightings, 'first_seen': first_seen,
                  'kill_rolls': sorted(kill_rolls), 'candidates': candidates,
                  'same_page_death_state_likely': same_page,
                  'off_page_unattributed': pickup_like,
                  'victim_codes': {k: hex(codes[k]) for k in ('update_code', 'create_code')},
                  'findings': findings,
                  'limitations': ['soul-crystal spawns not observable in this actor window',
                                  'collection/grant uncertified: no soul-inventory RAM address or menu proof',
                                  'rarity formula unproven; absence is not a drop-rate measurement']}
        opts.out.write_text(json.dumps(report, indent=2))
        print(json.dumps({'enemy': opts.enemy, 'rarity': opts.rarity, 'rolls': opts.rolls,
                          'findings': findings,
                          'kill_rolls': sorted(kill_rolls)}, indent=2))
    finally:
        e.close()
        assert host.read_bytes() == original


if __name__ == '__main__':
    main()
