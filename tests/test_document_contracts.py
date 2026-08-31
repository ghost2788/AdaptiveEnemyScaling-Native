import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_UUID = "bb8bdf43-775b-4451-9ffd-69b5f3f531e8"


class DocumentContracts(unittest.TestCase):
    def test_identity_is_consistent(self):
        identity_path = ROOT / "build/module-identity.json"
        self.assertTrue(identity_path.exists(), "module identity record must exist")
        identity = json.loads(
            identity_path.read_text(encoding="utf-8")
        )
        self.assertEqual(identity["moduleUuid"], MODULE_UUID)
        for name in ("README.md", "DESIGN.md"):
            self.assertIn(
                MODULE_UUID,
                (ROOT / name).read_text(encoding="utf-8"),
            )

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


if __name__ == "__main__":
    unittest.main()
