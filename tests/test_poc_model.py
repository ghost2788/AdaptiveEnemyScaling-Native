import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_model(test_case: unittest.TestCase):
    try:
        from tools import poc_model
    except (ImportError, ModuleNotFoundError) as error:
        test_case.fail(f"policy model must be implemented: {error}")
    return poc_model


class PocModelTests(unittest.TestCase):
    def test_hp_transaction_fixtures_are_exact(self):
        model = load_model(self)
        rows = json.loads(
            (ROOT / "tests/fixtures/hp_transactions.json").read_text(
                encoding="utf-8"
            )
        )

        for row in rows:
            with self.subTest(row=row["id"]):
                if row["operation"] == "cleanup":
                    restored = model.restore_current(
                        row["current"],
                        row["scaledMaximum"],
                        row["baseMaximum"],
                        alive=row["alive"],
                    )
                    self.assertEqual(restored, row["restoredCurrent"])
                    continue

                if row["operation"] == "policy_plan":
                    policy = model.policy_from_summary(
                        row["eligibleSize"], row["averageLevel"]
                    )
                    target = model.target_maximum(row["baseMaximum"], policy)
                else:
                    target = row["targetMaximum"]

                if "error" in row:
                    with self.assertRaisesRegex(
                        model.PolicyError, row["error"]
                    ):
                        model.plan_hp_target(
                            row["current"],
                            row["baseMaximum"],
                            target,
                            alive=row["alive"],
                        )
                    continue

                plan = model.plan_hp_target(
                    row["current"],
                    row["baseMaximum"],
                    target,
                    alive=row["alive"],
                )
                self.assertEqual(plan.target_maximum, row["targetMaximum"])
                self.assertEqual(plan.delta, row["delta"])
                self.assertEqual(list(plan.bits), row["bits"])
                self.assertEqual(plan.restored_current, row["restoredCurrent"])
                self.assertEqual(plan.outcome, row["outcome"])

    def test_build_policy_floors_average_and_calculates_schema2_policy(self):
        model = load_model(self)

        policy = model.build_policy([5, 7, 8])

        self.assertEqual(policy.eligible_size, 3)
        self.assertEqual(policy.level_sum, 20)
        self.assertEqual(policy.average_level, 6)
        self.assertEqual(policy.hardened_tier, 2)
        self.assertEqual(policy.target_hp_percent, 190)
        self.assertEqual(policy.attack_save_dc_bonus, 2)
        self.assertEqual(policy.ac_bonus, 1)
        self.assertEqual(policy.action_budget, 1)
        self.assertEqual(policy.bonus_action_budget, 0)
        self.assertEqual(policy.recipient_cap, 1)
        self.assertFalse(policy.clamped)

    def test_build_policy_caps_hp_and_relentless_inputs_above_twelve(self):
        model = load_model(self)

        policy = model.build_policy([7] * 13)

        self.assertEqual(policy.eligible_size, 13)
        self.assertEqual(policy.effective_size, 12)
        self.assertEqual(policy.target_hp_percent, 370)
        self.assertEqual(policy.action_budget, 6)
        self.assertEqual(policy.bonus_action_budget, 4)
        self.assertEqual(policy.recipient_cap, 6)
        self.assertTrue(policy.clamped)

    def test_hardened_matrix_matches_approved_literal_boundaries(self):
        model = load_model(self)

        rows = (
            (1, 1, 125, 1, 0),
            (4, 1, 125, 1, 0),
            (5, 2, 150, 2, 1),
            (8, 2, 150, 2, 1),
            (9, 3, 180, 3, 1),
            (12, 3, 180, 3, 1),
            (13, 4, 220, 4, 2),
            (16, 4, 220, 4, 2),
            (17, 5, 260, 5, 2),
            (18, 5, 260, 5, 2),
            (19, 6, 300, 6, 3),
            (20, 6, 300, 6, 3),
        )

        for level, tier, solo_hp, stat_bonus, ac_bonus in rows:
            with self.subTest(level=level):
                policy = model.build_policy([level])
                self.assertEqual(policy.hardened_tier, tier)
                self.assertEqual(policy.target_hp_percent, solo_hp)
                self.assertEqual(
                    policy.attack_save_dc_bonus,
                    stat_bonus,
                )
                self.assertEqual(policy.ac_bonus, ac_bonus)

    def test_party_size_adds_twenty_hp_points_per_member_through_twelve(self):
        model = load_model(self)

        expected = {
            1: 125,
            2: 145,
            3: 165,
            4: 185,
            8: 265,
            12: 345,
            13: 345,
        }

        for size, target_hp_percent in expected.items():
            with self.subTest(size=size):
                policy = model.build_policy([1] * size)
                self.assertEqual(
                    policy.target_hp_percent,
                    target_hp_percent,
                )

    def test_relentless_budget_caps_each_recipient_at_tier_two(self):
        model = load_model(self)

        rows = (
            (1, 1, 0, 0, 0, 0),
            (1, 5, 1, 0, 1, 0),
            (2, 20, 1, 0, 1, 0),
            (4, 5, 1, 0, 1, 0),
            (4, 13, 1, 1, 0, 1),
            (4, 17, 2, 1, 1, 1),
            (4, 19, 2, 2, 0, 2),
            (6, 1, 2, 1, 1, 1),
            (8, 19, 6, 4, 2, 4),
            (12, 19, 6, 6, 0, 6),
        )

        for size, level, action, bonus, tier_one, tier_two in rows:
            with self.subTest(size=size, level=level):
                policy = model.build_policy([level] * size)
                self.assertEqual(policy.action_budget, action)
                self.assertEqual(policy.bonus_action_budget, bonus)
                self.assertEqual(
                    policy.relentless_i_recipients,
                    tier_one,
                )
                self.assertEqual(
                    policy.relentless_ii_recipients,
                    tier_two,
                )

    def test_build_policy_rejects_empty_or_non_positive_levels(self):
        model = load_model(self)

        with self.assertRaises(model.PolicyError):
            model.build_policy([])
        with self.assertRaises(model.PolicyError):
            model.build_policy([0, 7])

    def test_target_maximum_matches_hand_calculated_solo_and_three_member_values(self):
        model = load_model(self)

        self.assertEqual(model.target_maximum(100, model.build_policy([7])), 150)
        self.assertEqual(
            model.target_maximum(100, model.build_policy([5, 7, 8])),
            190,
        )

    def test_target_maximum_rejects_unsafe_product(self):
        model = load_model(self)

        with self.assertRaises(model.PolicyError):
            model.target_maximum(100_000_000, model.build_policy([7]))

    def test_world_refresh_subtracts_owned_bits_before_reapplying_policy(self):
        model = load_model(self)
        policy = model.build_policy([5, 5, 5, 5])

        plan = model.plan_hardened_refresh(
            88,
            175,
            25,
            policy,
            alive=True,
        )

        self.assertEqual(plan.external_base, 150)
        self.assertEqual(plan.target_maximum, 315)
        self.assertEqual(plan.delta, 165)
        self.assertEqual(sum(plan.bits), 165)
        self.assertEqual(plan.restored_current, 158)

    def test_world_lifecycle_uses_visibility_only_for_discovery(self):
        model = load_model(self)

        visible = model.decide_world_hardened(
            tracked=False,
            committed=False,
            in_combat=False,
            alive=True,
            active=True,
            on_stage=True,
            invisible=False,
            hostile=True,
        )
        hidden = model.decide_world_hardened(
            tracked=True,
            committed=True,
            in_combat=False,
            alive=True,
            active=True,
            on_stage=True,
            invisible=True,
            hostile=True,
        )
        fighting = model.decide_world_hardened(
            tracked=True,
            committed=True,
            in_combat=True,
            alive=True,
            active=True,
            on_stage=True,
            invisible=False,
            hostile=True,
        )

        self.assertEqual(visible.action, "apply")
        self.assertEqual(hidden.action, "retain")
        self.assertEqual(fighting.action, "defer")

    def test_reconsideration_only_reopens_neutral_rejection_that_is_now_hostile(self):
        model = load_model(self)

        self.assertTrue(
            model.should_reconsider_rejected_hostile(
                rejected_reason="HostileToNoParticipant",
                still_in_combat=True,
                hostile_to_participant=True,
            )
        )
        self.assertFalse(
            model.should_reconsider_rejected_hostile(
                rejected_reason="HostileToNoParticipant",
                still_in_combat=True,
                hostile_to_participant=False,
            )
        )
        self.assertFalse(
            model.should_reconsider_rejected_hostile(
                rejected_reason="DeadAtEntry",
                still_in_combat=True,
                hostile_to_participant=True,
            )
        )
        self.assertFalse(
            model.should_reconsider_rejected_hostile(
                rejected_reason="HostileToNoParticipant",
                still_in_combat=False,
                hostile_to_participant=True,
            )
        )

    def test_decompose_delta_uses_exact_descending_bits_and_enforces_bounds(self):
        model = load_model(self)

        self.assertEqual(model.decompose_delta(61), [32, 16, 8, 4, 1])
        self.assertEqual(model.decompose_delta(0), [])
        self.assertEqual(model.decompose_delta(65_535)[0], 32_768)
        self.assertEqual(sum(model.decompose_delta(65_535)), 65_535)
        with self.assertRaises(model.PolicyError):
            model.decompose_delta(-1)
        with self.assertRaises(model.PolicyError):
            model.decompose_delta(65_536)

    def test_restore_current_rounds_half_up_and_preserves_living_and_dead_bounds(self):
        model = load_model(self)

        self.assertEqual(model.restore_current(50, 100, 115, alive=True), 58)
        self.assertEqual(model.restore_current(58, 115, 100, alive=True), 50)
        self.assertEqual(model.restore_current(0, 100, 115, alive=False), 0)
        self.assertEqual(model.restore_current(1, 1_000, 1, alive=True), 1)

    def test_restore_current_rejects_invalid_maximum_or_negative_current(self):
        model = load_model(self)

        with self.assertRaises(model.PolicyError):
            model.restore_current(10, 0, 100, alive=True)
        with self.assertRaises(model.PolicyError):
            model.restore_current(-1, 100, 115, alive=True)

    def test_merge_policy_selects_higher_average_and_larger_size_independently(self):
        model = load_model(self)
        high_level_solo = model.build_policy([7])
        lower_level_trio = model.build_policy([5, 5, 5])

        merged = model.canonical_merge_policy(high_level_solo, lower_level_trio)

        self.assertEqual(merged.average_level, 7)
        self.assertEqual(merged.eligible_size, 3)
        self.assertEqual(merged.level_sum, 21)
        self.assertEqual(merged.hardened_tier, 2)
        self.assertEqual(merged.target_hp_percent, 190)

    def test_merge_fixtures_migrate_ownership_and_suppress_discarded_cleanup(self):
        model = load_model(self)
        rows = json.loads(
            (ROOT / "tests/fixtures/merge_cases.json").read_text(
                encoding="utf-8"
            )
        )

        for row in rows:
            with self.subTest(row=row["id"]):
                result = model.reconcile_merge_case(row)
                final = row["expectedFinal"]
                policy = result.snapshots[final]

                self.assertEqual(policy.average_level, row["expectedAverage"])
                self.assertEqual(policy.eligible_size, row["expectedSize"])
                self.assertEqual(
                    result.mismatch_count,
                    row["expectedMismatchCount"],
                )
                for discarded in row["discardedEnds"]:
                    self.assertEqual(
                        model.cleanup_commands(result, discarded),
                        (),
                    )
                    self.assertEqual(
                        model.resolve_combat_owner(result.aliases, discarded),
                        final,
                    )
                self.assertEqual(
                    model.cleanup_commands(result, final),
                    tuple(row["expectedCleanup"]),
                )

    def test_reload_reconciliation_retains_only_valid_active_commit(self):
        model = load_model(self)

        decision = model.reconcile_reload_state(
            combat_active=True,
            schema_version=2,
            hp_state="HPCommitted",
            component_state="FullyCommitted",
            identities_valid=True,
        )

        self.assertEqual(decision.action, "retain")
        self.assertFalse(decision.mutate)
        self.assertEqual(decision.reason, "ValidActiveCommit")

    def test_reload_reconciliation_cleans_stale_commit_and_rolls_back_partial_states(self):
        model = load_model(self)

        cases = (
            (
                dict(
                    combat_active=False,
                    schema_version=2,
                    hp_state="HPCommitted",
                    component_state="FullyCommitted",
                    identities_valid=True,
                ),
                ("cleanup", "InactiveCombat"),
            ),
            (
                dict(
                    combat_active=True,
                    schema_version=2,
                    hp_state="ApplyingHP",
                    component_state=None,
                    identities_valid=True,
                ),
                ("rollback", "PendingApplication"),
            ),
            (
                dict(
                    combat_active=True,
                    schema_version=2,
                    hp_state="HPCommitted",
                    component_state="ApplyingAction",
                    identities_valid=True,
                ),
                ("rollback", "PendingApplication"),
            ),
            (
                dict(
                    combat_active=True,
                    schema_version=1,
                    hp_state="HPCommitted",
                    component_state="FullyCommitted",
                    identities_valid=True,
                ),
                ("cleanup", "UnsupportedSchema"),
            ),
            (
                dict(
                    combat_active=True,
                    schema_version=2,
                    hp_state="HPCommitted",
                    component_state="FullyCommitted",
                    identities_valid=False,
                ),
                ("cleanup", "IdentityMismatch"),
            ),
        )

        for arguments, expected in cases:
            with self.subTest(arguments=arguments):
                decision = model.reconcile_reload_state(**arguments)
                self.assertEqual((decision.action, decision.reason), expected)
                self.assertTrue(decision.mutate)


if __name__ == "__main__":
    unittest.main()
