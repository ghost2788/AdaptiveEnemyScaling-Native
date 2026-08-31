# Adaptive Enemy Scaling Native POC Design

## Decision

Use modular native statuses plus a versioned Osiris state machine. Maximum HP is represented by fork-owned binary flat-HP statuses; the stat tier, Action, and Bonus Action are separate fork-owned statuses. This makes every mutation attributable and reversible without removing another mod's resources.

The binary HP mechanism is a POC hypothesis until its isolated runtime gate passes. A mandatory gate failure stops the native path and leaves the Script Extender fallback untouched.

## Project identity and isolation

- Project/module: `AdaptiveEnemyScalingNativePOC`
- Module UUID: `bb8bdf43-775b-4451-9ffd-69b5f3f531e8`
- Module folder: `AdaptiveEnemyScalingNativePOC_bb8bdf43-775b-4451-9ffd-69b5f3f531e8`
- Version: `0.1.0`
- Status namespace: `AESN_*`
- Database namespace: `DB_AESN_*`
- No Script Extender tree
- No mod dependencies

Toolkit working files and repository-owned artifacts live on `B:`. The live game `Mods` directory and `modsettings.lsx` are read only for pre/post-build manifests until a separate installation approval.

## Source layout

```text
AdaptiveEnemyScaling-Native-POC/
|-- README.md
|-- DESIGN.md
|-- TEST-PLAN.md
|-- CAPABILITY-PROOF.md
|-- UPSTREAM.md
|-- THIRD-PARTY-NOTICE.md
|-- toolkit/
|   |-- Mods/AdaptiveEnemyScalingNativePOC_bb8bdf43-775b-4451-9ffd-69b5f3f531e8/meta.lsx
|   `-- Public/AdaptiveEnemyScalingNativePOC_bb8bdf43-775b-4451-9ffd-69b5f3f531e8/
|       |-- Stats/Generated/Data/Status_BOOST.txt
|       `-- Localization/English/AdaptiveEnemyScalingNativePOC.xml
|-- story/RawFiles/Goals/
|   |-- AESN_00_Init.txt
|   |-- AESN_10_Roster.txt
|   |-- AESN_20_Policy.txt
|   |-- AESN_30_Combat.txt
|   |-- AESN_40_HpTransaction.txt
|   |-- AESN_50_Applications.txt
|   |-- AESN_60_Merge.txt
|   |-- AESN_70_Reconcile.txt
|   |-- AESN_90_Diagnostics.txt
|   `-- AESN_99_TestHarness.txt
|-- tests/
|   |-- fixtures/
|   |-- test_poc_model.py
|   |-- validate_identities.py
|   |-- validate_package.py
|   `-- verify_live_directories_unchanged.ps1
`-- artifacts/                       # ignored
```

Numeric goal names aid navigation. Story goal dependencies, rather than filenames, establish execution order.

## Persistent state

All POC facts carry schema version `1` where applicable.

- `DB_AESN_SchemaVersion(1)`
- `DB_AESN_CombatSnapshot(combat, schema, eligibleSize, levelSum, averageLevel, levelPercent, partyPercent, policyState)`
- `DB_AESN_SnapshotMember(combat, member, level)`
- `DB_AESN_CombatParticipant(combat, member)`
- `DB_AESN_CombatAlias(discardedCombat, survivingCombat)`
- `DB_AESN_MergedCombat(discardedCombat, survivingCombat)`
- `DB_AESN_EnemyApplication(enemy, ownerCombat, schema, baseMaximum, targetMaximum, appliedDelta, statStatus, actionStatus, bonusStatus, state)`
- `DB_AESN_EnemyHpBit(enemy, ownerCombat, bitValue, statusId)`
- `DB_AESN_HpTransaction(enemy, ownerCombat, operation, capturedCurrent, capturedMaximum, expectedMaximum, restoreCurrent, acknowledgementCount, state)`
- `DB_AESN_DiagnosticOnce(key)`

Transaction states are `Planned`, `ApplyingHP`, `HPCommitted`, `FullyCommitted`, `Replanning`, `Removing`, and `Cleared`.

## Eligible roster

`DB_PartyMembers` is the only candidate source. `DB_PartOfTheTeam` is never unioned into eligibility.

For every `DB_PartyMembers` candidate:

1. Deduplicate by character GUID.
2. Exclude `IsSummon == 1`.
3. Exclude a character ownership relationship identifying an owned entity.
4. Exclude `IsPartyFollower == 1`.
5. Retain dead or downed active members.
6. Record team, player, follower, owner, summon, and transformation observations only as exclusion evidence, validation, or diagnostics.

An empty eligible roster fails closed and creates no scaling snapshot. Active companion and hireling inclusion is a mandatory runtime gate rather than an assumption.

## Snapshot and hostile targets

At combat start, snapshot eligible member GUIDs, levels, exact count, level sum, and floored average. Build `DB_AESN_CombatParticipant` from the intersection of the snapshot and native participants in that combat.

An enemy character is eligible only when an existential query succeeds:

```text
DB_AESN_CombatParticipant(combat, member)
AND IsEnemy(enemy, member) == 1
```

No representative party member, archetype, team, owner, or faction shortcut classifies the enemy. Hostile summons remain eligible when hostile to a participating snapshotted member. Repeated combat events are idempotent; late entrants receive the existing snapshot policy.

## Narrow POC policy

Average level is `floor(levelSum / eligibleSize)`.

The single stat tier is average level 5 through 8 inclusive:

- Level HP percent: `115`
- Attack: `+1`
- Saving throws: `+1`
- AC: `+1`
- Spell DC: `+1`

Party HP percent is `100 + 20 * (min(eligibleSize, 8) - 1)`. Counts above eight remain recorded and produce one clamp diagnostic.

Target maximum HP is:

```text
floor(baseMaximum * levelPercent * partyPercent / 10000)
```

The POC action probe is deliberately separate from production balance: an eligible party size of exactly three applies one `+1 ActionPoint` status and one `+1 BonusActionPoint` status. No exact total normalization is claimed.

Outside average level 5 through 8, the POC records the snapshot but performs no enemy mutation.

## Status registry

`Status_BOOST.txt` owns:

- `AESN_HP_BIT_00001` through `AESN_HP_BIT_32768`: sixteen hidden, independently stacked `IncreaseMaxHP` statuses.
- `AESN_TIER_LEVEL_05_08`: the single attack/save/AC/spell-DC tier.
- `AESN_EXTRA_ACTION_1`: additive `ActionPoint(1)`.
- `AESN_EXTRA_BONUS_ACTION_1`: additive `BonusActionPoint(1)`.

Every status has an `AESN_` ID and `AESN_` stack ID. No status changes reactions, Legendary Actions, class resources, Action Surge-like abilities, or boss-specific resources.

## HP transaction

The maximum supported fork delta is `65,535`.

### Apply

1. Capture current and maximum HP.
2. Validate positive maximum, safe multiplication, target maximum, and delta.
3. Calculate one target maximum and one restored current value.
4. Decompose the positive delta into fork-owned binary statuses.
5. Enter `ApplyingHP`, apply each bit, and record only acknowledged bits.
6. Verify the resulting maximum equals the captured maximum plus the delta.
7. Restore current HP percentage once.
8. Enter `HPCommitted`, then apply stat/action statuses and enter `FullyCommitted`.

Maximum HP uses floor rounding. Current HP uses integer round-half-up and is clamped to `[1, targetMaximum]` for a living character. A dead character remains at zero.

Delta zero applies no HP bits but may proceed with other POC components. Negative delta, delta above `65,535`, unsafe arithmetic, non-positive maximum, unexpected maximum, missing acknowledgement, or timeout fails closed for the whole enemy. A partial attempt removes only acknowledged fork bits, restores the captured percentage, applies no stat/action component, and retains a diagnostic record until rollback is confirmed.

An enemy already dead at initial application is skipped.

### Cleanup

1. Capture current and maximum HP.
2. Remove exactly the `DB_AESN_EnemyHpBit` rows recorded for the enemy.
3. Verify the maximum decreased by exactly their recorded sum, preserving unrelated modifiers.
4. Restore the captured percentage once if alive; never set HP on a dead enemy.
5. Remove only the exact recorded stat/action status IDs.
6. Delete application records only after confirmation.

### Replan

A merge policy change atomically removes the old recorded bits, applies the new bits, verifies the expected net maximum, and restores percentage once. It does not perform a full cleanup followed by a second percentage restoration.

## Merged combat ownership

The first `SwitchedCombat(object, oldCombat, survivingCombat)` event:

1. Creates the merged marker and alias before cleanup rules can act.
2. Migrates all enemy, transaction, bit, member, and participant bookkeeping from the old owner, not only the switching object.
3. Unions participating eligible member facts for hostility tests.
4. Suppresses all cleanup for `CombatEnded(oldCombat)`.

If both snapshots exist and differ, canonical average level is the higher average and canonical party size is the larger eligible size. Policy is recomputed from that synthetic pair, every tracked enemy from both combats is replanned, and the mismatch is logged once with both source snapshots. Alias chains resolve to the final surviving combat. Only the final combat end cleans the records.

## Save/load reconciliation

`SavegameLoaded`, `GameModeStarted(..., IsStoryReload)`, and gameplay-ready events trigger one guarded reconciliation pass.

- Active combat with matching committed records and statuses: retain unchanged.
- Active combat with a mismatch: remove only detected fork-owned statuses, preserve percentage once, and rebuild the persisted canonical plan.
- Discarded merged combat: resolve to the active surviving alias.
- Inactive combat: perform exact stale cleanup, then delete records.
- Pending transaction: verify and complete or rollback; never start a second application.
- Unsupported schema: use an explicit version cleanup handler or fail closed without reinterpreting facts.

If persistent database facts do not survive the isolated save/load spike, the native design is rejected under this requirement.

## Diagnostics

Diagnostics are disabled by default. Test mode emits structured, one-shot records for roster decisions, snapshots, policy, hostility, bit applications, rollback, cleanup, merge mismatch, reload reconciliation, and failure-closed conditions. Diagnostic queries never add a roster candidate or classify an enemy.

## Publication boundary

The official Toolkit is installed on `B:` after design approval. The project is built with Publish Local and the prompted output location is set to this repository's ignored `artifacts/` directory. Before and after manifests must prove that the live Mods directory and `modsettings.lsx` did not change. Work stops after the local package and static package report are ready. Installation, activation, multiplayer testing, and upload require a separate approval.

