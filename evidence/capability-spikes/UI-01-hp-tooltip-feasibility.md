# UI-01: one-line HP attribution feasibility

Date: 2026-09-03. Static investigation only; no deployed change or runtime
proof. User authorized investigating while replaying the unchanged Nere fight.
Balance changes are explicitly deferred, including the earlier lower-HP idea.

## Evidence

- Fresh narrow extracts of the installed Shared.pak and Patch8_HotFix9.pak
  are in ignored `artifacts/tooltip-proof-20260903/`.
- Shared Modifiers.txt SHA-256:
  `812F86A4ECD3C073EFCF31F98FF9D06B5EFEC478E248F27BC6A184FBC846F3D4`.
- Shared ValueLists.txt SHA-256:
  `48EF84E0A377172BDA603D1238CAFCD026B7FBB234F786B87E5C060FB3BE2188`.
  Both match the previously inspected local schema extracts.
- Patch UI `Public/Game/GUI/Override/Clairmont/Library/Tooltips.xaml`,
  StatParamsTemplate at line 5208, renders an ItemsControl over
  CalculationParameters with Value, Description, and SourceName.Str for each
  row. VMStatTooltip routes Health through this template. No grouping/summing
  stage is present in the inspected template. Engine-side collection creation
  is not exposed by this XAML and was not reverse-engineered.
- AES HP-bit statuses already share DisplayName `AESNHpSourceName`, whose
  localization is `Adaptive Enemy Scaling`. User runtime observation still
  shows multiple contributions. A common name alone is therefore insufficient.
- The inspected StatusData schema/StatusPropertyFlags expose no identified
  HP-contribution grouping control. Existing DisableOverhead,
  DisableCombatlog, and DisablePortraitIndicator flags already apply to the
  HP bits. Their presence does not suppress these HP-breakdown rows.
- Native Toolkit Shared Story header lines 1045-1046 declare:
  `AddBoosts(GUIDSTRING, STRING, STRING, GUIDSTRING)` and
  `RemoveBoosts(CHARACTER, STRING, INTEGER, STRING, GUIDSTRING)`.
  The current AES Story log lists both as unreferenced DIV calls. This proves
  the declarations exist, not that the desired runtime behavior works.

## Capability classification

| Claim | Classification | Basis |
| --- | --- | --- |
| Giving all current bits the same display name merges them | Rejected | They already share the name; user observes separate rows |
| An identified native display-only setting aggregates AES rows | Assumption/unsupported | No such setting found; absence is not proof that none can exist |
| Native AddBoosts/RemoveBoosts can be considered for a probe | Documented but unverified locally | Current official Toolkit signatures exist; no local acceptance test for this use |
| One direct flat boost gives one correctly named row and safe persistence/removal | Assumption/unsupported | Not demonstrated in this runtime |

No unverified capability is being used as a production implementation
dependency. No Script Extender dependency or global UI override was added.

## Recommendation and scope boundary

An isolated follow-up probe could compare the existing six pieces totaling
111 HP against one `IncreaseMaxHP(111)` native Story boost. It must not apply
both at once to the same test subject. Independently verify exact maximum HP,
current-HP handling, source label, one-row rendering, save/load persistence,
duplicate prevention, and source-scoped removal preserving another source's
boost. Do not use broad ClearStoryBoosts as cleanup.

Even a successful probe would not authorize replacing production HP ownership:
the current transaction engine relies on status acknowledgements, reconciliation,
and exact removal. Direct-boost ownership and migration of existing saved bits
would require a separately approved design and regression tests. Preserve all
current targets, integer rounding, and third-party HP compatibility semantics.

Do not stage a probe during the current AI baseline. No production source,
Toolkit staging, installed package, load order, or game save was changed here.
The installed AES PAK hash remains
`4ED446243B9E209093CC66EC677D55C2245A0E165449047F292E3F377108CCC3`, matching
the audit baseline. This spike did not produce deployable code.

## Authorized isolated proof preparation

After the user completed a clean fresh-fight and mid-combat-reload comparison
and confirmed the game exited, they authorized preparing the single-boost
proof. This is not approval for a production HP-engine migration.

Added disabled-by-default `AESN_83_HpTooltipProof.txt`; only its staged Toolkit
copy is enabled. The normal production-sync allowlist excludes this goal.
The fixture is a spawned kobold near the host on an out-of-combat save load,
assigned the host's faction and prohibited from fighting/joining combat.
It does not modify party members, Nere, the policy table, or production HP bits.

Sequence:

1. Wait for spawn readiness, capture living fixture baseline, add a single
   flat +111 boost using SourceID `AESN_HP_BIT_00001`, and restore full HP.
2. Verify exact maximum/current HP, then pause indefinitely in Inspect state
   for manual tooltip inspection and a separate disposable save.
3. On reload, verify +111 without reapplication. Add a second identical +111
   expression under SourceID `AESN_HP_BIT_00002` and verify baseline +222.
4. Remove only source 00001 and verify baseline +111 still remains. Remove
   source 00002 and verify baseline maximum/current HP is restored.

Both source IDs resolve to AES's existing shared display label; the initial
inspection has only one contribution. Distinct SourceIDs with identical boost
expressions deliberately test removal isolation. Whether native SourceID
actually produces the desired visible attribution is NOT yet established.
Any observed HP mismatch records a failure and halts further advancement.
There is no broad ClearStoryBoosts cleanup. The harmless fixture remains in
the disposable save after completion; discard that save and return to an
untouched campaign save after restoring production.

This first fixture checks full-health handling only. Wounded-percentage
rounding, save migration from existing HP bits, duplication after unusual
reload timing, combat merges, and production reconciliation remain future
requirements before any real migration. Save only after the Inspect checkpoint,
not midway through the automated setup/cleanup stages.

Seven executable proof-rule tests pass using the existing limited Osiris
subset runner. Native engine queries/results are explicit fixtures, not an
emulation of boost behavior. Initial tests failed before the proof existed;
an additional native-argument check caught and corrected a missing HealTypes
argument to SetHitpointsPercentage. Toolkit compilation remains pending.
An isolated command-line compiler attempt failed module discovery before
parsing; it is not a successful compiler check.

Backups are under `artifacts/tooltip-proof-20260903/pre-stage/`: all 12 prior
staged goals, original Toolkit metadata, and the installed production PAK.
Live manifests before/after staging verify the installed setup is unchanged.
No identity/version metadata was overwritten during staging.

Manual next gate: open Adaptive Enemy Scaling in Toolkit, generate definitions
and build Story. Only after success, Publish Local (never online Publish), load
an out-of-combat disposable/camp save, inspect the spawned kobold's HP tooltip,
and save as `AES single boost proof`. Capture tooltip and save evidence before
reloading that proof save; after reload wait at least five seconds for the
source-isolation/cleanup sequence and save separately for evidence extraction.

### First Toolkit build: orphan observation warning

Screenshot_725 reports BUILD FAILED. The corresponding Toolkit `Story/log.txt`
ends with `0 error(s), 1 warning(s)` and identifies only the never-queried
`DB_AESN_HpTooltipProofObservation` database. The proof now consumes each recorded
observation to validate the matching active, non-failed phase rather than
calling validation separately. No ignore-list entry was added.

The observation-driven advancement regression failed before this change and
passes afterward; wrong-phase and failed-proof guards are covered. All 132
discovery tests pass. The repo and enabled staged proof were patched together;
production goals and HP policy were not changed. Toolkit rebuild and native
runtime/tooltip verification remain pending.

### Retail proof result: single row works, reload retention fails

The user reported the corrected Toolkit build succeeded and ran the local
proof in retail Grymforge. Screenshot_726 shows the spawned kobold at 131/131
with one `+111 from` line; the source name is blank. Screenshot_727 after reload
shows 20/20 without the boost. That final screenshot alone was initially
misinterpreted as cleanup; extracted StorySave facts disprove that interpretation.

Inspected saves (read-only extraction using Divine, StorySave parsed with
LSLib 1.20.4):

- `Lae'zel-13312622811__AES single boost proof/AES single boost proof.lsv`
- `Lae'zel-14312622854__AES single boost cleanup/AES single boost cleanup.lsv`

Fixture: `Kobolds_Melee_Drunk_15ff26e5-7e2b-2bb5-e05c-3e5a1d5f7a07`.
The first save records state `Inspect`, baseline 20, and no failures.
The second records state `Reloading` and failure `Reloading`, NOT `Complete`.

| Recorded phase | Expected HP | Current HP | Maximum HP |
| --- | ---: | ---: | ---: |
| Baseline | 20 | 20 | 20 |
| Applying | 131 | 131 | 131 |
| Reloading | 131 | 20 | 20 |

Verified locally for this exact fixture: spawn, single +111 arithmetic and
single tooltip contribution. Rejected for this exact implementation: boost
retention across save/load and populated source attribution. Source-specific
removal and cleanup were NOT reached and remain unverified. Do not migrate
production HP logic to this implementation. Production balance remains frozen.
Extracted binaries are under ignored `artifacts/tooltip-proof-20260903/inspect`
and `cleanup`. At this checkpoint the local proof package has not been restored
to production; do not continue a normal campaign using the proof package/save.

### Version 2 correction prepared: one status-owned total

User authorized fixing the isolated proof, with production still untouched.
The demonstrated failure is specific to the direct `AddBoosts` route: its
string SourceID did not resolve to a visible status display name, and its
contribution was absent on reload. We have not reverse-engineered the engine's
serialization internals or established that every possible direct-boost call
behaves identically. No AES production goal calls AddBoosts/RemoveBoosts or
ClearStoryBoosts, so the test has no production direct-boost cleanup competing
with its own operation.

Version 2 replaces the direct boost with one real BOOST status containing
`IncreaseMaxHP(111)`, and a second independently stacked reference status with
the same amount. Both use the existing `AESNHpSourceName;1` DisplayName. These
follow the already-used AES HP status mechanism rather than relying on a
SourceID string to create an owned status. The official
[ApplyStatus documentation](https://docs.baldursgate3.game/index.php?title=ApplyStatus)
describes indefinite duration with -1.0 and recommends statuses for buffs;
the local Toolkit header verifies the exact 5-argument ApplyStatus and
3-argument RemoveStatus signatures. Exact version-2 native retention, rendering,
and removal still require the next local acceptance test.

Changes are confined to the proof plus production-staging cleanup protection:

- `proofs/hp-tooltip/Status_AESN_HpTooltipProof.txt` contains the two fixture
  definitions, outside the production `toolkit/Public` copy source.
- The proof records `DB_AESN_HpTooltipProofVersion(2)` on a new run and requires
  it before reload continuation. Old direct-boost proof saves cannot be used
  as a valid v2 run. Start from the original pre-combat save without a kobold.
- Status changes settle before filling this disposable fixture and checking
  HP. Reload validation has neither a heal nor a status reapplication.
- Removal targets exact proof status IDs. No broad removal is used.
- Normal production sync removes the exact separately staged proof stats
  filename as well as excluded proof goals. A temporary-directory integration
  test verifies that production/unrelated stats files are preserved.

Red/green verification: the new status application, legacy-save guard,
delayed-full-HP and production-staging cleanup tests failed against the prior
implementation, then passed. All 136 discovery tests and 8 identity checks pass.
Tests exercise real Story bodies against explicit engine-result fixtures and
resolve their requested stats definitions/localization; they do not certify
native persistence or GUI rendering.

Staging was stopped before any copy because `bg3_dx11` (PID 20712) was still
running. The attempted enabled-gate patch found no match and changed nothing.
No v2 stats file or v2 staging-backup directory was created. The old proof
package and staged v1 goal remain in place pending confirmed full game exit.

After staging/build/local-publish: use the untouched pre-combat save, inspect
one +111 line with its source label, then save separately as
`AES single status proof`. Reload, allow at least ten seconds for the recorded
retention/reference/removal checks, and save separately as
`AES single status cleanup`. For the prior 20-HP baseline, expected recorded
max/current totals are 20, 131, 131, 242, 131, 20. Only extracted `Complete`
state, zero failures, and all observations establish a pass; the final 20/20
screenshot cannot do so alone.

This is a fixed +111 fixture, not a completed dynamic one-status HP engine.
Selecting arbitrary calculated totals, migration of existing bits and wounded
HP handling remain separate design/verification work. Do not infer approval
to replace the production transaction engine from this proof's preparation.

### Version 2 staged after confirmed game exit

After the user confirmed full exit, a process check found neither BG3 nor
Toolkit running. Backed up staged goals, production stats, module metadata,
and the installed v1 proof PAK under
`artifacts/tooltip-proof-20260903/v2-pre-stage/`. Copied only the revised
`AESN_83_HpTooltipProof.txt` and the isolated
`Public/<module>/Stats/Generated/Data/Status_AESN_HpTooltipProof.txt`.
Enabled the proof gate only in the staged goal; repository source stays disabled.

Hash checks verified all 12 production goals, `Status_BOOST.txt`, module
metadata, and installed PAK unchanged from the immediate backup. Staged proof
stats match the repository fixture; the goal differs only by the enabled gate.
The 12 proof tests and 8 identity checks pass again. Toolkit build, local
publish, and retail v2 verification are still pending. No online publication.

### Version 2 retail acceptance: PASS for the fixed +111 fixture

Screenshot_729 shows 131/131 HP with exactly one labelled
`+111 from Adaptive Enemy Scaling` contribution. After the user's save/reload
sequence and full game exit, both saves were extracted read-only and their
StorySave facts parsed with LSLib 1.20.4:

- `Lae'zel-45312622817__AES single status proof/AES single status proof.lsv`
- `Lae'zel-46312622829__AES single status cleanup/AES single status cleanup.lsv`

Fixture: `Kobolds_Melee_Drunk_cc9c3368-8eb3-fadf-b935-e008bbbdb922`.
Both saves record proof version 2 and zero failure facts. The first records
`Inspect`; the second records `Complete`, with all six observations below.

| Phase | Expected | Current | Maximum |
| --- | ---: | ---: | ---: |
| Baseline | 20 | 20 | 20 |
| Applying | 131 | 131 | 131 |
| Reloading | 131 | 131 | 131 |
| Reference | 242 | 242 | 242 |
| OwnRemoved | 131 | 131 | 131 |
| Cleaning | 20 | 20 | 20 |

Verified locally for these exact status definitions: single labelled HP row,
exact flat addition, full-current HP, persistence without reload reapplication,
two independently stacked +111 contributions, exact-status removal preserving
the other contribution, and return to baseline. This does NOT verify direct
AddBoosts persistence, wounded behavior, arbitrary calculated totals, migration,
or production transaction integration. Those remain outside this fixture.

Extracts: ignored `artifacts/tooltip-proof-20260903/v2-inspect` and `v2-cleanup`.
The temporary v2 proof remains staged/installed at this checkpoint. Do not
resume the normal campaign until restoring a production build; retain the
untouched pre-combat save and keep proof saves separate.
