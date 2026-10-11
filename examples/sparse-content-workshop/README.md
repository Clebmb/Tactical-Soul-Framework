# Sparse native content workshop

Run `TacticalSoul.cmd play examples/sparse-content-workshop/mod.json`. Finish opening dialogue, obtain a Potion normally, then Start, Down, Down, A opens Item Use.

The manifest changes page-0 8x8 tiles 0 and 1 using original circular fragments, and palette color 1 in each of seven banks. These are 78 claimed bytes total. All other ROM bytes and resource headers are preserved. Native item-menu rendering and VRAM confirm the selective tile changes. Tiles/colors can be shared by several items; these indices are not item IDs or a complete Potion icon mapping.

Only mod.json is needed: original pixels, RGB changes, provenance and registered original hashes are inline. Read docs/RESOURCE-AUTHORING.md to export a private sheet, author changes, generate a sparse diff, and build. The verifier declares one Potion ownership byte in every capture; the mod grants no item. Original authored fragments/colors are MIT.
