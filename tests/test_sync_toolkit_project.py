import pathlib
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
            "AESN_30_Combat.txt",
            "AESN_40_HpTransaction.txt",
            "AESN_50_Applications.txt",
            "AESN_55_Components.txt",
            "AESN_56_Relentless.txt",
            "AESN_60_Merge.txt",
            "AESN_65_Reconciliation.txt",
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


if __name__ == "__main__":
    unittest.main()
