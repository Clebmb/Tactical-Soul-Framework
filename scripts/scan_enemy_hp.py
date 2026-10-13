"""Native zombie HP-word hunt via isolated sword hits (private).

Vanilla ROM, controller-only: walk into the zombie room, snapshot all 224
actor records, land isolated single sword hits with snapshots between them,
and intersect repeated identical drops with ``scan_decreases``. A kill loop
then confirms the candidate reaches ~0 as EXP pays +1.

Read-only: no ROM writes, no authoring, no RNG/inventory forcing. A repeated
drop plus kill correlation names an HP candidate, not a certified HP semantic.
Outputs stay under local/. Original ROM is never modified.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aria.soul_projectiles import (
    ACTOR_SLOTS,
    read_slot_record,
    scan_decreases,
)
from emulator import Emulator

ZOMBIE_ROOM = 0x0850F15C
MAX_PROBES = 6
MAX_KILL_ROLLS = 150
HP_FLOOR = 50


def full_scan(e):
    return {slot: read_slot_record(e.read, slot) for slot in range(ACTOR_SLOTS)}


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
        for _ in range(600):
            e.run(1, [7])
            if e.read(0x02000088) == ZOMBIE_ROOM:
                break
        assert e.read(0x02000088) == ZOMBIE_ROOM, 'did not reach zombie room'
        e.run(70, [7])
        e.run(60)
        exp0 = e.read(0x0201328C)
        probes = []
        scans = [full_scan(e)]
        for probe in range(MAX_PROBES):
            if e.read(0x0201327A, 2) < HP_FLOOR:
                break
            e.run(6, [7])
            soma_x = e.read(0x02000526, 2) + e.read(0x0200A09A, 2)
            e.run(1, [0, 7])
            e.run(24)
            scans.append(full_scan(e))
            leads = scan_decreases(scans[-2], scans[-1], 1, 60)['leads']
            probes.append({'probe': probe, 'leads': leads, 'soma_x': soma_x,
                           'hp': e.read(0x0201327A, 2), 'exp': e.read(0x0201328C)})
            hits = [lead for lead in leads if lead['drop'] >= 1]
            if hits and probe >= 1:
                break
        repeated = []
        if len(probes) >= 2:
            keys = [{(lead['slot'], lead['index'], lead['drop']) for lead in probes[i]['leads']}
                    for i in range(len(probes))]
            common = set.intersection(*keys)
            repeated = sorted({'slot': slot, 'index': index, 'drop': drop}
                              for slot, index, drop in common)
        from collections import Counter
        drop_counts = Counter()
        drop_last = {}
        kill_rolls = 0
        kill_track = []
        kill_pair_leads = []
        prev = full_scan(e)
        while kill_rolls < MAX_KILL_ROLLS:
            if e.read(0x0201327A, 2) < HP_FLOOR or e.read(0x0201328C) != exp0:
                break
            direction = 7 if (kill_rolls // 10) % 2 == 0 else 6
            e.run(1, [0, direction])
            e.run(12, [direction])
            e.run(1)
            e.run(12)
            current = full_scan(e)
            pair_leads = scan_decreases(prev, current, 1, 60)['leads']
            for lead in pair_leads:
                key = (lead['slot'], lead['index'], lead['drop'])
                drop_counts[key] += 1
                drop_last[key] = lead['after']
            kill_pair_leads.append({'roll': kill_rolls, 'leads': pair_leads})
            prev = current
            kill_track.append({'roll': kill_rolls,
                               'hp': e.read(0x0201327A, 2),
                               'exp': e.read(0x0201328C)})
            kill_rolls += 1
        exp1 = e.read(0x0201328C)
        final = full_scan(e)
        report = {
            'route': 'vanilla opening + walk-right + isolated single hits + kill loop',
            'probes': probes,
            'repeated_drops': repeated,
            'kill_rolls': kill_rolls,
            'exp_before': exp0,
            'exp_after': exp1,
            'killed': exp1 != exp0,
            'candidate_final_words': [
                {'slot': cand['slot'], 'index': cand['index'],
                 'final_hex': hex(final[cand['slot']][cand['index']])}
                for cand in repeated],
            'kill_track': kill_track,
            'kill_pair_leads': kill_pair_leads,
            'repeated_kill_drops': [
                {'slot': slot, 'index': index, 'drop': drop, 'pairs': count,
                 'last_hex': hex(drop_last[(slot, index, drop)])}
                for (slot, index, drop), count in sorted(drop_counts.items())
                if count >= 2],
            'scope': ('a repeated identical drop plus kill correlation names an HP '
                      'candidate, not a certified HP semantic'),
            'original_unchanged': host.read_bytes() == original,
            'rom_sha256': hashlib.sha256(original).hexdigest(),
            'limits': [
                'vanilla zombie room only; one run',
                'whiffed probes (out of range) yield no leads by design',
                'contact damage to Soma bounds probe count via HP floor',
            ],
        }
        (ROOT / 'local/enemy-hp-scan.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps({k: report[k] for k in (
            'probes', 'repeated_drops', 'kill_rolls', 'exp_before', 'exp_after',
            'killed', 'candidate_final_words', 'scope', 'limits')}, indent=2))
    finally:
        e.close()
        assert host.read_bytes() == original


if __name__ == '__main__':
    main()
