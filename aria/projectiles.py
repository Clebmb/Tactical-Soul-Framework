"""Bounded owned-projectile budgeting model (proposal scaffolding).

A pure reservation/accounting layer for tear-style soul projectiles. It does
not spawn actors, write ROM/RAM, render, or play audio: every native binding
(spawn allocator, record layout, SFX dispatch) is still open and must come
from decompiler evidence before any tear-art work. What it does establish is
the framework-side contract a future native binder must satisfy: slot
ownership, MP accounting with regen, press budgeting for the count-gate, and
the observed live window.

Bounds come from native observation (see docs/SOUL-PROJECTILE-TRACE.md):
``mana_cost`` 12, ``max_at_once`` 6, live window frames +7..+61, ~3-press
arming budget, ~1 MP regen per 60 frames.
"""

from .core import PatchError

MANA_COST = 12
MAX_AT_ONCE = 6
PRESS_BUDGET_PER_CAST = 3
REGEN_MP_PER_FRAME = 1.0 / 60.0
LIVE_FIRST_FRAME = 7
LIVE_LAST_FRAME = 61
KNOWN_SLOTS = (2, 3)

# 40th slice (scripts/pin_damage_high_hp.py, local/damage-pin.json): one
# Winged Skeleton cast deals exactly 22 damage to a zombie victim in a
# single frame (200->178, one change-point, n=2, EXP 0 non-lethal). This
# supersedes the 26th slice's clamped 18-drop (18-HP victim killed with
# 4 overkill). Zombie-only; other enemy types untested.
SOUL_ZOMBIE_PER_HIT_DAMAGE = 22

# 44th-45th slices (scripts/pin_damage_def_raised.py,
# local/damage-pin-def10.json, local/damage-pin-def5.json): three-point
# empirical fit, single-frame each. DEF 1 -> 22 (n=2), DEF 10 -> 17 (n=2,
# victim DEF read live), DEF 5 -> 20 (victim def_at_cast 5) against
# 200-HP boosted zombies. All three fit damage = (45 - DEF) // 2 with 45
# the soul-record multiplier — equivalently 22 - DEF // 2. Predicts 22 vs
# DEF-0 skeletons (untested: all skeleton pins missed on positioning).
SOUL_DAMAGE_MULTIPLIER = 45


def damage_vs_defense(victim_def):
    """Predicted per-hit soul damage vs a victim with ``victim_def`` DEF."""
    if type(victim_def) is not int or victim_def < 0:
        raise PatchError('Victim DEF must be a nonnegative int')
    return (SOUL_DAMAGE_MULTIPLIER - victim_def) // 2


def casts_to_kill_for(hp, victim_def):
    """Predicted live casts to kill a victim with ``hp`` HP and DEF.

    Composes the empirical ``damage_vs_defense`` model with ceiling
    division; same two-to-three-point evidence basis, zombie-room only.
    """
    if type(hp) is not int or hp < 1:
        raise PatchError('Victim HP must be a positive int')
    per_hit = damage_vs_defense(victim_def)
    if per_hit < 1:
        raise PatchError('Model predicts no damage at this DEF')
    return (hp + per_hit - 1) // per_hit


def mp_spend_adjusted(gross_spent, window_frames):
    """Add back regen over a spend window before comparing to cost.

    ``gross_spent`` is the observed MP drop; ``window_frames`` the frames
    between the two MP reads. Returns the regen-corrected spend estimate.
    """
    if type(gross_spent) is not int or gross_spent < 0:
        raise PatchError('Gross MP spend must be a non-negative int')
    if type(window_frames) is not int or window_frames < 0:
        raise PatchError('Spend window must be a non-negative int frame count')
    return gross_spent + REGEN_MP_PER_FRAME * window_frames


def cast_fired(gross_spent, window_frames, tolerance=2):
    """True when regen-corrected spend matches ``MANA_COST`` within tolerance."""
    if type(tolerance) is not int or tolerance < 0:
        raise PatchError('Cast tolerance must be a non-negative int')
    return abs(mp_spend_adjusted(gross_spent, window_frames) - MANA_COST) <= tolerance


def total_damage(casts):
    """Total zombie damage for ``casts`` live casts at 22 per hit."""
    if type(casts) is not int or casts < 1:
        raise PatchError('Cast count must be a positive int')
    return casts * SOUL_ZOMBIE_PER_HIT_DAMAGE


def casts_to_kill(hp):
    """Live casts needed to kill a zombie victim with ``hp`` hit points."""
    if type(hp) is not int or hp < 1:
        raise PatchError('Victim HP must be a positive int')
    return (hp + SOUL_ZOMBIE_PER_HIT_DAMAGE - 1) // SOUL_ZOMBIE_PER_HIT_DAMAGE


def presses_for_casts(casts):
    """Press budget for the count-gate: ~3 presses per real cast."""
    if type(casts) is not int or casts < 1:
        raise PatchError('Cast count must be a positive int')
    return casts * PRESS_BUDGET_PER_CAST


def is_live_frame(frame):
    """True inside the observed +7..+61 live window (inclusive)."""
    if type(frame) is not int:
        raise PatchError('Frame must be an int')
    return LIVE_FIRST_FRAME <= frame <= LIVE_LAST_FRAME


class ProjectileLedger:
    """Slot ownership ledger for at most ``MAX_AT_ONCE`` live projectiles.

    Slots are opaque owner tags (observed actor slots 2/3 by default, but any
    hashable tag works — the native slot binding is unproven). Double reserve
    and over-capacity raise; releasing an unheld slot raises. Pure bookkeeping:
    no emulator, ROM, or RAM access.
    """

    def __init__(self, capacity=MAX_AT_ONCE):
        if type(capacity) is not int or not 1 <= capacity <= MAX_AT_ONCE:
            raise PatchError('Ledger capacity must be 1..%d' % MAX_AT_ONCE)
        self._capacity = capacity
        self._held = {}

    @property
    def capacity(self):
        return self._capacity

    def reserve(self, slot, frame):
        """Hold ``slot`` from ``frame``; raises on double reserve or full ledger."""
        if slot in self._held:
            raise PatchError('Slot already held: %r' % (slot,))
        if len(self._held) >= self._capacity:
            raise PatchError('Projectile ledger full (%d)' % self._capacity)
        if type(frame) is not int or frame < 0:
            raise PatchError('Reserve frame must be a non-negative int')
        self._held[slot] = frame
        return {'slot': slot, 'since_frame': frame, 'held': len(self._held)}

    def release(self, slot):
        """Release ``slot``; raises when unheld."""
        if slot not in self._held:
            raise PatchError('Slot not held: %r' % (slot,))
        since = self._held.pop(slot)
        return {'slot': slot, 'since_frame': since, 'held': len(self._held)}

    def live(self, frame):
        """Held slots whose age falls inside the observed live window."""
        if type(frame) is not int or frame < 0:
            raise PatchError('Live query frame must be a non-negative int')
        return sorted(slot for slot, since in self._held.items()
                      if is_live_frame(frame - since))

    def held(self):
        """Sorted held slots (ownership facts, not liveness)."""
        return sorted(self._held)
