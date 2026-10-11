# Mods you can make with the current foundation

Current scope is balance/mechanics variants and small authored-room experiments,
not full total conversions. Use the exact private USA revision-0 host, preserve
it, and build separate outputs. Original code is MIT; this does not license game
artwork. The framework and the Aria of Mario World sibling remain independent.

## 1. Dracula's Budget Cuts

Make a comedic difficulty/economy remix: absurdly strong bargain weapons,
high-value weak enemies, stingy powerful enemies and surprising existing-item
drops. Equipment signed stats, enemy stats/EXP and named native drops are exposed.
The native attack animation, AI and item identities remain existing content.

Agent starter: "Read AGENTS.md, EQUIPMENT.md and ENEMIES.md. Create a separate
budget-cuts mod using equipment-workshop and enemy-workshop as examples. Change
five named equipment stat records and five named enemy balance/drop records,
with expected-value guards. Preserve unknown flags and attack families. Document
each gameplay effect, build a separate ROM and run relevant existing native
verification. Do not invent item slots or change AI."

## 2. Soma's Mandatory Tea Break

A recovery challenge: standing still restores HP, and the registered focus-heal
ability trades MP for emergency healing with a cooldown. Tune the implemented
features instead of promising arbitrary scripted mechanics.

Agent starter: "Read ABILITIES.md and examples/ability-workshop. Make a tea-break
variant with slow stationary regeneration and a costly R-button heal. Use only
the registered still_regen and focus_heal features. Explain timing units, tune
cost/cooldown to prevent free spam, preserve state guards, build and run the
ability verifier. Include a short balancing guide."

## 3. The Castle's Worst Renovation

An original-art obstacle micro-mod in the registered first hallway: silly tile
art, a small step/jump obstacle, and the demonstrated save-room route. This is a
narrow room experiment; room resizing and campaign construction remain pending.

Agent starter: "Read ROOM-ASSETS.md, CUSTOM-TERRAIN.md and ROOM-GEOMETRY.md. Copy
original-room-art to a separate renovation project. Create original 4bpp tiles
and a 16-color palette fitting the registered chunk/bank budget. Author a small
obstacle using supported collision bytes 0/3 in the registered hallway only.
Preserve dimensions, doors and saves. Build, preview, and run room-art lifecycle
verification; document traversal, death, save and fresh-continue evidence."

## 4. Bat Union Strike

A limited encounter remix: move existing enemies and conservatively duplicate
eligible Bat, Zombie or Skeleton templates where already supported. Combine with
stat/drop tuning for a goofy encounter. No arbitrary species insertion or AI.

Agent starter: "Read ENEMIES.md. Inspect a candidate room's original encounters.
Create a small bat-union mod by moving existing actors and cloning at most two
eligible zero-parameter Bat/Zombie/Skeleton templates already in that room.
Reject unsupported spawners and parameterized records. Tune named stats/drops,
preserve IDs/resource constraints and verify native traversal and return. If no
eligible template exists, choose another existing room; do not bypass guards."

## 5. Discount Vampire Equipment Pack

Create original diamond, candy or joke item icons on registered icon pages,
then rebalance existing equipment to match their new visual theme. This changes
icons and stats, not Soma's character animation or weapon sprite system.

Agent starter: "Read CUSTOM-CONTENT.md and RESOURCE-AUTHORING.md. Base a separate
discount-vampire project on named-content-workshop or sparse-content-workshop.
Use original indexed 4bpp artwork within registered pages/palettes and rebalance
existing equipment through named APIs. Keep provenance and preimage guards.
Preview, build and verify native icon rendering and equipment records."

## Exploration rather than playable asset replacement

Agents can browse 343 base-state slots, inspect all 925 nonempty layers and
preview type-1/type-3 background source images. They can plan future mashups and
resource layouts from these reports. Those read-only capabilities do not yet
permit replacing arbitrary backgrounds, animation, music or whole campaigns.

Full new worlds, imported enemy AI, new weapon attack families, original sprite
animation pipelines, audible custom music and total conversions remain roadmap
work. Combining existing modules still needs validation of the combined build;
passing individual examples is not evidence that every combination is safe.


## Two-room original art (v0.14.0)

See [TWO-ROOM-ART.md](TWO-ROOM-ART.md) for hallway plus save-room registered main layers, contrasting original graphics/palettes, native entry/return/save/death/fresh-continue evidence and limits. Run examples/two-room-art/mod.json. Full suite: 163 tests. Current estimate: 25%. No arbitrary-room or multiplayer permission.


## Three-room original-art route (v0.15.0)

See [THREE-ROOM-ART.md](THREE-ROOM-ART.md) for registered room 0,6 plus hallway/save targets, native contrasting-resource route and lifecycle checks, effect-aware fixed-rectangle capture and campaign limits. Run examples/three-room-art/mod.json. 164 tests; current estimate 26%. No arbitrary-room registration or repaired full campaign graph.


## Static world graph (v0.16.0)

See [WORLD-GRAPH.md](WORLD-GRAPH.md) for world-graph, incoming/outgoing edges, observed direct returns and mod routing deltas. Three-room example: four displaced incoming links explicitly identified. 170 tests; no automatic repairs, progression certification or new room permissions. Current estimate: 26%.
