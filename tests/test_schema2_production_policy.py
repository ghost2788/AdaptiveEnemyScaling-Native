import pathlib
import re
import unittest

from tools.poc_model import build_policy


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE = "AdaptiveEnemyScalingNativePOC_a4567f52-1665-df50-b84c-3992f80fdb90"
GOALS = ROOT / "story" / "RawFiles" / "Goals"
STATUS = (
    ROOT
    / "toolkit"
    / "Public"
    / MODULE
    / "Stats"
    / "Generated"
    / "Data"
    / "Status_BOOST.txt"
)
LOCALIZATION = (
    ROOT
    / "toolkit"
    / "Mods"
    / MODULE
    / "Localization"
    / "English"
    / "AdaptiveEnemyScalingNativePOC.xml"
)


def status_entries():
    text = STATUS.read_text(encoding="utf-8")
    matches = list(re.finditer(r'^new entry "([^"]+)"$', text, re.MULTILINE))
    result = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        result[match.group(1)] = text[match.start():end]
    return result


class Schema2ProductionPolicyContracts(unittest.TestCase):
    def test_hp_breakdown_uses_friendly_shared_source_name(self):
        """Catch internal binary status IDs leaking into the Hit Points tooltip."""
        entries = status_entries()
        hp_bits = {
            name: entry
            for name, entry in entries.items()
            if name.startswith("AESN_HP_BIT_")
        }
        self.assertEqual(16, len(hp_bits))
        for status_id, entry in hp_bits.items():
            self.assertIn(
                'data "DisplayName" "AESNHpSourceName;1"',
                entry,
                status_id,
            )

        localization = LOCALIZATION.read_text(encoding="utf-8")
        self.assertIn(
            'contentuid="AESNHpSourceName" version="1">Adaptive Enemy Scaling</content>',
            localization,
        )

    def test_upgrade_save_reseeds_static_data_and_resumes_incomplete_snapshot(self):
        """Catch saves whose completed INITSECTION predates schema-2 static rows."""
        init = (GOALS / "AESN_00_Init.txt").read_text(encoding="utf-8")
        policy = (GOALS / "AESN_20_Policy.txt").read_text(encoding="utf-8")

        self.assertRegex(
            init,
            r"IF\s+SavegameLoaded\(\)\s+THEN\s+DB_AESN_RelentlessCapability\(1\);",
            "an upgraded save must regain the verified Relentless capability fact",
        )

        reload_match = re.search(
            r"IF\s+SavegameLoaded\(\)\s+THEN(?P<actions>.*?)"
            r"\n\s*\nPROC\s+PROC_AESN_ResumeIncompleteSnapshots\(\)",
            policy,
            re.DOTALL,
        )
        self.assertIsNotNone(reload_match)
        expected_bands = (
            (1, 4, 1, 125, 1, 0, 0, 0),
            (5, 8, 2, 150, 2, 1, 1, 0),
            (9, 12, 3, 180, 3, 1, 1, 0),
            (13, 16, 4, 220, 4, 2, 1, 1),
            (17, 18, 5, 260, 5, 2, 2, 1),
            (19, 2147483647, 6, 300, 6, 3, 2, 2),
        )
        reseed_actions = reload_match.group("actions")
        for band in expected_bands:
            args = ", ".join(str(value) for value in band)
            self.assertIn(
                f"DB_AESN_HardenedPolicyBand({args})",
                reseed_actions,
                "every schema-2 policy row must be restored on upgrade load",
            )
        self.assertIn(
            "PROC_AESN_ResumeIncompleteSnapshots()",
            reseed_actions,
            "a combat already counted before the fix must resume without re-entering combat",
        )
        self.assertRegex(
            policy,
            r"(?s)PROC\s+PROC_AESN_ResumeIncompleteSnapshots\(\)"
            r".*?DB_AESN_RosterAggregate\(_Combat, _EligibleSize, _LevelSum\)"
            r".*?NOT DB_AESN_CombatSnapshotV2\(_Combat, _, _, _, _, _, _, _, _, _, _, _\)"
            r".*?THEN\s+PROC_AESN_FinalizeSnapshot\(_Combat\);",
            "recovery must finalize only an aggregate that has no schema-2 snapshot",
        )

    def test_schema2_snapshot_contains_frozen_policy_outputs(self):
        init = (GOALS / "AESN_00_Init.txt").read_text(encoding="utf-8")
        policy = (GOALS / "AESN_20_Policy.txt").read_text(encoding="utf-8")

        self.assertIn("DB_AESN_SchemaVersion(2);", init)
        self.assertIn("SavegameLoaded()", init)
        self.assertIn("DB_AESN_SchemaVersion(_PersistedVersion)", init)
        self.assertIn("_PersistedVersion != 2", init)
        self.assertIn("NOT DB_AESN_SchemaVersion(_PersistedVersion);", init)
        self.assertRegex(init, r"(?m)^DB_AESN_RelentlessCapability\(1\);$")
        self.assertNotIn("NOT DB_AESN_RelentlessCapability(1);", init)
        self.assertIn(
            "NOT DB_AESN_CombatSnapshot((GUIDSTRING)NULL_00000000-0000-0000-0000-000000000000, "
            '0, 0, 0, 0, 0, 0, "");',
            init,
        )
        self.assertIn("DB_AESN_CombatSnapshotV2(", policy)
        for token in (
            "_EffectiveSize",
            "_HardenedTier",
            "_TargetHpPercent",
            "_ActionBudget",
            "_BonusActionBudget",
            "_RecipientCap",
        ):
            self.assertIn(token, policy)
        expected_bands = (
            (1, 4, 1, 125, 1, 0, 0, 0),
            (5, 8, 2, 150, 2, 1, 1, 0),
            (9, 12, 3, 180, 3, 1, 1, 0),
            (13, 16, 4, 220, 4, 2, 1, 1),
            (17, 18, 5, 260, 5, 2, 2, 1),
            (19, 2147483647, 6, 300, 6, 3, 2, 2),
        )
        for band in expected_bands:
            args = ", ".join(str(value) for value in band)
            self.assertIn(f"DB_AESN_HardenedPolicyBand({args});", policy)
        self.assertIn(
            "DB_AESN_HardenedPolicyBand(_MinLevel, _MaxLevel, "
            "_HardenedTier, _SoloHpPercent, _AttackBonus, _AcBonus, "
            "_BaseActionBudget, _BaseBonusActionBudget)",
            policy,
        )
        self.assertIn("_AverageLevel >= _MinLevel", policy)
        self.assertIn("_AverageLevel <= _MaxLevel", policy)
        self.assertIn("IntegerProduct(_PartyMinusOne, 20, _PartyBonus)", policy)
        self.assertIn("PartySizeClampedAbove12", policy)

    def test_six_hardened_statuses_have_exact_non_damage_bonuses(self):
        entries = status_entries()
        expected = {
            1: "RollBonus(Attack,1);RollBonus(SavingThrow,1);SpellSaveDC(1);",
            2: "RollBonus(Attack,2);RollBonus(SavingThrow,2);AC(1);SpellSaveDC(2);",
            3: "RollBonus(Attack,3);RollBonus(SavingThrow,3);AC(1);SpellSaveDC(3);",
            4: "RollBonus(Attack,4);RollBonus(SavingThrow,4);AC(2);SpellSaveDC(4);",
            5: "RollBonus(Attack,5);RollBonus(SavingThrow,5);AC(2);SpellSaveDC(5);",
            6: "RollBonus(Attack,6);RollBonus(SavingThrow,6);AC(3);SpellSaveDC(6);",
        }
        for tier, boosts in expected.items():
            status_id = f"AESN_HARDENED_FOE_{tier:02d}"
            entry = entries[status_id]
            self.assertIn(f'data "Icon" "AESN_HardenedFoe_{tier:02d}"', entry)
            self.assertIn(f'data "Boosts" "{boosts}"', entry)
            self.assertNotIn("Damage", entry)
            self.assertNotIn("DisablePortraitIndicator", entry)

    def test_relentless_definitions_are_cumulative_and_component_layer_delegates(self):
        entries = status_entries()
        tier_one = entries["AESN_RELENTLESS_FOE_01"]
        tier_two = entries["AESN_RELENTLESS_FOE_02"]
        self.assertIn('data "Boosts" "ActionResource(ActionPoint,1,0);"', tier_one)
        self.assertIn(
            'data "Boosts" "ActionResource(ActionPoint,1,0);'
            'ActionResource(BonusActionPoint,1,0);"',
            tier_two,
        )
        self.assertIn('data "Icon" "AESN_RelentlessFoe_01"', tier_one)
        self.assertIn('data "Icon" "AESN_RelentlessFoe_02"', tier_two)

        components = (GOALS / "AESN_55_Components.txt").read_text(encoding="utf-8")
        self.assertNotIn('ApplyStatus(_Enemy, "AESN_RELENTLESS_FOE_', components)

    def test_hardened_tooltips_lead_with_qualitative_flavor(self):
        localization = LOCALIZATION.read_text(encoding="utf-8")
        for tier in range(1, 7):
            description = re.search(
                rf'contentuid="AESNHardenedFoe{tier:02d}Description"[^>]*>(.*?)</content>',
                localization,
            )
            self.assertIsNotNone(description)
            flavor = description.group(1).split("&lt;br&gt;", 1)[0]
            self.assertNotRegex(flavor, r"(?:\+|\b\d+%|\b\d+ additional)")

    def test_compact_status_names_and_hybrid_mechanics_copy(self):
        localization = LOCALIZATION.read_text(encoding="utf-8")
        hardened_values = {
            1: "+1 to Attack Rolls, Saving Throws, and Spell Save DC.",
            2: "+2 to Attack Rolls, Saving Throws, and Spell Save DC; +1 Armour Class.",
            3: "+3 to Attack Rolls, Saving Throws, and Spell Save DC; +1 Armour Class.",
            4: "+4 to Attack Rolls, Saving Throws, and Spell Save DC; +2 Armour Class.",
            5: "+5 to Attack Rolls, Saving Throws, and Spell Save DC; +2 Armour Class.",
            6: "+6 to Attack Rolls, Saving Throws, and Spell Save DC; +3 Armour Class.",
        }
        roman = ("I", "II", "III", "IV", "V", "VI")
        for tier, mechanics in hardened_values.items():
            self.assertIn(
                f'contentuid="AESNHardenedFoe{tier:02d}Name" version="1">'
                f'Hardened {roman[tier - 1]}',
                localization,
            )
            description = re.search(
                rf'contentuid="AESNHardenedFoe{tier:02d}Description"[^>]*>(.*?)</content>',
                localization,
            )
            self.assertIsNotNone(description)
            self.assertIn("Increased maximum HP", description.group(1))
            self.assertIn(mechanics, description.group(1))

        relentless_values = {
            1: "+1 Action.",
            2: "+1 Action and +1 Bonus Action.",
        }
        for tier, mechanics in relentless_values.items():
            self.assertIn(
                f'contentuid="AESNRelentlessFoe{tier:02d}Name" version="1">'
                f'Relentless {roman[tier - 1]}',
                localization,
            )
            description = re.search(
                rf'contentuid="AESNRelentlessFoe{tier:02d}Description"[^>]*>(.*?)</content>',
                localization,
            )
            self.assertIsNotNone(description)
            self.assertIn(mechanics, description.group(1))

    def test_hp_planner_uses_frozen_total_percent_directly(self):
        planner = (GOALS / "AESN_40_HpTransaction.txt").read_text(encoding="utf-8")
        self.assertIn(
            "IntegerProduct(_BeforeMaximum, _TargetHpPercent, _CombinedProduct)",
            planner,
        )
        self.assertIn("IntegerDivide(_CombinedProduct, 100, _TargetMaximum)", planner)
        self.assertNotIn("_LevelPercent", planner)
        self.assertNotIn("_PartyPercent", planner)

    def test_production_contains_no_reload_proof_notifications(self):
        for path in GOALS.glob("AESN_*.txt"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("ShowNotification(", text, path.name)

    def test_test_only_component_status_registry_is_not_in_production(self):
        components = (GOALS / "AESN_55_Components.txt").read_text(encoding="utf-8")
        pending_probe = (GOALS / "AESN_35_PendingReloadProbe.txt").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("DB_AESN_ComponentStatusId", components)
        self.assertIn('DB_AESN_ComponentStatusId("AESN_HARDENED_FOE_01");', pending_probe)
        self.assertIn('DB_AESN_ComponentStatusId("AESN_RELENTLESS_FOE_02");', pending_probe)
        self.assertIn('DB_AESN_ComponentStatusId("AESN_TIER_LEVEL_05_08");', pending_probe)

    def test_relentless_allocator_is_persistent_and_enabled_after_verified_proof(self):
        allocator = (GOALS / "AESN_56_Relentless.txt").read_text(encoding="utf-8")
        for required in (
            "DB_AESN_RelentlessCapability(1)",
            "DB_AESN_RelentlessLedger",
            "DB_AESN_RelentlessRecipient",
            "DB_AESN_RelentlessApplication",
            "DB_AESN_RelentlessRejected",
            'GetActionResourceValuePersonal(_Enemy, "ActionPoint", 0, _ActionValue)',
            'GetActionResourceValuePersonal(_Enemy, "BonusActionPoint", 0, _BonusActionValue)',
            'ApplyStatus(_Enemy, "AESN_RELENTLESS_FOE_01"',
            'ApplyStatus(_Enemy, "AESN_RELENTLESS_FOE_02"',
            'DB_AESN_EnemyComponent(_Combat, _Enemy, "Relentless", _Status)',
        ):
            self.assertIn(required, allocator)
        self.assertIn("_ActionValue > 1.0", allocator)
        self.assertIn("_BonusActionValue > 1.0", allocator)

        init = (GOALS / "AESN_00_Init.txt").read_text(encoding="utf-8")
        self.assertRegex(
            init,
            r"(?m)^DB_AESN_RelentlessCapability\(1\);$",
            "production Relentless may be enabled only after the live proof passes",
        )
        self.assertNotIn("NOT DB_AESN_RelentlessCapability(1);", init)

    def test_action_resource_proof_exercises_hostile_values_and_cleanup(self):
        proof = (GOALS / "AESN_87_ActionResourceProof.txt").read_text(
            encoding="utf-8"
        )
        for required in (
            'TextEvent("AESN_TEST_ACTION_RESOURCE_PROOF")',
            "CreateAtObject((CHARACTERROOT)Kobolds_Melee_Drunk_45e31b7d-32ec-4f3d-8067-79061aeec77b",
            "SetFaction(_Ally, _HostFaction)",
            "SetCanFight(_Ally, 1)",
            "SetCanJoinCombat(_Ally, 1)",
            "PROC_EnterCombat(_Enemy, _Ally)",
            "TurnStarted(_Object)",
            'DB_AESN_ActionProofActive(_Combat, (CHARACTER)_Object, "WaitingRelentlessITurn")',
            'DB_AESN_ActionProofActive(_Combat, (CHARACTER)_Object, "WaitingRelentlessICleanupTurn")',
            'DB_AESN_ActionProofActive(_Combat, (CHARACTER)_Object, "WaitingRelentlessIITurn")',
            'DB_AESN_ActionProofActive(_Combat, (CHARACTER)_Object, "WaitingRelentlessIICleanupTurn")',
            'GetActionResourceValuePersonal((CHARACTER)_Object, "ActionPoint", 0, _ActionValue)',
            'GetActionResourceValuePersonal((CHARACTER)_Object, "BonusActionPoint", 0, _BonusActionValue)',
            'ApplyStatus((CHARACTER)_Object, "AESN_RELENTLESS_FOE_01"',
            'RemoveStatus(_Enemy, "AESN_RELENTLESS_FOE_01"',
            'ApplyStatus((CHARACTER)_Object, "AESN_RELENTLESS_FOE_02"',
            'RemoveStatus((CHARACTER)_Object, "AESN_RELENTLESS_FOE_02"',
            'DB_AESN_RelentlessRejected(_Combat, _Enemy, "PreexistingActionResource")',
            "normal=1/1,relentlessI=2/1,relentlessII=2/2,cleanup=1/1,preexistingSkipped=1",
        ):
            self.assertIn(required, proof)
        self.assertGreaterEqual(
            proof.count(
                "CreateAtObject((CHARACTERROOT)Kobolds_Melee_Drunk_45e31b7d-32ec-4f3d-8067-79061aeec77b"
            ),
            2,
            "the native resource proof must use an ordinary spawned-NPC pair",
        )
        self.assertNotIn(
            "DB_AESN_EnemyEligible(_Combat, _Enemy)",
            proof,
            "production eligibility is proved by the separate narrative trace, not fabricated in the resource fixture",
        )
        self.assertNotIn("DB_AESN_ActionProofHostFlags", proof)
        self.assertNotIn("ShowNotification(", proof)
        self.assertNotRegex(
            proof,
            r"StatusApplied\([^\n]+AESN_RELENTLESS_FOE_01.*?"
            r"GetActionResourceValuePersonal\([^\n]+ActionPoint[^\n]+2\.0",
            "Relentless I must be measured after turn refresh, not synchronously in StatusApplied",
        )
        rule_conditions = re.findall(r"(?:IF|PROC)\s+(.*?)\s+THEN", proof, re.DOTALL)
        self.assertFalse(
            any(
                "StatusRemoved(" in condition
                and "GetActionResourceValuePersonal(" in condition
                for condition in rule_conditions
            ),
            "resource cleanup must be measured on the next turn refresh, not synchronously in StatusRemoved",
        )

    def test_action_resource_proof_consumes_failure_records(self):
        proof = (GOALS / "AESN_87_ActionResourceProof.txt").read_text(
            encoding="utf-8"
        )
        rule_conditions = re.findall(r"(?:IF|PROC)\s+(.*?)\s+THEN", proof, re.DOTALL)
        self.assertTrue(
            any(
                re.search(r"\bDB_AESN_ActionProofFailure\s*\(", condition)
                for condition in rule_conditions
            ),
            "ActionProofFailure must be positively queried so the Toolkit does not reject it as an orphan database",
        )

    def test_story_policy_harness_covers_every_boundary_and_party_size(self):
        harness = (GOALS / "AESN_86_PolicyHarness.txt").read_text(
            encoding="utf-8"
        )
        rows = re.findall(
            r"DB_AESN_PolicyHarnessCase\("
            r"(\d+), (\d+), (\d+), (\d+), (\d+), (\d+), (\d+), (\d+)\);",
            harness,
        )
        self.assertEqual(144, len(rows))
        boundaries = (1, 4, 5, 8, 9, 12, 13, 16, 17, 18, 19, 20)
        observed = set()
        for _, level, size, tier, hp, action, bonus, cap in rows:
            values = tuple(map(int, (level, size, tier, hp, action, bonus, cap)))
            level_value, size_value, tier_value, hp_value, action_value, bonus_value, cap_value = values
            policy = build_policy([level_value] * size_value)
            self.assertEqual(
                (
                    policy.hardened_tier,
                    policy.target_hp_percent,
                    policy.action_budget,
                    policy.bonus_action_budget,
                    policy.recipient_cap,
                ),
                (tier_value, hp_value, action_value, bonus_value, cap_value),
            )
            observed.add((level_value, size_value))
        self.assertEqual(
            {(level, size) for level in boundaries for size in range(1, 13)},
            observed,
        )
        self.assertIn('TextEvent("AESN_TEST_SCHEMA2_POLICY_MATRIX")', harness)
        self.assertIn("AESN_POLICY_HARNESS PASS cases=144", harness)


if __name__ == "__main__":
    unittest.main()
