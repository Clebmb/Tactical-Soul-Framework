# Composable bridge project

Five source modules reproduce the already verified flat bridge-route ROM byte-for-byte. Split room5 terrain modules merge into one checked geometry batch; routes merge into one level batch. Six original authored JSON assets live below the artwork module's folder. This adds no new native gameplay and retains the bridge-route limitations.

From the framework root:

```powershell
.\TacticalSoul.cmd plan-project examples/bridge-project/project.json --out local/bridge-project-plan.json
.\TacticalSoul.cmd build examples/bridge-project/project.json
.\TacticalSoul.cmd play examples/bridge-project/project.json
```

Expected ROM SHA256: `bbe3d4b0cc80eee76bec1c77322050caf4547b9641c4e450457bbf22fe7fe840`.

Edit the appropriate module, then plan/build again. Do not duplicate terrain coordinates or door endpoints in another module; composition rejects ownership conflicts instead of overriding. Keep the shared source layout hash for split terrain batches. Assets must remain below the module folder. See [project composition](../../docs/PROJECT-COMPOSITION.md) for supported fields, path rules, transactional semantics, provenance and extensions.
