"""Synthetic contracts for the owned-projectile budgeting model (no ROM)."""
import unittest

from aria.core import PatchError
from aria.projectiles import (
    MANA_COST,
    MAX_AT_ONCE,
    SOUL_DAMAGE_MULTIPLIER,
    SOUL_ZOMBIE_PER_HIT_DAMAGE,
    ProjectileLedger,
    cast_fired,
    casts_to_kill,
    is_live_frame,
    mp_spend_adjusted,
    casts_to_kill_for,
    damage_vs_defense,
    presses_for_casts,
    total_damage,
)


class ProjectileBudgetTests(unittest.TestCase):

    def test_regen_adjustment_recovers_fired_cast(self):
        # 18th-slice case: net 11 over 60 frames is a fired cost-12 cast.
        self.assertAlmostEqual(mp_spend_adjusted(11, 60), 12.0)
        self.assertTrue(cast_fired(11, 60))

    def test_clean_spend_fires_without_window(self):
        self.assertTrue(cast_fired(12, 0))
        self.assertFalse(cast_fired(0, 60))

    def test_fizzle_stays_unfired(self):
        self.assertFalse(cast_fired(0, 0))
        self.assertFalse(cast_fired(0, 6))

    def test_press_budget(self):
        self.assertEqual(presses_for_casts(1), 3)
        self.assertEqual(presses_for_casts(2), 6)
        with self.assertRaises(PatchError):
            presses_for_casts(0)

    def test_live_window_edges(self):
        self.assertFalse(is_live_frame(6))
        self.assertTrue(is_live_frame(7))
        self.assertTrue(is_live_frame(61))
        self.assertFalse(is_live_frame(62))

    def test_ledger_reserve_release(self):
        ledger = ProjectileLedger()
        ledger.reserve(2, 0)
        ledger.reserve(3, 0)
        self.assertEqual(ledger.held(), [2, 3])
        with self.assertRaises(PatchError):
            ledger.reserve(2, 5)
        self.assertEqual(ledger.release(2)['held'], 1)
        with self.assertRaises(PatchError):
            ledger.release(2)

    def test_ledger_capacity_bound(self):
        ledger = ProjectileLedger(capacity=1)
        ledger.reserve('a', 0)
        with self.assertRaises(PatchError):
            ledger.reserve('b', 0)
        with self.assertRaises(PatchError):
            ProjectileLedger(capacity=MAX_AT_ONCE + 1)

    def test_ledger_liveness_window(self):
        ledger = ProjectileLedger()
        ledger.reserve(2, 0)
        self.assertEqual(ledger.live(0), [])
        self.assertEqual(ledger.live(7), [2])
        self.assertEqual(ledger.live(61), [2])
        self.assertEqual(ledger.live(62), [])

    def test_zombie_damage_helpers(self):
        # 40th slice: 22 per hit vs zombies; 18-HP zombie dies in one cast.
        self.assertEqual(SOUL_ZOMBIE_PER_HIT_DAMAGE, 22)
        self.assertEqual(total_damage(1), 22)
        self.assertEqual(total_damage(2), 44)
        self.assertEqual(casts_to_kill(18), 1)
        self.assertEqual(casts_to_kill(22), 1)
        self.assertEqual(casts_to_kill(23), 2)
        with self.assertRaises(PatchError):
            total_damage(0)
        with self.assertRaises(PatchError):
            casts_to_kill(0)

    def test_damage_vs_defense_two_point_fit(self):
        # 44th-45th slices: DEF 1 -> 22 (n=2), DEF 10 -> 17 (n=2, victim
        # DEF live), DEF 5 -> 20 (victim def_at_cast 5).
        self.assertEqual(SOUL_DAMAGE_MULTIPLIER, 45)
        self.assertEqual(damage_vs_defense(1), 22)
        self.assertEqual(damage_vs_defense(10), 17)
        self.assertEqual(damage_vs_defense(5), 20)
        self.assertEqual(damage_vs_defense(0), 22)
        # Skeleton prediction: 20 HP / DEF 0 dies in one predicted cast.
        self.assertEqual(casts_to_kill_for(20, 0), 1)
        self.assertEqual(casts_to_kill_for(18, 1), 1)
        self.assertEqual(casts_to_kill_for(200, 10), 12)
        with self.assertRaises(PatchError):
            casts_to_kill_for(0, 0)
        with self.assertRaises(PatchError):
            damage_vs_defense(-1)

    def test_bad_inputs_raise(self):
        with self.assertRaises(PatchError):
            mp_spend_adjusted(-1, 60)
        with self.assertRaises(PatchError):
            mp_spend_adjusted(11, -1)
        with self.assertRaises(PatchError):
            is_live_frame('7')
        with self.assertRaises(PatchError):
            ProjectileLedger().reserve(2, -1)


if __name__ == '__main__':
    unittest.main()
