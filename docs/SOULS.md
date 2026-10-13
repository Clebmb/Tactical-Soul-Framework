# Narrow named soul authoring

Winged Skeleton is the first registered editable soul: the first red-soul
ownership nibble, equipped native ID 1, `red_souls` record 1, text ID `0xE3`.
See [native evidence](NATIVE-EVENTS.md) for acquisition, menu identity, use cost
and save/continue proof. Record 0 is empty. This registration does not imply
that every soul record field or native call signature is understood.

An ordinary schema-1 manifest or source-project module accepts:

```json
"soul_edits": [
  {"soul": "winged-skeleton", "expect": {"mana_cost": 12},
   "fields": {"mana_cost": 6}}
]
```

`aria.souls.plan_soul_edits` validates the entire supported batch without ROM
mutation. `apply_soul_edits` requires the registered exact host and an unchanged
original non-cost record, verifies the explicit current-cost expectation and
writes exactly the two little-endian cost bytes through the overlap ledger.
The immutable original cost must be 12. Reports are returned and retained as
`rom.soul_report` by manifest application. Code pointers, animation, max-at-once,
damage multiplier, effects and unknown bytes are preserved.

Only one edit is supported, with exactly the shown keys and field. New costs
accept integers or numeric strings, range 1..999; booleans and free cost 0 fail.
This is a conservative authoring bound, not native certification of every value.
Unknown souls/fields, missing expectations, empty/duplicate batches, changed
other fields and overlapping writes fail. Costs above available MP can prevent
casting. Project composition validates each entry before ROM loading and permits one owner
per named soul; duplicate claims (including within a module) name both owners.
The report includes `soul_targets`; module contents are fingerprinted. A project
combining a named soul edit with any `table_edits` entry for its entire native
record fails before ROM loading, naming both owners in either module order.
This includes identical cost writes and changes to other fields: the named
writer requires the remaining record to preserve its original identity.
Other record indices and raw-only projects retain their existing contracts.
Flat manifests still rely on authoritative domain and overlap-ledger checks.

## Native acceptance

`examples/soul-cost/mod.json` is playable with normal native acquisition and a
6-MP spell. `examples/soul-cost/project.json` composes the same edit from
`modules/cost.json`; its ROM bytes, ledger and allocations match the flat build.
`python scripts/verify_soul_cost.py` builds a private probe, then runs
two original controls and the edited build through identical native opening,
menu and casting input. Controls must render identically. Edited menu pixels
may differ only in the cost display; labels and other UI remain unchanged.
Native Up+B spends 80→68 MP in controls and 80→74 in the edited build. HP,
ownership and equipped ID remain unchanged. The build has one ledger entry.
There are no game RAM/input/SRAM fixtures and the original ROM is unchanged.
Probe images, ROM and report stay under `local/soul-cost/` and
`local/soul-cost-verification.json`.

This verifies cost 6 versus original 12, not projectile graphics, damage,
collision, every cost boundary, multiple concurrent casts or other soul types.
No native code change, compiler, custom persistence or callable grant ABI is
introduced. Next extend named fields only with their own native effect evidence,
with no increase in native permissions from project composition.
