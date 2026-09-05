"""Execute real wounded-probe rules; native HP/status results are explicit inputs.

These tests catch missing guards/writes, wrong arguments and incorrect phase
advancement. They do not simulate native HP rounding, status timing or saves.
"""
from pathlib import Path
import unittest
from tests.osiris_subset import StoryFixture, call, value

GOAL = Path(__file__).resolve().parents[1] / "story/RawFiles/Goals/AESN_81_HpWoundedProof.txt"
NULL = "NULL_00000000-0000-0000-0000-000000000000"
TEMPLATE = "Kobolds_Melee_Drunk_45e31b7d-32ec-4f3d-8067-79061aeec77b"
BITS = {1: ("00001",), 111: ("00001", "00002", "00004", "00008", "00032", "00064")}
CASES = ((1, 20, 28, 13), (111, 20, 138, 69))


class WoundedFixture(StoryFixture):
    def action(self, text, env):
        name, tokens = call(text) if not text.startswith("NOT ") else ("", [])
        if name in {"ApplyStatus", "RemoveStatus", "SetHitpoints", "SetFaction",
                    "SetCanFight", "SetCanJoinCombat", "PROC_SelfHealing_Disable"}:
            # External base-game boundary only: do not simulate healing efficacy.
            self.calls.append((name, tuple(value(token, env) for token in tokens)))
        else:
            super().action(text, env)


class HpWoundedProofTests(unittest.TestCase):
    def setUp(self):
        self.s = WoundedFixture([GOAL] if GOAL.exists() else [])
        self.s.add("DB_AESN_HpWoundedEnabled", 1, fire=False)
        self.s.native["GetHostCharacter"] = [("host",)]
        for name in ("IsDead", "IsInCombat"):
            self.s.native[name] = [("host", 0), ("npc1", 0), ("npc111", 0)]
        self.s.native["GetFaction"] = [("host", "friends")]
        self.s.native["CreateAtObject"] = [
            (TEMPLATE, "host", 0, 1, "", 1, "npc1"),
            (TEMPLATE, "npc1", 0, 1, "", 1, "npc111")]
        self.s.native["GetHitpoints"] = [("npc1", 20), ("npc111", 20)]
        self.s.native["GetMaxHitpoints"] = [("npc1", 20), ("npc111", 20)]
        self.s.native["HasActiveStatus"] = []

    def timer(self, npc, phase):
        self.s.event("ObjectTimerFinished", npc, "AESN_HpWounded_" + phase)

    def hp(self, amount, current, maximum):
        for name, number in (("GetHitpoints", current), ("GetMaxHitpoints", maximum)):
            self.s.native[name] = [r for r in self.s.native[name] if r[0] != f"npc{amount}"]
            self.s.native[name].append((f"npc{amount}", number))

    def statuses(self, amount, *, legacy=False, total=False, reference=True):
        npc = f"npc{amount}"
        self.s.native["HasActiveStatus"] = [r for r in self.s.native["HasActiveStatus"] if r[0] != npc]
        self.s.native["HasActiveStatus"] += [
            (npc, "AESN_HP_TOTAL_7", int(reference)),
            (npc, f"AESN_HP_TOTAL_{amount}", int(total)),
            *((npc, "AESN_HP_BIT_" + bit, int(legacy)) for bit in BITS[amount])]

    def writes(self, name=None):
        return [(n, a) for n, a in self.s.calls
                if n in {"ApplyStatus", "RemoveStatus", "SetHitpoints"} and (name is None or n == name)]

    def state(self, amount, phase):
        _, base, target, wounded = next(c for c in CASES if c[0] == amount)
        self.assertIn((f"npc{amount}", amount, base, target, wounded, phase),
                      self.s.rows("DB_AESN_HpWoundedState"))

    def start(self):
        self.s.event("SavegameLoaded")
        self.timer("host", "Spawn")
        self.timer("npc1", "Spawn")
        for amount, _, _, _ in CASES:
            self.timer(f"npc{amount}", "Baseline")

    def legacy(self):
        self.start()
        for amount, _, target, wounded in CASES:
            self.statuses(amount, legacy=True)
            self.hp(amount, target, target)
            self.timer(f"npc{amount}", "LegacyApplying")
            self.hp(amount, wounded, target)
            self.timer(f"npc{amount}", "LegacyWounding")
            self.state(amount, "LegacyInspect")

    def convert(self):
        self.legacy()
        self.s.event("SavegameLoaded")
        for amount, _, target, wounded in CASES:
            self.timer(f"npc{amount}", "LegacyReloading")
            self.statuses(amount)
            # Deliberately chosen external observations, not inferred native rules.
            self.hp(amount, 11, 27)
            self.timer(f"npc{amount}", "LegacyRemoving")
            self.statuses(amount, total=True)
            self.hp(amount, 17, target)
            self.timer(f"npc{amount}", "TotalApplying")
            self.hp(amount, wounded, target)
            self.timer(f"npc{amount}", "TotalRestoring")
            self.state(amount, "TotalInspect")

    def test_default_disabled_cannot_spawn_or_mutate(self):
        self.s = WoundedFixture([GOAL] if GOAL.exists() else [])
        self.s.native["GetHostCharacter"] = [("host",)]
        self.s.native["IsDead"] = [("host", 0)]
        self.s.native["IsInCombat"] = [("host", 0)]
        self.s.event("SavegameLoaded")
        self.timer("host", "Spawn")
        self.assertEqual([], self.s.calls)
        self.assertEqual([], self.s.rows("DB_AESN_HpWoundedFixture"))

    def test_adopted_fixtures_disable_self_healing_before_hp_or_status_mutations(self):
        self.s.event("SavegameLoaded")
        self.timer("host", "Spawn")
        self.timer("npc1", "Spawn")
        self.assertEqual([("npc1", 1), ("npc111", 111)],
                         self.s.rows("DB_AESN_HpWoundedFixture"))
        self.assertEqual([("PROC_SelfHealing_Disable", ("npc1",)),
                          ("PROC_SelfHealing_Disable", ("npc111",))],
                         [call for call in self.s.calls if call[0] == "PROC_SelfHealing_Disable"])
        self.assertEqual([], self.writes())
        for npc in ("npc1", "npc111"):
            self.timer(npc, "Baseline")
            disable_index = self.s.calls.index(("PROC_SelfHealing_Disable", (npc,)))
            hp_status_indices = [index for index, (name, args) in enumerate(self.s.calls)
                                 if name in {"ApplyStatus", "RemoveStatus", "SetHitpoints"}
                                 and args[0] == npc]
            self.assertTrue(hp_status_indices)
            self.assertLess(disable_index, min(hp_status_indices))
        self.s.calls.clear()
        self.s.event("SavegameLoaded")
        self.assertEqual([], self.writes())
        self.assertEqual([], [call for call in self.s.calls if call[0] == "PROC_SelfHealing_Disable"])

    def test_legacy_exact_bits_reference_wound_and_saved_checkpoint(self):
        self.legacy()
        applied = [args for _, args in self.writes("ApplyStatus")]
        for amount, _, target, wounded in CASES:
            expected = ["AESN_HP_TOTAL_7"] + ["AESN_HP_BIT_" + b for b in BITS[amount]]
            self.assertEqual([(f"npc{amount}", status, -1.0, 1, NULL) for status in expected],
                             [a for a in applied if a[0] == f"npc{amount}"])
            self.assertIn(("SetHitpoints", (f"npc{amount}", wounded, "Guaranteed")), self.writes())
            self.assertIn((f"npc{amount}", amount, "LegacyWounding", target, wounded, target),
                          self.s.rows("DB_AESN_HpWoundedObservation"))
        self.assertEqual([], self.s.rows("DB_AESN_HpWoundedFailure"))
        self.assertEqual([], [a for _, a in self.writes() if a[0] == "host"])

    def test_conversion_observes_interim_hp_restores_exactly_and_cleanup_preserves_reference(self):
        self.convert()
        for amount, _, target, wounded in CASES:
            self.assertIn((f"npc{amount}", amount, "LegacyRemoving", 27, 11, 27),
                          self.s.rows("DB_AESN_HpWoundedObservation"))
            self.assertIn((f"npc{amount}", amount, "TotalApplying", target, 17, target),
                          self.s.rows("DB_AESN_HpWoundedObservation"))
            self.assertIn((f"npc{amount}", amount, "Converted", target, wounded, target),
                          self.s.rows("DB_AESN_HpWoundedObservation"))
        self.s.calls.clear()
        self.s.event("SavegameLoaded")
        self.assertEqual([], self.writes())
        for amount, _, _, _ in CASES:
            self.timer(f"npc{amount}", "TotalReloading")
            self.statuses(amount)
            self.hp(amount, 9, 27)
            self.timer(f"npc{amount}", "TotalRemoving")
            self.state(amount, "Complete")
            self.assertIn((f"npc{amount}", amount, "Cleanup", 27, 9, 27),
                          self.s.rows("DB_AESN_HpWoundedObservation"))
        self.assertEqual([("RemoveStatus", ("npc1", "AESN_HP_TOTAL_1", NULL)),
                          ("RemoveStatus", ("npc111", "AESN_HP_TOTAL_111", NULL))], self.writes())
        self.s.calls.clear()
        self.s.event("SavegameLoaded")
        self.assertEqual([], self.writes())

    def test_first_reload_does_not_heal_or_reapply_and_removes_exact_owned_bits(self):
        self.legacy()
        self.s.calls.clear()
        self.s.event("SavegameLoaded")
        self.assertEqual([], self.writes())
        for amount, _, _, _ in CASES:
            self.timer(f"npc{amount}", "LegacyReloading")
        self.assertEqual([("RemoveStatus", (f"npc{amount}", "AESN_HP_BIT_" + b, NULL))
                          for amount, _, _, _ in CASES for b in BITS[amount]], self.writes())

    def test_wrong_legacy_max_current_reference_or_bit_fails_without_conversion(self):
        for defect in ("maximum", "current", "reference", "bit"):
            with self.subTest(defect=defect):
                self.setUp()
                self.legacy()
                self.s.event("SavegameLoaded")
                if defect == "maximum":
                    self.hp(111, 69, 137)
                elif defect == "current":
                    self.hp(111, 68, 138)
                elif defect == "reference":
                    self.statuses(111, legacy=True, reference=False)
                else:
                    self.s.native["HasActiveStatus"].remove(("npc111", "AESN_HP_BIT_00064", 1))
                self.s.calls.clear()
                self.timer("npc111", "LegacyReloading")
                self.assertIn(("npc111", 111, "LegacyReloading"), self.s.rows("DB_AESN_HpWoundedFailure"))
                self.assertEqual([], self.writes())

    def test_failed_absolute_setter_never_records_inspect_success(self):
        self.start()
        self.statuses(111, legacy=True)
        self.hp(111, 138, 138)
        self.timer("npc111", "LegacyApplying")
        self.hp(111, 70, 138)
        self.timer("npc111", "LegacyWounding")
        self.assertIn(("npc111", 111, "LegacyWounding"), self.s.rows("DB_AESN_HpWoundedFailure"))
        self.assertFalse(any(r[-1] == "LegacyInspect" for r in self.s.rows("DB_AESN_HpWoundedState")))

    def test_disabled_dead_combat_zero_and_wrong_version_continuations_cannot_restore(self):
        for defect in ("disabled", "dead", "combat", "zero", "version"):
            with self.subTest(defect=defect):
                self.setUp()
                self.start()
                self.statuses(111, legacy=True)
                self.hp(111, 138, 138)
                if defect == "disabled":
                    self.s.facts["DB_AESN_HpWoundedEnabled"].clear()
                elif defect == "version":
                    self.s.facts["DB_AESN_HpWoundedVersion"].clear()
                elif defect in ("dead", "combat"):
                    query = "IsDead" if defect == "dead" else "IsInCombat"
                    self.s.native[query] = [("host", 0), ("npc1", 0), ("npc111", 1)]
                else:
                    self.hp(111, 0, 138)
                self.s.calls.clear()
                self.timer("npc111", "LegacyApplying")
                self.assertEqual([], self.writes())
                self.assertIn(("npc111", 111, "LegacyApplying"), self.s.rows("DB_AESN_HpWoundedFailure"))

    def test_duplicate_timers_and_spawn_do_not_repeat_writes(self):
        self.legacy()
        before = list(self.s.calls)
        for _ in range(2):
            self.timer("host", "Spawn")
            self.timer("npc1", "Spawn")
            for amount, _, _, _ in CASES:
                for phase in ("Baseline", "LegacyApplying", "LegacyWounding"):
                    self.timer(f"npc{amount}", phase)
        self.assertEqual(before, self.s.calls)

    def test_interrupted_transient_reload_is_permanent_failure_without_repair(self):
        phases = ("Baseline", "LegacyApplying", "LegacyWounding", "LegacyReloading",
                  "LegacyRemoving", "TotalApplying", "TotalRestoring", "TotalReloading", "TotalRemoving")
        for phase in phases:
            with self.subTest(phase=phase):
                self.setUp()
                self.s.add("DB_AESN_HpWoundedStarted", 1, fire=False)
                self.s.add("DB_AESN_HpWoundedVersion", 1, fire=False)
                self.s.add("DB_AESN_HpWoundedFixture", "npc111", 111, fire=False)
                self.s.add("DB_AESN_HpWoundedState", "npc111", 111, 20, 138, 69, phase, fire=False)
                self.s.add("DB_AESN_HpWoundedPending", "npc111", phase, fire=False)
                self.statuses(111, legacy=True, total=True)
                self.hp(111, 69, 138)
                self.s.event("SavegameLoaded")
                self.timer("npc111", phase)
                self.assertIn(("npc111", 111, "Interrupted"), self.s.rows("DB_AESN_HpWoundedFailure"))
                self.assertEqual([], self.writes())

    def test_injured_zero_or_oversized_baseline_and_unsupported_samples_fail(self):
        for current, maximum, amount in ((0, 20, 111), (19, 20, 111), (1000000, 1000000, 111), (20, 20, 999)):
            with self.subTest(current=current, maximum=maximum, amount=amount):
                self.setUp()
                self.s.event("SavegameLoaded")
                self.timer("host", "Spawn")
                self.timer("npc1", "Spawn")
                if amount == 999:
                    self.s.facts["DB_AESN_HpWoundedFixture"] = [("npc111", 999)]
                    self.s.facts["DB_AESN_HpWoundedState"] = [("npc111", 999, 0, 0, 69, "Baseline")]
                self.hp(111, current, maximum)
                self.s.calls.clear()
                self.timer("npc111", "Baseline")
                self.assertEqual([], self.writes())
                self.assertTrue(self.s.rows("DB_AESN_HpWoundedFailure"))

    def test_bad_removal_or_total_observation_cannot_apply_or_restore(self):
        for phase, current, maximum, legacy, total, reference in (
            ("LegacyRemoving", 11, 28, False, False, True),
            ("LegacyRemoving", 11, 27, True, False, True),
            ("LegacyRemoving", 0, 27, False, False, True),
            ("TotalApplying", 17, 137, False, True, True),
            ("TotalApplying", 0, 138, False, True, True),
            ("TotalApplying", 17, 138, False, False, True),
            ("TotalApplying", 17, 138, False, True, False),
            ("TotalRestoring", 68, 138, False, True, True),
            ("TotalReloading", 68, 138, False, True, True),
            ("TotalRemoving", 28, 27, False, False, True),
            ("TotalRemoving", 9, 27, False, True, True)):
            with self.subTest(phase=phase, current=current, maximum=maximum, legacy=legacy, total=total, reference=reference):
                self.setUp()
                self.start()
                self.s.facts["DB_AESN_HpWoundedState"] = [("npc111", 111, 20, 138, 69, phase)]
                self.s.facts["DB_AESN_HpWoundedPending"] = [("npc111", phase)]
                # Keep every unrelated invariant valid so each altered native
                # answer, rather than missing removal history, causes failure.
                self.s.facts["DB_AESN_HpWoundedRemovedBit"] = [
                    ("npc111", "AESN_HP_BIT_" + bit) for bit in BITS[111]]
                self.statuses(111, legacy=legacy, total=total, reference=reference)
                self.hp(111, current, maximum)
                self.s.calls.clear()
                self.timer("npc111", phase)
                self.assertIn(("npc111", 111, phase), self.s.rows("DB_AESN_HpWoundedFailure"))
                self.assertEqual([], self.writes())

    def test_missing_native_hp_response_fails_closed(self):
        self.start()
        self.statuses(111, legacy=True)
        self.hp(111, 138, 138)
        self.s.native["GetMaxHitpoints"] = [("npc1", 20)]
        self.s.calls.clear()
        self.timer("npc111", "LegacyApplying")
        self.assertIn(("npc111", 111, "LegacyApplying"), self.s.rows("DB_AESN_HpWoundedFailure"))
        self.assertEqual([], self.writes())

    def test_dead_combat_disabled_spawn_consumes_token_and_never_retries(self):
        for defect in ("dead", "combat", "disabled"):
            with self.subTest(defect=defect):
                self.setUp()
                self.s.event("SavegameLoaded")
                if defect == "disabled":
                    self.s.facts["DB_AESN_HpWoundedEnabled"].clear()
                else:
                    query = "IsDead" if defect == "dead" else "IsInCombat"
                    self.s.native[query] = [("host", 1), ("npc1", 0), ("npc111", 0)]
                self.timer("host", "Spawn")
                self.assertEqual([], self.s.rows("DB_AESN_HpWoundedFixture"))
                self.assertEqual([], self.s.rows("DB_AESN_HpWoundedSpawn"))
                self.s.native["IsDead"] = [("host", 0)]
                self.s.native["IsInCombat"] = [("host", 0)]
                self.s.add("DB_AESN_HpWoundedEnabled", 1, fire=False)
                self.s.calls.clear()
                self.timer("host", "Spawn")
                self.assertEqual([], self.s.calls)

    def test_successful_replacement_writes_each_total_and_absolute_hp_only_once(self):
        self.convert()
        for amount, _, _, wounded in CASES:
            self.assertEqual(1, self.writes().count(("ApplyStatus", (
                f"npc{amount}", f"AESN_HP_TOTAL_{amount}", -1.0, 1, NULL))))
            self.assertEqual(2, self.writes().count(("SetHitpoints", (
                f"npc{amount}", wounded, "Guaranteed"))))
        self.assertFalse(any(a[1] == "AESN_HP_TOTAL_7" for _, a in self.writes("RemoveStatus")))
        before = list(self.s.calls)
        for amount, _, _, _ in CASES:
            for phase in ("LegacyReloading", "LegacyRemoving", "TotalApplying", "TotalRestoring"):
                self.timer(f"npc{amount}", phase)
        self.assertEqual(before, self.s.calls)


if __name__ == "__main__":
    unittest.main()
