import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_UUID = "a4567f52-1665-df50-b84c-3992f80fdb90"
MODULE_FOLDER = f"AdaptiveEnemyScalingNativePOC_{MODULE_UUID}"
GOALS = ROOT / "story/RawFiles/Goals"
STATUS = (
    ROOT
    / "toolkit/Public"
    / MODULE_FOLDER
    / "Stats/Generated/Data/Status_BOOST.txt"
)
ROSTER = GOALS / "AESN_10_Roster.txt"
POLICY = GOALS / "AESN_20_Policy.txt"
COMBAT = GOALS / "AESN_30_Combat.txt"
RELENTLESS = GOALS / "AESN_56_Relentless.txt"
WORLD = GOALS / "AESN_25_WorldHardened.txt"
WORLD_RUNTIME = GOALS / "AESN_66_WorldHardenedRuntime.txt"
WORLD_HARNESS = GOALS / "AESN_84_WorldHardenedHarness.txt"
SAVE_LOAD_PROBE = GOALS / "AESN_89_SaveLoadProbe.txt"
DIAGNOSTICS = GOALS / "AESN_90_Diagnostics.txt"
NARRATIVE_HARNESS = GOALS / "AESN_94_NarrativeCombatHarness.txt"
TEST_HARNESS = GOALS / "AESN_99_TestHarness.txt"
EXPECTED_BITS = tuple(1 << index for index in range(16))


class IdentityAndRosterContracts(unittest.TestCase):
    def test_full_hp_registry_is_exact_and_namespaced(self):
        text = STATUS.read_text(encoding="utf-8")
        entries = re.findall(r'^new entry "([^"]+)"$', text, re.MULTILINE)
        stack_ids = re.findall(r'^data "StackId" "([^"]+)"$', text, re.MULTILINE)

        self.assertTrue(entries)
        self.assertTrue(all(entry.startswith("AESN_") for entry in entries))
        self.assertTrue(all(stack.startswith("AESN_") for stack in stack_ids))

        for bit in EXPECTED_BITS:
            status_id = f"AESN_HP_BIT_{bit:05d}"
            self.assertEqual(entries.count(status_id), 1)
            self.assertEqual(stack_ids.count(status_id), 1)
            self.assertEqual(
                text.count(f'data "Boosts" "IncreaseMaxHP({bit});"'),
                1,
            )

        for required in (
            'new entry "AESN_HARDENED_FOE_01"',
            'new entry "AESN_HARDENED_FOE_06"',
            'new entry "AESN_RELENTLESS_FOE_01"',
            'new entry "AESN_RELENTLESS_FOE_02"',
            'new entry "AESN_TIER_LEVEL_05_08"',
            'data "Boosts" "RollBonus(Attack,1);'
            'RollBonus(SavingThrow,1);AC(1);SpellSaveDC(1);"',
            'new entry "AESN_EXTRA_ACTION_1"',
            'data "Boosts" "ActionResource(ActionPoint,1,0);"',
            'new entry "AESN_EXTRA_BONUS_ACTION_1"',
            'data "Boosts" "ActionResource(BonusActionPoint,1,0);"',
        ):
            self.assertIn(required, text)

    def test_story_database_tokens_are_namespaced(self):
        allowed_vanilla = {"DB_NOOP", "DB_PartyMembers", "DB_PartOfTheTeam"}
        for path in GOALS.glob("AESN_*.txt"):
            text = path.read_text(encoding="utf-8")
            allowed_for_path = set(allowed_vanilla)
            if path == TEST_HARNESS:
                allowed_for_path.update({"DB_Players", "DB_Avatars"})
            if path == SAVE_LOAD_PROBE:
                allowed_for_path.add("DB_Players")
            if path in (
                COMBAT,
                RELENTLESS,
                WORLD,
                WORLD_RUNTIME,
                WORLD_HARNESS,
                NARRATIVE_HARNESS,
                GOALS / "AESN_47_HpMigration.txt",
            ):
                allowed_for_path.add("DB_Is_InCombat")
            for token in re.findall(r"\bDB_[A-Za-z0-9_]+\b", text):
                self.assertTrue(
                    token.startswith("DB_AESN_") or token in allowed_for_path,
                    f"{path.name}: unexpected database token {token}",
                )

        harness_text = TEST_HARNESS.read_text(encoding="utf-8")
        exact_fixture_facts = (
            "DB_Players((CHARACTER)S_Player_ShadowHeart_"
            "3ed74f06-3c60-42dc-83f6-f034cb47c679);",
            "DB_Players((CHARACTER)S_Player_Gale_"
            "ad9af97d-75da-406a-ae13-7071c563f604);",
            "DB_Players((CHARACTER)S_Player_Astarion_"
            "c7c13742-bacd-460a-8f65-f864fe41f255);",
        )
        self.assertEqual(harness_text.count("DB_Players("), 3)
        for exact_fact in exact_fixture_facts:
            self.assertEqual(harness_text.count(exact_fact), 1)

        exact_avatar_fact = (
            "DB_Avatars((CHARACTER)S_Player_ShadowHeart_"
            "3ed74f06-3c60-42dc-83f6-f034cb47c679);"
        )
        self.assertEqual(harness_text.count("DB_Avatars("), 1)
        self.assertEqual(harness_text.count(exact_avatar_fact), 1)

    def test_roster_uses_only_party_members_as_positive_candidates(self):
        text = ROSTER.read_text(encoding="utf-8")
        self.assertIn("DB_PartyMembers(_Member)", text)
        party_tokens = set(
            re.findall(r"\bDB_[A-Za-z0-9_]*Party[A-Za-z0-9_]*\b", text)
        )
        self.assertEqual(party_tokens, {"DB_PartyMembers"})

        for required in (
            "QRY_AESN_IsEligibleRosterMember((CHARACTER)_Member)",
            "PROC_AESN_BuildRoster((GUIDSTRING)_Combat)",
            "PROC_AESN_RecordEligibleMember((GUIDSTRING)_Combat, (CHARACTER)_Member, (INTEGER)_Level)",
            "IsSummon(_Member, 0)",
            "NOT CharacterGetOwner(_Member, _)",
            "IsPartyFollower(_Member, 0)",
            "GetLevel(_Member, _Level)",
            'ConcatenateGUID("AESN_SNAPSHOT_FINALIZE_", _Combat, _Timer)',
            "TimerLaunch(_Timer, 100);",
            "PROC_AESN_FinalizeSnapshot(_Combat);",
        ):
            self.assertIn(required, text)

    def test_diagnostics_cannot_add_snapshot_members(self):
        diagnostic_text = DIAGNOSTICS.read_text(encoding="utf-8")
        self.assertIn("DB_PartOfTheTeam", diagnostic_text)
        self.assertIn("IsPlayer", diagnostic_text)
        self.assertIn("GetFaction", diagnostic_text)
        self.assertIn("ObjectTransformed", diagnostic_text)
        self.assertNotIn("DB_AESN_SnapshotMember", diagnostic_text)
        for required in (
            '"AESN_CAP03 DIAGNOSTIC member="',
            '"AESN_CAP03 TRANSFORMED member="',
            "DB_AESN_RosterDiagnostic(",
            "DB_AESN_RosterDiagnosticFlag(",
            "DB_AESN_RosterDiagnosticFaction(",
            "DB_AESN_TransformationDiagnostic(",
            "DebugLog(_Message);",
        ):
            self.assertIn(required, diagnostic_text)

        for path in GOALS.glob("AESN_*.txt"):
            if path == DIAGNOSTICS:
                continue
            self.assertNotIn(
                "DB_PartOfTheTeam",
                path.read_text(encoding="utf-8"),
                f"{path.name}: DB_PartOfTheTeam is diagnostic-only",
            )

    def test_policy_records_versioned_exact_snapshot(self):
        text = POLICY.read_text(encoding="utf-8")
        for required in (
            "PROC_AESN_FinalizeSnapshot((GUIDSTRING)_Combat)",
            "DB_AESN_CombatSnapshotV2(",
            "DB_AESN_SchemaVersion(2)",
            "IntegerDivide(_LevelSum, _EligibleSize, _AverageLevel)",
            "IntegerProduct(_PartyMinusOne, 20, _PartyBonus)",
            "IntegerSum(_SoloHpPercent, _PartyBonus, _TargetHpPercent)",
            "PartySizeClampedAbove12",
            '"Supported"',
        ):
            self.assertIn(required, text)

    def test_combat_uses_participant_intersection_and_existential_hostility(self):
        text = COMBAT.read_text(encoding="utf-8")

        for required in (
            "CombatStarted(_Combat)",
            "EnteredCombat(_Object, _Combat)",
            "DB_AESN_SnapshotMember(_Combat, _Member, _)",
            "DB_Is_InCombat(_Member, _Combat)",
            "DB_AESN_CombatParticipant(_Combat, _Member)",
            "QRY_AESN_IsEligibleHostile((CHARACTER)_Enemy, (GUIDSTRING)_Combat)",
            "IsEnemy(_Enemy, _Member, 1)",
            "PROC_AESN_ConsiderEnemy((CHARACTER)_Enemy, (GUIDSTRING)_Combat)",
            "DB_AESN_EnemyConsidered(_Combat, _Enemy)",
            "DB_AESN_EnemyEligible(_Combat, _Enemy)",
            "DB_AESN_EnemyRejected(_Combat, _Enemy, \"HostileToNoParticipant\")",
            "IF\nDB_AESN_EnemyEligible(_Combat, _Enemy)",
            "IF\nDB_AESN_EnemyRejected(_Combat, _Enemy, \"HostileToNoParticipant\")",
            'ConcatenateGUID("AESN_COMBAT_DISPATCH_", _Combat, _Timer)',
            "TimerLaunch(_Timer, 100);",
        ):
            self.assertIn(required, text)

        for forbidden in (
            "DB_Players",
            "GetHostCharacter",
            "GetBaseArchetype",
            "DB_PartOfTheTeam",
            "DB_AESN_Representative",
        ):
            self.assertNotIn(forbidden, text)

    def test_cap03_editor_command_emits_roster_evidence(self):
        harness_text = TEST_HARNESS.read_text(encoding="utf-8")
        roster_text = ROSTER.read_text(encoding="utf-8")
        policy_text = POLICY.read_text(encoding="utf-8")

        self.assertIn('TextEvent("AESN_TEST_BUILD_ROSTER")', harness_text)
        self.assertIn("PROC_AESN_BuildRoster(", harness_text)
        for required in (
            '"AESN_ROSTER ELIGIBLE member="',
            '",source=DB_PartyMembers"',
            '"AESN_ROSTER EXCLUDED member="',
        ):
            self.assertIn(required, roster_text)
        for required in (
            '"AESN_POLICY schema=2,size="',
            '"EmptyEligibleRoster"',
            "DebugLog(_Message);",
        ):
            self.assertIn(required, policy_text)

    def test_no_tactician_identity_or_identifier_in_executable_sources(self):
        paths = list(GOALS.glob("AESN_*.txt")) + [STATUS]
        for path in paths:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn(
                "7d6712c3-3b64-e94d-6f1a-9de67678b44b",
                text,
                f"{path.name}: forbidden Tactician module UUID",
            )
            self.assertIsNone(
                re.search(r"(?<![A-Za-z0-9])TE_[A-Za-z0-9_]*", text),
                f"{path.name}: forbidden Tactician-style identifier",
            )


if __name__ == "__main__":
    unittest.main()
