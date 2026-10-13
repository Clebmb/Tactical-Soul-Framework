# Bridge-art example

The bridge-route design plus an original ironwood-and-bronze deck reskin: room5
metatile 6 is redefined through `metatile_replacements` onto a newly imported
chunk-24 / palette-bank-8 load, with byte-identical collision. Run
`make_art.py` to regenerate `bridge-tiles.json`/`bridge-palette.json`; the six
other artwork/palette files are copied original framework content from the
bridge-route example. Native reused room tiles come from the user's private
host and are not distributed as extracted artwork.

Build/play from the framework root:

```powershell
.\TacticalSoul.cmd build examples/bridge-art/mod.json
.\TacticalSoul.cmd play examples/bridge-art/mod.json
```

Final ROM SHA256: `d86932c9a1ab8c860c2846e67acc29ec3e67f11b64c8324acbac829f36b95762`.

Native evidence (`scripts/verify_bridge_art.py`) proves exact imported tile and
palette loads in live VRAM, input-only bridge crossings in both directions over
the reskinned deck, and exact art reload on natural room5 return, with no
gameplay RAM writes. See [room assets](../../docs/ROOM-ASSETS.md) for exact
construction, checks, limitations and next-agent instructions.
