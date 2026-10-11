# Bridge-route example

A separate copied example combines the three original-art room showcase, checked neighbor repairs and a redesigned room5 stone bridge. Six native room slots participate: original-art rooms 0:3, 0:6, 0:31; bridge room 0:5; neighbors 0:9 and 0:25. Original room IDs, dimensions and castle-map ownership are retained. This is not a total conversion or newly authored campaign.

Build/play from the framework root:

```powershell
.\TacticalSoul.cmd build examples/bridge-route/mod.json
.\TacticalSoul.cmd play examples/bridge-route/mod.json
```

Final ROM SHA256: `bbe3d4b0cc80eee76bec1c77322050caf4547b9641c4e450457bbf22fe7fe840`.

`terrain-plan.json` reproduces the 22 room5 cell edits through `plan-terrain` against the original host. Six copied procedural artwork/palette JSON files are original framework content; native reused room tiles come from the user's private host and are not distributed as extracted artwork.

Native evidence proves a continuous bridge crossing in both directions using a declared separate entry harness and no gameplay RAM writes. A separate final-build regression proves the original-art main route's save/death/fresh-continue lifecycle. Natural campaign/event access to the neighbor branch is not certified. See [terrain authoring](../../docs/TERRAIN-PAINTING.md) for exact construction, checks, limitations and next-agent instructions.
