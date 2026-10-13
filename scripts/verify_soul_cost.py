"""Native named soul-cost authoring: deterministic controls and edited MP use."""
import hashlib
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aria.cli import load_image, apply_manifest
from aria.tables import read_record
from verify_soul_menu import capture


def main():
    host = ROOT/'CastlevaniaAoS.gba'; original = host.read_bytes()
    rom = load_image(host)
    apply_manifest(rom, ROOT/'examples/soul-cost/mod.json')
    assert len(rom.ledger) == 1
    cost = read_record(rom, 'red_souls', 1)['mana_cost']; assert cost == 6
    folder = ROOT/'local/soul-cost'; folder.mkdir(parents=True, exist_ok=True)
    out = folder/'probe.gba'; rom.output(out, host)
    control, base_use = capture(host, 12)
    repeat, repeat_use = capture(host, 12)
    edited, edited_use = capture(out, cost)
    assert control.tobytes() == repeat.tobytes()
    for name, image in (('control', control), ('edited', edited)):
        image.save(folder/(name+'.png'))
    pixels = [(x, y) for y in range(160) for x in range(240)
              if control.getpixel((x, y)) != edited.getpixel((x, y))]
    assert pixels
    bounds = [min(x for x,y in pixels), min(y for x,y in pixels),
              max(x for x,y in pixels)+1, max(y for x,y in pixels)+1]
    assert all(24 <= x < 48 and 124 <= y < 140 for x,y in pixels), bounds
    assert base_use == repeat_use
    assert base_use['mp_before'] == edited_use['mp_before'] == 80
    assert base_use['mp_after'] == 68 and edited_use['mp_after'] == 74
    assert host.read_bytes() == original
    report = {'baseline': base_use, 'edited': edited_use, 'control_repeat_identical': True,
              'menu_cost_changed_pixels': len(pixels), 'menu_cost_difference_bounds': bounds,
              'patch_count': len(rom.ledger), 'original_unchanged': True,
              'rom_sha256': hashlib.sha256(out.read_bytes()).hexdigest(),
              'limits': ['first red-soul mana cost only; no damage/animation/grant or other soul authoring proof',
                         'one native cast per fresh run; no duplicate-count or broad combat certification']}
    (ROOT/'local/soul-cost-verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
