# Original custom-content workshop

Run `TacticalSoul.cmd play examples/content-workshop/mod.json`. Finish the opening dialogue; Start, Down, Down, A opens Item Use after obtaining a Potion to see original diamond icons. The first native icon page and seven palette banks are replaced without changing their wrapper headers. Other pages remain native.

Edit diamonds.json (128x128 indexed pixels 0..15) and colors.json (112 RGB colors). Healing mechanics reuse the D SDK. chirp.wav is original synthesized audio imported as signed PCM; it is not connected to native playback. Read docs/CUSTOM-CONTENT.md before editing bindings, adding graphics targets or sound playback. All authored sample assets are original MIT material.
