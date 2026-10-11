# Input replay descriptors

This folder contains native-test inputs, not buildable mod manifests. `room5-left-jump.json` is a diagnostic trace that ends below the central platform; passing its expectations does not mean the cross-room goal succeeded. It requires the exact loaded room5 left-endpoint fixture from `scripts/verify_room5_search.py`. Do not replay it from the title screen or assume it bootstraps the game. See `docs/INPUT-REPLAYS.md` for contracts, checkpoints, evidence and extension instructions.
