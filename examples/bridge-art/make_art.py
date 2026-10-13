"""Generate original ironwood-and-bronze bridge-deck tiles for room5's reskin.

No host ROM or extracted art is read. Run in any working directory; outputs
stay beside this script. Only the sixteen tile positions referenced by room5
metatile 6 are painted (1-3, 8-11, 16-19, 24-27, 56); the rest stay index 0.
Palette index zero stays transparent. Deterministic: fixed seed only.
"""
import json
import random
from pathlib import Path

W = H = 64
# 0 transparent, 1 outline, 2 wood-dark, 3 wood-mid, 4 wood-light,
# 5 wood-hi, 6 bronze-dark, 7 bronze-mid, 8 bronze-light, 9 bronze-hi,
# 10 iron-dark, 11 iron-light, 12 moss, 13 shadow, 14 rust, 15 specular
PALETTE = [
    [0, 0, 0], [16, 12, 10], [64, 44, 30], [112, 76, 48],
    [168, 120, 76], [216, 170, 110], [72, 52, 26], [128, 92, 40],
    [200, 150, 70], [248, 220, 140], [40, 40, 48], [120, 124, 140],
    [52, 88, 44], [24, 20, 28], [96, 60, 60], [240, 240, 240],
]

rng = random.Random(0xB41D63)
pixels = [0] * (W * H)


def put(tx, ty, x, y, color):
    pixels[(ty * 8 + y) * W + tx * 8 + x] = color


def tile_rect(t, x0, y0, x1, y1, color):
    tx, ty = t % 8, t // 8
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(tx, ty, x, y, color)


def grain(t, rows, base=3, dark=2, seed_jitter=True):
    """Horizontal wood grain with staggered vertical seams and speckle."""
    tx = t % 8
    tile_rect(t, 0, 0, 7, 7, base)
    for y in rows:
        for x in range(8):
            if rng.random() < 0.85:
                put(tx, t // 8, x, y, dark)
    seam = (t * 3 + 1) % 7 + 1
    for y in range(8):
        put(tx, t // 8, seam, y, 1 if y not in rows else dark)
    for _ in range(6 if seed_jitter else 0):
        put(tx, t // 8, rng.randrange(8), rng.randrange(8),
            dark if rng.random() < 0.7 else 12)


def rivet(t, cx, cy):
    tx, ty = t % 8, t // 8
    for dy in (0, 1):
        for dx in (0, 1):
            put(tx, ty, cx + dx, cy + dy, 8)
    put(tx, ty, cx, cy, 15)


def artwork():
    # Top lip row: dark cap, highlight edge, wood below.
    for t in (8, 9, 10, 11):
        tile_rect(t, 0, 0, 7, 1, 13)
        tile_rect(t, 0, 2, 7, 2, 5)
        grain(t, [4, 6], base=3, dark=2)
        tile_rect(t, 0, 0, 7, 0, 1)
    # Mid planks.
    for t in (24, 25, 26, 27):
        grain(t, [1, 4, 6])
    # Post segment plus lower planks.
    tile_rect(56, 0, 0, 1, 7, 2)
    tile_rect(56, 2, 0, 5, 7, 7)
    tile_rect(56, 2, 0, 5, 0, 9)
    tile_rect(56, 2, 7, 5, 7, 6)
    tile_rect(56, 6, 0, 7, 7, 2)
    rivet(56, 3, 1)
    rivet(56, 3, 5)
    for t in (1, 2, 3):
        grain(t, [2, 5, 7], base=2, dark=1)
    # Bronze band with rivets, rust flecks, shadow foot.
    for t in (16, 17, 18, 19):
        tile_rect(t, 0, 0, 7, 7, 7)
        tile_rect(t, 0, 0, 7, 1, 9)
        tile_rect(t, 0, 3, 7, 3, 6)
        tile_rect(t, 0, 6, 7, 7, 13)
        rivet(t, 3, 4)
        for _ in range(4):
            put(t % 8, t // 8, rng.randrange(8), rng.randrange(2, 6), 14)
    return {"width": W, "height": H, "pixels": pixels}


def main():
    folder = Path(__file__).resolve().parent
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "bridge-tiles.json").write_text(
        json.dumps(artwork(), separators=(",", ":")) + "\n")
    (folder / "bridge-palette.json").write_text(
        json.dumps(PALETTE, indent=2) + "\n")
    print("Generated original bridge-tiles.json and bridge-palette.json")


if __name__ == "__main__":
    main()
