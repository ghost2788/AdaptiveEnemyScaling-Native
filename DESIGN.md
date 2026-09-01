# Adaptive Enemy Scaling Native Design

## Decision

Use modular native statuses plus a versioned Osiris state machine. Maximum HP is represented by AESN-owned binary flat-HP statuses; Hardened and Relentless are separate owned statuses. This makes every mutation attributable and reversible without removing another mod's resources.

The HP, roster, hostility, merge, save/load, and personal Action/Bonus-Action resource mechanisms have passed their isolated native capability gates. Hardened and Relentless are production-enabled.

## Project identity and isolation

- Project/module: `AdaptiveEnemyScalingNativePOC`
- Module UUID: `a4567f52-1665-df50-b84c-3992f80fdb90`
- Module folder: `AdaptiveEnemyScalingNativePOC_a4567f52-1665-df50-b84c-3992f80fdb90`
- Internal POC milestone: `0.1.0`
- Toolkit module version: `1.0.0.0`; the Toolkit UI rejected major version `0`
- Expected first Publish Local version: `1.0.0.1` with auto-increment enabled
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
|   |-- Mods/AdaptiveEnemyScalingNativePOC_a4567f52-1665-df50-b84c-3992f80fdb90/meta.lsx
|   `-- Public/AdaptiveEnemyScalingNativePOC_a4567f52-1665-df50-b84c-3992f80fdb90/
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

Production policy state uses schema version `2`. The frozen snapshot contains derived policy outputs; mutable Relentless expenditure is kept in a separate monotonic ledger so the immutable combat policy never changes.

- `DB_AESN_SchemaVersion(2)`
- `DB_AESN_CombatSnapshotV2(combat, schema, eligibleSize, effectiveSize, levelSum, averageLevel, hardenedTier, targetHpPercent, actionBudget, bonusActionBudget, recipientCap, policyState)`
- `DB_AESN_SnapshotMember(combat, member, level)`
- `DB_AESN_CombatParticipant(combat, member)`
- `DB_AESN_CombatAlias(discardedCombat, survivingCombat)`
- `DB_AESN_MergedCombat(discardedCombat, survivingCombat)`
- `DB_AESN_HpTransaction(combat, enemy, version, state, beforeCurrent, beforeMaximum, beforePercentage, targetMaximum, delta, appliedSum)`
- `DB_AESN_EnemyHpBit(combat, enemy, bitValue, statusId)`
- `DB_AESN_EnemyComponent(combat, enemy, kind, statusId)`
- `DB_AESN_RelentlessLedger(combat, schema, actionBudget, bonusActionBudget, recipientCap, actionSpent, bonusActionSpent, recipientsSpent)`
- `DB_AESN_RelentlessRecipient(combat, enemy, tier)`
- `DB_AESN_DiagnosticOnce(key)`

Schema-1 snapshot and legacy status definitions remain only as migration handles. Loading a schema-1 save removes legacy AESN-owned components through the existing acknowledgement-driven cleanup, restores recorded HP, deletes the old snapshot, and builds a fresh schema-2 snapshot for an active combat.

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

## Production policy

Average level is `floor(levelSum / eligibleSize)` and both level and size are frozen for the combat. Effective size is capped at twelve. No gear inspection, module detection, enemy-level mutation, ability distribution, or flat damage bonus participates in policy.

| Tier | Average level | Solo HP | Attack/saves/DC | AC | Base Action budget | Base Bonus-Action budget |
|---|---:|---:|---:|---:|---:|---:|
| I | 1–4 | 125% | +1 | +0 | 0 | 0 |
| II | 5–8 | 150% | +2 | +1 | 1 | 0 |
| III | 9–12 | 180% | +3 | +1 | 1 | 0 |
| IV | 13–16 | 220% | +4 | +2 | 1 | 1 |
| V | 17–18 | 260% | +5 | +2 | 2 | 1 |
| VI | 19+ | 300% | +6 | +3 | 2 | 2 |

Each permanent member after the first adds twenty percentage points to HP. Target maximum is `floor(preAESNMaximum * targetHpPercent / 100)`. All six bands are stored as `DB_AESN_HardenedPolicyBand` data rows.

For parties above four, each extra member adds one Action-budget point and each two extra members add one Bonus-Action point. Solo and duo use no Relentless at tier I and exactly one tier-I-sized recipient from tier II onward. For sizes three and above, the recipient ceiling is `min(partySize - 2, 6)`. Bonus-Action budget upgrades recipients from Relentless I to II; remaining Action budget creates Relentless-I recipients. AESN never grants more than one extra Action or Bonus Action to one foe.

Relentless expenditure is monotonic. Failed applications, death, late entry, save/load, and combat merges never refund a spent point or replace a recipient. Production allocation additionally requires `DB_AESN_RelentlessCapability(1)`, which is present after the accepted runtime proof. Candidates whose personal Action or Bonus-Action pool is already above the normal `1/1` baseline are rejected rather than stacked.

## Status registry

`Status_BOOST.txt` owns:

- `AESN_HP_BIT_00001` through `AESN_HP_BIT_32768`: sixteen hidden, independently stacked `IncreaseMaxHP` statuses. Every bit shares the localized display name `Adaptive Enemy Scaling`, preventing internal status IDs from leaking into the Hit Points breakdown.
- `AESN_HARDENED_FOE_01` through `AESN_HARDENED_FOE_06`: visible tier statuses carrying the approved attack/save/DC and AC boosts. Their compact `Hardened I`–`VI` tooltips lead with thematic prose, then list the tier's static bonuses; the party-dependent HP percentage remains summarized as increased maximum HP rather than showing a misleading fixed value.
- `AESN_RELENTLESS_FOE_01`: additive `ActionPoint(1)`.
- `AESN_RELENTLESS_FOE_02`: additive `ActionPoint(1)` plus `BonusActionPoint(1)`.
- Hidden schema-1 cleanup handles `AESN_TIER_LEVEL_05_08`, `AESN_EXTRA_ACTION_1`, and `AESN_EXTRA_BONUS_ACTION_1`.

Every status has an `AESN_` ID and `AESN_` stack ID. Hardened I–VI use the approved armored-guardian icon family, while Relentless I–VI use the approved aggressive-face icon family. Both families use steel, cyan, and gold intensity bands for tiers I–II, III–IV, and V–VI. Relentless III–VI artwork remains packaged but unused. Hardened and Relentless use hybrid thematic/mechanical tooltips. No status changes damage, reactions, Legendary Actions, class resources, Action Surge-like abilities, or boss-specific resources.

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
8. Enter `HPCommitted`, apply the selected Hardened status, and enter `FullyCommitted`.
9. If the Relentless proof gate is open, allocate from the combat ledger only after checking the foe's personal resource totals.

Maximum HP uses floor rounding. Current HP uses integer round-half-up and is clamped to `[1, targetMaximum]` for a living character. A dead character remains at zero.

Delta zero applies no HP bits but may proceed with Hardened. Negative delta, delta above `65,535`, unsafe arithmetic, non-positive maximum, unexpected maximum, missing acknowledgement, or timeout fails closed for the whole enemy. A partial attempt removes only acknowledged AESN bits, restores the captured percentage, applies no Hardened or Relentless component, and retains a diagnostic record until rollback is confirmed.

An enemy already dead at initial application is skipped.

### Cleanup

1. Capture current and maximum HP.
2. Remove exactly the `DB_AESN_EnemyHpBit` rows recorded for the enemy.
3. Verify the maximum decreased by exactly their recorded sum, preserving unrelated modifiers.
4. Restore the captured percentage once if alive; never set HP on a dead enemy.
5. Remove only the exact recorded Hardened/Relentless status IDs.
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

Relentless recipients and spent counters persist unchanged. A load never refunds budget or selects a replacement recipient.

## Diagnostics

Production emits structured debug-log records for roster decisions, snapshots, policy, hostility, rollback, cleanup, merge mismatch, reload reconciliation, and failure-closed conditions. UI banners and reload-proof notifications are absent. Test commands live only in goals excluded by the default synchronization allowlist.

## Publication boundary

The official Toolkit is installed on `B:`. Repository sources synchronize only to the verified Toolkit `Data` root. Default synchronization copies the ten production goals and removes stale proof/test goals; explicit switches are required to stage test harnesses or the isolated resource proof. Publish Local may write to the live player Mods directory, so package handling and mod-manager activation remain user-operated and must preserve the user's existing load order. No workflow uploads to mod.io.
