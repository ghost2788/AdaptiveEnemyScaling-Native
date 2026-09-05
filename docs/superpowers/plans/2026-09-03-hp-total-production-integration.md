# Single-Contribution HP Production Integration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace newly applied AES binary HP bonuses with one exact total status and safely convert validated existing ownership, without changing balance.

**Architecture:** Keep the existing transaction tuple and distinguish HP representation1 (legacy bits) from2 (one total). Add a focused total-status backend and a separate durable legacy-conversion journal. Route existing component, cleanup, reconciliation and ownership-transfer paths through explicit supported-representation checks. Qualify intervention/recovery before enabling automatic conversion; no partial implementation is staged for normal play.

**Tech Stack:** BG3 Toolkit Osiris Story, generated BOOST catalog, Python unittest with tests.osiris_subset, user-run Toolkit/retail qualification and read-only LSLib save inspection.

**Spec:** docs/superpowers/specs/2026-09-03-single-contribution-hp.md

## User-approved scope reduction — 2026-09-04

This amendment supersedes automatic representation migration and its remaining
Task3B/Task4 intervention experiments: STOP and defer those tasks. User accepts
existing saved bonuses retaining their old multi-line display. New allocations
use the reviewed exact-total backend; normal policy-driven replans/cleanup retain
their existing semantics. This is per bonus, not a new-game-only save format:
an old campaign can contain both formats as new bonuses are applied.

Proceed with reduced Task5: enable only HpTotalIntegrationEnabled for new planning,
including established-save initialization; keep HpMigrationEnabled absent. No
attempt to migrate existing committed v1 on load, no migration fixture or diagnostic
is staged. Retain v1 definitions/readers and independently reviewed ordinary v2
lifecycles. Dormant47 interfaces may remain because current shared guards reference
them, but no automatic migration can be enabled or called past its disabled gate.
Do not run the stopped prerequisite review or more migration experiments.

Remaining acceptance is proportionate: source tests for old-v1 read-only retention
and new-v2 allocation/reload, safe proof-free staging, Toolkit compile/local package
inspection, and a short retail smoke confirming single-line new allocation and
unchanged legacy retention. This is not release approval until those checks pass.

## Global Constraints

- Preserve the current supported delta range0..65535 and policy schema2; no balance or Relentless changes.
- The current formula remains `floor(externalBase * targetPercent / 100)`; delta is target maximum minus external base.
- Changes in policy continue to use the existing wounded-HP percentage behavior. Merely converting representation must not change either the maximum or current HP, and must not recalculate policy.
- No reapplication or healing-on-load workaround is allowed.
- Cleanup removes only the recorded AES status and preserves unrelated sources.
- No automatic commit, merge, push, online publication, duplicate mod listing or load-order change is included in this design.
- Do not copy stale repo metadata over current Toolkit metadata.
- Normal play must use the restored production package and an untouched campaign save, not a proof save.
- Retain all legacy HP status definitions and supported legacy recovery. Component schema1, policy schema2 and HP representation2 are different concepts; do not replace every literal1.
- Do not copy the test fixture's SelfHealing disable into production. Natural healing, damage, combat entry and death are external interventions, not permission to restore an old HP snapshot.

## Evidence and activation boundary

UI02 qualifies the exact catalog and records the user's acceptance of limited performance measurement. UI03 qualifies two controlled wounded replacements, including legacy/total reload and reference-preserving cleanup. Native observations show why the absolute restore matters: the111 sample goes69/138 ->27/27 ->138/138 ->69/138 during replacement.

These facts do not establish safe intervention detection, interrupted migration recovery, normal NPC self-healing interactions or full production behavior. Wounded visual screenshots remain outstanding; text confirmations and saved observations are not relabeled as screenshots. Collect visual evidence in the integrated native gate before release.

Current installed1.0.0.16 is an isolated proof package. All work below first occurs only in the existing isolated worktree. A closed game/Toolkit is not permission to publish online. Stage only after source review and an exact backed-up manifest; preserve PublishHandle6353123 and UUIDa4567f52-1665-df50-b84c-3992f80fdb90.

## File responsibilities and integration map

| File | Responsibility |
| --- | --- |
| New `story/RawFiles/Goals/AESN_45_HpTotal.txt` | Exact total ID construction, pending/committed ownership, status acknowledgement, bounded timeout and exact removal |
| New `story/RawFiles/Goals/AESN_47_HpMigration.txt` | Validated legacy capture, enemy-scoped hold, sequential journal, intervention handling and recovery |
| `AESN_40_HpTransaction.txt` | Retain policy math; choose representation2 only when the integrated gate enables it |
| `AESN_50_Applications.txt` | Preserve v1 backend; dispatch v2 application/removal and preserve percentage-based policy changes |
| `AESN_55_Components.txt` | Accept valid committed representation1 or2; component schema remains1 |
| `AESN_60_Merge.txt` | Transfer all new ownership/pending/journal records under existing merge barrier without duplicate owners |
| `AESN_65_Reconciliation.txt` | Read-only valid-v2 reload; journal recovery before generic legacy cleanup |
| `AESN_66_WorldHardenedRuntime.txt` | Retain/replan either representation; defer journal-held targets without blocking unrelated world targets |
| `tools/hp_catalog.py` | Reuse exact deterministic catalog unchanged |
| `tools/sync_toolkit_project.ps1` | Production allowlist/catalog delivery and metadata preservation; never invoke on live paths until its tests pass |
| New `tests/hp_story_fixture.py` | Test-only real-rule loading and external-call recording, not an engine simulator |
| New `tests/test_hp_total_story.py`, `tests/test_hp_migration_story.py`, `tests/test_hp_total_integration.py` | Backend, migration and cross-goal regression tests respectively |
| `tools/poc_model.py` and its existing tests | Update representation description only; retain policy outputs and independently calculated expectations |
| New `evidence/capability-spikes/UI-04-hp-production-integration.md` | Source/native receipts, intervention traces, release gates and limitations |

Existing tuples that retain their shapes:

```text
DB_AESN_HpTransaction(Owner,Enemy,Representation,State,BeforeCurrent,ExternalBase,BeforePercentage,TargetMaximum,Delta,AppliedSum)
DB_AESN_HpReplan(Owner,Enemy,1,State,CapturedPercentage)
DB_AESN_HpApplicationHold(Owner,Enemy)
DB_AESN_EnemyHpBit(Owner,Enemy,Bit,Status)
```

New facts and interfaces (Owner GUIDSTRING, Enemy CHARACTER, numeric values INTEGER except percentage REAL, IDs/phases/reasons STRING):

```text
DB_AESN_HpTotalDesired(Owner,Enemy,Delta,Status)
DB_AESN_EnemyHpTotal(Owner,Enemy,Delta,Status)
DB_AESN_HpTotalPending(Owner,Enemy,Operation,Status,Epoch)
DB_AESN_HpTotalEpoch(Enemy,Epoch)
DB_AESN_HpTotalUncertain(Owner,Enemy,Operation,Status,Epoch,Reason)
DB_AESN_HpMigrationHold(Enemy,Owner)
DB_AESN_HpMigration(Owner,Enemy,Phase,CapturedCurrent,CapturedMaximum,ExternalBase,Delta,Status,Epoch)
DB_AESN_HpMigrationBit(Owner,Enemy,Bit,Status,State)
DB_AESN_HpMigrationCheckpoint(Owner,Enemy,Phase,Current,Maximum)
DB_AESN_HpMigrationConflict(Owner,Enemy,Reason)
DB_AESN_HpMigrationDeferred(Owner,Enemy)

QRY_AESN_HpRepresentationSupported(Representation)
PROC_AESN_QueueHpTotal(Owner,Enemy,Delta)
PROC_AESN_BeginHpTotalApply(Owner,Enemy)
PROC_AESN_BeginHpTotalRemove(Owner,Enemy,Mode)
PROC_AESN_ReconcileHpTotal(Owner,Enemy)
PROC_AESN_TryHpMigration(Owner,Enemy)
PROC_AESN_RecoverHpMigration(Owner,Enemy)
PROC_AESN_TransferHpTotalFacts(OldOwner,NewOwner,Enemy)
```

Epochs distinguish timers/intent lifetimes; they do not magically identify native events. An old same-status acknowledgement must not be interpreted as belonging to a new operation. Do not reuse an uncertain status operation until reconciliation resolves it.

## Task 1: Implement an independently tested total-status backend

**Files:** create45, test fixture and test_hp_total_story; leave production planning representation unchanged at this task boundary.

**Interfaces:** consume existing HpTransaction/SetHpState and native status/HP queries; produce the total desired, pending, committed, uncertain facts and backend procedures above. Shared supported-representation query accepts only1 and2.

- [ ] Write failing real-rule tests before implementation. Use explicit native observations and recorded external actions. The test fixture loads actual45 and50 rules and records ApplyStatus, RemoveStatus, SetHitpoints and SetHitpointsPercentage without silently updating native responses.

```python
from pathlib import Path
from tests.osiris_subset import StoryFixture, call, value

GOALS = Path(__file__).resolve().parents[1] / 'story/RawFiles/Goals'
class HpStoryFixture(StoryFixture):
    def action(self, text, env):
        name, tokens = call(text) if not text.startswith('NOT ') else ('', [])
        if name in {'ApplyStatus', 'RemoveStatus', 'SetHitpoints', 'SetHitpointsPercentage'}:
            self.calls.append((name, tuple(value(token, env) for token in tokens)))
        else:
            super().action(text, env)

# Independent boundary values for tests; no zero status and no binary fallback.
cases = [(0, None), (1, 'AESN_HP_TOTAL_1'), (111, 'AESN_HP_TOTAL_111'),
         (32768, 'AESN_HP_TOTAL_32768'), (65535, 'AESN_HP_TOTAL_65535')]
```

- [ ] Run `python -m unittest tests.test_hp_total_story -v`, record missing-behavior RED, then implement positive ID generation with the supported native query:

```text
PROC
PROC_AESN_QueueHpTotal((GUIDSTRING)_Owner, (CHARACTER)_Enemy, (INTEGER)_Delta)
AND
_Delta > 0
AND
_Delta <= 65535
AND
ConcatenateInteger("AESN_HP_TOTAL_", _Delta, _Status)
THEN
DB_AESN_HpTotalDesired(_Owner, _Enemy, _Delta, _Status);
```

- [ ] Add guarded apply/removal state machines. Store intent before native call, validate unique owner, version/state, exact desired ID and live presence, wait for matching acknowledgement, verify maximum before commit. A preexisting unowned same-ID status is a conflict, not adoptable ownership. Preserve pending identity on timeout in Uncertain rather than forget it. Zero requires no status; ordinary zero must not write HP.
- [ ] For ordinary policy application retain the existing percentage restore after maximum verification. For representation conversion do not use this percentage path: Task3 owns exact restoration. Removal accepts only recorded total ownership or its unresolved intent; preserve other totals/statuses, including reference7.
- [ ] Add cases for missing/failed/duplicate/delayed acknowledgement, timeout then late application, wrong maximum, zero current/death, existing unowned total, replayed timer, unknown version and foreign event. Literal example: external20 +111 =>131; observed130 must not commit. Ack alone is insufficient.
- [ ] Run focused tests GREEN and full169-test baseline plus added tests. No live stage or normal-planner activation.

## Task 2: Integrate both representations into ordinary lifecycles

**Files:** modify40/50/55/60/65/66 and model; create test_hp_total_integration. No policy/tier/Relentless allocation edits.

**Interfaces:** consume Task1 API; new backend becomes selectable in isolated tests. Existing HpReplan and ComponentApplication versions stay1. Migration APIs are not invoked until Task3 exists.

- [ ] Add real multi-goal tests for new and legacy transactions under combat and world owners. Assert policy outputs are unchanged for parties1..4 and existing large-party cases. Hand-check base101 at210percent => target212,delta111, not213. Exercise source planner, not just model output.
- [ ] Replace version1-only committed consumers with a supported-representation binding where behavior is representation-independent. Dispatch representation-specific operations explicitly; do not let old bit apply/remove handlers run for2.

```text
DB_AESN_HpTransaction(_Owner,_Enemy,_Representation,"HPCommitted",_,_,_,_,_Delta,_Delta)
AND
QRY_AESN_HpRepresentationSupported(_Representation)
```

- [ ] Wire new planning and replanning to representation2 behind one documented integration activation fact that remains absent from staged/live production until Task5. Keep representation1 readers and exact cleanup. Populate all desired data before queuing application.
- [ ] Transfer Desired/Owned/Pending/Epoch-associated ownership/Uncertain records using PROC_AESN_TransferHpTotalFacts while existing merge barrier is active. Preserve one enemy owner; reject a destination with conflicting ownership. Preserve native timer identity or cancel/rearm through the same saved epoch; do not replay application on transfer.
- [ ] Extend normal cleanup/replan dispatcher and record deletion for exact v2 removal. The old percentage capture and final restore semantics remain unchanged, including replanning from nonzero tozero. Never delete unresolved ownership merely because a timer failed.
- [ ] Reconcile fully committed v2 saves by observation only: known ID matches delta, exact owned status exists, max equals stored target, no journal/uncertain/pending work. Releasing a hold must not reapply status, recalculate policy, rewrite currentHP or regrant Relentless.
- [ ] Test world readiness, sticky out-of-range retention, policy changes, external HP source changes, combat joins/merges, cleanup and repeated committed reload. Compare Relentless ledger before/after representation-only events. Add mixed1/2 owner transfer test with one surviving owner and no duplicate ApplyStatus calls.
- [ ] Run all source, identity and model tests; independently review this cross-goal diff before migration work.

## Task 3: Implement a durable, fail-closed legacy migration journal

Execution checkpoint (controller ruling during implementation): split this task
into3A (trace-ready validation/journal/deferral/metadata recovery, no HP restoration)
and3B (remaining exact restoration/rollback and its tests). Run Task4A's native
causality trace between them. The current native HP-change event has no cause ID;
pending status intent does not prove that an HP change is AES-owned. Do not build
a caller-attested qualification token or guess a classifier to make source tests
pass.3A may advance through independently observed status checkpoints in an
opted-in disposable proof, but must stop at unclassified HP changes and must not
restore HP or commit a partially converted transaction as validv2. If it reaches
TotalPresent, exact restoration remains explicitly NativeCausalityUnqualified.
Automatic migration staysOFF. All original3B/4/5 acceptance requirements below
remain outstanding;3A review is not full Task3 completion.

**Files:** create47 and test_hp_migration_story; modify40/50/60/65/66 only for holds/routing/deferred retries.

Scope correction: narrowly guard55's direct component cleanup/replan entry against
persisted migration holds too; transaction state alone cannot protect these paths.
65's generic application holds must exclude journal-held records so an uncertain
world conversion does not enter66's global refresh barrier. These guards use
persisted facts, not assumptions about order among independent SavegameLoaded rules.

**Interfaces:** consume exact legacy registry, Task1 status backend and Task2 owner transfer; produce Migration/Hold/Bit/Checkpoint/Conflict/Deferred facts. One journal per enemy; owner may transfer only under the merge barrier.

- [ ] Write failing tests with literal captured states and native checkpoints from UI03. Preserve original policy, components and Relentless facts throughout. Seed legacy bit rows, not inferred HP differences.

```python
# Each sequence lists explicit observed (current,max), not simulated effects.
replacement_cases = [
    (1, (13,28), (13,27), (14,28), (13,28)),
    (111, (69,138), (27,27), (138,138), (69,138)),
]
# Adversarial supplied responses must reject stale restoration.
conflicts = ['CombatEntered', 'DamageObserved', 'Dying', 'ExternalMaximumChanged',
             'UncertainNativeEvent', 'MissingOwnedBit', 'DuplicateOwner']
```

- [ ] Validate fully committed v1, exact recorded bit IDs/values against16-entry registry, sum==Delta==AppliedSum, live target maximum, living positive currentHP, and stable supported policy/component ownership. Defer combat/replan/cleanup/merge. Capture current live HP rather than old entry-time BeforeCurrent. For delta0 validate no owned bits and convert only metadata with no HP/status write.
- [ ] Acquire enemy-scoped hold before mutations and move v1 transaction into a migration state ordinary handlers cannot process. Freeze exact legacy set and target; record Captured checkpoint. Do not use a global world barrier that blocks every unrelated target if one conversion cannot recover.
- [ ] Advance sequentially through Captured -> RemovingLegacy -> LegacyRemoved -> ApplyingTotal -> TotalPresent -> RestoringCurrent -> Verified -> committed representation2. Store per-bit pending/acknowledged state before/after exact removal; status intents before native calls. Record observed HP/max after each acknowledged step. Require original maximum before exact captured-current restore and verify both values afterward. Commit ownership last, then release hold without triggering reapplication.
- [ ] Invalidate restoration on combat entry, Dying/Died, positive AttackedBy damage, unexpected maximum/status ownership or unclassifiable HP change. Current header confirms these event signatures; it does not establish delivery ordering or universal damage coverage. Do not treat every HitpointsChanged as external (own boosts trigger it), or assume every change while a request is pending belongs to AES.
- [ ] Add an explicit event-trace qualification surface for Task4. Until native own-vs-external ordering is qualified, leave automatic migration activation OFF. A source-only fake must not certify that distinction. If native evidence cannot support safe classification, block automatic conversion and revisit the design rather than accept stale healing.
- [ ] Save/load recovery runs before generic legacy cleanup. Captured+exact untouched legacy can safely retain legacy and release the conversion hold. A verified TotalPresent/current checkpoint can advance only after matching exact ownership and fresh native guards. A pending native request with ambiguous before/after state stays Conflict-held with its original intent retained; it must not reapply or write HP. Verified exact-current states may commit metadata without a second setter call. Safely validated rollback restores only the frozen legacy set, verifies original max/current, then retires the journal; otherwise remain visibly blocked.
- [ ] Test reload snapshots at every phase, duplicate events, late events after timeout, death/damage/combat between phases and owner transfer during a deferred migration. Test that held targets cannot be replanned/cleaned by ordinary paths and unrelated world targets still progress. A conflict cannot silently lose journal/status ownership.
- [ ] Test deferred retry from LeftCombat and tracked-world maintenance without requiring rediscovery range. Recheck live state before acquiring hold; do not convert stale inactive combat ownership that should undergo ordinary cleanup instead.
- [ ] Run focused and full tests and independent review. Do not enable production automatic migration on source tests alone.

## Task 4: Qualify interventions and interrupted recovery natively

Task4A is the earlier native event-trace checkpoint after3A, before implementing
the restoration classifier. Exercise actual45/47 request/checkpoint guards and
record own changes plus external damage/healing/combat/death. Do not bypass journal
guards to claim a successful full conversion. Use its evidence to decide whether
3B is supportable or the design needs revision; the remaining full Task4 scenarios
and visual acceptance still follow3B. This reordering does not authorize automatic
conversion or waive the final retail gate.

**Files:** create disabled `proofs/hp-total-integration/AESN_84_HpIntegrationProof.txt`, its real-rule tests, and UI04; use ignored artifacts/hp-integration/ for traces/backups.

**Interfaces:** exercise actual45/47 production procedures, not a separate replacement implementation. Test callbacks may pause journal phases but may not bypass production eligibility/restoration guards.

- [ ] Write failing fixture tests showing disabled-by-default behavior, no mutation of host/normal NPCs and exact pause/continue controls. Use existing two disposable templates/sample values; do not make the user find naturally occurring kobolds.
- [ ] Record native event sequence, requested status, pending epoch, journal phase, HP/max before/after, conflict reason and one-shot setter count. Test one self-healing-disabled disposable control and one with normal healing unchanged. Include non-attack HP changes and damage-triggered combat. The purpose is safe cancellation/non-restoration under intervention, not stopping the game from healing normally.
- [ ] Native scenarios: clean1/111 replacement; external damage before and during pending application; normal healing before restoration; combat entry; death; external reference HP addition/removal; save/reload before and after each removal/application/restoration checkpoint; failed and delayed status request; repeated valid-v2 reload; mixed-owner transfer. A no-intervention sample must converge with exact current/max; an intervention must never restore the old snapshot over it.
- [ ] Back up/manifest exact live inputs, verify closure, stage only reviewed production+one opted-in proof, preserve meta/UUID/handle. User builds and publishes locally. Inspect resulting package before retail load. Ask one native action at a time and inspect named saves read-only.
- [ ] Collect screenshots of named single-line HP contribution and wounded values alongside saved phase facts. Record missing/failed observations honestly. Native ordering or recovery failure blocks automatic migration activation; do not waive it because the simpler UI03 primitive passed.

## Task 5: Assemble and test the proof-free production candidate

**Files:** sync_toolkit_project, tests/test_sync_toolkit_project, tests/validate_identities, UI04 and integration activation in40/47; no stale-meta overwrite.

**Interfaces:** consumes accepted reviewed backend/journal and native intervention gate. Produces an explicit production manifest including45/47 and exact generated catalog, excluding every proof goal and temporary proof-only status.

- [ ] Write staging tests using temporary fake Data roots. Assert current metadata survives unchanged, original production files and catalog delivered, all known proof goals excluded, unrelated files preserved, generated catalog hash validated and no installed retail PAK modified by staging. A source tree carrying old metadata must not overwrite a newer destination.
- [ ] Add45/47 to production allowlist and deterministic catalog generation/validation. Keep legacy bits and named localization. Remove only inventoried known proof outputs after backup, not broad globbed directories. Fix staging code/tests before using it live.
- [ ] Turn on production representation2 and automatic conversion only after Task4 records acceptance. Validate no source SelfHealing disable or fixture spawn logic is in the production manifest. Do not copy new probe controls into production.
- [ ] Run `python -m unittest discover -s tests`, `python tests/validate_identities.py`, and catalog check; independent whole-integration review, then closed-process backup and exact staging. User Build Story/Publish Local. Inspect actual PAK for reviewed files, original identity, absence of proofs and accepted catalog.
- [ ] Retail smoke on disposable copies of untouched pre-Nere and existing midcombat saves: new total allocation; legacy combat conversion deferred; stable world conversion without balance change; party/level replan; Nere priority and unchanged recipient budget; late hostile entrant; save/load retention; normal AI turns. Capture HP tooltip screenshots and parse ownership/journal facts. Failures remain local; never publish online as part of this plan.
- [ ] Restore the supported production build if a candidate gate fails and user needs normal play; do not leave a proof build represented as a finished patch. Publish/merge/commit require a separate user request.

## Self-review and execution boundaries

Spec coverage: catalog reuse Task1/5; unchanged policy Task2; exact ownership/zero/late status Task1; world/combat transfer/replan/reload Task2; validated legacy/defer/journal/rollback Task3; intervention and interrupted recovery Task4; visual evidence/proof-free candidate/retail gates Task4/5. No production-safety gate is waived by this plan.

Type consistency: Owner is GUIDSTRING even for world context; Enemy is CHARACTER; events bind GUIDSTRING then cast as current native header requires. Component/Replan schema1 remains distinct from HP representation2. Procedure names above are the cross-task contract.

Current capability boundary: native ordering/coverage for intervention detection is intentionally a test gate, not a claimed capability. If that test rejects the design, do not ship partial unsafe migration. All backend work before that gate is isolated and testable without automatic live conversion.

Execution recommendation: continue the existing subagent-driven workflow in the same isolated worktree, one implementer at a time, independent scoped reviews, no commits. Controller keeps stage/native gates with the user. This plan is ready for execution choice; no production executable changes were made while writing it.
