import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools import hp_catalog as catalog


class StatusIdTests(unittest.TestCase):
    def test_returns_exact_named_id_for_supported_positive_deltas(self):
        # Catches a wrong prefix, decimal conversion, or boundary selection.
        for delta, expected in [
            (0, None),
            (1, "AESN_HP_TOTAL_1"),
            (111, "AESN_HP_TOTAL_111"),
            (32768, "AESN_HP_TOTAL_32768"),
            (65535, "AESN_HP_TOTAL_65535"),
        ]:
            self.assertEqual(expected, catalog.status_id(delta))

    def test_rejects_values_outside_the_supported_integer_range(self):
        # Catches acceptance of overflow, bool, or non-integer values.
        for invalid in [-1, 65536, True, 1.0, "111", None]:
            with self.assertRaises(ValueError):
                catalog.status_id(invalid)


class CatalogTests(unittest.TestCase):
    def test_rendered_catalog_has_each_hand_derived_status_definition_once(self):
        # Catches omitted, repeated, zero, or malformed amount definitions.
        text = catalog.render_catalog()
        entries = _parse_entries_independently(text)
        self.assertEqual(65535, len(entries))
        self.assertEqual(set(range(1, 65536)), set(entries))
        self.assertEqual("AESN_HP_TOTAL_1", entries[1]["id"])
        self.assertEqual("AESN_HP_TOTAL_111", entries[111]["id"])
        self.assertEqual("AESN_HP_TOTAL_32768", entries[32768]["id"])
        self.assertEqual("AESN_HP_TOTAL_65535", entries[65535]["id"])
        for amount, entry in entries.items():
            self.assertEqual(f"AESN_HP_TOTAL_{amount}", entry["StackId"])
            self.assertEqual(f"IncreaseMaxHP({amount});", entry["Boosts"])
            self.assertEqual("BOOST", entry["StatusType"])
            self.assertEqual("AESNHpSourceName;1", entry["DisplayName"])
            self.assertEqual(
                "DisableOverhead;DisableCombatlog;DisablePortraitIndicator",
                entry["StatusPropertyFlags"],
            )

    def test_rendering_is_byte_deterministic_and_validator_reports_utf8_hash(self):
        # Catches non-deterministic ordering/encoding and an invalid validator receipt.
        first = catalog.render_catalog()
        second = catalog.render_catalog()
        self.assertEqual(first.encode("utf-8"), second.encode("utf-8"))
        receipt = catalog.validate_catalog(first)
        self.assertEqual(65535, receipt["count"])
        self.assertEqual(hashlib.sha256(first.encode("utf-8")).hexdigest(), receipt["sha256"])

    def test_validator_rejects_missing_duplicate_wrong_and_extra_status_data(self):
        # Catches validators that only count lines or compare renderer output.
        text = catalog.render_catalog()
        first_entry_end = text.index("\n\n")
        missing = text[first_entry_end + 2 :]
        duplicate = text + text[: first_entry_end + 2]
        wrong_amount = text.replace("IncreaseMaxHP(111);", "IncreaseMaxHP(112);", 1)
        swapped_stack = text.replace(
            'data "StackId" "AESN_HP_TOTAL_111"',
            'data "StackId" "AESN_HP_TOTAL_112"',
            1,
        )
        extra_boost = text.replace(
            'data "Boosts" "IncreaseMaxHP(111);"',
            'data "Boosts" "IncreaseMaxHP(111);UnlockSpell(Shout);"',
            1,
        )
        for malformed in [missing, duplicate, wrong_amount, swapped_stack, extra_boost]:
            with self.assertRaises(ValueError):
                catalog.validate_catalog(malformed)

    def test_existing_localization_handle_resolves_to_adaptive_enemy_scaling(self):
        # Catches a catalog label that would not attribute the contribution to this mod.
        localization = Path(
            "toolkit/Mods/AdaptiveEnemyScalingNativePOC_a4567f52-1665-df50-b84c-3992f80fdb90/"
            "Localization/English/AdaptiveEnemyScalingNativePOC.xml"
        ).read_text(encoding="utf-8")
        self.assertIn(
            '<content contentuid="AESNHpSourceName" version="1">Adaptive Enemy Scaling</content>',
            localization,
        )


class CliTests(unittest.TestCase):
    def test_generate_check_idempotence_and_refusal_preserve_existing_file(self):
        # Catches unsafe overwrite behavior and a check command that accepts invalid input.
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "Status_AESN_HP_Total.txt"
            generate = _run_cli("generate", "--output", str(path))
            self.assertEqual(0, generate.returncode, generate.stderr)
            initial = path.read_bytes()
            rerun = _run_cli("generate", "--output", str(path))
            self.assertEqual(0, rerun.returncode, rerun.stderr)
            self.assertEqual(initial, path.read_bytes())
            self.assertEqual(0, _run_cli("check", str(path)).returncode)

            path.write_bytes(b"different content\n")
            refusal = _run_cli("generate", "--output", str(path))
            self.assertNotEqual(0, refusal.returncode)
            self.assertEqual(b"different content\n", path.read_bytes())
            invalid = _run_cli("check", str(path))
            self.assertNotEqual(0, invalid.returncode)
            self.assertIn("invalid catalog", invalid.stderr)


def _parse_entries_independently(text):
    entries = {}
    for block in text.strip().split("\n\n"):
        lines = block.splitlines()
        if len(lines) != 7 or not lines[0].startswith('new entry "AESN_HP_TOTAL_'):
            raise AssertionError(f"unexpected entry format: {block[:80]!r}")
        identifier = lines[0][11:-1]
        amount = int(identifier.removeprefix("AESN_HP_TOTAL_"))
        fields = {}
        for line in lines[2:]:
            _, rest = line.split(' "', 1)
            name, value = rest.split('" "', 1)
            fields[name] = value[:-1]
        fields["id"] = identifier
        if amount in entries:
            raise AssertionError(f"duplicate amount {amount}")
        entries[amount] = fields
    return entries


def _run_cli(*arguments):
    return subprocess.run(
        [sys.executable, "-m", "tools.hp_catalog", *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
