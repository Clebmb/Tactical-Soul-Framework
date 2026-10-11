# Equipment workshop

From the Tactical Soul Framework root run:

```powershell
.\TacticalSoul.cmd play examples/equipment-workshop/mod.json
```

Start a new game. Your starting Knife gains ATK but costs 2 STR; starting clothes gain DEF but cost 1 LCK. Both have flame-related flags. Native names/descriptions and graphics remain unchanged. Cape gains DEF and INT, but is not automatically granted by this mod. The automated verifier declares its own inventory fixture for immediate menu testing. Original progression and room topology remain intact in the shipped example.

Edit `mod.json` after inspecting equipment with `TacticalSoul.cmd equipment`. Every changed field needs a matching `expect`. Use signed bonuses, and named flag add/remove operations. See ../../docs/EQUIPMENT.md for the full contract and documented gameplay evidence. No compiler is required for these table edits. Save files belong to this separate output ROM; broad cross-mod save compatibility is not certified.
