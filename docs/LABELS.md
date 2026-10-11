# Custom item and enemy names (v0.38)

`aria/labels.py` renames native item labels (136) and enemy labels (113)
through checked, in-place byte edits. No string moves, no new text, no
dialogue codec.

## Contracts

- Resolution is by kind plus exact name/key or numeric index:
  `resolve_label(rom, 'item'|'enemy', name=..., index=...)`. Item names
  come from the equipment catalog; enemy names from the native label bank.
- `apply_label_edits(rom, edits)` takes `{kind, item|enemy|index,
  expect, to}`. `expect` must equal the current text (omit it only to
  accept whatever is there). The whole batch validates before anything
  writes; repeated claims on one label fail.
- The replacement must be printable ASCII (`0x20`–`0x7E`) and fit the
  original byte length. Shorter names are space-padded and the original
  terminator byte is preserved, so the ROM grows by zero bytes and no
  pointer moves. One ledger entry per rename with the overwritten bytes
  as the expected preimage.
- Manifests use the `label_edits` section (also composable from
  `tsf-project` modules). Build reports echo
  `{kind, index, before, after}` per rename.

## Native proof

`scripts/verify_labels.py` builds a Knife→Fangs rename (same length, 5
bytes, 1 ledger entry) and twin-runs a fixed 26-snapshot menu tour on
the original and the renamed build: the control pair is exactly
deterministic, and 12 frames differ in tight 8px-cell clusters where the
menu renders the name. The ROM diff is exactly those 5 bytes.

## Limits

Longer-than-original names need a string allocator that does not exist
yet. Relocated strings, dialogue text, soul names and shop behavior are
unverified. Glyph-level transcripts are not produced; heat localization
is the render evidence.
