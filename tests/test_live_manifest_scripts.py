import json
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "tools/capture_live_manifest.ps1"
COMPARE = ROOT / "tests/verify_live_directories_unchanged.ps1"


def run_powershell(script: pathlib.Path, *arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["powershell", "-NoProfile", "-File", str(script), *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class LiveManifestScriptsTests(unittest.TestCase):
    def test_capture_is_stable_and_comparison_detects_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            mods = root / "Mods"
            mods.mkdir()
            (mods / "example.pak").write_bytes(b"original")
            settings = root / "modsettings.lsx"
            settings.write_text("original settings", encoding="utf-8")
            before = root / "before.json"
            same = root / "same.json"
            changed = root / "changed.json"

            for output in (before, same):
                result = run_powershell(
                    CAPTURE,
                    "-OutputPath",
                    str(output),
                    "-ModsPath",
                    str(mods),
                    "-ModSettingsPath",
                    str(settings),
                )
                self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

            self.assertEqual(
                json.loads(before.read_text(encoding="utf-8-sig")),
                json.loads(same.read_text(encoding="utf-8-sig")),
            )
            equal_result = run_powershell(
                COMPARE,
                "-Before",
                str(before),
                "-After",
                str(same),
            )
            self.assertEqual(
                equal_result.returncode,
                0,
                equal_result.stderr or equal_result.stdout,
            )

            (mods / "example.pak").write_bytes(b"changed")
            capture_changed = run_powershell(
                CAPTURE,
                "-OutputPath",
                str(changed),
                "-ModsPath",
                str(mods),
                "-ModSettingsPath",
                str(settings),
            )
            self.assertEqual(
                capture_changed.returncode,
                0,
                capture_changed.stderr or capture_changed.stdout,
            )
            changed_result = run_powershell(
                COMPARE,
                "-Before",
                str(before),
                "-After",
                str(changed),
            )
            self.assertNotEqual(changed_result.returncode, 0)
            self.assertIn("example.pak", changed_result.stdout)


if __name__ == "__main__":
    unittest.main()
