import json
import pathlib
import re
import struct
import unittest

from PIL import Image


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
        self.assertEqual(identity["toolkitModuleVersion"], "1.0.0.5")
        self.assertEqual(identity["toolkitModuleVersion64"], 36028797018963973)
        self.assertEqual(identity["schemaVersion"], 2)
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
        self.assertIn('value="ghost2788"', meta)
        self.assertIn('value="36028797018963977"', meta)

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

    def test_reachable_presentation_statuses_are_exact_and_nonduplicating(self):
        module = (
            "AdaptiveEnemyScalingNativePOC_"
            "a4567f52-1665-df50-b84c-3992f80fdb90"
        )
        status_path = (
            ROOT
            / "toolkit"
            / "Public"
            / module
            / "Stats"
            / "Generated"
            / "Data"
            / "Status_BOOST.txt"
        )
        localization_path = (
            ROOT
            / "toolkit"
            / "Mods"
            / module
            / "Localization"
            / "English"
            / "AdaptiveEnemyScalingNativePOC.xml"
        )
        text = status_path.read_text(encoding="utf-8")

        def entry(name):
            start = text.index(f'new entry "{name}"')
            end = text.find("\nnew entry ", start + 1)
            return text[start:] if end == -1 else text[start:end]

        for tier in range(1, 7):
            hardened = entry(f"AESN_HARDENED_FOE_{tier:02d}")
            self.assertIn(
                f'data "DisplayName" "AESNHardenedFoe{tier:02d}Name;1"',
                hardened,
            )
            self.assertIn(
                f'data "Description" "AESNHardenedFoe{tier:02d}Description;1"',
                hardened,
            )
            self.assertIn(
                f'data "Icon" "AESN_HardenedFoe_{tier:02d}"', hardened
            )
            self.assertNotIn("DisablePortraitIndicator", hardened)

        for tier in (1, 2):
            relentless = entry(f"AESN_RELENTLESS_FOE_{tier:02d}")
            self.assertIn(
                f'data "DisplayName" "AESNRelentlessFoe{tier:02d}Name;1"',
                relentless,
            )
            self.assertIn(
                f'data "Icon" "AESN_RelentlessFoe_{tier:02d}"', relentless
            )
            self.assertNotIn("DisablePortraitIndicator", relentless)

        for legacy_id in (
            "AESN_TIER_LEVEL_05_08",
            "AESN_EXTRA_ACTION_1",
            "AESN_EXTRA_BONUS_ACTION_1",
        ):
            legacy = entry(legacy_id)
            self.assertNotIn('data "DisplayName"', legacy)
            self.assertNotIn('data "Description"', legacy)
            self.assertNotIn('data "Icon"', legacy)
            self.assertIn("DisablePortraitIndicator", legacy)

        localization = localization_path.read_text(encoding="utf-8")
        for tier in range(1, 7):
            self.assertIn(f'contentuid="AESNHardenedFoe{tier:02d}Name"', localization)
            self.assertIn(
                f'contentuid="AESNHardenedFoe{tier:02d}Description"',
                localization,
            )
        for tier in (1, 2):
            self.assertIn(f'contentuid="AESNRelentlessFoe{tier:02d}Name"', localization)
            self.assertIn(
                f'contentuid="AESNRelentlessFoe{tier:02d}Description"',
                localization,
            )
        self.assertNotIn("Mechanics:", localization)

        source_icons = ROOT / "assets" / "icons" / "source"
        gui_root = ROOT / "toolkit" / "Public" / module / "GUI"
        icon_root = gui_root / "SourceIcons"
        expected = []
        icon_names = []
        for family in ("HardenedFoe", "RelentlessFoe"):
            for tier in range(1, 7):
                icon_name = f"AESN_{family}_{tier:02d}"
                icon_names.append(icon_name)
                expected.append((source_icons / f"{icon_name}.png", (1254, 1254)))
                for size in (64, 144, 380):
                    expected.append(
                        (icon_root / str(size) / f"{icon_name}.png", (size, size))
                    )
        for path, dimensions in expected:
            data = path.read_bytes()
            self.assertEqual(b"\x89PNG\r\n\x1a\n", data[:8], path)
            self.assertEqual(dimensions, struct.unpack(">II", data[16:24]), path)
            self.assertEqual(6, data[25], f"{path} must remain RGBA")

        atlas_text = (gui_root / "AESN_ConditionIcons.lsx").read_text(encoding="utf-8")
        for icon_name in icon_names:
            self.assertIn(f'value="{icon_name}"', atlas_text)
        self.assertEqual(12, atlas_text.count('<node id="IconUV">'))

        atlas_path = (
            ROOT
            / "toolkit"
            / "Public"
            / module
            / "Assets"
            / "Textures"
            / "Icons"
            / "AESN_ConditionIcons.dds"
        )
        atlas = atlas_path.read_bytes()
        self.assertEqual(b"DDS ", atlas[:4])
        self.assertEqual((512, 512), struct.unpack("<II", atlas[12:20]))

    def test_approved_icon_tiers_preserve_dark_infill(self):
        module = f"AdaptiveEnemyScalingNativePOC_{MODULE_UUID}"
        source_icons = ROOT / "assets" / "icons" / "source"
        small_icons = (
            ROOT / "toolkit" / "Public" / module / "GUI" / "SourceIcons" / "64"
        )
        protected_points = {
            "HardenedFoe": ((627, 320), (32, 16), 64),
            "RelentlessFoe": ((627, 450), (32, 23), 192),
        }

        for family, (master_point, small_point, minimum_alpha) in protected_points.items():
            for tier in range(1, 7):
                icon_name = f"AESN_{family}_{tier:02d}.png"
                with Image.open(source_icons / icon_name) as master:
                    self.assertGreaterEqual(
                        master.convert("RGBA").getpixel(master_point)[3],
                        minimum_alpha,
                        f"{icon_name} lost its dark interior alpha",
                    )
                with Image.open(small_icons / icon_name) as small:
                    self.assertGreaterEqual(
                        small.convert("RGBA").getpixel(small_point)[3],
                        minimum_alpha,
                        f"64px {icon_name} lost its dark interior alpha",
                    )

    def test_compact_status_icons_remain_legible_at_hud_size(self):
        module = f"AdaptiveEnemyScalingNativePOC_{MODULE_UUID}"
        icon_root = (
            ROOT / "toolkit" / "Public" / module / "GUI" / "SourceIcons" / "64"
        )

        family_bands = {}
        for family in ("HardenedFoe", "RelentlessFoe"):
            band_pixels = []
            for tier in range(1, 7):
                icon_path = icon_root / f"AESN_{family}_{tier:02d}.png"
                with Image.open(icon_path) as image:
                    rgba = image.convert("RGBA")
                    self.assertEqual((64, 64), rgba.size, icon_path)
                    pixels = tuple(rgba.getdata())

                nontransparent = sum(alpha > 8 for _, _, _, alpha in pixels)
                opaque = sum(alpha > 192 for _, _, _, alpha in pixels)
                bright = sum(
                    alpha > 64
                    and (0.2126 * red + 0.7152 * green + 0.0722 * blue) > 150
                    for red, green, blue, alpha in pixels
                )
                dark = sum(
                    alpha > 192
                    and (0.2126 * red + 0.7152 * green + 0.0722 * blue) < 70
                    for red, green, blue, alpha in pixels
                )

                # Compact HUD icons need a broad readable silhouette, a solid
                # interior, luminous linework, and retained dark infill.  The
                # approved Hardened palettes intentionally trade opacity for
                # glow in the cyan/gold bands and use restrained highlights in
                # the steel band, so each property has its own floor rather
                # than forcing every palette toward the same white balance.
                self.assertGreaterEqual(nontransparent / 4096, 0.40, icon_path)
                self.assertGreaterEqual(opaque / 4096, 0.30, icon_path)
                self.assertGreaterEqual(bright / 4096, 0.10, icon_path)
                self.assertGreaterEqual(dark / 4096, 0.09, icon_path)
                band_pixels.append(pixels)

            self.assertEqual(band_pixels[0], band_pixels[1])
            self.assertEqual(band_pixels[2], band_pixels[3])
            self.assertEqual(band_pixels[4], band_pixels[5])
            family_bands[family] = {band_pixels[0], band_pixels[2], band_pixels[4]}

        self.assertEqual(3, len(family_bands["HardenedFoe"]))
        self.assertEqual(3, len(family_bands["RelentlessFoe"]))

    def test_flat_hp_probe_story_contract(self):
        init_path = ROOT / "story/RawFiles/Goals/AESN_00_Init.txt"
        harness_path = ROOT / "story/RawFiles/Goals/AESN_99_TestHarness.txt"
        self.assertTrue(init_path.exists(), "initialization goal must exist")
        self.assertTrue(harness_path.exists(), "flat-HP test harness must exist")

        init_text = init_path.read_text(encoding="utf-8")
        self.assertIn("DB_AESN_SchemaVersion(2);", init_text)
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

    def test_cap03_host_fixture_assigns_shadowheart_to_host(self):
        """Catch removal or misrouting of the isolated host-fixture probe."""
        harness_text = (
            ROOT / "story/RawFiles/Goals/AESN_99_TestHarness.txt"
        ).read_text(encoding="utf-8")

        event = 'TextEvent("AESN_TEST_MAKE_SHADOWHEART_HOST")'
        make_player = (
            "MakePlayer((CHARACTER)S_Player_ShadowHeart_"
            "3ed74f06-3c60-42dc-83f6-f034cb47c679, "
            "NULL_00000000-0000-0000-0000-000000000000, 1);"
        )
        self.assertIn(event, harness_text)
        self.assertIn(make_player, harness_text)
        self.assertLess(harness_text.index(event), harness_text.index(make_player))

    def test_cap03_host_fixture_uses_vanilla_player_registry(self):
        """Catch bypassing the vanilla DB_Players -> DB_PartyMembers path."""
        harness_text = (
            ROOT / "story/RawFiles/Goals/AESN_99_TestHarness.txt"
        ).read_text(encoding="utf-8")

        player_fact = (
            "DB_Players((CHARACTER)S_Player_ShadowHeart_"
            "3ed74f06-3c60-42dc-83f6-f034cb47c679);"
        )
        self.assertIn(player_fact, harness_text)
        self.assertNotIn("DB_PartyMembers((CHARACTER)S_Player_ShadowHeart_", harness_text)

    def test_cap03_crashing_three_member_fixture_is_retired(self):
        """Prevent reintroduction of the off-level SetLevel crash fixture."""
        harness_text = (
            ROOT / "story/RawFiles/Goals/AESN_99_TestHarness.txt"
        ).read_text(encoding="utf-8")

        self.assertNotIn('TextEvent("AESN_TEST_MAKE_THREE_MEMBER_PARTY")', harness_text)
        self.assertNotIn("SetLevel((CHARACTER)S_Player_", harness_text)

    def test_cap03_gale_probe_has_exactly_one_native_operation(self):
        """Keep the post-crash companion probe isolated to MakePlayer."""
        harness_text = (
            ROOT / "story/RawFiles/Goals/AESN_99_TestHarness.txt"
        ).read_text(encoding="utf-8")

        event = 'TextEvent("AESN_TEST_MAKE_GALE_OWNED_PLAYER")'
        operation = (
            "MakePlayer((CHARACTER)S_Player_Gale_"
            "ad9af97d-75da-406a-ae13-7071c563f604, "
            "(CHARACTER)S_Player_ShadowHeart_"
            "3ed74f06-3c60-42dc-83f6-f034cb47c679, 1);"
        )
        start = harness_text.index(event)
        end = harness_text.index("// Editor-only CAP-03 registry probe", start)
        block = harness_text[start:end]
        self.assertEqual(block.count("MakePlayer("), 1)
        self.assertIn(operation, block)
        self.assertNotIn("DB_Players(", block)
        self.assertNotIn("RegisterAsCompanion(", block)
        self.assertNotIn("SetLevel(", block)

    def test_cap03_gale_registry_probe_has_exactly_one_fact(self):
        """Keep the second companion probe isolated to vanilla DB_Players."""
        harness_text = (
            ROOT / "story/RawFiles/Goals/AESN_99_TestHarness.txt"
        ).read_text(encoding="utf-8")

        event = 'TextEvent("AESN_TEST_REGISTER_GALE_PLAYER_FACT")'
        fact = (
            "DB_Players((CHARACTER)S_Player_Gale_"
            "ad9af97d-75da-406a-ae13-7071c563f604);"
        )
        start = harness_text.index(event)
        end = harness_text.index("// Editor-only CAP-03 Astarion ownership probe", start)
        block = harness_text[start:end]
        self.assertEqual(block.count("DB_Players("), 1)
        self.assertIn(fact, block)
        self.assertNotIn("DB_PartyMembers(", block)
        self.assertNotIn("MakePlayer(", block)
        self.assertNotIn("RegisterAsCompanion(", block)
        self.assertNotIn("SetLevel(", block)

    def test_cap03_astarion_probes_keep_operations_isolated(self):
        """Apply the verified ownership/registry sequence without combining it."""
        harness_text = (
            ROOT / "story/RawFiles/Goals/AESN_99_TestHarness.txt"
        ).read_text(encoding="utf-8")

        ownership_event = 'TextEvent("AESN_TEST_MAKE_ASTARION_OWNED_PLAYER")'
        ownership_operation = (
            "MakePlayer((CHARACTER)S_Player_Astarion_"
            "c7c13742-bacd-460a-8f65-f864fe41f255, "
            "(CHARACTER)S_Player_ShadowHeart_"
            "3ed74f06-3c60-42dc-83f6-f034cb47c679, 1);"
        )
        ownership_start = harness_text.index(ownership_event)
        ownership_end = harness_text.index(
            "// Editor-only CAP-03 Astarion registry probe", ownership_start
        )
        ownership_block = harness_text[ownership_start:ownership_end]
        self.assertEqual(ownership_block.count("MakePlayer("), 1)
        self.assertIn(ownership_operation, ownership_block)
        self.assertNotIn("DB_Players(", ownership_block)
        self.assertNotIn("SetLevel(", ownership_block)

        registry_event = 'TextEvent("AESN_TEST_REGISTER_ASTARION_PLAYER_FACT")'
        registry_fact = (
            "DB_Players((CHARACTER)S_Player_Astarion_"
            "c7c13742-bacd-460a-8f65-f864fe41f255);"
        )
        registry_start = harness_text.index(registry_event)
        registry_end = harness_text.index(
            "// Editor-only CAP-03 observation trigger", registry_start
        )
        registry_block = harness_text[registry_start:registry_end]
        self.assertEqual(registry_block.count("DB_Players("), 1)
        self.assertIn(registry_fact, registry_block)
        self.assertNotIn("DB_PartyMembers(", registry_block)
        self.assertNotIn("MakePlayer(", registry_block)
        self.assertNotIn("SetLevel(", registry_block)

    def test_cap03_shadowheart_avatar_registry_probe_is_isolated(self):
        """Register only the vanilla avatar fact before the native hireling probe."""
        harness_text = (
            ROOT / "story/RawFiles/Goals/AESN_99_TestHarness.txt"
        ).read_text(encoding="utf-8")

        event = 'TextEvent("AESN_TEST_REGISTER_SHADOWHEART_AVATAR_FACT")'
        exact_fact = (
            "DB_Avatars((CHARACTER)S_Player_ShadowHeart_"
            "3ed74f06-3c60-42dc-83f6-f034cb47c679);"
        )
        start = harness_text.index(event)
        end = harness_text.index(
            "// Editor-only CAP-03 observation trigger", start
        )
        block = harness_text[start:end]
        self.assertEqual(block.count("DB_Avatars("), 1)
        self.assertIn(exact_fact, block)
        self.assertNotIn("DB_PartyMembers(", block)
        self.assertNotIn("DB_Players(", block)
        self.assertNotIn("MakePlayer(", block)
        self.assertNotIn("SetLevel(", block)

    def test_cap03_familiar_probe_uses_native_spell_and_records_owner(self):
        """Create a genuine engine-owned familiar without fabricating roster facts."""
        harness_text = (
            ROOT / "story/RawFiles/Goals/AESN_99_TestHarness.txt"
        ).read_text(encoding="utf-8")

        for required in (
            'TextEvent("AESN_TEST_SUMMON_SCRATCH_FAMILIAR")',
            'HasSpell(_Caster, "Target_FindFamiliar_Dog", 0)',
            'AddSpell(_Caster, "Target_FindFamiliar_Dog", 0, 0);',
            'FindValidPosition(_X, _Y, _Z, 250.0, _Caster, 0, '
            '_StageX, _StageY, _StageZ)',
            'TeleportToPosition(_Caster, _StageX, _StageY, _StageZ, '
            '"", 0, 0, 0, 0, 1);',
            'DebugLog("AESN_CAP03 FAMILIAR_HOST_STAGED")',
            'RealSum(_X, 3.0, _CandidateX)',
            'FindValidPosition(_CandidateX, _Y, _Z, 8.0, _Caster, 0, '
            '_CastX, _CastY, _CastZ)',
            'UseSpellAtPosition(_Caster, "Target_FindFamiliar_Dog", '
            '_CastX, _CastY, _CastZ);',
            'DebugLog("AESN_CAP03 FAMILIAR_COMMAND_RECEIVED")',
            'DebugLog("AESN_CAP03 FAMILIAR_CAST_REQUESTED")',
            'CastSpellFailed(_Caster, "Target_FindFamiliar_Dog", _, _, _)',
            'DB_AESN_TestGrantedFamiliarSpell((CHARACTER)_Caster)',
            'DebugLog("AESN_CAP03 FAMILIAR_CAST_FAILED")',
            'CharacterJoinedParty(_Summon)',
            'IsSummon(_Summon, 1)',
            'CharacterGetOwner(_Summon, _Owner)',
            'DB_AESN_TestFamiliar(_Summon, _Owner);',
            'RemoveSpell(_Owner, "Target_FindFamiliar_Dog", 0);',
            'DebugLog("AESN_CAP03 SUMMON familiar=1,ownerVerified=1")',
            'DB_AESN_TestFamiliar((CHARACTER)_Summon, (CHARACTER)_Owner)',
            'DebugLog("AESN_CAP03 SUMMON_RECORDED familiar=1,ownerVerified=1")',
        ):
            self.assertIn(required, harness_text)

        event_start = harness_text.index(
            'TextEvent("AESN_TEST_SUMMON_SCRATCH_FAMILIAR")'
        )
        event_end = harness_text.index(
            "// Editor-only CAP-03 observation trigger", event_start
        )
        event_block = harness_text[event_start:event_end]
        self.assertNotIn("DB_PartyMembers(", event_block)
        self.assertNotIn("MakePlayer(", event_block)
        self.assertNotIn("SetLevel(", event_block)

    def test_cap03_familiar_probe_has_explicit_stale_spell_reset(self):
        """Recover only the known editor-harness spell state after a Story rebuild."""
        harness_text = (
            ROOT / "story/RawFiles/Goals/AESN_99_TestHarness.txt"
        ).read_text(encoding="utf-8")

        event = 'TextEvent("AESN_TEST_RESET_SCRATCH_FAMILIAR")'
        start = harness_text.index(event)
        end = harness_text.index(
            '// ReCon command: oe AESN_TEST_SUMMON_SCRATCH_FAMILIAR', start
        )
        block = harness_text[start:end]
        self.assertIn('HasSpell(_Caster, "Target_FindFamiliar_Dog", 1)', block)
        self.assertIn(
            'RemoveSpell(_Caster, "Target_FindFamiliar_Dog", 0);', block
        )
        self.assertIn(
            'NOT DB_AESN_TestGrantedFamiliarSpell(_Caster);', block
        )
        self.assertIn(
            'DebugLog("AESN_CAP03 FAMILIAR_RESET removedSpell=1")', block
        )
        self.assertNotIn("DB_PartyMembers(", block)

    def test_cap03_temporary_follower_probe_uses_native_party_api(self):
        """Create an engine-owned follower without fabricating roster facts."""
        harness_text = (
            ROOT / "story/RawFiles/Goals/AESN_99_TestHarness.txt"
        ).read_text(encoding="utf-8")

        for required in (
            'TextEvent("AESN_TEST_ADD_TEMP_FOLLOWER")',
            "DB_AESN_TestFollowerPending",
            "DB_AESN_TestFollower",
            "CreateAtObject((CHARACTERROOT)"
            "Kobolds_Melee_Drunk_45e31b7d-32ec-4f3d-8067-79061aeec77b",
            'RealtimeObjectTimerLaunch((CHARACTER)_Follower, '
            '"AESN_CAP03_FOLLOWER_READY", 250);',
            'ObjectTimerFinished((CHARACTER)_Follower, '
            '"AESN_CAP03_FOLLOWER_READY")',
            "AddPartyFollower(_Follower, _Leader);",
            'RealtimeObjectTimerLaunch(_Follower, '
            '"AESN_CAP03_FOLLOWER_VERIFY", 250);',
            'ObjectTimerFinished((CHARACTER)_Follower, '
            '"AESN_CAP03_FOLLOWER_VERIFY")',
            "IsPartyFollower(_Follower, 1)",
            "CharacterGetOwner(_Follower, _Leader)",
            'DebugLog("AESN_CAP03 FOLLOWER_RECORDED follower=1,ownerVerified=1");',
            'TextEvent("AESN_TEST_FOLLOWER_ROSTER")',
            "PROC_AESN_BuildRoster((GUIDSTRING)_Follower);",
            'TextEvent("AESN_TEST_RESET_TEMP_FOLLOWER")',
            "RemovePartyFollower(_Follower, _Leader);",
            'RealtimeObjectTimerLaunch(_Follower, '
            '"AESN_CAP03_FOLLOWER_REMOVE", 250);',
            "PROC_SetOnStage(_Follower, 0);",
        ):
            self.assertIn(required, harness_text)

        start = harness_text.index(
            'TextEvent("AESN_TEST_ADD_TEMP_FOLLOWER")'
        )
        end = harness_text.index(
            "// Editor-only CAP-03 observation trigger", start
        )
        block = harness_text[start:end]
        self.assertNotIn("DB_PartyMembers(", block)
        self.assertNotIn("DB_Players(", block)
        self.assertNotIn("MakePlayer(", block)
        self.assertNotIn("SetLevel(", block)

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

    def test_cap05_probe_statuses_are_independent_exact_bits(self):
        status_text = (
            ROOT
            / "toolkit/Public"
            / f"AdaptiveEnemyScalingNativePOC_{MODULE_UUID}"
            / "Stats/Generated/Data/Status_BOOST.txt"
        ).read_text(encoding="utf-8")

        for bit in (1, 4, 8):
            status_id = f"AESN_HP_BIT_{bit:05d}"
            self.assertEqual(status_text.count(f'new entry "{status_id}"'), 1)
            self.assertEqual(status_text.count(f'data "StackId" "{status_id}"'), 1)
            self.assertEqual(
                status_text.count(f'data "Boosts" "IncreaseMaxHP({bit});"'),
                1,
            )

    def test_cap05_harness_applies_and_removes_exact_13_once(self):
        harness_text = (
            ROOT / "story/RawFiles/Goals/AESN_98_CAP05_Harness.txt"
        ).read_text(encoding="utf-8")

        for required in (
            'TextEvent("AESN_TEST_SPAWN_AND_APPLY_13_HP")',
            'TextEvent("AESN_TEST_REMOVE_SPAWNED_13_HP")',
            "PROC_AESN_CAP05_Apply13Hp",
            "PROC_AESN_CAP05_Remove13Hp",
            'ApplyStatus(_Target, "AESN_HP_BIT_00001"',
            'ApplyStatus(_Target, "AESN_HP_BIT_00004"',
            'ApplyStatus(_Target, "AESN_HP_BIT_00008"',
            'RemoveStatus(_Target, "AESN_HP_BIT_00001"',
            'RemoveStatus(_Target, "AESN_HP_BIT_00004"',
            'RemoveStatus(_Target, "AESN_HP_BIT_00008"',
            "IntegerSum(_BeforeMaximum, 13, _ExpectedMaximum)",
            "IntegerSubtract(_BeforeMaximum, 13, _ExpectedMaximum)",
            '"AESN_CAP05 APPLY13 beforeCurrent="',
            '"AESN_CAP05 REMOVE13 beforeCurrent="',
            '",percentagePreserved=1,bits=1|4|8"',
        ):
            self.assertIn(required, harness_text)

        self.assertEqual(harness_text.count("SetHitpointsPercentage("), 2)

    def test_action_pair_harness_is_additive_and_exactly_owned(self):
        """Prove the action POC applies and removes only its two statuses."""
        text = (
            ROOT / "story/RawFiles/Goals/AESN_97_ActionHarness.txt"
        ).read_text(encoding="utf-8")

        for required in (
            'TextEvent("AESN_TEST_APPLY_ACTION_PAIR")',
            'ApplyStatus(_Target, "AESN_EXTRA_ACTION_1", -1.0, 1,',
            'ApplyStatus(_Target, "AESN_EXTRA_BONUS_ACTION_1", -1.0, 1,',
            'StatusApplied((CHARACTER)_Target, "AESN_EXTRA_ACTION_1", _, _)',
            'StatusApplied((CHARACTER)_Target, "AESN_EXTRA_BONUS_ACTION_1", _, _)',
            'HasActiveStatus(_Target, "AESN_EXTRA_ACTION_1", 1)',
            'HasActiveStatus(_Target, "AESN_EXTRA_BONUS_ACTION_1", 1)',
            'DebugLog("AESN_ACTION_PAIR APPLY additiveAction=1,additiveBonusAction=1")',
            'TextEvent("AESN_TEST_REMOVE_ACTION_PAIR")',
            'RemoveStatus(_Target, "AESN_EXTRA_ACTION_1",',
            'RemoveStatus(_Target, "AESN_EXTRA_BONUS_ACTION_1",',
            'StatusRemoved((CHARACTER)_Target, "AESN_EXTRA_ACTION_1", _, _)',
            'StatusRemoved((CHARACTER)_Target, "AESN_EXTRA_BONUS_ACTION_1", _, _)',
            'HasActiveStatus(_Target, "AESN_EXTRA_ACTION_1", 0)',
            'HasActiveStatus(_Target, "AESN_EXTRA_BONUS_ACTION_1", 0)',
            'DebugLog("AESN_ACTION_PAIR REMOVE additiveAction=1,additiveBonusAction=1")',
        ):
            self.assertIn(required, text)

        self.assertNotIn("Legendary", text)
        self.assertNotIn("Reaction", text)
        self.assertNotIn("ActionSurge", text)
        self.assertNotIn("PartyIncreaseActionResourceValue", text)
        self.assertNotIn("AddActionPoints", text)

    def test_stat_tier_harness_applies_and_removes_only_owned_status(self):
        """Keep the isolated stat-tier primitive exact and reversible."""
        text = (
            ROOT / "story/RawFiles/Goals/AESN_96_StatHarness.txt"
        ).read_text(encoding="utf-8")

        for required in (
            'TextEvent("AESN_TEST_SPAWN_AND_APPLY_STAT_TIER")',
            'TextEvent("AESN_TEST_REMOVE_SPAWNED_STAT_TIER")',
            'ApplyStatus(_Target, "AESN_TIER_LEVEL_05_08", -1.0, 1,',
            'StatusApplied((CHARACTER)_Target, "AESN_TIER_LEVEL_05_08", _, _)',
            'HasActiveStatus(_Target, "AESN_TIER_LEVEL_05_08", 1)',
            'RemoveStatus(_Target, "AESN_TIER_LEVEL_05_08",',
            'StatusRemoved((CHARACTER)_Target, "AESN_TIER_LEVEL_05_08", _, _)',
            'HasActiveStatus(_Target, "AESN_TIER_LEVEL_05_08", 0)',
            'DebugLog("AESN_STAT_TIER APPLY attack=1,saves=1,ac=1,spellDC=1,statusOwned=1")',
            'DebugLog("AESN_STAT_TIER REMOVE attack=1,saves=1,ac=1,spellDC=1,statusOwned=1")',
            "PROC_SetOnStage(_Target, 0);",
        ):
            self.assertIn(required, text)

        self.assertEqual(text.count('ApplyStatus(_Target, "AESN_TIER_LEVEL_05_08"'), 1)
        self.assertEqual(text.count('RemoveStatus(_Target, "AESN_TIER_LEVEL_05_08"'), 1)
        self.assertNotIn("AESN_HP_BIT_", text)
        self.assertNotIn("AESN_EXTRA_ACTION_1", text)
        self.assertNotIn("AESN_EXTRA_BONUS_ACTION_1", text)

    def test_hostility_harness_uses_production_existential_interface(self):
        """Prove the fixture controls inputs but delegates classification."""
        text = (
            ROOT / "story/RawFiles/Goals/AESN_95_HostilityHarness.txt"
        ).read_text(encoding="utf-8")

        for required in (
            'TextEvent("AESN_TEST_EXISTENTIAL_HOSTILITY")',
            'TextEvent("AESN_TEST_RESET_EXISTENTIAL_HOSTILITY")',
            "DB_AESN_HostilityFixture",
            "DB_AESN_CombatParticipant(_Combat, _First);",
            "DB_AESN_CombatParticipant(_Combat, (CHARACTER)_Second);",
            "SetIndividualRelation(_Neutral, _SecondFaction, 50);",
            "SetIndividualRelation(_Hostile, _SecondFaction, 0);",
            "IsEnemy(_Hostile, _First, 0)",
            "IsEnemy(_Hostile, _Second, 1)",
            "PROC_AESN_ConsiderEnemy(_Neutral, _Combat);",
            "PROC_AESN_ConsiderEnemy(_Hostile, _Combat);",
            "DB_AESN_EnemyRejected(_Combat, _Neutral, \"HostileToNoParticipant\")",
            "DB_AESN_EnemyEligible(_Combat, _Hostile)",
            'DebugLog("AESN_HOSTILITY_HARNESS PASS neutralRejected=1,firstNeutral=1,secondHostile=1,eligible=1")',
            "ClearIndividualRelation(_Neutral, _SecondFaction);",
            "ClearIndividualRelation(_Hostile, _SecondFaction);",
        ):
            self.assertIn(required, text)

        self.assertNotIn("DB_PartyMembers", text)
        self.assertNotIn("DB_PartOfTheTeam", text)
        self.assertNotIn("THEN\nDB_AESN_EnemyEligible", text)
        self.assertNotIn("THEN\nDB_AESN_EnemyRejected", text)

    def test_narrative_combat_harness_exercises_native_events_and_late_entry(self):
        """Keep RT-15 wired through native combat events, not fabricated facts."""
        text = (
            ROOT / "story/RawFiles/Goals/AESN_94_NarrativeCombatHarness.txt"
        ).read_text(encoding="utf-8")

        for required in (
            'TextEvent("AESN_TEST_START_NARRATIVE_COMBAT")',
            'TextEvent("AESN_TEST_ADD_LATE_NARRATIVE_HOSTILE")',
            'TextEvent("AESN_TEST_RESET_NARRATIVE_COMBAT")',
            "CreateNarrativeCombat(_Combat)",
            "SetInNarrativeCombat(_Host, _Combat, 1);",
            "SetInNarrativeCombat(_Initial, _Combat, 1);",
            "SetInNarrativeCombat(_Late, _Combat, 1);",
            "CombatStarted(_Combat)",
            "EnteredCombat(_Object, _Combat)",
            "DB_AESN_CombatSnapshotV2(_Combat, 2,",
            "DB_AESN_CombatParticipant(_Combat, _Host)",
            "DB_AESN_EnemyEligible(_Combat, _Initial)",
            "DB_AESN_EnemyEligible(_Combat, _Late)",
            'DebugLog("AESN_NARRATIVE START_PASS nativeCombatStarted=1,initialEligible=1")',
            'DebugLog("AESN_NARRATIVE LATE_PASS nativeEnteredCombat=1,lateEligible=1,duplicateSafe=1")',
            "SetInNarrativeCombat(_Late, _Combat, 0);",
            "SetInNarrativeCombat(_Initial, _Combat, 0);",
            "SetInNarrativeCombat(_Host, _Combat, 0);",
            "DestroyNarrativeCombat(_Combat);",
            "PROC_AESN_NarrativeCleanupOwnedFacts(_Combat);",
            "DB_AESN_HpTransaction(_Combat, _Enemy, _Version, _State,",
            "DB_AESN_HpDesiredBit(_Combat, _Enemy, _Bit, _Status)",
            "DB_AESN_HpPlanQueued(_Combat, _Enemy)",
            "DB_AESN_HpFailure(_Combat, _Enemy, _Reason)",
        ):
            self.assertIn(required, text)

        self.assertNotIn("DB_PartyMembers", text)
        self.assertNotIn("DB_PartOfTheTeam", text)
        self.assertNotIn("DB_AESN_CombatSnapshotV2(_Combat, 2, 1, 1,", text)
        self.assertNotIn("DB_AESN_CombatParticipant(_Combat, _Host);", text)
        self.assertNotIn("DB_AESN_EnemyEligible(_Combat, _Initial);", text)
        self.assertNotIn("DB_AESN_EnemyEligible(_Combat, _Late);", text)

        combat_started = text.index("CombatStarted(_Combat)")
        verify_timer = text.index(
            'RealtimeObjectTimerLaunch(_Host, '
            '"AESN_NARRATIVE_START_VERIFY", 500);'
        )
        verify_event = text.index(
            'ObjectTimerFinished((CHARACTER)_Host, '
            '"AESN_NARRATIVE_START_VERIFY")'
        )
        self.assertLess(combat_started, verify_timer)
        self.assertLess(verify_timer, verify_event)
        self.assertEqual(text.count("AESN_NARRATIVE_START_VERIFY"), 2)

    def test_supported_hp_plan_harness_calls_production_without_mutation(self):
        """Prove the supported fixture controls inputs but not planner output."""
        text = (
            ROOT / "story/RawFiles/Goals/AESN_93_HpPlanHarness.txt"
        ).read_text(encoding="utf-8")

        for required in (
            'TextEvent("AESN_TEST_PLAN_SUPPORTED_HP")',
            'TextEvent("AESN_TEST_RESET_SUPPORTED_HP_PLAN")',
            "DB_AESN_CombatSnapshotV2(_Combat, 2, 3, 3, 3, 1, 1, 165, 0, 0, 1, \"Supported\");",
            "PROC_AESN_PlanEnemy(_Target, _Combat);",
            "DB_AESN_HpTransaction(_Combat, _Target, 1, \"Planned\", 12, 12,",
            "19, 7, 0)",
            'DB_AESN_HpDesiredBit(_Combat, _Target, 4, "AESN_HP_BIT_00004")',
            'DB_AESN_HpDesiredBit(_Combat, _Target, 2, "AESN_HP_BIT_00002")',
            'DB_AESN_HpDesiredBit(_Combat, _Target, 1, "AESN_HP_BIT_00001")',
            'DebugLog("AESN_HP_PLAN_HARNESS PASS base=12,target=19,delta=7,bits=4|2|1,mutation=0")',
            "PROC_AESN_HpPlanHarnessCleanup(_Combat, _Target);",
        ):
            self.assertIn(required, text)

        self.assertNotIn("ApplyStatus(", text)
        self.assertNotIn("RemoveStatus(", text)
        self.assertNotIn("SetHitpointsPercentage(", text)
        self.assertNotIn("DB_AESN_EnemyEligible", text)

    def test_hp_transaction_planner_is_versioned_exact_and_failure_closed(self):
        """Require one persisted target and an exact 16-bit desired registry."""
        text = (
            ROOT / "story/RawFiles/Goals/AESN_40_HpTransaction.txt"
        ).read_text(encoding="utf-8")

        for required in (
            "PROC_AESN_PlanEnemy((CHARACTER)_Enemy, (GUIDSTRING)_Combat)",
            "DB_AESN_CombatSnapshotV2(_Combat, 2,",
            '"Supported"',
            "GetHitpoints(_Enemy, _BeforeCurrent)",
            "GetMaxHitpoints(_Enemy, _BeforeMaximum)",
            "GetHitpointsPercentage(_Enemy, _BeforePercentage)",
            "_BeforeMaximum <= 4129776",
            "IntegerProduct(_BeforeMaximum, _TargetHpPercent, _CombinedProduct)",
            "IntegerDivide(_CombinedProduct, 100, _TargetMaximum)",
            "IntegerSubtract(_TargetMaximum, _BeforeMaximum, _Delta)",
            "_Delta >= 0",
            "_Delta <= 65535",
            "DB_AESN_HpTransaction(_Combat, _Enemy, 1, \"Planned\"",
            "PROC_AESN_QueueHpBit",
            "IntegerDivide(_Delta, _Bit, _Quotient)",
            "IntegerDivide(_Quotient, 2, _Half)",
            "IntegerProduct(_Half, 2, _Even)",
            "IntegerSubtract(_Quotient, _Even, 1)",
            "DB_AESN_HpDesiredBit(_Combat, _Enemy, _Bit, _Status)",
            'DB_AESN_HpFailure(_Combat, _Enemy, "DeadAtEntry")',
            'DB_AESN_HpFailure(_Combat, _Enemy, "UnsafeBaseMaximum")',
            'DB_AESN_HpFailure(_Combat, _Enemy, "UnsafeDelta")',
        ):
            self.assertIn(required, text)

        expected_bits = tuple(1 << exponent for exponent in range(15, -1, -1))
        for bit in expected_bits:
            self.assertIn(
                f'PROC_AESN_QueueHpBit(_Combat, _Enemy, _Delta, {bit}, '
                f'"AESN_HP_BIT_{bit:05d}");',
                text,
            )

        self.assertEqual(text.count("SetHitpointsPercentage("), 0)
        self.assertEqual(text.count("ApplyStatus("), 0)
        self.assertNotIn("DB_PartOfTheTeam", text)

    def test_hp_application_is_acknowledged_exact_and_reversible(self):
        """Require sequential owned-bit application, rollback, and cleanup."""
        text = (
            ROOT / "story/RawFiles/Goals/AESN_50_Applications.txt"
        ).read_text(encoding="utf-8")

        for required in (
            "DB_AESN_HpBitOrder(15, 32768, \"AESN_HP_BIT_32768\");",
            "DB_AESN_HpBitOrder(0, 1, \"AESN_HP_BIT_00001\");",
            "PROC_AESN_ApplyNextHpBit((GUIDSTRING)_Combat, (CHARACTER)_Enemy, (INTEGER)_Index)",
            "DB_AESN_HpPendingApply(_Combat, _Enemy, _Index, _Bit, _Status);",
            "HasActiveStatus(_Enemy, _Status, 0)",
            "ApplyStatus(_Enemy, _Status, -1.0, 1,",
            "StatusApplied((CHARACTER)_Enemy, _Status, _, _)",
            "DB_AESN_EnemyHpBit(_Combat, _Enemy, _Bit, _Status);",
            "StatusAttemptFailed((CHARACTER)_Enemy, _Status, _, _)",
            '"AESN_HP_APPLY_TIMEOUT"',
            "PROC_AESN_BeginHpRollback(_Combat, _Enemy);",
            "PROC_AESN_RemoveNextHpBit",
            "DB_AESN_HpPendingRemove(_Combat, _Enemy, _Index, _Bit, _Status, _Mode);",
            "RemoveStatus(_Enemy, _Status,",
            "StatusRemoved((CHARACTER)_Enemy, _Status, _, _)",
            "NOT DB_AESN_EnemyHpBit(_Combat, _Enemy, _Bit, _Status);",
            "SetHitpointsPercentage(_Enemy, _BeforePercentage, \"Guaranteed\");",
            "PROC_AESN_CleanupEnemy((CHARACTER)_Enemy, (GUIDSTRING)_Combat)",
            "SetHitpointsPercentage(_Enemy, _CleanupPercentage, \"Guaranteed\");",
            'DB_AESN_HpFailure(_Combat, _Enemy, "ApplyTimeout")',
            'DB_AESN_HpFailure(_Combat, _Enemy, "StatusAttemptFailed")',
            'DB_AESN_HpFailure(_Combat, _Enemy, "MaximumMismatch")',
            "NOT DB_AESN_HpApplicationHold(_Combat, _Enemy)",
        ):
            self.assertIn(required, text)

        self.assertNotIn("RemoveStatusByType", text)
        self.assertNotIn("AESN_TIER_LEVEL_05_08", text)
        self.assertNotIn("AESN_EXTRA_ACTION_1", text)
        self.assertNotIn("AESN_EXTRA_BONUS_ACTION_1", text)
        self.assertNotIn("DB_PartOfTheTeam", text)

    def test_supported_hp_apply_harness_uses_production_and_exact_observations(self):
        text = (
            ROOT / "story/RawFiles/Goals/AESN_92_HpApplyHarness.txt"
        ).read_text(encoding="utf-8")

        for required in (
            'TextEvent("AESN_TEST_APPLY_SUPPORTED_HP")',
            'TextEvent("AESN_TEST_CLEANUP_SUPPORTED_HP")',
            "PROC_AESN_PlanEnemy(_Target, _Combat);",
            "PROC_AESN_CleanupEnemy(_Target, _Combat);",
            "DB_AESN_HpTransaction(_Combat, _Target, 1, \"HPCommitted\", 12, 12, 100.0, 19, 7, 7)",
            'DB_AESN_EnemyHpBit(_Combat, _Target, 4, "AESN_HP_BIT_00004")',
            'DB_AESN_EnemyHpBit(_Combat, _Target, 2, "AESN_HP_BIT_00002")',
            'DB_AESN_EnemyHpBit(_Combat, _Target, 1, "AESN_HP_BIT_00001")',
            'DB_AESN_ComponentApplication(_Combat, _Target, 1, "FullyCommitted")',
            'HasActiveStatus(_Target, "AESN_HARDENED_FOE_01", 1)',
            'DebugLog("AESN_HP_APPLY_HARNESS PASS before=12/12,target=19/19,percentage=100,bits=4|2|1,hardened=1,relentless=0,appliedSum=7")',
            'DebugLog("AESN_HP_APPLY_HARNESS CLEANUP_PASS restored=12/12,percentage=100,exactBitsRemoved=4|2|1,hardened=0,relentless=0")',
        ):
            self.assertIn(required, text)

        self.assertNotIn("ApplyStatus(", text)
        self.assertNotIn("RemoveStatus(", text)
        self.assertNotIn("SetHitpointsPercentage(", text)

    def test_component_application_is_additive_exact_and_cleanup_owned(self):
        text = (
            ROOT / "story/RawFiles/Goals/AESN_55_Components.txt"
        ).read_text(encoding="utf-8")

        for required in (
            "DB_AESN_CombatSnapshotV2(_Combat, 2,",
            "NOT DB_AESN_ComponentStarted(_Combat, _Enemy)",
            "DB_AESN_ComponentStarted(_Combat, _Enemy);",
            "PROC_AESN_ApplyHardenedStatus",
            'ApplyStatus(_Enemy, "AESN_HARDENED_FOE_01", -1.0, 1,',
            'ApplyStatus(_Enemy, "AESN_HARDENED_FOE_06", -1.0, 1,',
            "StatusApplied((CHARACTER)_Enemy, _Status, _, _)",
            'DB_AESN_EnemyComponent(_Combat, _Enemy, "Stat", _Status);',
            'DebugLog("AESN_COMPONENTS COMMIT hardened=1,relentless=0,proofGate=closed")',
            "PROC_AESN_CleanupEnemy((CHARACTER)_Enemy, (GUIDSTRING)_Combat)",
            "DB_AESN_ComponentPendingRemove",
            "RemoveStatus(_Enemy, _Status,",
            "StatusRemoved((CHARACTER)_Enemy, _Status, _, _)",
            "NOT DB_AESN_EnemyComponent(_Combat, _Enemy, _Kind, _Status);",
            'DebugLog("AESN_COMPONENTS CLEANUP exactOwnedStatuses=1")',
        ):
            self.assertIn(required, text)

        self.assertNotIn('ApplyStatus(_Enemy, "AESN_RELENTLESS_FOE_', text)

        for forbidden in (
            "Legendary",
            "Reaction",
            "ActionSurge",
            "RemoveStatusByType",
            "PartyIncreaseActionResourceValue",
            "AddActionPoints",
        ):
            self.assertNotIn(forbidden, text)

    def test_merge_probe_marks_native_switch_before_discarded_end(self):
        text = (
            ROOT / "story/RawFiles/Goals/AESN_91_MergeHarness.txt"
        ).read_text(encoding="utf-8")

        for required in (
            'TextEvent("AESN_TEST_START_MERGE_PROBE")',
            'TextEvent("AESN_TEST_TRIGGER_MERGE_PROBE")',
            'TextEvent("AESN_TEST_RESET_MERGE_PROBE")',
            "PROC_EnterCombat(_OldFirst, _OldSecond);",
            "PROC_EnterCombat(_NewFirst, _NewSecond);",
            'DB_AESN_MergeProbePairCombat("Old", _Combat);',
            'DB_AESN_MergeProbePairCombat("New", _Combat);',
            "SwitchedCombat(_Object, _OldCombat, _NewCombat)",
            "DB_AESN_MergeProbeMarked(_DiscardedCombat, _SurvivingCombat);",
            "PROC_EnterCombat(_OldFirst, _NewSecond);",
            "CombatEnded(_DiscardedCombat)",
            'DB_AESN_MergeProbeOldEnded(_DiscardedCombat, _SurvivingCombat, "AfterMarker");',
            'DebugLog("AESN_MERGE_PROBE PASS switchedObserved=1,markedFirst=1,discardedEndedAfterMarker=1")',
            "DB_AESN_MergedCombat(_DiscardedCombat, _SurvivingCombat)",
            "DB_AESN_CombatAlias(_DiscardedCombat, _SurvivingCombat)",
            'DebugLog("AESN_MERGE_EQUAL PASS ownershipMigrated=1,discardedCleanupSuppressed=1,canonicalReplan=0")',
        ):
            self.assertIn(required, text)

        first_switch = text.index(
            "SwitchedCombat(_Object, _OldCombat, _NewCombat)"
        )
        marker = text.index(
            "DB_AESN_MergeProbeMarked(_DiscardedCombat, _SurvivingCombat);",
            first_switch,
        )
        first_end = text.index("CombatEnded(_DiscardedCombat)")
        self.assertLess(first_switch, marker)
        self.assertLess(marker, first_end)

        # Keeping the fixture alive must not eject its actors from their
        # ordinary combats.  The engine treats SetCanFight(..., 0) as an
        # immediate LeaveCombat request, which makes the merge probe vacuous.
        setup_pass = text[text.index("DB_AESN_MergeProbeFixture(") : text.index(
            'DebugLog("AESN_MERGE_PROBE SETUP_PASS distinctOrdinaryCombats=1")'
        )]
        self.assertNotIn("SetCanFight(_OldFirst, 0);", setup_pass)
        for actor in ("_OldFirst", "_OldSecond", "_NewFirst", "_NewSecond"):
            self.assertIn(f"PROC_SetInvulnerable({actor}, 1);", setup_pass)
            self.assertIn(f"PROC_SetInvulnerable({actor}, 0);", text)

    def test_mismatch_merge_harness_reconciles_two_real_transactions(self):
        text = (
            ROOT / "story/RawFiles/Goals/AESN_91_MergeHarness.txt"
        ).read_text(encoding="utf-8")

        for required in (
            'TextEvent("AESN_TEST_PREPARE_MISMATCH_MERGE")',
            "DB_AESN_MergeMismatchVerifyStarted",
            "DB_AESN_CombatSnapshotV2(_OldCombat, 2, 1, 1, 7, 7, 2, 150, 1, 0, 1, \"Supported\");",
            "DB_AESN_CombatSnapshotV2(_NewCombat, 2, 3, 3, 15, 5, 2, 190, 1, 0, 1, \"Supported\");",
            "PROC_AESN_PlanEnemy((CHARACTER)_OldFirst, _OldCombat);",
            "PROC_AESN_PlanEnemy((CHARACTER)_NewFirst, _NewCombat);",
            'DebugLog("AESN_MERGE_MISMATCH PREPARE_PASS opposingDimensions=1,trackedEnemies=2")',
            "DB_AESN_MergePolicyMismatch(_DiscardedCombat, _SurvivingCombat, _, _, _, _, 7, 3)",
            "DB_AESN_CombatSnapshotV2(_SurvivingCombat, 2, 3, 3, 21, 7, 2, 190, 1, 0, 1, \"Supported\")",
            "DB_AESN_HpTransaction(_SurvivingCombat, _OldFirst, 1, \"HPCommitted\", 12, 12, 100.0, 22, 10, 10)",
            "DB_AESN_HpTransaction(_SurvivingCombat, _NewFirst, 1, \"HPCommitted\", 12, 12, 100.0, 22, 10, 10)",
            'DebugLog("AESN_MERGE_MISMATCH PASS canonicalAverage=7,canonicalSize=3,reconciledEnemies=2,percentageWrites=1|1")',
            'DebugLog("AESN_MERGE_MISMATCH FAIL reconciliationIncomplete=1")',
        ):
            self.assertIn(required, text)

        # The harness may seed opposing source policies, but production owns
        # canonical selection and every HP/component transition.
        self.assertNotIn("PROC_AESN_CommitCanonicalMergePolicy(", text)
        self.assertNotIn("DB_AESN_HpTransaction(_OldCombat, _OldFirst, 1, \"HPCommitted\"", text)
        self.assertNotIn(
            'ObjectTimerFinished(_OldFirst, "AESN_MERGE_MISMATCH_VERIFY")',
            text,
        )
        self.assertEqual(
            text.count(
                'ObjectTimerFinished((CHARACTER)_OldFirst, "AESN_MERGE_MISMATCH_VERIFY")'
            ),
            2,
        )

        verify_proc_start = text.index(
            "PROC_AESN_StartMismatchMergeVerify((GUIDSTRING)_DiscardedCombat"
        )
        verify_proc_end = text.index(
            'ObjectTimerFinished((CHARACTER)_OldFirst, "AESN_MERGE_MISMATCH_VERIFY")',
            verify_proc_start,
        )
        verify_proc = text[verify_proc_start:verify_proc_end]
        mark_started = verify_proc.index(
            "DB_AESN_MergeMismatchVerifyStarted(_DiscardedCombat, _SurvivingCombat);"
        )
        add_pending = verify_proc.index(
            "DB_AESN_MergeMismatchVerifyPending(_DiscardedCombat, _SurvivingCombat, _OldFirst, _NewFirst);"
        )
        self.assertLess(mark_started, add_pending)
        self.assertGreaterEqual(
            text.count(
                "NOT DB_AESN_MergeMismatchVerifyStarted(_DiscardedCombat, _SurvivingCombat)"
            ),
            2,
        )

    def test_final_merge_cleanup_retires_mismatch_diagnostic(self):
        text = (
            ROOT / "story/RawFiles/Goals/AESN_60_Merge.txt"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "DB_AESN_MergePolicyMismatch(_Source, _Combat, _OldAverage, _OldSize, _NewAverage, _NewSize, _CanonicalAverage, _CanonicalSize)",
            text,
        )
        self.assertIn(
            "NOT DB_AESN_MergePolicyMismatch(_Source, _Combat, _OldAverage, _OldSize, _NewAverage, _NewSize, _CanonicalAverage, _CanonicalSize);",
            text,
        )

    def test_merge_chain_harness_uses_two_native_merges_and_final_aliases(self):
        text = (
            ROOT / "story/RawFiles/Goals/AESN_91_MergeHarness.txt"
        ).read_text(encoding="utf-8")

        for required in (
            'TextEvent("AESN_TEST_START_CHAIN_EXTENSION")',
            'TextEvent("AESN_TEST_TRIGGER_CHAIN_EXTENSION")',
            "DB_AESN_MergeChainFixture",
            "DB_AESN_MergeChainMarked",
            "DB_AESN_MergeChainPass",
            "PROC_EnterCombat(_ChainFirst, _ChainSecond);",
            "SwitchedCombat(_Object, _SurvivingCombat, _ThirdCombat)",
            "SwitchedCombat(_Object, _ThirdCombat, _SurvivingCombat)",
            "DB_AESN_CombatAlias(_FirstDiscarded, _FinalCombat)",
            "DB_AESN_CombatAlias(_SecondDiscarded, _FinalCombat)",
            "NOT DB_AESN_CombatAlias(_, _SecondDiscarded)",
            'DebugLog("AESN_MERGE_CHAIN PASS aliasesFlattened=2,discardedCleanupSuppressed=2,finalCleanupOwner=1")',
            "PROC_AESN_ResetOptionalChainActors(_OldFirst);",
            "PROC_AESN_ResetMergeChainFacts(_Owner);",
        ):
            self.assertIn(required, text)

        # The fixture drives two native ordinary-combat merges. Production is
        # solely responsible for alias creation, flattening, and migration.
        self.assertEqual(text.count("PROC_AESN_MergeCombat("), 0)
        self.assertEqual(text.count("PROC_AESN_FlattenCombatAliases("), 0)

        start = text.index('TextEvent("AESN_TEST_START_CHAIN_EXTENSION")')
        trigger = text.index('TextEvent("AESN_TEST_TRIGGER_CHAIN_EXTENSION")')
        self.assertLess(start, trigger)
        self.assertNotIn("EnteredCombat(_ChainFirst,", text)
        self.assertEqual(text.count("EnteredCombat((CHARACTER)_ChainFirst,"), 2)

    def test_combat_dispatch_barrier_is_one_shot(self):
        text = (
            ROOT / "story/RawFiles/Goals/AESN_30_Combat.txt"
        ).read_text(encoding="utf-8")

        self.assertIn("NOT DB_AESN_CombatDispatched(_Combat)", text)
        self.assertIn("NOT DB_AESN_CombatRetired(_Combat)", text)
        timer_event = text.index("TimerFinished(_Timer)")
        mark = text.index("DB_AESN_CombatDispatched(_Combat);", timer_event)
        clear_pending = text.index(
            "NOT DB_AESN_CombatDispatchPending(_Combat, _Timer);",
            timer_event,
        )
        self.assertLess(mark, clear_pending)

    def test_production_merge_marks_migrates_reconciles_and_suppresses_old_cleanup(self):
        path = ROOT / "story/RawFiles/Goals/AESN_60_Merge.txt"
        self.assertTrue(path.exists(), "production merge goal must exist")
        text = path.read_text(encoding="utf-8")

        for required in (
            "SwitchedCombat(_Object, _OldCombat, _NewCombat)",
            "DB_AESN_MergedCombat(_OldCombat, _NewCombat);",
            "DB_AESN_CombatAlias(_OldCombat, _NewCombat);",
            "PROC_AESN_MergeCombat(_OldCombat, _NewCombat);",
            "PROC_AESN_MigrateRosterState",
            "PROC_AESN_MigrateCombatState",
            "PROC_AESN_MigrateHpState",
            "PROC_AESN_MigrateComponentState",
            "PROC_AESN_ReconcileMergePolicy",
            "IntegerProduct(_CanonicalAverage, _CanonicalSize, _CanonicalSum)",
            'DebugLog("AESN_MERGE CLEANUP_SUPPRESSED discardedOwner=1")',
            "CombatEnded(_SurvivingCombat)",
            "PROC_AESN_RequestCombatCleanup(_SurvivingCombat);",
        ):
            self.assertIn(required, text)

        switch = text.index("SwitchedCombat(_Object, _OldCombat, _NewCombat)")
        mark = text.index(
            "DB_AESN_MergedCombat(_OldCombat, _NewCombat);", switch
        )
        migrate = text.index(
            "PROC_AESN_MergeCombat(_OldCombat, _NewCombat);", mark
        )
        self.assertLess(mark, migrate)

        for combat_owned in (
            "DB_AESN_SnapshotMember",
            "DB_AESN_CombatParticipant",
            "DB_AESN_EnemyConsidered",
            "DB_AESN_EnemyEligible",
            "DB_AESN_EnemyRejected",
            "DB_AESN_HpTransaction",
            "DB_AESN_HpDesiredBit",
            "DB_AESN_HpPlanQueued",
            "DB_AESN_HpFailure",
            "DB_AESN_HpPendingApply",
            "DB_AESN_EnemyHpBit",
            "DB_AESN_HpPendingRemove",
            "DB_AESN_HpCleanup",
            "DB_AESN_HpApplicationHold",
            "DB_AESN_ComponentApplication",
            "DB_AESN_ComponentStarted",
            "DB_AESN_EnemyComponent",
            "DB_AESN_ComponentPendingApply",
            "DB_AESN_ComponentPendingRemove",
        ):
            self.assertIn(combat_owned, text)

    def test_canonical_merge_replan_restores_percentage_only_after_new_bits(self):
        hp_plan = (
            ROOT / "story/RawFiles/Goals/AESN_40_HpTransaction.txt"
        ).read_text(encoding="utf-8")
        hp_apply = (
            ROOT / "story/RawFiles/Goals/AESN_50_Applications.txt"
        ).read_text(encoding="utf-8")
        components = (
            ROOT / "story/RawFiles/Goals/AESN_55_Components.txt"
        ).read_text(encoding="utf-8")

        for required in (
            "DB_AESN_HpReplan",
            "PROC_AESN_ReplanEnemy",
            'PROC_AESN_RemoveNextHpBit(_Combat, _Enemy, 15, "Replan")',
            'PROC_AESN_FinalizeHpRemoval((GUIDSTRING)_Combat, (CHARACTER)_Enemy, "Replan")',
            'PROC_AESN_PlanEnemyForReplan(_Enemy, _Combat, _CapturedPercentage);',
        ):
            self.assertIn(required, hp_apply)

        self.assertIn("PROC_AESN_PlanEnemyForReplan", hp_plan)
        self.assertIn(
            'DB_AESN_HpTransaction(_Combat, _Enemy, 1, "Planned", '
            "_BeforeCurrent, _BeforeMaximum, _CapturedPercentage,",
            hp_plan,
        )
        self.assertIn('"ReplanningComponents"', components)
        self.assertIn(
            'DebugLog("AESN_MERGE REPLAN_COMPLETE percentageWrite=1")',
            components,
        )

        replan_finalize = hp_apply.index(
            'PROC_AESN_FinalizeHpRemoval((GUIDSTRING)_Combat, (CHARACTER)_Enemy, "Replan")'
        )
        new_plan = hp_apply.index(
            "PROC_AESN_PlanEnemyForReplan(_Enemy, _Combat, _CapturedPercentage);",
            replan_finalize,
        )
        self.assertNotIn(
            "SetHitpointsPercentage", hp_apply[replan_finalize:new_plan]
        )
        self.assertIn(
            'DB_AESN_HpReplan(_Combat, _Enemy, 1, "ApplyingNew", '
            "_CapturedPercentage)",
            hp_apply,
        )
        self.assertIn(
            'DebugLog("AESN_MERGE REPLAN_ZERO_DELTA percentageWrite=1")',
            hp_apply,
        )

        # Osiris reacts synchronously to fact deletion. Keep a replan row
        # present throughout every state transition so the NOT-HpReplan start
        # rule cannot recursively restart in the delete/add gap.
        transition_start = hp_apply.index(
            "PROC_AESN_SetHpReplanState((GUIDSTRING)_Combat"
        )
        transition_end = hp_apply.index(
            "PROC\nPROC_AESN_BeginHpReplanRemoval", transition_start
        )
        transition = hp_apply[transition_start:transition_end]
        add_new = transition.index(
            "DB_AESN_HpReplan(_Combat, _Enemy, _Version, _NewState, _CapturedPercentage);"
        )
        delete_old = transition.index(
            "NOT DB_AESN_HpReplan(_Combat, _Enemy, _Version, _OldState, _CapturedPercentage);"
        )
        self.assertLess(add_new, delete_old)

        complete_start = components.index(
            'DB_AESN_HpReplan(_Combat, _Enemy, 1, "ApplyingNew", _CapturedPercentage)'
        )
        complete_end = components.index(
            'DebugLog("AESN_MERGE REPLAN_COMPLETE percentageWrite=1")',
            complete_start,
        )
        complete = components[complete_start:complete_end]
        clear_request = complete.index(
            "NOT DB_AESN_MergeReplanRequired(_Combat, _Enemy);"
        )
        clear_guard = complete.index(
            'NOT DB_AESN_HpReplan(_Combat, _Enemy, 1, "ApplyingNew", _CapturedPercentage);'
        )
        self.assertLess(clear_request, clear_guard)

    def test_cap06_save_load_probe_is_persistent_observation_only(self):
        path = ROOT / "story/RawFiles/Goals/AESN_89_SaveLoadProbe.txt"
        self.assertTrue(path.exists(), "CAP-06 save/load proof goal must exist")
        text = path.read_text(encoding="utf-8")

        for required in (
            "SavegameLoadStarted()",
            "SavegameLoaded()",
            "DB_AESN_SaveLoadProbeArmed",
            "DB_AESN_SaveLoadCheckOpen",
            "DB_AESN_CombatSnapshot",
            'DB_AESN_HpTransaction(_Combat, _Enemy, 1, "HPCommitted"',
            'DB_AESN_ComponentApplication(_Combat, _Enemy, 1, "FullyCommitted")',
            "DB_AESN_EnemyHpBit",
            "DB_AESN_EnemyComponent",
            "HasActiveStatus",
            "CombatIsActive",
            "GetMaxHitpoints",
            'DebugLog("AESN_CAP06 RELOAD_PASS',
        ):
            self.assertIn(required, text)
        self.assertNotIn("ShowNotification(", text)

        # CAP-06 proves persistence; it must not mutate the transaction it is
        # observing or mask a reload defect by reapplying fork-owned effects.
        for forbidden in (
            "ApplyStatus(",
            "RemoveStatus(",
            "SetHitpoints(",
            "SetHitpointsPercentage(",
            "PROC_AESN_PlanEnemy",
            "PROC_AESN_CleanupEnemy",
        ):
            self.assertNotIn(forbidden, text)

    def test_production_reload_reconciliation_is_delayed_failure_closed_and_exact(self):
        path = ROOT / "story/RawFiles/Goals/AESN_65_Reconciliation.txt"
        self.assertTrue(path.exists(), "production reconciliation goal must exist")
        text = path.read_text(encoding="utf-8")

        for required in (
            "SavegameLoaded()",
            "DB_AESN_ReconcileCombatPending",
            "DB_AESN_ReconcileEnemyPending",
            "CombatIsActive",
            'TimerLaunch(_Timer, 500)',
            '"ValidActiveCommit"',
            '"InactiveCombat"',
            '"PendingApplication"',
            '"UnsupportedSchema"',
            '"IdentityMismatch"',
            "PROC_AESN_CleanupEnemy(_Enemy, _Combat);",
            "PROC_AESN_BeginHpRollback(_Combat, _Enemy);",
            "DB_AESN_HpApplicationHold(_Combat, _Enemy);",
        ):
            self.assertIn(required, text)

        # Production reconciliation may retain, clean up, or roll back. It may
        # never apply a status, write HP directly, or fabricate ownership.
        for forbidden in (
            "ApplyStatus(",
            "SetHitpoints(",
            "SetHitpointsPercentage(",
        ):
            self.assertNotIn(forbidden, text)
        self.assertNotIn("THEN\nDB_AESN_EnemyHpBit(", text)
        self.assertNotIn("THEN\nDB_AESN_EnemyComponent(", text)

        retain_marker = text.index(
            'DB_AESN_ReconcileResult(_Combat, _Enemy, "RETAIN", "ValidActiveCommit")'
        )
        retain_start = text.rfind("IF\n", 0, retain_marker)
        retain_end = text.index("IF\n", retain_marker)
        retain = text[retain_start:retain_end]
        self.assertNotIn("PROC_AESN_CleanupEnemy", retain)
        self.assertNotIn("PROC_AESN_BeginHpRollback", retain)

    def test_reconciliation_actions_bind_every_argument(self):
        """Catch wildcard variables used as mutation arguments after THEN."""
        unbound = []
        for filename in (
            "AESN_35_PendingReloadProbe.txt",
            "AESN_65_Reconciliation.txt",
            "AESN_88_ReconciliationHarness.txt",
        ):
            text = (ROOT / "story/RawFiles/Goals" / filename).read_text(
                encoding="utf-8"
            )
            in_actions = False
            for line_number, line in enumerate(text.splitlines(), start=1):
                stripped = line.strip()
                if stripped == "THEN":
                    in_actions = True
                    continue
                if in_actions and not stripped:
                    in_actions = False
                    continue
                if (
                    in_actions
                    and not stripped.startswith("//")
                    and re.search(r"(?:\(|,\s*)_(?:\s*[,\)])", stripped)
                ):
                    unbound.append((filename, line_number, stripped))

        self.assertEqual([], unbound, f"unbound action arguments: {unbound}")

    def test_reconciliation_harness_exercises_production_recovery_only(self):
        path = ROOT / "story/RawFiles/Goals/AESN_88_ReconciliationHarness.txt"
        self.assertTrue(path.exists(), "focused reconciliation harness must exist")
        text = path.read_text(encoding="utf-8")

        for required in (
            'TextEvent("AESN_TEST_RECONCILE_PENDING")',
            'TextEvent("AESN_TEST_RECONCILE_STALE")',
            'TextEvent("AESN_TEST_RESET_RECONCILE_HARNESS")',
            "CreateNarrativeCombat",
            "DestroyNarrativeCombat",
            'ObjectTimerFinished((CHARACTER)_Host, "AESN_RECON_HARNESS_STALE_RETIRE")',
            "CombatEnded(_Combat)",
            'DB_AESN_HpTransaction(_Combat, _Enemy, 1, "Planned"',
            'DB_AESN_HpTransaction(_Combat, _Enemy, 1, "HPCommitted"',
            "DB_AESN_ComponentStarted(_Combat, _Enemy);",
            "PROC_AESN_OpenCombatReconciliation(_Combat);",
            'DB_AESN_ReconcileResult(_Combat, _Enemy, "ROLLED_BACK", "PendingApplication")',
            'DB_AESN_ReconcileResult(_Combat, _Enemy, "CLEANUP", "InactiveCombat")',
            'DebugLog("AESN_RECONCILE_HARNESS PENDING_PASS',
            'DebugLog("AESN_RECONCILE_HARNESS STALE_PASS',
            'PROC_AESN_ClearReconcileHarnessResult("Pending");',
            'PROC_AESN_ClearReconcileHarnessResult("Stale");',
        ):
            self.assertIn(required, text)

        for forbidden in (
            "ApplyStatus(",
            "RemoveStatus(",
            "SetHitpoints(",
            "SetHitpointsPercentage(",
            "PROC_AESN_BeginHpRollback(",
            "PROC_AESN_RequestCombatCleanup(",
            "PROC_AESN_CleanupEnemy(",
        ):
            self.assertNotIn(forbidden, text)

        stale_seed = text.index(
            'ObjectTimerFinished((CHARACTER)_Host, "AESN_RECON_HARNESS_STALE_SEED")'
        )
        stale_open = text.index(
            "PROC_AESN_OpenCombatReconciliation(_Combat);", stale_seed
        )
        stale_block = text[stale_seed:stale_open]
        self.assertLess(
            stale_block.index("DB_AESN_ComponentStarted(_Combat, _Enemy);"),
            stale_block.index(
                'DB_AESN_HpTransaction(_Combat, _Enemy, 1, "HPCommitted"'
            ),
        )

    def test_pending_retail_reload_probe_is_dormant_and_observation_only(self):
        path = ROOT / "story/RawFiles/Goals/AESN_35_PendingReloadProbe.txt"
        self.assertTrue(path.exists(), "pending retail reload probe must exist")
        text = path.read_text(encoding="utf-8")

        for required in (
            "NOT DB_AESN_PendingReloadTestEnabled(1);",
            "DB_AESN_EnemyEligible(_Combat, _Enemy)",
            "DB_AESN_HpApplicationHold(_Combat, _Enemy);",
            'DB_AESN_HpTransaction(_Combat, _Enemy, 1, "Planned"',
            "SavegameLoadStarted()",
            "SavegameLoaded()",
            'DB_AESN_ReconcileResult(_Combat, _Enemy, "ROLLED_BACK", "PendingApplication")',
            'DebugLog("AESN_CAP06_PENDING RELOAD_PASS',
        ):
            self.assertIn(required, text)
        self.assertNotIn("ShowNotification(", text)

        self.assertNotRegex(
            text,
            r"(?m)^DB_AESN_PendingReloadTestEnabled\(1\);$",
            "tracked source must leave the retail probe disabled",
        )
        for forbidden in (
            "ApplyStatus(",
            "RemoveStatus(",
            "SetHitpoints(",
            "SetHitpointsPercentage(",
            "PROC_AESN_BeginHpRollback(",
            "PROC_AESN_RequestCombatCleanup(",
            "PROC_AESN_CleanupEnemy(",
        ):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
