# Sky Invaders

Original procedural UFOs replace AoS's shared decorative Castle Corridor
bats/clouds artwork and palette. The native game still loads, moves, animates
and blends these sprites; their behavior and existing frame rectangles stay intact.

```
TacticalSoul.cmd build examples/sky-invaders/mod.json
TacticalSoul.cmd play examples/sky-invaders/mod.json
TacticalSoul.cmd build examples/sky-invaders/project.json
TacticalSoul.cmd preview-sprite background-bats --mod examples/sky-invaders/mod.json --frame 11 --out local/sprite-previews/invaders.png
```

The flat `mod.json` and the single-module `project.json` (art in
`modules/art.json`, shared sources under `modules/assets/`) build byte-identical
ROMs. Copy this folder and change the mod/project IDs for your own variation.

Walk right into the first hallway; look through the broken window. Edit
`modules/assets/invaders.json` (128x32 indexed pixels) and
`modules/assets/palette.json` (16 RGB colors), or change `make_art.py` and run
it to regenerate both. Regeneration overwrites edits to those two files. Artwork,
palette and generator are original MIT-licensed example content; no ROM is included.

The replacement affects **all native users** of this shared page/palette. It is
not room-local. Existing AI, frames and animation are unchanged. No new actor or
VRAM slots are granted. See [authoring guide](../../docs/SPRITE-AUTHORING.md) for
layout, expected hashes, constraints, native evidence and agent extension steps.

Verification: `python scripts/verify_sprite_assets.py --lifecycle`. Final-example
entry/pause/reentry is checked directly; save/death/fresh-continue is checked in a
separate composed room-workshop shortcut harness. Ordinary visible OAM pixels
are compared; blended cloud pixels are excluded from opaque comparisons.
