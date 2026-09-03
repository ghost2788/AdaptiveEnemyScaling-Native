# Precombat Hardened Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply real, dynamically refreshed Hardened mechanics to nearby active hostile enemies before combat while leaving Relentless combat-scoped.

**Architecture:** Reuse the acknowledged schema-2 HP/component transaction engine under one durable world-context GUID. A new world lifecycle goal owns roster refresh, three-second discovery-only proximity/visibility/hostility scans, failure cleanup, and replan requests; combat recognizes a committed world transaction as Hardened-ready without taking ownership or double-applying HP.

**Tech Stack:** BG3 Osiris Story, BG3 Toolkit, Python 3 `unittest`, PowerShell synchronization scripts

**Spec:** `docs/superpowers/specs/2026-09-03-precombat-hardened.md`

## Global Constraints

- Preserve the six released Hardened tiers, HP percentages, stat bonuses, and Relentless budgets exactly.
- Preserve exact acknowledged HP-bit application/removal and percentage restoration.
- Do not require Script Extender.
- Do not write to the live player Mods directory.
- Do not copy Tactician Enhanced source, identifiers, localization, assets, UUIDs, or database/status names.
- Treat the world owner GUID `da8f9f22-2125-45f1-ac0f-a8c264596f04` only as an AES-owned database key.
- Do not publish or replace the released package until the runtime proof gate passes.

---

### Task 1: Model exact world refresh behavior

**Files:**
- Modify: `tests/test_poc_model.py`
- Modify: `tools/poc_model.py`

**Interfaces:**
- Consumes: existing `Policy`, `target_maximum`, `decompose_delta`, and `restore_current` functions.
- Produces: `HardenedRefreshPlan`, `plan_hardened_refresh(...)`, `WorldHardenedDecision`, and `decide_world_hardened(...)`.

- [ ] **Step 1: Write failing arithmetic and lifecycle tests**

```python
def test_world_refresh_subtracts_owned_bits_before_reapplying_policy(self):
    policy = model.build_policy([5, 5, 5, 5])
    plan = model.plan_hardened_refresh(88, 175, 25, policy, alive=True)
    self.assertEqual(plan.external_base, 150)
    self.assertEqual(plan.target_maximum, 315)
    self.assertEqual(plan.delta, 165)
    self.assertEqual(sum(plan.bits), 165)
    self.assertEqual(plan.restored_current, 158)

def test_world_lifecycle_uses_visibility_only_for_discovery(self):
    visible = model.decide_world_hardened(
        tracked=False, committed=False, in_combat=False, alive=True,
        active=True, on_stage=True, invisible=False,
        hostile=True,
    )
    hidden = model.decide_world_hardened(
        tracked=True, committed=True, in_combat=False, alive=True,
        active=True, on_stage=True, invisible=True,
        hostile=True,
    )
    fighting = model.decide_world_hardened(
        tracked=True, committed=True, in_combat=True, alive=True,
        active=True, on_stage=True, invisible=False,
        hostile=True,
    )
    self.assertEqual(visible.action, "apply")
    self.assertEqual(hidden.action, "retain")
    self.assertEqual(fighting.action, "defer")
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `python -m unittest tests.test_poc_model.PocModelTests.test_world_refresh_subtracts_owned_bits_before_reapplying_policy tests.test_poc_model.PocModelTests.test_world_lifecycle_defers_active_combat_and_cleans_lost_visibility -v`

Expected: errors because the new interfaces do not exist.

- [ ] **Step 3: Implement the minimal pure model**

```python
@dataclass(frozen=True)
class HardenedRefreshPlan:
    external_base: int
    target_maximum: int
    delta: int
    bits: tuple[int, ...]
    restored_current: int

def plan_hardened_refresh(observed_current, observed_maximum, owned_applied_sum, policy, *, alive):
    external_base = observed_maximum - owned_applied_sum
    target = target_maximum(external_base, policy)
    delta = target - external_base
    return HardenedRefreshPlan(
        external_base, target, delta, tuple(decompose_delta(delta)),
        restore_current(observed_current, observed_maximum, target, alive=alive),
    )
```

Implement `decide_world_hardened` with this precedence: active combat => `defer`; any fully committed tracked world package => `retain`; any tracked pending transaction => `wait`; eligible untracked => `apply`; otherwise => `ignore`.

- [ ] **Step 4: Run the focused tests and verify GREEN**

Run the Step 2 command. Expected: both tests pass.

- [ ] **Step 5: Run all model tests**

Run: `python -m unittest tests.test_poc_model -v`

Expected: all model tests pass.

### Task 2: Add the world policy and discovery lifecycle

**Files:**
- Create: `story/RawFiles/Goals/AESN_25_WorldHardened.txt`
- Create: `story/RawFiles/Goals/AESN_66_WorldHardenedRuntime.txt`
- Create: `tests/test_world_hardened_contracts.py`
- Modify: `tools/sync_toolkit_project.ps1`
- Modify: `tests/test_sync_toolkit_project.py`

**Interfaces:**
- Consumes: `PROC_AESN_BuildRoster`, `PROC_AESN_DeleteCombatOwnedFacts`, `PROC_AESN_ConsiderEnemy`, `PROC_AESN_CleanupEnemy`, `PROC_AESN_ReplanEnemy`, and schema-2 snapshot tables.
- Produces: `DB_AESN_WorldContext`, `DB_AESN_WorldTracked`, `DB_AESN_WorldHardenedReady`, `DB_AESN_WorldReplanDeferred`, `PROC_AESN_RequestWorldPolicyRefresh`, and `PROC_AESN_RequestWorldScan`.

- [ ] **Step 1: Write failing source-contract tests**

The tests must require:

```python
self.assertIn('DB_AESN_WorldContext((GUIDSTRING)AESN_WorldHardenedOwner_da8f9f22-2125-45f1-ac0f-a8c264596f04);', world)
self.assertIn('IterateCharactersAround((GUIDSTRING)_Member, 100.0, "AESN_WORLD_CANDIDATE", "AESN_WORLD_SCAN_COMPLETE")', world)
for gate in ('IsDead(_Enemy, 0)', 'IsActive(_Enemy, 1)', 'IsOnStage(_Enemy, 1)', 'IsInvisible(_Enemy, 0)', 'IsEnemy(_Enemy, _Member, 1)'):
    self.assertIn(gate, world)
self.assertNotIn('AESN_RELENTLESS_FOE_', world)
```

Also require the production synchronization allowlist to include both world-Hardened goals. Goal 25 declares the shared world database schema; goal 66 contains runtime rules after all referenced core databases have been declared.

- [ ] **Step 2: Run the new contract tests and verify RED**

Run: `python -m unittest tests.test_world_hardened_contracts tests.test_sync_toolkit_project -v`

Expected: failure because the goal and allowlist entry do not exist.

- [ ] **Step 3: Implement world initialization, roster refresh, and scan cadence**

Create the durable owner fact in both `INITSECTION` and `SavegameLoaded`. Debounce refresh requests from gameplay start/load and permanent roster level/membership events. Delete only the world owner's old policy/roster facts, rebuild through `PROC_AESN_BuildRoster`, then populate `DB_AESN_CombatParticipant` from its eligible snapshot members.

Run one scan at a time. Iterate 100 metres around every `DB_AESN_SnapshotMember` of the world owner, collect `EntityEvent` candidates, count completion events, and finalize on all completions or a three-second timeout. Relaunch the normal scan timer for three seconds after finalization.

- [ ] **Step 4: Implement eligibility, exact cleanup, and deferred replan rules**

Gate new world candidates by living/active/on-stage/not-invisible/hostility/out-of-combat conditions without NPC-perception or line-of-sight checks. Mark tracked candidates before calling `PROC_AESN_ConsiderEnemy`. On scan completion, record a scan miss for a tracked unseen enemy without removing its committed world package. Queue `DB_AESN_MergeReplanRequired(_World, _Enemy)` for policy or observed-maximum mismatch only outside combat; store `DB_AESN_WorldReplanDeferred` otherwise and release it on `LeftCombat`.

- [ ] **Step 5: Add the production goal to synchronization**

Insert `'AESN_25_WorldHardened.txt'` between policy and combat and `'AESN_66_WorldHardenedRuntime.txt'` after reconciliation in `$productionGoalNames`.

- [ ] **Step 6: Run contracts and full unit suite**

Run: `python -m unittest tests.test_world_hardened_contracts tests.test_sync_toolkit_project -v`

Run: `python -m unittest discover -s tests -v`

Expected: all tests pass.

### Task 3: Hand off Hardened readiness without double application

**Files:**
- Modify: `story/RawFiles/Goals/AESN_40_HpTransaction.txt`
- Modify: `story/RawFiles/Goals/AESN_56_Relentless.txt`
- Modify: `story/RawFiles/Goals/AESN_60_Merge.txt`
- Modify: `tests/test_world_hardened_contracts.py`

**Interfaces:**
- Consumes: `DB_AESN_WorldTracked`, `DB_AESN_WorldHardenedReady`, combat eligibility, and existing component acknowledgement state.
- Produces: `DB_AESN_CombatHardenedReady(combat, enemy)` as the sole Relentless prerequisite.

- [ ] **Step 1: Write failing combat-handoff tests**

Require the combat HP planner to contain `NOT DB_AESN_WorldTracked(_Enemy)`. Require rules that materialize `DB_AESN_CombatHardenedReady` from either a combat `FullyCommitted` component application or `DB_AESN_WorldHardenedReady`. Require Relentless allocation to depend on `DB_AESN_CombatHardenedReady` and reject direct dependence on `DB_AESN_ComponentApplication(..., "FullyCommitted")` in its candidate rule.

- [ ] **Step 2: Run the focused test and verify RED**

Run: `python -m unittest tests.test_world_hardened_contracts.WorldHardenedContracts.test_combat_handoff_uses_one_hardened_owner -v`

Expected: failure because combat readiness is not yet materialized.

- [ ] **Step 3: Implement the handoff and Relentless gate**

Add `NOT DB_AESN_WorldTracked(_Enemy)` to combat-owned planning. In `AESN_56_Relentless.txt`, declare and populate `DB_AESN_CombatHardenedReady` from both supported ownership paths, and use it in `PROC_AESN_ConsiderRelentlessCandidate`.

- [ ] **Step 4: Extend merge and cleanup bookkeeping**

Migrate `DB_AESN_CombatHardenedReady` from discarded to surviving combat. Delete it in `PROC_AESN_DeleteCombatOwnedFacts`. Extend combat cleanup dispatch to call `PROC_AESN_CleanupEnemy` for a combat-owned `Relentless` component even when that combat owns no HP transaction.

- [ ] **Step 5: Run focused and full tests**

Run the Step 2 command, then `python -m unittest discover -s tests -v`.

Expected: all tests pass.

### Task 4: Retain valid world transactions across save/load

**Files:**
- Modify: `story/RawFiles/Goals/AESN_65_Reconciliation.txt`
- Modify: `tests/test_world_hardened_contracts.py`

**Interfaces:**
- Consumes: existing delayed reconciliation and identity checks.
- Produces: reconciliation mode `2` for the durable world owner and reconstituted `DB_AESN_WorldHardenedReady` on a valid retained commit.

- [ ] **Step 1: Write failing reconciliation tests**

Require `PROC_AESN_OpenCombatReconciliation` to branch on `DB_AESN_WorldContext(_Combat)` without calling `CombatIsActive` for that owner. Require a valid world mode-2 commit to record `RETAIN`, remove `DB_AESN_HpApplicationHold`, and restore `DB_AESN_WorldHardenedReady`. Require invalid world identity to enter exact cleanup rather than be trusted.

- [ ] **Step 2: Run the focused test and verify RED**

Run: `python -m unittest tests.test_world_hardened_contracts.WorldHardenedContracts.test_save_load_retains_only_valid_world_commit -v`

Expected: failure because the reconciler currently classifies every non-combat owner as stale.

- [ ] **Step 3: Implement world reconciliation mode**

Split the reconciliation opener into combat and world-owner rules. Preserve all existing version, maximum, bit, and component identity checks. Add the valid mode-2 retain transition and route any mode-2 failure through `PROC_AESN_CleanupEnemy`.

- [ ] **Step 4: Run focused and full tests**

Run the Step 2 command, then `python -m unittest discover -s tests -v`.

Expected: all tests pass.

### Task 5: Document, synchronize, compile, and stage runtime proof

**Files:**
- Modify: `DESIGN.md`
- Modify: `TEST-PLAN.md`
- Modify: `CAPABILITY-PROOF.md`
- Modify: `README.md`
- Create: `story/RawFiles/Goals/AESN_84_WorldHardenedHarness.txt`
- Modify: `tests/test_world_hardened_contracts.py`

**Interfaces:**
- Consumes: complete world lifecycle and existing safe Toolkit synchronization.
- Produces: a disabled-by-default isolated acceptance harness and an evidence checklist for release.

- [ ] **Step 1: Write failing documentation and harness contracts**

Require the docs to distinguish world-owned Hardened from combat-owned Relentless, state the 100-metre/3-second discovery-only visible-hostile scope, describe no-compounding external HP replans, and label runtime status as unverified until tested. Require the harness gate to be disabled in source and excluded from production synchronization.

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `python -m unittest tests.test_world_hardened_contracts -v`

Expected: documentation/harness contract failures.

- [ ] **Step 3: Add the disabled acceptance harness and documentation**

The harness must log machine-checkable checkpoints for: precombat commit, no second combat HP owner, Relentless combat allocation, post-combat world retention, policy replan, external maximum mismatch replan, sticky retention after a scan miss, and save/load retain. It must not fabricate production eligibility facts or ship enabled.

- [ ] **Step 4: Run all local tests**

Run: `python -m unittest discover -s tests -v`

Expected: all tests pass.

- [ ] **Step 5: Synchronize to the verified Toolkit Data root**

Run: `powershell -NoProfile -ExecutionPolicy Bypass -File tools/sync_toolkit_project.ps1 -ToolkitDataRoot 'B:\SteamLibrary\steamapps\common\Baldurs Gate 3\Data' -IncludeTestHarnesses`

Expected: synchronization succeeds and the script refuses no safety gate.

- [ ] **Step 6: Compile Story in the Toolkit**

Open `AdaptiveEnemyScalingNativePOC`, build Story, and require zero Osiris compile errors. If the compiler rejects any new signature or owner key, classify that capability as rejected and stop dependent work.

- [ ] **Step 7: Run the isolated in-game acceptance matrix**

Verify each harness checkpoint and manually inspect precombat HP attribution, Hardened tooltip/icon, no duplicate HP at initiative, Relentless removal, Hardened retention, party-level refresh, external HP-mod refresh, hidden/offstage non-disclosure before discovery, sticky retention after leaving range, and save/load retention.

- [ ] **Step 8: Preserve production safety**

After proof, synchronize production without `-IncludeTestHarnesses`, rebuild locally, and compare the live-player-directory manifest before any package replacement or publication.
