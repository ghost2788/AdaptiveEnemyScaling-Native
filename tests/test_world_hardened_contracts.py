import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
GOALS = ROOT / "story" / "RawFiles" / "Goals"
WORLD_SCHEMA_GOAL = GOALS / "AESN_25_WorldHardened.txt"
WORLD_RUNTIME_GOAL = GOALS / "AESN_66_WorldHardenedRuntime.txt"
WORLD_OWNER = (
    "AESN_WorldHardenedOwner_da8f9f22-2125-45f1-ac0f-a8c264596f04"
)


class WorldHardenedContracts(unittest.TestCase):
    def world_goal(self) -> str:
        self.assertTrue(
            WORLD_SCHEMA_GOAL.exists(), "world Hardened schema goal must exist"
        )
        self.assertTrue(
            WORLD_RUNTIME_GOAL.exists(), "world Hardened runtime goal must exist"
        )
        return "\n".join(
            (
                WORLD_SCHEMA_GOAL.read_text(encoding="utf-8"),
                WORLD_RUNTIME_GOAL.read_text(encoding="utf-8"),
            )
        )

    def test_world_runtime_compiles_after_core_database_declarations(self):
        goal_names = sorted(path.name for path in GOALS.glob("AESN_*.txt"))

        self.assertLess(
            goal_names.index("AESN_65_Reconciliation.txt"),
            goal_names.index("AESN_66_WorldHardenedRuntime.txt"),
        )
        schema = WORLD_SCHEMA_GOAL.read_text(encoding="utf-8")
        runtime = WORLD_RUNTIME_GOAL.read_text(encoding="utf-8")
        self.assertNotIn("IterateCharactersAround", schema)
        self.assertIn("IterateCharactersAround", runtime)

    def test_world_goal_declares_durable_owner_without_relentless(self):
        world = self.world_goal()

        owner_fact = (
            "DB_AESN_WorldContext((GUIDSTRING)"
            f"{WORLD_OWNER});"
        )
        self.assertGreaterEqual(
            world.count(owner_fact),
            2,
            "new and upgraded saves must both receive the durable owner fact",
        )
        self.assertNotIn("AESN_RELENTLESS_FOE_", world)

    def test_world_scan_is_discovery_only_and_sticky_after_commit(self):
        world = self.world_goal()

        self.assertIn(
            'IterateCharactersAround(_Member, 100.0, '
            '"AESN_WORLD_CANDIDATE", "AESN_WORLD_SCAN_COMPLETE")',
            world,
        )
        for gate in (
            "IsDead(_Enemy, 0)",
            "IsActive(_Enemy, 1)",
            "IsOnStage(_Enemy, 1)",
            "IsInvisible(_Enemy, 0)",
            "IsEnemy(_Enemy, _Member, 1)",
            "NOT DB_Is_InCombat(_Enemy, _)",
        ):
            self.assertIn(gate, world)

        discovery_query = re.search(
            r"(?s)QRY\s+QRY_AESN_IsDiscoverableWorldHostile"
            r"(?P<body>.*?)(?=\nQRY\s|\nPROC\s|\nIF\s|\nEXITSECTION)",
            world,
        )
        self.assertIsNotNone(discovery_query)
        self.assertNotIn("HasLineOfSight", discovery_query.group("body"))
        self.assertNotIn("CanSee", discovery_query.group("body"))

        self.assertIn("DB_AESN_WorldScanSeen(_Enemy)", world)
        self.assertIn("DB_AESN_WorldScanMiss(_Enemy)", world)
        self.assertIn('TimerLaunch("AESN_WORLD_SCAN", 3000)', world)
        scan_miss = re.search(
            r"(?s)PROC\s+PROC_AESN_RecordWorldScanMisses"
            r"(?P<body>.*?)(?=\nPROC\s|\nIF\s|\nQRY\s|\nEXITSECTION)",
            world,
        )
        self.assertIsNotNone(scan_miss)
        self.assertNotIn(
            "PROC_AESN_RequestWorldCleanup",
            scan_miss.group("body"),
            "leaving scan range or visibility must not remove a committed package",
        )

    def test_world_policy_refresh_and_external_hp_replan_are_explicit(self):
        world = self.world_goal()

        for event in (
            "SavegameLoaded()",
            "LevelGameplayStarted(_Level, _IsEditorMode)",
            "CharacterJoinedParty(_Character)",
            "CharacterLeftParty(_Character)",
            "LeveledUp(_Character)",
            "RespecCompleted(_Character)",
            "WentOnStage(_Object, _IsOnStageNow)",
            "RelationChanged(_SourceFaction, _TargetFaction, _Relation, _Permanent)",
            "TemporaryHostileRelationRequestHandled(_Character1, _Character2, _Success)",
            "TemporaryHostileRelationRemoved(_Enemy, _SourceFaction, _TargetFaction)",
            "BaseFactionChanged(_Target, _OldFaction, _NewFaction)",
            "LeftCombat(_Object, _Combat)",
        ):
            self.assertIn(event, world)

        self.assertRegex(
            world,
            r"(?s)GetMaxHitpoints\(_Enemy, _ObservedMaximum\).*?"
            r"DB_AESN_HpTransaction\(_World, _Enemy, _Representation, \"HPCommitted\", "
            r"_, _, _, _TargetMaximum, _Delta, _AppliedSum\).*?"
            r"_ObservedMaximum != _TargetMaximum.*?"
            r"DB_AESN_MergeReplanRequired\(_World, _Enemy\)",
        )
        self.assertIn("DB_AESN_WorldReplanDeferred(_Enemy)", world)
        self.assertGreaterEqual(
            world.count("NOT DB_AESN_HpApplicationHold(_World, _)"),
            2,
            "world policy refresh must wait for save/load reconciliation",
        )
        self.assertRegex(
            world,
            r"(?s)DB_AESN_HpFailure\(_World, _Enemy, _Reason\).*?"
            r"DB_AESN_WorldTracked\(_Enemy\).*?"
            r"PROC_AESN_RequestWorldCleanup\(_Enemy, _World\);",
        )
        self.assertRegex(
            world,
            r"(?s)DB_AESN_SnapshotFailure\(_World, \"EmptyEligibleRoster\"\).*?"
            r"NOT DB_AESN_WorldPolicyRefreshState\(\"Building\"\);.*?"
            r"TimerLaunch\(\"AESN_WORLD_POLICY_RETRY\", 5000\);",
        )
        self.assertRegex(
            world,
            r"(?s)TimerFinished\(\"AESN_WORLD_POLICY_RETRY\"\).*?"
            r"PROC_AESN_RequestWorldPolicyRefresh\(\);",
        )

    def test_save_load_clears_and_rearms_transient_world_scheduler(self):
        world = self.world_goal()

        self.assertRegex(
            world,
            r"(?s)SavegameLoaded\(\).*?"
            r"PROC_AESN_ResetWorldTransient\(\(GUIDSTRING\)"
            r"AESN_WorldHardenedOwner_da8f9f22-2125-45f1-ac0f-a8c264596f04\);.*?"
            r"TimerLaunch\(\"AESN_WORLD_LOAD_REFRESH\", 500\);",
        )
        self.assertRegex(
            world,
            r"(?s)TimerFinished\(\"AESN_WORLD_LOAD_REFRESH\"\).*?"
            r"PROC_AESN_RequestWorldPolicyRefresh\(\);",
        )
        for transient_fact in (
            "DB_AESN_WorldPolicyRefreshState(_State)",
            "DB_AESN_WorldPreviousPolicy(_World, _Tier, _TargetHpPercent)",
            "DB_AESN_WorldPolicyFinalizePending(_World)",
            "DB_AESN_WorldScanScheduled(_World)",
            "DB_AESN_WorldScanOpen(_World)",
            "DB_AESN_WorldScanCenter(_Member)",
            "DB_AESN_WorldScanCompletionCount(_Count)",
            "DB_AESN_WorldScanSeen(_Enemy)",
        ):
            self.assertRegex(
                world,
                rf"(?s)PROC_AESN_ResetWorldTransient.*?"
                rf"{re.escape(transient_fact)}.*?NOT {re.escape(transient_fact)};",
            )

    def test_world_goal_is_in_the_production_sync_allowlist(self):
        sync = (ROOT / "tools" / "sync_toolkit_project.ps1").read_text(
            encoding="utf-8"
        )

        production_block = re.search(
            r"\$productionGoalNames = @\((?P<body>.*?)\n\)",
            sync,
            re.DOTALL,
        )
        self.assertIsNotNone(production_block)
        self.assertIn(
            "'AESN_25_WorldHardened.txt'",
            production_block.group("body"),
        )
        self.assertIn(
            "'AESN_66_WorldHardenedRuntime.txt'",
            production_block.group("body"),
        )

    def test_combat_handoff_uses_one_hardened_owner(self):
        hp = (GOALS / "AESN_40_HpTransaction.txt").read_text(encoding="utf-8")
        relentless = (GOALS / "AESN_56_Relentless.txt").read_text(
            encoding="utf-8"
        )
        merge = (GOALS / "AESN_60_Merge.txt").read_text(encoding="utf-8")

        initial_planner = re.search(
            r"IF\s+DB_AESN_EnemyEligible\(_Combat, _Enemy\)"
            r"(?P<guards>.*?)THEN\s+PROC_AESN_PlanEnemy\(_Enemy, _Combat\);",
            hp,
            re.DOTALL,
        )
        self.assertIsNotNone(initial_planner)
        self.assertIn(
            "QRY_AESN_InitialHpPlanAllowed(_Combat, _Enemy)",
            initial_planner.group("guards"),
        )
        self.assertRegex(
            hp,
            r"(?s)QRY\s+QRY_AESN_HardenedPlanOwnerAllowed"
            r"\(\(GUIDSTRING\)_Combat, \(CHARACTER\)_Enemy\).*?"
            r"DB_AESN_WorldContext\(_Combat\).*?DB_NOOP\(1\);",
        )
        self.assertRegex(
            hp,
            r"(?s)QRY\s+QRY_AESN_HardenedPlanOwnerAllowed"
            r"\(\(GUIDSTRING\)_Combat, \(CHARACTER\)_Enemy\).*?"
            r"NOT DB_AESN_WorldContext\(_Combat\).*?"
            r"NOT DB_AESN_WorldTracked\(_Enemy\).*?DB_NOOP\(1\);",
        )

        self.assertIn(
            "NOT DB_AESN_CombatHardenedReady((GUIDSTRING)"
            "NULL_00000000-0000-0000-0000-000000000000, "
            "(CHARACTER)NULL_00000000-0000-0000-0000-000000000000);",
            relentless,
        )
        self.assertRegex(
            relentless,
            r"(?s)DB_AESN_ComponentApplication\(_Combat, _Enemy, 1, "
            r"\"FullyCommitted\"\).*?NOT DB_AESN_WorldContext\(_Combat\).*?"
            r"DB_AESN_CombatHardenedReady\(_Combat, _Enemy\);",
        )
        self.assertRegex(
            relentless,
            r"(?s)DB_AESN_WorldHardenedReady\(_Enemy\).*?"
            r"DB_AESN_EnemyEligible\(_Combat, _Enemy\).*?"
            r"DB_AESN_CombatHardenedReady\(_Combat, _Enemy\);",
        )

        candidate = re.search(
            r"PROC\s+PROC_AESN_ConsiderRelentlessCandidate"
            r"(?P<body>.*?)(?=\nPROC\s|\nIF\s|\nEXITSECTION)",
            relentless,
            re.DOTALL,
        )
        self.assertIsNotNone(candidate)
        self.assertIn(
            "DB_AESN_CombatHardenedReady(_Combat, _Enemy)",
            candidate.group("body"),
        )
        self.assertNotIn(
            'DB_AESN_ComponentApplication(_Combat, _Enemy, 1, "FullyCommitted")',
            candidate.group("body"),
        )

        self.assertIn(
            "DB_AESN_CombatHardenedReady(_OldCombat, _Enemy)",
            merge,
        )
        self.assertIn(
            "DB_AESN_CombatHardenedReady(_Combat, _Enemy)",
            merge,
        )
        self.assertRegex(
            merge,
            r"(?s)PROC_AESN_DispatchCombatEnemyCleanup.*?"
            r"DB_AESN_EnemyComponent\(_Combat, _Enemy, \"Relentless\", _\).*?"
            r"NOT DB_AESN_HpTransaction\(_Combat, _Enemy, _, _, _, _, _, _, _, _\).*?"
            r"PROC_AESN_CleanupEnemy\(_Enemy, _Combat\);",
        )

    def test_neutral_combat_rejection_is_rechecked_after_hostility_change(self):
        combat = (GOALS / "AESN_30_Combat.txt").read_text(encoding="utf-8")
        merge = (GOALS / "AESN_60_Merge.txt").read_text(encoding="utf-8")

        self.assertIn("DB_AESN_HostilityRecheckPending", combat)
        for event in (
            "AttackedBy(_Defender, _AttackerOwner, _Attacker, _DamageType, _DamageAmount, _DamageCause, _StoryActionID)",
            "RelationChanged(_SourceFaction, _TargetFaction, _Relation, _Permanent)",
            "TemporaryHostileRelationRequestHandled(_Character1, _Character2, _Success)",
            "BaseFactionChanged(_Target, _OldFaction, _NewFaction)",
        ):
            self.assertIn(event, combat)

        self.assertRegex(
            combat,
            r"(?s)PROC\s+PROC_AESN_ReconsiderRejectedHostiles"
            r".*?DB_AESN_EnemyRejected\(_Combat, _Enemy, "
            r'"HostileToNoParticipant"\).*?'
            r"DB_Is_InCombat\(_Enemy, _Combat\).*?"
            r"QRY_AESN_IsEligibleHostile\(_Enemy, _Combat\).*?"
            r"NOT DB_AESN_EnemyRejected\(_Combat, _Enemy, "
            r'"HostileToNoParticipant"\);.*?'
            r"NOT DB_AESN_EnemyConsidered\(_Combat, _Enemy\);.*?"
            r"PROC_AESN_ConsiderEnemy\(_Enemy, _Combat\);",
        )
        self.assertRegex(
            merge,
            r"(?s)PROC_AESN_DeleteCombatOwnedFacts.*?"
            r"DB_AESN_HostilityRecheckPending\(_Combat, _Timer\).*?"
            r"NOT DB_AESN_HostilityRecheckPending\(_Combat, _Timer\);",
        )

    def test_save_load_retains_only_valid_world_commit(self):
        reconciliation = (
            GOALS / "AESN_65_Reconciliation.txt"
        ).read_text(encoding="utf-8")

        world_open = re.search(
            r"(?s)PROC\s+PROC_AESN_OpenCombatReconciliation"
            r"\(\(GUIDSTRING\)_Combat\)\s+AND\s+"
            r"DB_AESN_WorldContext\(_Combat\).*?"
            r"DB_AESN_ReconcileEnemyPending\(_Combat, _Enemy, 2\);",
            reconciliation,
        )
        self.assertIsNotNone(world_open)
        self.assertNotIn("CombatIsActive", world_open.group(0))

        self.assertRegex(
            reconciliation,
            r"(?s)DB_AESN_ReconcileEnemyPending\(_Combat, _Enemy, 2\).*?"
            r"DB_AESN_HpTransaction\(_Combat, _Enemy, _Representation, \"HPCommitted\".*?"
            r"DB_AESN_ComponentApplication\(_Combat, _Enemy, 1, \"FullyCommitted\"\).*?"
            r"GetMaxHitpoints\(_Enemy, _TargetMaximum\).*?"
            r"NOT DB_AESN_WorldCleanupRequested\(_Enemy\).*?"
            r"NOT DB_AESN_HpReplan\(_Combat, _Enemy, _, _, _\).*?"
            r"NOT DB_AESN_MergeReplanRequired\(_Combat, _Enemy\).*?"
            r"NOT DB_AESN_ReconcileFailure\(_Combat, _Enemy, _\).*?"
            r"DB_AESN_ReconcileResult\(_Combat, _Enemy, \"RETAIN\", "
            r"\"ValidWorldCommit\"\);.*?"
            r"NOT DB_AESN_HpApplicationHold\(_Combat, _Enemy\);.*?"
            r"DB_AESN_WorldHardenedReady\(_Enemy\);.*?"
            r"PROC_AESN_ClearWorldMutationPending\(_Enemy\);",
        )
        self.assertRegex(
            reconciliation,
            r"(?s)DB_AESN_ReconcileEnemyPending\(_Combat, _Enemy, 2\).*?"
            r"DB_AESN_ReconcileFailure\(_Combat, _Enemy, _Reason\).*?"
            r"PROC_AESN_CleanupEnemy\(_Enemy, _Combat\);",
        )
        self.assertRegex(
            reconciliation,
            r"(?s)SavegameLoaded\(\).*?"
            r"DB_AESN_ReconcileResult\(_Combat, _Enemy, \"RETAIN\", _Reason\).*?"
            r"NOT DB_AESN_ReconcileResult\(_Combat, _Enemy, \"RETAIN\", _Reason\);",
        )
        for pending_fact in (
            "DB_AESN_WorldCleanupRequested(_Enemy)",
            "DB_AESN_HpReplan(_Combat, _Enemy, _, _, _)",
            "DB_AESN_MergeReplanRequired(_Combat, _Enemy)",
        ):
            self.assertIn(pending_fact, reconciliation)

    def test_replan_and_cleanup_preserve_external_hp_modifiers(self):
        applications = (GOALS / "AESN_50_Applications.txt").read_text(
            encoding="utf-8"
        )

        self.assertRegex(
            applications,
            r"(?s)PROC_AESN_ReplanEnemy.*?"
            r"GetMaxHitpoints\(_Enemy, _ObservedMaximum\).*?"
            r"IntegerSubtract\(_ObservedMaximum, _AppliedSum, _ExternalBase\).*?"
            r"DB_AESN_HpTransaction\(_Combat, _Enemy, _Representation, \"HPCommitted\", "
            r"_BeforeCurrent, _ExternalBase, _BeforePercentage",
        )
        self.assertRegex(
            applications,
            r"(?s)PROC_AESN_FinalizeHpRemoval"
            r"\(\(GUIDSTRING\)_Combat, \(CHARACTER\)_Enemy, \"Cleanup\"\).*?"
            r"DB_AESN_HpCleanup\(_Combat, _Enemy, _CleanupCurrent, "
            r"_CleanupMaximum, _CleanupPercentage\).*?"
            r"IntegerSubtract\(_CleanupMaximum, _AppliedSum, _ExpectedMaximum\).*?"
            r"GetMaxHitpoints\(_Enemy, _ExpectedMaximum\)",
        )

    def test_docs_describe_world_scope_no_compounding_and_pending_proof(self):
        combined = "\n".join(
            (ROOT / name).read_text(encoding="utf-8")
            for name in ("README.md", "DESIGN.md", "TEST-PLAN.md", "CAPABILITY-PROOF.md")
        )

        for phrase in (
            "world-owned Hardened",
            "combat-owned Relentless",
            "100 metres",
            "three seconds",
            "discovery-only",
            "observed maximum - AES-owned applied sum",
            "Runtime verification: pending",
        ):
            self.assertIn(phrase, combined)

    def test_world_acceptance_harness_is_disabled_and_non_fabricating(self):
        harness_path = GOALS / "AESN_84_WorldHardenedHarness.txt"
        self.assertTrue(harness_path.exists(), "world acceptance harness must exist")
        harness = harness_path.read_text(encoding="utf-8")

        self.assertIn("NOT DB_AESN_WorldHarnessEnabled(1);", harness)
        for checkpoint in (
            "AESN_WORLD_PROOF PRECOMBAT_COMMIT",
            "AESN_WORLD_PROOF SINGLE_OWNER_COMBAT",
            "AESN_WORLD_PROOF RELENTLESS_COMBAT",
            "AESN_WORLD_PROOF POSTCOMBAT_RETAIN",
            "AESN_WORLD_PROOF POLICY_REPLAN",
            "AESN_WORLD_PROOF EXTERNAL_HP_REPLAN",
            "AESN_WORLD_PROOF STICKY_RETAIN",
            "AESN_WORLD_PROOF SAVELOAD_RETAIN",
        ):
            self.assertIn(checkpoint, harness)

        self.assertNotRegex(
            harness,
            r"(?s)THEN\s+DB_AESN_EnemyEligible\(",
            "the harness must observe production eligibility, not insert it",
        )
        self.assertNotRegex(
            harness,
            r"(?s)THEN\s+DB_AESN_WorldTracked\(",
            "the harness must observe production tracking, not insert it",
        )

        sync = (ROOT / "tools" / "sync_toolkit_project.ps1").read_text(
            encoding="utf-8"
        )
        production_block = re.search(
            r"\$productionGoalNames = @\((?P<body>.*?)\n\)",
            sync,
            re.DOTALL,
        )
        self.assertIsNotNone(production_block)
        self.assertNotIn(
            "AESN_84_WorldHardenedHarness.txt",
            production_block.group("body"),
        )


if __name__ == "__main__":
    unittest.main()
