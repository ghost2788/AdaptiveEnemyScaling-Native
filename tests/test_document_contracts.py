import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_UUID = "a4567f52-1665-df50-b84c-3992f80fdb90"


class DocumentContracts(unittest.TestCase):
    def test_identity_is_consistent(self):
        identity_path = ROOT / "build/module-identity.json"
        self.assertTrue(identity_path.exists(), "module identity record must exist")
        identity = json.loads(
            identity_path.read_text(encoding="utf-8")
        )
        self.assertEqual(identity["moduleUuid"], MODULE_UUID)
        self.assertEqual(identity["version"], "0.1.0")
        self.assertEqual(identity["toolkitModuleVersion"], "1.0.0.0")
        self.assertEqual(identity["toolkitModuleVersion64"], 36028797018963968)
        self.assertEqual(identity["expectedFirstPublishVersion"], "1.0.0.1")
        for name in ("README.md", "DESIGN.md"):
            self.assertIn(
                MODULE_UUID,
                (ROOT / name).read_text(encoding="utf-8"),
            )

        meta = (
            ROOT
            / "toolkit"
            / "Mods"
            / identity["moduleFolder"]
            / "meta.lsx"
        ).read_text(encoding="utf-8")
        self.assertIn('value="Adaptive Enemy Scaling"', meta)
        self.assertIn('value="ghost"', meta)
        self.assertIn('value="36028797018963968"', meta)

    def test_upstream_hashes_are_exact(self):
        text = (ROOT / "UPSTREAM.md").read_text(encoding="utf-8")
        self.assertIn(
            "16B34DE94FDBD3704F8D3053A29CE00E9423DA774D8F2779B907455A68126B96",
            text,
        )
        self.assertIn(
            "3D5F28550D9633321E68531E069510A75965C633F461825EA791BC30153F41D9",
            text,
        )

    def test_no_script_extender_tree(self):
        offenders = [
            path
            for path in ROOT.rglob("*")
            if path.is_dir() and path.name == "ScriptExtender"
        ]
        self.assertEqual(offenders, [])

    def test_one_hp_probe_status_is_exact_and_hidden(self):
        status_path = (
            ROOT
            / "toolkit"
            / "Public"
            / "AdaptiveEnemyScalingNativePOC_a4567f52-1665-df50-b84c-3992f80fdb90"
            / "Stats"
            / "Generated"
            / "Data"
            / "Status_BOOST.txt"
        )
        self.assertTrue(status_path.exists(), "one-HP probe status must exist")
        text = status_path.read_text(encoding="utf-8")
        self.assertIn('new entry "AESN_HP_BIT_00001"', text)
        self.assertIn('data "StackId" "AESN_HP_BIT_00001"', text)
        self.assertIn('data "Boosts" "IncreaseMaxHP(1);"', text)
        self.assertIn(
            'data "StatusPropertyFlags" '
            '"DisableOverhead;DisableCombatlog;DisablePortraitIndicator"',
            text,
        )

    def test_flat_hp_probe_story_contract(self):
        init_path = ROOT / "story/RawFiles/Goals/AESN_00_Init.txt"
        harness_path = ROOT / "story/RawFiles/Goals/AESN_99_TestHarness.txt"
        self.assertTrue(init_path.exists(), "initialization goal must exist")
        self.assertTrue(harness_path.exists(), "flat-HP test harness must exist")

        init_text = init_path.read_text(encoding="utf-8")
        self.assertIn("DB_AESN_SchemaVersion(1);", init_text)
        self.assertIn("PROC_AESN_RecordDiagnostic", init_text)
        self.assertIn("DB_AESN_DiagnosticOnce", init_text)

        harness_text = harness_path.read_text(encoding="utf-8")
        for required in (
            "PROC_AESN_TestApplyOneHp",
            "PROC_AESN_TestRemoveOneHp",
            "GetHitpoints(",
            "GetHitpointsPercentage(",
            "GetMaxHitpoints(",
            'ApplyStatus(_Target, "AESN_HP_BIT_00001"',
            'RemoveStatus(_Target, "AESN_HP_BIT_00001"',
            'StatusApplied((CHARACTER)_Target, "AESN_HP_BIT_00001"',
            'StatusRemoved((CHARACTER)_Target, "AESN_HP_BIT_00001"',
            "SetHitpointsPercentage(",
            "DB_AESN_TestObservation",
        ):
            self.assertIn(required, harness_text)

    def test_editor_console_triggers_target_only_the_host_character(self):
        harness_text = (
            ROOT / "story/RawFiles/Goals/AESN_99_TestHarness.txt"
        ).read_text(encoding="utf-8")

        for event_name, procedure_name in (
            ("AESN_TEST_APPLY_ONE_HP", "PROC_AESN_TestApplyOneHp"),
            ("AESN_TEST_REMOVE_ONE_HP", "PROC_AESN_TestRemoveOneHp"),
        ):
            self.assertIn(f'TextEvent("{event_name}")', harness_text)
            event_position = harness_text.index(f'TextEvent("{event_name}")')
            host_position = harness_text.index(
                "GetHostCharacter(_Target)", event_position
            )
            call_position = harness_text.index(
                f"{procedure_name}(_Target);", host_position
            )
            self.assertLess(event_position, host_position)
            self.assertLess(host_position, call_position)

        self.assertIn(
            'DB_AESN_TestObservation("APPLY_POST"', harness_text
        )
        self.assertIn(
            'DB_AESN_TestObservation("REMOVE_POST"', harness_text
        )

    def test_editor_staged_target_probe_is_explicit_and_isolated(self):
        harness_text = (
            ROOT / "story/RawFiles/Goals/AESN_99_TestHarness.txt"
        ).read_text(encoding="utf-8")

        for required in (
            "DB_AESN_TestSpawnedTarget",
            'TextEvent("AESN_TEST_SPAWN_AND_APPLY_ONE_HP")',
            "CreateAtObject((CHARACTERROOT)"
            "Kobolds_Melee_Drunk_45e31b7d-32ec-4f3d-8067-79061aeec77b",
            "S_CampSetup_CAMP_TrainingDummy_"
            "9819c93a-fd5e-474a-b1b8-7ee0cc3a19a7",
            "SetCanFight((CHARACTER)_Target, 0);",
            "SetCanJoinCombat((CHARACTER)_Target, 0);",
            "DB_AESN_TestSpawnPendingReady((CHARACTER)_Target);",
            'RealtimeObjectTimerLaunch((CHARACTER)_Target, "AESN_CAP04_SPAWN_READY", 250);',
            'ObjectTimerFinished((CHARACTER)_Target, "AESN_CAP04_SPAWN_READY")',
            "PROC_AESN_TestApplyOneHp((CHARACTER)_Target);",
            'TextEvent("AESN_TEST_REMOVE_SPAWNED_ONE_HP")',
            "PROC_AESN_TestRemoveOneHp(_Target);",
        ):
            self.assertIn(required, harness_text)

    def test_flat_hp_probe_emits_strict_pass_only_debug_records(self):
        harness_text = (
            ROOT / "story/RawFiles/Goals/AESN_99_TestHarness.txt"
        ).read_text(encoding="utf-8")

        for required in (
            '"AESN_CAP04 APPLY beforeCurrent="',
            '"AESN_CAP04 REMOVE beforeCurrent="',
            '",percentagePreserved=1,bit=1"',
            "IntegerSum(_BeforeMaximum, 1, _ExpectedMaximum)",
            "IntegerSubtract(_BeforeMaximum, 1, _ExpectedMaximum)",
            "_AfterPercentage == _BeforePercentage",
            "DebugLog(_Message);",
        ):
            self.assertIn(required, harness_text)

    def test_flat_hp_dead_probe_skips_mutation_and_retires_target(self):
        harness_text = (
            ROOT / "story/RawFiles/Goals/AESN_99_TestHarness.txt"
        ).read_text(encoding="utf-8")

        for required in (
            'TextEvent("AESN_TEST_SPAWN_DEAD_AND_APPLY_ONE_HP")',
            "DB_AESN_TestSpawnPendingDeath",
            "Die((CHARACTER)_Target, DEATHTYPE.DoT,",
            'DB_AESN_TestObservation("SKIP_DEAD"',
            'DB_AESN_TestObservation("SKIP_DEAD_POST"',
            '"AESN_CAP04 SKIP_DEAD current="',
            '",statusApplied=0,percentageWrite=0"',
            'HasActiveStatus(_Target, "AESN_HP_BIT_00001", 0)',
            "_BeforeCurrent > 0",
            "_AfterCurrent == 0",
        ):
            self.assertIn(required, harness_text)


if __name__ == "__main__":
    unittest.main()
