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


if __name__ == "__main__":
    unittest.main()
