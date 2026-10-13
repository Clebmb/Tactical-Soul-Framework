# Authored progression-policy demonstration

This is a planning example, **not a playable key/gate mod**. It uses the existing
flesh-sanctuary graph but declares a fictional `key` flag. No key, native event,
door lock or save bit is installed. The original playable example is unchanged.

From the framework root with the exact private host:

```powershell
python examples/progression-policy/make_policies.py
TacticalSoul.cmd plan-progression --mod examples/custom_room/mod.json --spec local/progression/key-before-gate.json --out local/progression/before-report.json
TacticalSoul.cmd plan-progression --mod examples/custom_room/mod.json --spec local/progression/key-behind-gate.json --out local/progression/behind-report.json
```

The generator applies the mod in memory and writes two image-bound policies
under `local/progression/`. The first grants `key` on entering the start room;
the hallway is then reachable. The second places the only grant in the hallway
behind its own required-key door; that destination has no observed policy path.
The reports retain policy/image hashes and witnesses. All outputs are private.
Both policies now also request the ordered itinerary `[hallway, start]`: the
before-gate policy observes a two-door round trip; the behind-gate policy cannot
reach its first waypoint. This is a static policy witness, not native route proof.

See [policy API, assumptions and limits](../../docs/PROGRESSION-POLICIES.md).
