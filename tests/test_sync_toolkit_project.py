import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SYNC = ROOT / "tools/sync_toolkit_project.ps1"
CATALOG = ROOT / "artifacts/hp-catalog/Status_AESN_HP_Total.txt"
MODULE = "AESN_Test_Module"
UUID = "a4567f52-1665-df50-b84c-3992f80fdb90"


def _meta(uuid=UUID, publish_handle="6353123", marker="source"):
    return f'''<?xml version="1.0" encoding="utf-8"?>
<save><region><node id="Module">
<children><node id="Dependencies"><children><node id="ModuleShortDesc">
<attribute id="UUID" value="cb555efe-2d9e-131f-8195-a89329d218ea"/>
<attribute id="PublishHandle" value="0"/>
</node></children></node>
<node id="ModuleInfo"><attribute id="UUID" value="{uuid}"/>
<attribute id="PublishHandle" value="{publish_handle}"/>
<attribute id="Marker" value="{marker}"/></node></children>
</node></region></save>\n'''


class SyncToolkitProjectTests(unittest.TestCase):
    def make_fixture(self):
        temporary = tempfile.TemporaryDirectory()
        root = pathlib.Path(temporary.name)
        repo = root / "repo"
        data = root / "Data"
        for relative in ("tools", "evidence", "build", "toolkit/Mods",
                         "toolkit/Public", "story/RawFiles/Goals"):
            (repo / relative).mkdir(parents=True)
        data.mkdir()
        shutil.copy2(SYNC, repo / "tools/sync_toolkit_project.ps1")
        shutil.copy2(ROOT / "tools/hp_catalog.py", repo / "tools/hp_catalog.py")
        (repo / "evidence/toolkit-paths.json").write_text(
            json.dumps({"gameDataRoot": str(data)}), encoding="utf-8"
        )
        (repo / "build/module-identity.json").write_text(json.dumps({
            "moduleFolder": MODULE, "moduleUuid": UUID
        }), encoding="utf-8")
        source_module = repo / "toolkit/Mods" / MODULE
        source_module.mkdir()
        (source_module / "meta.lsx").write_text(_meta(), encoding="utf-8")
        public = repo / "toolkit/Public" / MODULE / "Stats/Generated/Data"
        public.mkdir(parents=True)
        (public / "Status_BOOST.txt").write_text("production source", encoding="utf-8")
        goals = repo / "story/RawFiles/Goals"
        for name in ("AESN_00_Init.txt", "AESN_45_HpTotal.txt", "AESN_47_HpMigration.txt",
                     "AESN_81_HpWoundedProof.txt"):
            (goals / name).write_text(name, encoding="utf-8")
        return temporary, repo, data

    def run_sync(self, repo, data, catalog=CATALOG, *extra):
        return subprocess.run([
            "powershell", "-NoProfile", "-File", str(repo / "tools/sync_toolkit_project.ps1"),
            "-ToolkitDataRoot", str(data), "-CatalogPath", str(catalog), *extra
        ], cwd=repo, capture_output=True, text=True, check=False)

    def test_candidate_sync_delivers_total_backend_catalog_and_preserves_metadata(self):
        temporary, repo, data = self.make_fixture()
        with temporary:
            destination_module = data / "Mods" / MODULE
            destination_module.mkdir(parents=True)
            existing_meta = _meta(marker="destination")
            (destination_module / "meta.lsx").write_text(existing_meta, encoding="utf-8")
            proof_goal = destination_module / "Story/RawFiles/Goals/AESN_84_HpIntegrationProof.txt"
            proof_goal.parent.mkdir(parents=True)
            proof_goal.write_text("old proof", encoding="utf-8")
            unrelated_goal = proof_goal.with_name("AESN_User_Custom.txt")
            unrelated_goal.write_text("keep", encoding="utf-8")
            result = self.run_sync(repo, data)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual(existing_meta, (destination_module / "meta.lsx").read_text(encoding="utf-8"))
            goals = destination_module / "Story/RawFiles/Goals"
            self.assertTrue((goals / "AESN_45_HpTotal.txt").exists())
            self.assertTrue((goals / "AESN_47_HpMigration.txt").exists())
            self.assertFalse((goals / "AESN_81_HpWoundedProof.txt").exists())
            self.assertFalse(proof_goal.exists())
            self.assertEqual("keep", unrelated_goal.read_text(encoding="utf-8"))
            staged_catalog = data / "Public" / MODULE / "Stats/Generated/Data/Status_AESN_HP_Total.txt"
            self.assertEqual(CATALOG.read_bytes(), staged_catalog.read_bytes())

    def test_missing_or_bad_catalog_fails_before_any_destination_write(self):
        for catalog in (ROOT / "missing-catalog.txt",):
            temporary, repo, data = self.make_fixture()
            with temporary:
                sentinel = data / "sentinel.txt"
                sentinel.write_text("unchanged", encoding="utf-8")
                result = self.run_sync(repo, data, catalog)
                self.assertNotEqual(0, result.returncode)
                self.assertEqual("unchanged", sentinel.read_text(encoding="utf-8"))
        temporary, repo, data = self.make_fixture()
        with temporary:
            bad = data.parent / "bad-catalog.txt"
            bad.write_text("not a catalog", encoding="utf-8")
            sentinel = data / "sentinel.txt"
            sentinel.write_text("unchanged", encoding="utf-8")
            result = self.run_sync(repo, data, bad)
            self.assertNotEqual(0, result.returncode)
            self.assertEqual("unchanged", sentinel.read_text(encoding="utf-8"))

    def test_mismatched_destination_metadata_and_unverified_root_are_rejected(self):
        temporary, repo, data = self.make_fixture()
        with temporary:
            destination_module = data / "Mods" / MODULE
            destination_module.mkdir(parents=True)
            (destination_module / "meta.lsx").write_text(_meta(uuid="wrong"), encoding="utf-8")
            result = self.run_sync(repo, data)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("Existing Toolkit metadata module UUID", result.stdout + result.stderr)
            self.assertFalse((data / "Public").exists())
            other = data.parent / "other"
            other.mkdir()
            result = self.run_sync(repo, other)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("verified Toolkit data root", result.stdout + result.stderr)

    def test_script_requires_exact_catalog_and_explicit_inventory(self):
        text = SYNC.read_text(encoding="utf-8")
        for required in (
            "[string]$CatalogPath", "F54D4F4304F46E54976D206917D1FD30FB8226009C776DB1494C85553E47817A",
            "AESN_45_HpTotal.txt", "AESN_47_HpMigration.txt",
            "AESN_84_HpIntegrationProof.txt", "module UUID", "PublishHandle",
            "hp_catalog.py", "-not $IncludeTestHarnesses",
            "//node[@id='ModuleInfo']/attribute[@id='UUID']",
        ):
            self.assertIn(required, text)
        self.assertNotIn("$productionGoalNames -notcontains $stagedGoal.Name", text)


if __name__ == "__main__":
    unittest.main()
