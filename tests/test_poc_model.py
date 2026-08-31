import unittest


def load_model(test_case: unittest.TestCase):
    try:
        from tools import poc_model
    except (ImportError, ModuleNotFoundError) as error:
        test_case.fail(f"policy model must be implemented: {error}")
    return poc_model


class PocModelTests(unittest.TestCase):
    def test_build_policy_floors_average_and_calculates_party_factor(self):
        model = load_model(self)

        policy = model.build_policy([5, 7, 8])

        self.assertEqual(policy.eligible_size, 3)
        self.assertEqual(policy.level_sum, 20)
        self.assertEqual(policy.average_level, 6)
        self.assertEqual(policy.level_percent, 115)
        self.assertEqual(policy.party_percent, 140)
        self.assertFalse(policy.clamped)

    def test_build_policy_caps_only_the_balance_factor_above_eight(self):
        model = load_model(self)

        policy = model.build_policy([7] * 9)

        self.assertEqual(policy.eligible_size, 9)
        self.assertEqual(policy.party_percent, 240)
        self.assertTrue(policy.clamped)

    def test_build_policy_rejects_empty_or_non_positive_levels(self):
        model = load_model(self)

        with self.assertRaises(model.PolicyError):
            model.build_policy([])
        with self.assertRaises(model.PolicyError):
            model.build_policy([0, 7])

    def test_target_maximum_matches_hand_calculated_solo_and_three_member_values(self):
        model = load_model(self)

        self.assertEqual(model.target_maximum(100, model.build_policy([7])), 115)
        self.assertEqual(
            model.target_maximum(100, model.build_policy([5, 7, 8])),
            161,
        )

    def test_target_maximum_rejects_unsupported_tier_and_unsafe_product(self):
        model = load_model(self)

        with self.assertRaises(model.PolicyError):
            model.target_maximum(100, model.build_policy([9]))
        with self.assertRaises(model.PolicyError):
            model.target_maximum(100_000_000, model.build_policy([7]))

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
        self.assertEqual(merged.level_percent, 115)
        self.assertEqual(merged.party_percent, 140)


if __name__ == "__main__":
    unittest.main()
