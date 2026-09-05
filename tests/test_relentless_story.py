from pathlib import Path
import unittest

from tests.osiris_subset import StoryFixture


GOALS = Path(__file__).resolve().parents[1] / "story/RawFiles/Goals"
NERE = "S_UND_TheDrowNere_06bf05c5-216b-4eaf-91f5-8f1dd3d57f30"


class RelentlessStoryTests(unittest.TestCase):
    def setUp(self):
        self.story = StoryFixture([GOALS / "AESN_56_Relentless.txt"])
        self.story.native["CombatIsActive"] = [("fight", 1)]
        self.story.add("DB_AESN_RelentlessCapability", 1, fire=False)
        self.story.add("DB_AESN_CombatDispatched", "fight", fire=False)
        self.budget(1, 0, 1)

    def candidate(self, enemy, *, boss=0, ready=True, action=1.0, bonus=1.0):
        s = self.story
        s.native["IsBoss"].append((enemy, boss))
        s.native["IsDead"].append((enemy, 0))
        s.native["QRY_AESN_IsEligibleHostile"].append((enemy, "fight"))
        s.native["GetActionResourceValuePersonal"].extend([
            (enemy, "ActionPoint", 0, action), (enemy, "BonusActionPoint", 0, bonus)])
        s.add("DB_Is_InCombat", enemy, "fight", fire=False)
        s.add("DB_AESN_EnemyEligible", "fight", enemy)
        if ready:
            self.harden(enemy)

    def harden(self, enemy, owner="fight", *, representation=1,
               state="HPCommitted", delta=10, applied=10,
               component_state="FullyCommitted"):
        self.story.add("DB_AESN_HpTransaction", owner, enemy, representation, state,
                       10, 10, 100.0, 20, delta, applied, fire=False)
        self.story.add("DB_AESN_ComponentApplication", owner, enemy, 1, component_state, fire=False)
        self.story.add("DB_AESN_CombatHardenedReady", "fight", enemy)

    def budget(self, action, bonus, cap, spent=(0, 0, 0)):
        # Real combats retain this snapshot while ledger rows are replaced.
        self.story.facts["DB_AESN_CombatSnapshotV2"] = [
            ("fight", 2, 4, 4, 20, 5, 2, 210, action, bonus, cap, "Supported")]
        self.story.facts["DB_AESN_RelentlessLedger"] = [("fight", 2, action, bonus, cap, *spent)]

    def test_new_snapshot_initializes_ledger_once_without_resetting_spend(self):
        self.story.facts["DB_AESN_CombatSnapshotV2"].clear()
        self.story.facts["DB_AESN_RelentlessLedger"].clear()
        snapshot = ("fight", 2, 4, 4, 20, 5, 2, 210, 1, 0, 2, "Supported")
        self.story.add("DB_AESN_CombatSnapshotV2", *snapshot)
        self.assertEqual([("fight", 2, 1, 0, 2, 0, 0, 0)],
                         self.story.rows("DB_AESN_RelentlessLedger"))
        self.candidate(NERE)
        self.story.tick()
        self.story.event("DB_AESN_CombatSnapshotV2", *snapshot)
        self.assertEqual([("fight", 2, 1, 0, 2, 1, 0, 1)],
                         self.story.rows("DB_AESN_RelentlessLedger"))

    def test_world_snapshot_does_not_initialize_combat_ledger(self):
        self.story.add("DB_AESN_WorldContext", "world", fire=False)
        self.story.add("DB_AESN_CombatSnapshotV2", "world", 2, 4, 4, 20, 5, 2,
                       210, 1, 0, 2, "Supported")
        self.assertFalse(any(row[0] == "world" for row in
                             self.story.rows("DB_AESN_RelentlessLedger")))

    def test_native_boss_wins_even_when_guard_ready_first(self):
        self.candidate("guard")
        self.candidate("boss", boss=1)
        self.story.tick()
        self.assertEqual([("boss", "AESN_RELENTLESS_FOE_01")], self.story.applied)

    def test_nere_override_wins_when_native_flag_is_false(self):
        self.candidate("guard")
        self.candidate(NERE)
        self.story.tick()
        self.assertEqual([(NERE, "AESN_RELENTLESS_FOE_01")], self.story.applied)

    def test_unready_boss_reserves_priority_until_hardened_ready(self):
        self.candidate("guard")
        self.candidate(NERE, ready=False)
        self.story.tick()
        self.assertEqual([], self.story.applied)
        self.harden(NERE)
        self.story.tick()
        self.assertEqual([(NERE, "AESN_RELENTLESS_FOE_01")], self.story.applied)

    def test_resource_unsafe_boss_does_not_block_safe_guard(self):
        self.candidate("guard")
        self.candidate(NERE, action=2.0)
        self.story.tick()
        self.assertEqual([("guard", "AESN_RELENTLESS_FOE_01")], self.story.applied)
        self.assertEqual([("fight", NERE, "PreexistingActionResource")],
                         self.story.rows("DB_AESN_RelentlessRejected"))

    def test_strongest_package_goes_to_boss_once_then_elite(self):
        self.budget(2, 1, 2)
        self.story.add("DB_AESN_RelentlessPriorityOverride", "elite", 1, fire=False)
        self.candidate("guard")
        self.candidate("elite")
        self.candidate(NERE)
        self.story.tick()
        self.assertEqual([(NERE, "AESN_RELENTLESS_FOE_02"),
                          ("elite", "AESN_RELENTLESS_FOE_01")], self.story.applied)
        self.assertEqual([("fight", 2, 2, 1, 2, 2, 1, 2)],
                         self.story.rows("DB_AESN_RelentlessLedger"))

    def test_late_boss_cannot_replace_existing_recipient(self):
        self.candidate("guard")
        self.story.tick()
        self.candidate(NERE)
        self.story.tick()
        self.assertEqual([("guard", "AESN_RELENTLESS_FOE_01")], self.story.applied)

    def test_late_boss_uses_only_remaining_budget(self):
        self.budget(2, 1, 2, spent=(1, 1, 1))
        self.candidate(NERE)
        self.story.tick()
        self.assertEqual([(NERE, "AESN_RELENTLESS_FOE_01")], self.story.applied)

    def test_repeated_ready_and_timer_events_cannot_allocate_twice(self):
        self.budget(2, 1, 2)
        self.candidate(NERE)
        self.story.tick()
        self.story.event("DB_AESN_CombatHardenedReady", "fight", NERE)
        self.story.tick()
        self.assertEqual([(NERE, "AESN_RELENTLESS_FOE_02")], self.story.applied)

    def test_failed_hardened_boss_releases_priority_to_guard(self):
        self.candidate(NERE, ready=False)
        self.candidate("guard")
        self.story.add("DB_AESN_HpFailure", "fight", NERE, "ComponentApplyTimeout")
        self.story.tick()
        self.assertEqual([("guard", "AESN_RELENTLESS_FOE_01")], self.story.applied)

    def test_dead_or_now_friendly_boss_cannot_take_slot(self):
        for invalid in ("dead", "friendly"):
            with self.subTest(invalid=invalid):
                self.setUp()
                self.candidate(NERE)
                self.candidate("guard")
                if invalid == "dead":
                    self.story.native["IsDead"] = [(NERE, 1), ("guard", 0)]
                else:
                    self.story.native["QRY_AESN_IsEligibleHostile"] = [("guard", "fight")]
                self.story.tick()
                self.assertEqual([("guard", "AESN_RELENTLESS_FOE_01")], self.story.applied)

    def test_zero_budget_and_cap_do_not_start_selection(self):
        for action, cap in ((0, 1), (2, 0)):
            with self.subTest(action=action, cap=cap):
                self.setUp()
                self.budget(action, 0, cap)
                self.candidate(NERE)
                self.assertEqual({}, self.story.timers)
                self.assertEqual([], self.story.applied)

    def test_preexisting_bonus_resource_also_disqualifies_boss(self):
        self.candidate(NERE, bonus=2.0)
        self.candidate("guard")
        self.story.tick()
        self.assertEqual([("guard", "AESN_RELENTLESS_FOE_01")], self.story.applied)

    def test_failed_status_does_not_refund_budget(self):
        self.candidate(NERE)
        self.story.tick()
        self.story.event("StatusAttemptFailed", NERE, "AESN_RELENTLESS_FOE_01", "source", 0)
        self.candidate("guard")
        self.story.tick()
        self.assertEqual([(NERE, "AESN_RELENTLESS_FOE_01")], self.story.applied)

    def test_reload_reseeds_override_and_restarts_missing_timer(self):
        self.candidate("guard")
        self.candidate(NERE)
        self.story.facts["DB_AESN_RelentlessPriorityOverride"] = []
        self.story.timers.clear()  # Persisted pending DB, missing native timer.
        self.story.event("SavegameLoaded")
        self.story.tick()
        self.assertEqual([(NERE, "AESN_RELENTLESS_FOE_01")], self.story.applied)
        self.story.event("SavegameLoaded")
        self.story.tick()
        self.assertEqual(1, len(self.story.applied))

    def test_reconcile_hold_reserves_boss_slot_until_released(self):
        self.candidate("guard")
        self.candidate(NERE)
        self.story.add("DB_AESN_HpApplicationHold", "world", NERE, fire=False)
        self.story.tick()
        self.assertEqual([], self.story.applied)
        self.story.facts["DB_AESN_HpApplicationHold"].clear()
        self.story.tick()
        self.assertEqual([(NERE, "AESN_RELENTLESS_FOE_01")], self.story.applied)

    def test_cleanup_cancels_timer_and_deletes_rank_state(self):
        lifecycle = StoryFixture([GOALS / "AESN_60_Merge.txt"])
        self.story.rules.update(lifecycle.rules)
        self.candidate(NERE, ready=False)
        self.story.tick()
        self.story.proc("PROC_AESN_RequestCombatCleanup", "fight")
        self.assertEqual({}, self.story.timers)
        self.story.proc("PROC_AESN_DeleteCombatOwnedFacts", "fight")
        self.assertEqual([], self.story.rows("DB_AESN_RelentlessRank"))
        self.assertEqual([], self.story.rows("DB_AESN_RelentlessSelectionPending"))
        self.story.tick()
        self.assertEqual([], self.story.applied)

    def test_merge_invalidates_old_ranks_and_restarts_survivor(self):
        lifecycle = StoryFixture([GOALS / "AESN_60_Merge.txt"])
        self.story.rules.update(lifecycle.rules)
        self.candidate(NERE, ready=False)
        self.story.tick()
        # Actual production merge; policy is already canonical and no HP
        # transaction exists in this focused fixture.
        self.story.add("DB_AESN_CombatRetired", "fight", fire=False)
        self.story.add("DB_AESN_MergeInProgress", "fight", "survivor", fire=False)
        self.story.native["CombatIsActive"].append(("survivor", 1))
        self.story.add("DB_AESN_CombatSnapshotV2", "survivor", 2, 4, 4, 20, 5, 2, 210,
                       1, 0, 1, "Supported", fire=False)
        self.story.proc("PROC_AESN_MergeCombat", "fight", "survivor")
        self.assertEqual([], self.story.rows("DB_AESN_RelentlessRank"))
        self.assertEqual([("survivor", "AESN_RELENTLESS_SELECT_survivor")],
                         self.story.rows("DB_AESN_RelentlessSelectionPending"))
        self.assertNotIn("AESN_RELENTLESS_SELECT_fight", self.story.timers)

    def test_delayed_merge_replan_reserves_boss_without_spending(self):
        self.candidate("guard")
        self.candidate(NERE)
        self.story.add("DB_AESN_MergeReplanRequired", "fight", NERE, fire=False)
        self.story.add("DB_AESN_HpReplan", "fight", NERE, 1, "RemovingComponents", 100.0, fire=False)
        self.story.facts["DB_AESN_ComponentApplication"] = [
            ("fight", "guard", 1, "FullyCommitted"),
            ("fight", NERE, 1, "ReplanningComponents")]
        self.story.tick()
        self.assertEqual([], self.story.applied)
        self.assertEqual([("fight", 2, 1, 0, 1, 0, 0, 0)],
                         self.story.rows("DB_AESN_RelentlessLedger"))
        self.story.facts["DB_AESN_HpReplan"].clear()
        self.story.facts["DB_AESN_MergeReplanRequired"].clear()
        self.story.facts["DB_AESN_ComponentApplication"][-1] = ("fight", NERE, 1, "FullyCommitted")
        self.story.tick()
        self.assertEqual([(NERE, "AESN_RELENTLESS_FOE_01")], self.story.applied)

    def test_stale_readiness_without_committed_hp_cannot_allocate(self):
        self.candidate(NERE)
        self.story.facts["DB_AESN_HpTransaction"].clear()
        self.story.tick()
        self.assertEqual([], self.story.applied)

    def test_world_owned_hardened_can_qualify_without_combat_owned_hp(self):
        self.candidate(NERE, ready=False)
        self.story.add("DB_AESN_WorldContext", "world", fire=False)
        self.harden(NERE, owner="world")
        self.story.tick()
        self.assertEqual([(NERE, "AESN_RELENTLESS_FOE_01")], self.story.applied)

    def test_committed_legacy_and_total_hardened_nere_can_receive_one_grant(self):
        for owner in ("fight", "world"):
            for representation in (1, 2):
                with self.subTest(owner=owner, representation=representation):
                    self.setUp()
                    self.candidate(NERE, ready=False)
                    if owner == "world":
                        self.story.add("DB_AESN_WorldContext", owner, fire=False)
                    self.harden(NERE, owner=owner, representation=representation)
                    self.story.tick()
                    self.assertEqual([(NERE, "AESN_RELENTLESS_FOE_01")], self.story.applied)
                    self.assertEqual([("fight", 2, 1, 0, 1, 1, 0, 1)],
                                     self.story.rows("DB_AESN_RelentlessLedger"))

    def test_total_nere_priority_beats_ordinary_legacy_candidate(self):
        self.candidate("guard")
        self.candidate(NERE, ready=False)
        self.harden(NERE, representation=2)
        self.story.tick()
        self.assertEqual([(NERE, "AESN_RELENTLESS_FOE_01")], self.story.applied)

    def test_unfinished_or_invalid_total_commit_does_not_receive_relentless(self):
        cases = (
            {"state": "Planned"},
            {"delta": 10, "applied": 9},
            {"component_state": "Applying"},
            {"representation": 99},
        )
        for hardened in cases:
            with self.subTest(**hardened):
                self.setUp()
                self.candidate(NERE, ready=False)
                self.harden(NERE, **{"representation": 2, **hardened})
                self.story.tick()
                self.assertEqual([], self.story.applied)
                self.assertEqual([("fight", 2, 1, 0, 1, 0, 0, 0)],
                                 self.story.rows("DB_AESN_RelentlessLedger"))

    def test_spending_cannot_reinitialize_ledger_from_persisted_snapshot(self):
        # This persistent snapshot was absent from the old allocation fixture.
        # Removing the old spent-counter row must NOT trigger a new zero row.
        self.story.add("DB_AESN_CombatSnapshotV2", "fight", 2, 4, 4, 20, 5, 2,
                       210, 1, 0, 2, "Supported", fire=False)
        self.budget(1, 0, 2)
        self.candidate(NERE)
        self.candidate("dalthar")
        self.story.mutations.clear()
        self.story.tick()
        self.assertEqual([(NERE, "AESN_RELENTLESS_FOE_01")], self.story.applied)
        self.assertEqual([("fight", 2, 1, 0, 2, 1, 0, 1)],
                         self.story.rows("DB_AESN_RelentlessLedger"))
        self.assertNotIn(("add", "DB_AESN_RelentlessLedger",
                          ("fight", 2, 1, 0, 2, 0, 0, 0)), self.story.mutations)


if __name__ == "__main__":
    unittest.main()
