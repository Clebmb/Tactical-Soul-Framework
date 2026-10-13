# Custom tear-style soul ability: current boundary

Requested target: a custom soul that fires Binding of Isaac-style tears with
matching firing/impact SFX inside native Aria gameplay. This is not implemented.
The current framework cannot produce this complete ability from supported
manifest settings. Original runtime extensions are possible engineering work,
not evidence that a projectile API already exists.

Available foundations:

- Registered after-update ability dispatcher, input edges, guarded gameplay
  execution, declared transient RAM, MP spending and cooldown patterns. Current
  built-in modules heal/regenerate; the hook does not consume native input.
- Narrow Winged Skeleton soul identity/acquisition/save evidence and MP-cost
  edits. This does not replace its projectile behavior, artwork or sound.
- Original indexed graphics and mono8 PCM import; bounded boot music tracks,
  instruments and envelope authoring. Boot audio does not expose a gameplay
  sound-trigger API or identify a firing/impact SFX consumer.

Required implementation and acceptance before claiming the requested feature:

1. Establish a native projectile spawn/update/despawn ABI or implement a bounded
   owned projectile subsystem with explicit storage and lifecycle. Define
   direction, speed, lifetime, firing cadence, MP cost and simultaneous limit.
2. Prove native projectile graphics/palette/OAM ownership and tear animation
   binding. Existing decorative bats reskin permissions do not provision tears.
3. Establish enemy and terrain collision, damage attribution, hit cooldowns and
   impact cleanup. A moving sprite alone is not a functioning attack.
4. Establish native gameplay SFX dispatch and per-effect sample/voice ownership;
   import original or supplied authorized firing/impact assets and trigger them
   on actual fire/hit events. Verify coexistence with BGM and existing effects.
5. Bind the ability to soul acquisition/equipment/casting and native input without
   double spending/casting. Verify pauses, room transitions, death, save/continue
   and repeated fire/hit/miss cases with isolated negative controls.

Bounded 2026-10-12 observation: `scripts/trace_soul_projectile.py` reuses the
verified Up+B cast route and finds two cast-correlated actors in the established
224-slot window — soul `code 0x08026009` at slot 2 plus `0x08025F71` at slot 3,
present frames +7..+61, fixed slots, clean 30-frame idle negative, 12 MP spent.
Static exact-pointer search hits only the record itself. Rendering, OAM/palette,
position/velocity, damage/collision, lifecycle and isolated SFX remain unproven;
no new authoring permission follows. See SOUL-PROJECTILE-TRACE.md and
`aria/soul_projectiles.py`. No Isaac assets are bundled, extracted or downloaded
for this assessment.
See ABILITIES.md, SOULS.md, SPRITE-AUTHORING.md and MUSIC-SAMPLES.md.
