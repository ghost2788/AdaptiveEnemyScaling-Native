import pathlib
import json
import shutil
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SYNC = ROOT / "tools/sync_toolkit_project.ps1"


def run_sync(toolkit_data_root: pathlib.Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-File",
            str(SYNC),
            "-ToolkitDataRoot",
            str(toolkit_data_root),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class SyncToolkitProjectTests(unittest.TestCase):
    def test_production_sync_removes_only_the_isolated_hp_proof_stats(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            repo = root / 'repo'
            data = root / 'Data'
            module = 'AESN_Test_Module'
            for relative in ('tools', 'evidence', 'build', 'toolkit/Mods',
                             'toolkit/Public', 'story/RawFiles/Goals'):
                (repo / relative).mkdir(parents=True)
            data.mkdir()
            shutil.copy2(SYNC, repo / 'tools/sync_toolkit_project.ps1')
            (repo / 'evidence/toolkit-paths.json').write_text(json.dumps({'gameDataRoot': str(data)}))
            (repo / 'build/module-identity.json').write_text(json.dumps({'moduleFolder': module}))
            stats = data / 'Public' / module / 'Stats/Generated/Data'
            stats.mkdir(parents=True)
            proof = stats / 'Status_AESN_HpTooltipProof.txt'
            production = stats / 'Status_BOOST.txt'
            unrelated = stats / 'Status_Other.txt'
            proof.write_text('temporary proof')
            production.write_text('production sentinel')
            unrelated.write_text('unrelated sentinel')
            result = subprocess.run(['powershell', '-NoProfile', '-File',
                                     str(repo / 'tools/sync_toolkit_project.ps1'),
                                     '-ToolkitDataRoot', str(data)],
                                    capture_output=True, text=True, check=False)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertFalse(proof.exists(), 'Temporary proof stats leaked into production staging')
            self.assertEqual('production sentinel', production.read_text())
            self.assertEqual('unrelated sentinel', unrelated.read_text())

    def test_rejects_unverified_destination_before_copying(self):
        self.assertTrue(SYNC.exists(), "Toolkit sync script must exist")
        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary) / "Data"
            destination.mkdir()
            result = run_sync(destination)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("verified Toolkit data root", result.stderr + result.stdout)
            self.assertEqual(list(destination.iterdir()), [])

    def test_script_has_exact_sources_and_live_mod_refusal(self):
        text = SYNC.read_text(encoding="utf-8")
        for required in (
            "evidence/toolkit-paths.json",
            "build/module-identity.json",
            "toolkit\\Mods",
            "toolkit\\Public",
            "story\\RawFiles\\Goals",
            "AppData\\Local\\Larian Studios\\Baldur's Gate 3\\Mods",
        ):
            self.assertIn(required, text)

    def test_production_sync_excludes_test_and_proof_goals_by_default(self):
        text = SYNC.read_text(encoding="utf-8")
        self.assertIn("[switch]$IncludeTestHarnesses", text)
        for production_goal in (
            "AESN_00_Init.txt",
            "AESN_10_Roster.txt",
            "AESN_20_Policy.txt",
            "AESN_25_WorldHardened.txt",
            "AESN_30_Combat.txt",
            "AESN_40_HpTransaction.txt",
            "AESN_50_Applications.txt",
            "AESN_55_Components.txt",
            "AESN_56_Relentless.txt",
            "AESN_60_Merge.txt",
            "AESN_65_Reconciliation.txt",
            "AESN_66_WorldHardenedRuntime.txt",
        ):
            self.assertIn(f"'{production_goal}'", text)
        self.assertIn("Remove-Item -LiteralPath $destinationFile -Force", text)
        self.assertIn("-not $IncludeTestHarnesses", text)
        self.assertIn("Get-ChildItem -LiteralPath $productionGoalsDestination", text)
        self.assertIn("-Filter 'AESN_*.txt'", text)
        self.assertIn("$productionGoalNames -notcontains $stagedGoal.Name", text)

    def test_action_resource_proof_staging_is_explicit_and_source_preserving(self):
        text = SYNC.read_text(encoding="utf-8")
        self.assertIn("[switch]$EnableActionResourceProof", text)
        self.assertIn(
            "EnableActionResourceProof requires IncludeTestHarnesses", text
        )
        self.assertIn("AESN_87_ActionResourceProof.txt", text)
        self.assertIn("NOT DB_AESN_ActionProofHarnessEnabled(1);", text)
        self.assertIn("DB_AESN_ActionProofHarnessEnabled(1);", text)
        self.assertIn("Set-Content -LiteralPath $actionProofGoal", text)

    def test_world_hardened_proof_staging_is_explicit_and_source_preserving(self):
        text = SYNC.read_text(encoding="utf-8")
        self.assertIn("[switch]$EnableWorldHardenedProof", text)
        self.assertIn(
            "EnableWorldHardenedProof requires IncludeTestHarnesses", text
        )
        self.assertIn("AESN_84_WorldHardenedHarness.txt", text)
        self.assertIn("NOT DB_AESN_WorldHarnessEnabled(1);", text)
        self.assertIn("DB_AESN_WorldHarnessEnabled(1);", text)
        self.assertIn("Set-Content -LiteralPath $worldProofGoal", text)

    def test_boss_priority_proof_staging_is_explicit_and_source_preserving(self):
        text = SYNC.read_text(encoding="utf-8")
        self.assertIn("[switch]$EnableBossPriorityProof", text)
        self.assertIn(
            "EnableBossPriorityProof requires IncludeTestHarnesses", text
        )
        self.assertIn("AESN_85_BossPriorityHarness.txt", text)
        self.assertIn("NOT DB_AESN_BossPriorityHarnessEnabled(1);", text)
        self.assertIn("DB_AESN_BossPriorityHarnessEnabled(1);", text)
        self.assertIn("Set-Content -LiteralPath $bossPriorityProofGoal", text)


if __name__ == "__main__":
    unittest.main()
