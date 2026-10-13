# Winged Skeleton mana-cost workshop

```powershell
TacticalSoul.cmd play examples/soul-cost/mod.json
TacticalSoul.cmd build examples/soul-cost/mod.json
python scripts/verify_soul_cost.py
```

The native opening acquisition is unchanged. Winged Skeleton costs **6 MP**
instead of 12. Use native Up+B to cast under the default controls. This example
changes one two-byte field and supplies no native callback or custom save data.

The named `soul_edits` API currently registers only `winged-skeleton` and only
`mana_cost`. Each edit requires an explicit expected current cost. The builder
checks the exact host, original cost and unchanged other record bytes, then uses
the shared overlap ledger. Other soul fields, identities and grants fail rather
than being inferred. See [soul authoring](../../docs/SOULS.md).
