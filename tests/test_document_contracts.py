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


if __name__ == "__main__":
    unittest.main()
