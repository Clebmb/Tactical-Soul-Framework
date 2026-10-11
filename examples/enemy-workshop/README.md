# Enemy workshop

From the Tactical Soul Framework root run `TacticalSoul.cmd play examples/enemy-workshop/mod.json`.
Start a new game and progress through the original entrance dialogue. The first
hallway has tougher Zombies worth 7 EXP, a moved original spawner, and a chance
to drop Potions. Item rarity zero is not a guaranteed drop. The hallway's right
door now reaches a native Skeleton room with weaker Skeletons and one added
same-room clone; the left door returns. Original graphics and native AI remain.

This demonstration uses a nonadjacent shortcut. It does not repair displaced
neighbors or certify full campaign progression. Save/map data is preserved.
No extra equipment, inventory or character stats are granted by the mod.

See ../../docs/ENEMIES.md for selectors, expected values, drop IDs, resource
checks, native verification and extension work. Table changes affect every
instance of each edited enemy subtype. No compiler is needed for this example.
