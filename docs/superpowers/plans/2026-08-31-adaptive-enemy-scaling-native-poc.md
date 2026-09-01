# Adaptive Enemy Scaling Native POC Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and Publish Local an isolated native Baldur's Gate 3 Toolkit proof of concept that deterministically and reversibly scales eligible hostile enemies from a `DB_PartyMembers` snapshot, then stop before installation or upload.

**Architecture:** A versioned Osiris state machine owns combat snapshots, hostile-member evidence, per-enemy transactions, merge aliases, and reload reconciliation. Sixteen independently stacked `AESN_HP_BIT_*` statuses encode an exact positive flat-HP delta; separate fork-owned statuses implement one stat tier and explicitly additive Action and Bonus Action probes. Python's standard library supplies a deterministic policy/state oracle and source/package validators; the official Toolkit compiles Story/Stats and produces the local package.

**Tech Stack:** Baldur's Gate 3 Toolkit, Osiris Story, BG3 Stats `StatusData`, Python 3 standard library `unittest`, PowerShell 7/Windows PowerShell, LSLib Divine for read-only package inspection.

**Spec:** `DESIGN.md`

## Global Constraints

- Native implementation is the primary path; `B:\UserData\Tom\BG3ModAnalysis\AdaptiveEnemyScaling-PartyLevel` remains untouched as the Script Extender fallback.
- Module name is `AdaptiveEnemyScalingNativePOC`; Toolkit-generated and user-approved module UUID is `a4567f52-1665-df50-b84c-3992f80fdb90`; internal POC milestone is `0.1.0`; Toolkit module version is `1.0.0.0` with expected first-publish version `1.0.0.1`.
- Every owned status and stack ID begins `AESN_`; every owned Osiris database begins `DB_AESN_`.
- `DB_PartyMembers` is the only eligible-roster candidate database. `DB_PartOfTheTeam` is diagnostic only and may occur in production source only in `AESN_90_Diagnostics.txt`.
- Enemy eligibility requires hostility to at least one snapshotted eligible member participating in the same combat.
- HP mutation records and removes exact fork-owned binary statuses and preserves current percentage once per successful transaction.
- Maximum positive HP delta is `65,535`; negative, overflow, dead-at-entry, and unverified transactions fail closed.
- Version `0.1.0` Action and Bonus Action scaling is additive only; it does not normalize totals or touch other action resources.
- Optional spell injection and the complete production balance table are excluded.
- Tactician Enhanced is feasibility evidence only. Do not reuse its code, resource definitions, localization, UUIDs, database names, statuses, stack IDs, or other authored content.
- Credit Simple Enemy Scaling by trashcanhvnds as distribution labeled `1.4.1.2`, distribution SHA-256 `16B34DE94FDBD3704F8D3053A29CE00E9423DA774D8F2779B907455A68126B96`, package SHA-256 `3D5F28550D9633321E68531E069510A75965C633F461825EA791BC30153F41D9`.
- Install the official Toolkit to the `B:` Steam library. Before a separate approval, do not write the live Mods directory, change `modsettings.lsx`, install/activate the POC, or upload it.
- CAP-02 proved that this Toolkit build writes Publish Local output into the live player Mods directory. The exact probe package was moved to ignored `B:` storage and live state was restored. The user subsequently approved a narrow exception: future Publish Local runs may transiently stage only this POC package, which must be moved to `B:` before any game launch and followed by an exact live-manifest comparison; activation, `modsettings.lsx` edits, and uploads remain forbidden.
- A capability classified below **Verified locally** receives an isolated spike before dependent implementation. A rejected mandatory spike stops the native path.

---

### Task 1: Repository Safety Harness and Contract Tests

**Files:**
- Create: `build/module-identity.json`
- Create: `tests/test_document_contracts.py`
- Create: `tests/verify_live_directories_unchanged.ps1`
- Create: `tools/capture_live_manifest.ps1`
- Modify: `.gitignore`
- Test: `tests/test_document_contracts.py`

**Interfaces:**
- Consumes: approved identity and immutable boundaries from `DESIGN.md` and `UPSTREAM.md`.
- Produces: `build/module-identity.json`; `artifacts/safety/pre-build.json`; command `verify_live_directories_unchanged.ps1 -Before artifacts\safety\pre-build.json -After artifacts\safety\post-publish.json`.

- [ ] **Step 1: Write the failing document contract test**

Create `tests/test_document_contracts.py` with tests that load the repository root, require the exact module UUID in `README.md`, `DESIGN.md`, and `build/module-identity.json`, require both upstream hashes in `UPSTREAM.md`, require the no-live-write boundary in `README.md`, and reject `ScriptExtender` anywhere outside documentation fixtures.

```python
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_UUID = "a4567f52-1665-df50-b84c-3992f80fdb90"

class DocumentContracts(unittest.TestCase):
    def test_identity_is_consistent(self):
        identity = json.loads((ROOT / "build/module-identity.json").read_text())
        self.assertEqual(identity["moduleUuid"], MODULE_UUID)
        for name in ("README.md", "DESIGN.md"):
            self.assertIn(MODULE_UUID, (ROOT / name).read_text(encoding="utf-8"))

    def test_upstream_hashes_are_exact(self):
        text = (ROOT / "UPSTREAM.md").read_text(encoding="utf-8")
        self.assertIn("16B34DE94FDBD3704F8D3053A29CE00E9423DA774D8F2779B907455A68126B96", text)
        self.assertIn("3D5F28550D9633321E68531E069510A75965C633F461825EA791BC30153F41D9", text)

    def test_no_script_extender_tree(self):
        offenders = [p for p in ROOT.rglob("*") if p.is_dir() and p.name == "ScriptExtender"]
        self.assertEqual(offenders, [])

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the contract test and observe the missing identity failure**

Run: `python -m unittest tests.test_document_contracts -v`

Expected: FAIL because `build/module-identity.json` does not exist.

- [ ] **Step 3: Add the exact identity record**

Create `build/module-identity.json`:

```json
{
  "moduleName": "AdaptiveEnemyScalingNativePOC",
  "moduleFolder": "AdaptiveEnemyScalingNativePOC_a4567f52-1665-df50-b84c-3992f80fdb90",
  "moduleUuid": "a4567f52-1665-df50-b84c-3992f80fdb90",
  "version": "0.1.0",
  "schemaVersion": 1,
  "statusPrefix": "AESN_",
  "databasePrefix": "DB_AESN_"
}
```

- [ ] **Step 4: Implement live-state manifest capture and comparison**

`tools/capture_live_manifest.ps1` accepts `-OutputPath`. It hashes `C:\Users\Tom Girard\AppData\Local\Larian Studios\Baldur's Gate 3\PlayerProfiles\Public\modsettings.lsx` when present and records relative path, length, last-write UTC, and SHA-256 for every file under the live Mods directory. It serializes a stable, path-sorted JSON document.

`tests/verify_live_directories_unchanged.ps1` accepts `-Before` and `-After`, compares the parsed JSON with `Compare-Object`, prints differences, and exits `1` on any difference.

- [ ] **Step 5: Capture the pre-build boundary and run tests**

Run:

```powershell
New-Item -ItemType Directory -Force -Path artifacts\safety | Out-Null
& .\tools\capture_live_manifest.ps1 -OutputPath .\artifacts\safety\pre-build.json
python -m unittest tests.test_document_contracts -v
```

Expected: manifest created; all contract tests PASS.

- [ ] **Step 6: Initialize source control and commit the approved specification baseline**

```powershell
git init -b main
git add .gitignore README.md DESIGN.md TEST-PLAN.md CAPABILITY-PROOF.md UPSTREAM.md THIRD-PARTY-NOTICE.md build tests tools docs
git commit -m "docs: establish native POC specification and safety boundary"
```

Expected: clean repository except ignored `artifacts/`.

---

### Task 2: Deterministic Policy and Transaction Oracle

**Files:**
- Create: `tools/poc_model.py`
- Create: `tests/__init__.py`
- Create: `tests/test_poc_model.py`
- Test: `tests/test_poc_model.py`

**Interfaces:**
- Consumes: integer policy from `DESIGN.md`.
- Produces: `Policy(eligible_size, level_sum, average_level, level_percent, party_percent)`; `target_maximum`; `decompose_delta`; `restore_current`; `canonical_merge_policy`.

- [ ] **Step 1: Write failing policy tests**

Create `tests/test_poc_model.py`:

```python
import unittest
from tools.poc_model import (
    build_policy, target_maximum, decompose_delta,
    restore_current, canonical_merge_policy, PolicyError,
)

class PocModelTests(unittest.TestCase):
    def test_average_and_party_factor(self):
        p = build_policy([5, 7, 8])
        self.assertEqual((p.eligible_size, p.level_sum, p.average_level), (3, 20, 6))
        self.assertEqual((p.level_percent, p.party_percent), (115, 140))

    def test_solo_and_three_member_maximum(self):
        self.assertEqual(target_maximum(100, build_policy([7])), 115)
        self.assertEqual(target_maximum(100, build_policy([5, 7, 8])), 161)

    def test_binary_delta_and_bounds(self):
        self.assertEqual(decompose_delta(61), [32, 16, 8, 4, 1])
        self.assertEqual(decompose_delta(0), [])
        with self.assertRaises(PolicyError): decompose_delta(-1)
        with self.assertRaises(PolicyError): decompose_delta(65536)

    def test_percentage_rounding(self):
        self.assertEqual(restore_current(50, 100, 115, alive=True), 58)
        self.assertEqual(restore_current(58, 115, 100, alive=True), 50)
        self.assertEqual(restore_current(0, 100, 115, alive=False), 0)
        self.assertEqual(restore_current(1, 1000, 1, alive=True), 1)

    def test_merge_uses_independent_maxima(self):
        merged = canonical_merge_policy(build_policy([5, 5]), build_policy([8, 8, 8]))
        self.assertEqual((merged.average_level, merged.eligible_size), (8, 3))

if __name__ == "__main__": unittest.main()
```

- [ ] **Step 2: Run tests to verify the module is absent**

Run: `python -m unittest tests.test_poc_model -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'tools.poc_model'`.

- [ ] **Step 3: Implement the minimal deterministic oracle**

Create `tools/poc_model.py` with a frozen `Policy` dataclass. `build_policy` rejects an empty or non-positive level list, floors `sum // count`, uses level percent `115` only for averages `5..8`, uses `100 + 20 * (min(count, 8) - 1)`, and records a `clamped` boolean. `target_maximum` checks `base > 0`, rejects an unsupported average, verifies the intermediate product stays within signed 32-bit range, and performs one `// 10000`. `restore_current` uses `(old_current * new_maximum * 2 + old_maximum) // (old_maximum * 2)`, clamps living results to `1..new_maximum`, and returns zero for dead entities. `decompose_delta` walks `(32768, ..., 1)` and verifies the sum. `canonical_merge_policy` constructs a policy from the larger eligible size and higher average rather than choosing either snapshot wholesale.

- [ ] **Step 4: Run the focused and complete host-side tests**

Run:

```powershell
python -m unittest tests.test_poc_model -v
python -m unittest discover -s tests -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit the oracle**

```powershell
git add tools\poc_model.py tests\__init__.py tests\test_poc_model.py
git commit -m "test: lock native POC policy arithmetic"
```

---

### Task 3: Official Toolkit Installation and Isolation Proof

**Required execution skill:** `computer-use:computer-use` for the Steam and Toolkit UI operations.

**Files:**
- Create: `evidence/toolkit-install.json`
- Create: `evidence/toolkit-paths.json`
- Create: `artifacts/safety/post-toolkit-install.json` (ignored)
- Modify: `CAPABILITY-PROOF.md`
- Test: `tests/verify_live_directories_unchanged.ps1`

**Interfaces:**
- Consumes: Steam tool app `2934770`, BG3 Toolkit Data DLC app `2956320`, Baldur's Gate 3 app `1086940`, and `artifacts/safety/pre-build.json`.
- Produces: verified Toolkit executable/data roots and a no-live-change comparison.

- [ ] **Step 1: Reconfirm the exact installation target and available space**

Run:

```powershell
Get-PSDrive B | Select-Object Name,Free,Used
Test-Path -LiteralPath 'B:\SteamLibrary\steamapps\appmanifest_2934770.acf'
Test-Path -LiteralPath 'B:\SteamLibrary\steamapps\common\Baldurs Gate 3\Data\Editor'
```

Expected: adequate free space; the Toolkit manifest and BG3 editor-data folder are absent before installation.

- [ ] **Step 2: Install the official Baldur's Gate 3 Toolkit through Steam**

Use Steam's product page for the official Toolkit tool app `2934770`, select `B:\SteamLibrary`, and wait for Steam verification to complete. Then open Baldur's Gate 3 Properties > DLC and enable BG3 Toolkit Data (`2956320`) so Steam adds the editor-data depot to the installed game. Do not launch any third-party toolkit or mod manager.

- [ ] **Step 3: Record version-specific installation evidence**

Parse `B:\SteamLibrary\steamapps\appmanifest_2934770.acf` for `buildid`, `installdir`, and `LastUpdated`; inspect the Baldur's Gate 3 manifest for Toolkit Data depot `2330358` with DLC app ID `2956320`; resolve the Toolkit executable and BG3 data roots; write those exact values and SHA-256 hashes of the Toolkit executables to `evidence/toolkit-install.json` and `evidence/toolkit-paths.json`.

- [ ] **Step 4: Prove installation did not change live mod state**

Run:

```powershell
& .\tools\capture_live_manifest.ps1 -OutputPath .\artifacts\safety\post-toolkit-install.json
& .\tests\verify_live_directories_unchanged.ps1 -Before .\artifacts\safety\pre-build.json -After .\artifacts\safety\post-toolkit-install.json
```

Expected: PASS with no differences.

- [ ] **Step 5: Update the capability register**

Change only “Official Toolkit is installed on this machine” to **Verified locally**, recording app ID, build ID, install path, and verification date. Leave Publish Local, roster semantics, binary HP, persistence, merge, and multiplayer unverified.

- [ ] **Step 6: Commit installation evidence**

```powershell
git add evidence CAPABILITY-PROOF.md
git commit -m "docs: verify official Toolkit installation"
```

---

### Task 4: Isolated Toolkit Project and Flat-HP Capability Spike

**Files:**
- Create: `toolkit/Mods/AdaptiveEnemyScalingNativePOC_a4567f52-1665-df50-b84c-3992f80fdb90/meta.lsx`
- Create: `toolkit/Public/AdaptiveEnemyScalingNativePOC_a4567f52-1665-df50-b84c-3992f80fdb90/Stats/Generated/Data/Status_BOOST.txt`
- Create: `assets/thumbnail.png`
- Create: `story/RawFiles/Goals/AESN_00_Init.txt`
- Create: `story/RawFiles/Goals/AESN_99_TestHarness.txt`
- Create: `tools/sync_toolkit_project.ps1`
- Create: `artifacts/capability-spikes/CAP-02-minimal.pak` (ignored)
- Create: `artifacts/safety/post-minimal-publish.json` (ignored)
- Create: `evidence/capability-spikes/CAP-02-publish-local.md`
- Create: `evidence/capability-spikes/CAP-04-flat-hp.md`
- Modify: `CAPABILITY-PROOF.md`
- Test: Toolkit Stats/Story build and isolated editor probe

**Interfaces:**
- Consumes: `evidence/toolkit-paths.json`, fixed module identity.
- Produces: compiled native project; proven `AESN_HP_BIT_00001`; base initialization fact `DB_AESN_SchemaVersion(1)`.

- [x] **Step 1: Create the project and resolve the generated identity**

In the official Toolkit, create a new Adventure/add-on project named `AdaptiveEnemyScalingNativePOC` with no external mod dependencies and copy the generated `meta.lsx` into the exact repository path above. Set the user-facing name to `Adaptive Enemy Scaling` and the description to `Native proof of concept for Adaptive Enemy Scaling. Independently implemented with prominent credit to Simple Enemy Scaling by trashcanhvnds.` The Toolkit generated module UUID `a4567f52-1665-df50-b84c-3992f80fdb90`; a post-creation migration to the originally reserved UUID crashed project scanning, so the user explicitly approved the generated UUID on 2026-08-31. The Toolkit also rejected major version `0`, producing module version `1.0.0.0` while `0.1.0` remains the internal milestone. Evidence is recorded in `evidence/toolkit-project-identity.json`.

Create an original, non-game-art POC thumbnail at `assets/thumbnail.png` using the `imagegen` skill: a clean dark red and gold circular difficulty-scale emblem, no characters, logos, copyrighted game art, or third-party assets. Set it as the mandatory Project Settings thumbnail.

- [x] **Step 2: Write the failing static status test**

Extend `tests/test_document_contracts.py` to require `AESN_HP_BIT_00001`, exact boost `IncreaseMaxHP(1);`, unique stack ID `AESN_HP_BIT_00001`, and hidden flags; run it before creating the Stats file.

Run: `python -m unittest tests.test_document_contracts -v`

Expected: FAIL because `Status_BOOST.txt` is absent.

- [x] **Step 3: Add the independently authored one-bit probe status**

Create `Status_BOOST.txt` with this resource:

```text
new entry "AESN_HP_BIT_00001"
type "StatusData"
data "StatusType" "BOOST"
data "StackId" "AESN_HP_BIT_00001"
data "Boosts" "IncreaseMaxHP(1);"
data "StatusPropertyFlags" "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"
```

- [x] **Step 4: Add minimal Story initialization and probe procedures**

`AESN_00_Init.txt` declares `DB_AESN_SchemaVersion(1)` in `INIT` and supplies `PROC_AESN_RecordDiagnostic((STRING)_Key)` with `DB_AESN_DiagnosticOnce(_Key)` duplicate suppression.

`AESN_99_TestHarness.txt` supplies `PROC_AESN_TestApplyOneHp((CHARACTER)_Target)` and `PROC_AESN_TestRemoveOneHp((CHARACTER)_Target)`, which capture `GetHitpoints`/`GetMaxHitpoints`, call `ApplyStatus`/`RemoveStatus` for the exact probe ID, and record `StatusApplied`/`StatusRemoved` observations in `DB_AESN_TestObservation` facts. The harness contains no production policy rule.

- [x] **Step 5: Synchronize to the Toolkit project and compile**

`tools/sync_toolkit_project.ps1` accepts `-ToolkitDataRoot`, validates the destination ends in the installed Toolkit data root from `evidence/toolkit-paths.json`, then copies only the repository `toolkit/Mods`, `toolkit/Public`, and `story/RawFiles/Goals` trees to their matching project locations. It refuses any destination containing `AppData\Local\Larian Studios\Baldur's Gate 3\Mods`.

Run the sync script, then build Stats and Story in the Toolkit.

Expected: zero compiler errors and the project appears only in the Toolkit workspace.

- [x] **Step 6: Run CAP-04 in editor mode**

Authorized after review of the rejected CAP-02 isolation gate. Execute only in the Toolkit editor source project; do not install or activate the published package.

On a living test character, record `(current, maximum)`, apply `AESN_HP_BIT_00001`, wait for `StatusApplied`, verify maximum is exactly `maximum + 1`, restore percentage once, remove the status, wait for `StatusRemoved`, verify maximum returns exactly, and verify no resurrection behavior on a dead test entity. Save observations and Toolkit log excerpts in `evidence/capability-spikes/CAP-04-flat-hp.md`.

Expected: all observations pass. If any fails, mark binary flat HP **Rejected**, stop native implementation, and preserve the SE fallback.

Observed 2026-08-31: **Verified locally.** After an initial fail-closed `-1/-1` creation-frame observation, a 250 ms entity-bound native timer produced exact living records `12/12 -> 13/13 -> 12/12`, with matching status acknowledgements and 100% preserved once. Native `ApplyStatus` rejects dead characters; the final failure-closed policy detects `0` HP before mutation, applies no bit, performs no percentage write, preserves `0/12`, and retires the test target.

- [x] **Step 7: Verify Publish Local isolation with the minimal probe**

Capture a fresh live manifest, use **Publish Local** and choose `B:\UserData\Tom\BG3ModAnalysis\AdaptiveEnemyScaling-Native-POC\artifacts\capability-spikes\CAP-02-minimal.pak`, then capture `artifacts/safety/post-minimal-publish.json`. Compare both against `artifacts/safety/pre-build.json` and record the prompt, output path, package hash, and comparison result in `evidence/capability-spikes/CAP-02-publish-local.md`.

Expected: a local `.pak` is created at the chosen B: path, nothing is uploaded, and the live Mods directory and `modsettings.lsx` remain byte-for-byte unchanged. If Publish Local forces a live write, stop and report before continuing.

Observed 2026-08-31: **Rejected.** Publish Local created the package in the live player Mods directory. The exact new package was moved to ignored `B:` artifact storage, its SHA-256 was preserved, and the live manifest was restored exactly. Work stopped before CAP-04 runtime execution.

- [ ] **Step 8: Update proof status, run host tests, and commit**

Mark CAP-04 flat-HP behavior **Verified locally** and retain Publish Local direct-output isolation as **Rejected** with the current Toolkit/game builds.

```powershell
python -m unittest discover -s tests -v
git add toolkit story tools evidence CAPABILITY-PROOF.md tests
git commit -m "feat: prove isolated native flat HP status"
```

---

### Task 5: Full Status Registry and Roster Capability Gate

CAP-05 composition pre-gate observed 2026-08-31: **Verified locally.** The narrow independent `1|4|8` registry produced exact `+13` apply/cleanup transactions (`12/12 -> 25/25 -> 12/12`), distinct status acknowledgements, individual active/inactive queries, and one percentage restoration per transaction. The remaining status bits and CAP-03 roster work below are still open.

**Files:**
- Modify: `toolkit/Public/AdaptiveEnemyScalingNativePOC_a4567f52-1665-df50-b84c-3992f80fdb90/Stats/Generated/Data/Status_BOOST.txt`
- Create: `story/RawFiles/Goals/AESN_10_Roster.txt`
- Create: `story/RawFiles/Goals/AESN_20_Policy.txt`
- Create: `story/RawFiles/Goals/AESN_90_Diagnostics.txt`
- Create: `tests/validate_identities.py`
- Create: `evidence/capability-spikes/CAP-03-roster.md`
- Modify: `CAPABILITY-PROOF.md`
- Test: static identity tests, Story compile, CAP-03 editor fixtures

**Interfaces:**
- Consumes: verified flat-HP status primitive; `build_policy` oracle.
- Produces: sixteen HP statuses; `AESN_TIER_LEVEL_05_08`; additive action statuses; `PROC_AESN_BuildRoster`; `QRY_AESN_IsEligibleRosterMember`; finalized versioned snapshots.

- [x] **Step 1: Write failing status-registry and roster-source tests**

`tests/validate_identities.py` must parse Story and Stats text and assert:

- exact HP values `{1,2,4,...,32768}` appear once;
- every custom entry and stack ID begins `AESN_`;
- every custom database token begins `DB_AESN_`;
- `DB_PartOfTheTeam` appears only in `AESN_90_Diagnostics.txt`;
- `AESN_10_Roster.txt` contains `DB_PartyMembers` and contains no second `DB_*Party*` candidate predicate;
- no Tactician module UUID `7d6712c3-3b64-e94d-6f1a-9de67678b44b` or `TE_` identifier occurs in executable files.

Run: `python tests\validate_identities.py`

Expected: FAIL because the registry and roster goals are incomplete.

- [x] **Step 2: Expand the independently authored status registry**

Add `AESN_HP_BIT_00002` through `AESN_HP_BIT_32768`, each with its own matching stack ID and `IncreaseMaxHP(<bit>);`. Add:

```text
new entry "AESN_TIER_LEVEL_05_08"
type "StatusData"
data "StatusType" "BOOST"
data "StackId" "AESN_TIER_LEVEL_05_08"
data "Boosts" "RollBonus(Attack,1);RollBonus(SavingThrow,1);AC(1);SpellSaveDC(1);"
data "StatusPropertyFlags" "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"

new entry "AESN_EXTRA_ACTION_1"
type "StatusData"
data "StatusType" "BOOST"
data "StackId" "AESN_EXTRA_ACTION_1"
data "Boosts" "ActionResource(ActionPoint,1,0);"
data "StatusPropertyFlags" "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"

new entry "AESN_EXTRA_BONUS_ACTION_1"
type "StatusData"
data "StatusType" "BOOST"
data "StackId" "AESN_EXTRA_BONUS_ACTION_1"
data "Boosts" "ActionResource(BonusActionPoint,1,0);"
data "StatusPropertyFlags" "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"
```

- [x] **Step 3: Implement the candidate and diagnostic separation**

`AESN_10_Roster.txt` defines:

```text
QRY_AESN_IsEligibleRosterMember((CHARACTER)_Member)
PROC_AESN_BuildRoster((GUIDSTRING)_Combat)
PROC_AESN_RecordEligibleMember((GUIDSTRING)_Combat,(CHARACTER)_Member,(INTEGER)_Level)
```

The positive candidate rule starts only from `DB_PartyMembers(_Member)`, requires `IsSummon(_Member,0)`, `NOT CharacterGetOwner(_Member,_)`, and `IsPartyFollower(_Member,0)`, and uses `GetLevel` for its level. Separate exclusion rules record summon, owner, or follower reasons. `AESN_90_Diagnostics.txt` may observe `DB_PartOfTheTeam`, `IsPlayer`, team, and transformation queries but cannot insert `DB_AESN_SnapshotMember`.

After candidate rules have populated facts, `PROC_AESN_BuildRoster` calls `ConcatenateGUID("AESN_SNAPSHOT_FINALIZE_",_Combat,_Timer)`, stores `DB_AESN_SnapshotFinalizeTimer(_Timer,_Combat)`, and launches `TimerLaunch(_Timer,100)`. `TimerFinished(_Timer)` joined to that exact fact calls the policy-owned `PROC_AESN_FinalizeSnapshot(_Combat)`. CAP-03 must prove the 100 ms event barrier observes all expected candidate facts before this becomes a production dependency.

`AESN_20_Policy.txt` exposes `PROC_AESN_FinalizeSnapshot` and records the exact schema, size, sum, floored average, level percent, party percent, and supported/unsupported state. Arithmetic results must match `tools/poc_model.py` fixtures.

- [ ] **Step 4: Compile and run CAP-03 fixtures**

Use the editor harness to capture database observations for: solo avatar; three player avatars; active companion; active hireling; summon; familiar; temporary follower; transformed eligible member. Record exact GUID, source fact, exclusion result, and count in `evidence/capability-spikes/CAP-03-roster.md`.

Expected: avatar, active player avatars, active companion, and active hireling are included once; summon, familiar, and temporary follower are excluded; transformation does not duplicate identity.

If the approved query set cannot meet those results, mark the roster claim **Rejected** and stop rather than unioning `DB_PartOfTheTeam`.

Observed 2026-08-31: Story and the full Stats registry compile/load gates pass. The blank editor fixture verified the 100 ms event barrier and empty-roster failure-closed behavior. A managed Shadowheart fixture verified native `MakePlayer`, vanilla `DB_Players -> DB_PartyMembers` derivation, one positive eligible member, level capture, and `size=1,sum=1,average=1`. Incremental Gale ownership and registry probes then produced a verified two-member snapshot: both Shadowheart and Gale were eligible, neither had a gameplay owner, and the policy finalized `size=2,sum=2,average=1,partyPercent=120`. A prior combined fixture crashed on its first `SetLevel` call because the off-level Shadowheart origin lacked an Experience Component; no Gale or Astarion action executed. That command is retired and synthetic level mutation in this editor context is **Rejected**. Three-member, hireling, summon, familiar, follower, transformation, and supported-tier fixtures remain **Assumption/unsupported**; subsequent construction must proceed incrementally without `SetLevel`, and CAP-03 is still open.

- [ ] **Step 5: Run validators and commit the verified roster/policy layer**

```powershell
python tests\validate_identities.py
python -m unittest discover -s tests -v
git add toolkit story tests evidence CAPABILITY-PROOF.md
git commit -m "feat: add verified native roster and POC policy"
```

---

### Task 6: Combat Snapshot, Participants, and Existential Hostility

**Files:**
- Create: `story/RawFiles/Goals/AESN_30_Combat.txt`
- Modify: `story/RawFiles/Goals/AESN_99_TestHarness.txt`
- Modify: `tests/validate_identities.py`
- Test: Story compile; RT-13 through RT-16 editor cases

**Interfaces:**
- Consumes: `PROC_AESN_BuildRoster`, `DB_AESN_CombatSnapshot`, `DB_AESN_SnapshotMember`.
- Produces: `DB_AESN_CombatParticipant`; `QRY_AESN_IsEligibleHostile`; `PROC_AESN_ConsiderEnemy`; late-entry and duplicate-safe dispatch.

- [ ] **Step 1: Add failing static hostility tests**

Require `AESN_30_Combat.txt` to contain both `DB_AESN_CombatParticipant(_Combat,_Member)` and `IsEnemy(_Enemy,_Member,1)` in `QRY_AESN_IsEligibleHostile`, reject `DB_Players`, `GetHostCharacter`, single representative facts, `GetBaseArchetype`, and enemy classification through `DB_PartOfTheTeam`.

Run: `python tests\validate_identities.py`

Expected: FAIL because `AESN_30_Combat.txt` is absent.

- [ ] **Step 2: Implement combat snapshot dispatch**

On `CombatStarted(_Combat)`, guard on absence of `DB_AESN_CombatSnapshot`, build the roster once, populate participants from native combat-member enumeration intersected with `DB_AESN_SnapshotMember`, then consider current combat characters. On `EnteredCombat(_Object,_Combat)`, add `_Object` to participants only when it is a snapshotted member; otherwise call `PROC_AESN_ConsiderEnemy` for character objects after a snapshot exists.

`QRY_AESN_IsEligibleHostile(_Enemy,_Combat)` succeeds existentially for any participant member hostile under `IsEnemy(_Enemy,_Member,1)`. `DB_AESN_EnemyApplication(_Enemy,...)` suppresses duplicate consideration.

- [ ] **Step 3: Compile and execute focused editor fixtures**

Prove:

- neutral-to-all character is not eligible;
- hostile to the second of three participants is eligible even when neutral to the first;
- party-owned summon is not hostile to its party and is not scaled;
- hostile summon is eligible if `IsEnemy` succeeds;
- late entrant uses the existing snapshot;
- repeated `EnteredCombat` creates one consideration/application plan.

- [ ] **Step 4: Run validators and commit**

```powershell
python tests\validate_identities.py
python -m unittest discover -s tests -v
git add story tests
git commit -m "feat: snapshot combat participants and hostile enemies"
```

---

### Task 7: Exact HP Transaction and Fork-Owned Applications

**Files:**
- Create: `story/RawFiles/Goals/AESN_40_HpTransaction.txt`
- Create: `story/RawFiles/Goals/AESN_50_Applications.txt`
- Modify: `story/RawFiles/Goals/AESN_99_TestHarness.txt`
- Create: `tests/fixtures/hp_transactions.json`
- Modify: `tests/test_poc_model.py`
- Test: Story compile; RT-08 through RT-12 and RT-23 through RT-25 editor cases

**Interfaces:**
- Consumes: `QRY_AESN_IsEligibleHostile`, snapshot policy, exact status registry.
- Produces: `PROC_AESN_PlanEnemy`; `PROC_AESN_ApplyNextHpBit`; `PROC_AESN_CommitHp`; `PROC_AESN_RollbackHp`; `PROC_AESN_CleanupEnemy`; `PROC_AESN_ReplanEnemy`.

- [ ] **Step 1: Add failing transaction fixture tests**

Create `tests/fixtures/hp_transactions.json` with exact base/current/policy/target/delta/bits/restore rows for solo and three-member examples, zero delta, negative delta, `65,535`, `65,536`, dead-at-entry, and cleanup-after-damage. Extend `test_poc_model.py` to load every row and compare oracle output.

Run: `python -m unittest tests.test_poc_model -v`

Expected: FAIL until fixture-loading/state helpers exist.

- [ ] **Step 2: Implement persisted transaction planning**

`PROC_AESN_PlanEnemy` captures `GetHitpoints` and `GetMaxHitpoints`, rejects dead/non-positive/unsupported/unsafe plans, records one `DB_AESN_HpTransaction` in `Planned`, computes one target and restored current, and records a descending desired-bit queue without applying stat/action statuses.

- [ ] **Step 3: Implement acknowledged bit application and rollback**

Transition to `ApplyingHP`; call `ApplyStatus(_Enemy,_Status,-1.0,1,_Causee)` for one queued bit at a time. Only `StatusApplied(_Enemy,_Status,...)` creates `DB_AESN_EnemyHpBit` and advances. `StatusAttemptFailed` or the transaction timeout transitions to rollback. After the final acknowledgement, verify `GetMaxHitpoints == capturedMaximum + appliedDelta`, set restored current once, and enter `HPCommitted`.

Rollback removes only acknowledged `DB_AESN_EnemyHpBit` statuses, verifies the recorded sum, restores captured percentage once after removal, applies no stat/action status, and keeps failure evidence until confirmed.

- [ ] **Step 4: Implement additive stat/action commit and exact cleanup**

`AESN_50_Applications.txt` applies `AESN_TIER_LEVEL_05_08` after `HPCommitted`. It applies `AESN_EXTRA_ACTION_1` and `AESN_EXTRA_BONUS_ACTION_1` only for eligible size exactly three, records their exact IDs in `DB_AESN_EnemyApplication`, and enters `FullyCommitted`.

Cleanup captures the current percentage, removes exact `DB_AESN_EnemyHpBit` rows, verifies the maximum decreases by their exact sum, restores once if alive, does not set HP if dead, removes the three exact recorded component IDs, and deletes state only after acknowledgements.

- [ ] **Step 5: Implement atomic replan**

`PROC_AESN_ReplanEnemy` captures current/max once, removes old recorded bits, applies the new desired bits, expects `capturedMaximum - oldDelta + newDelta`, restores current percentage once after the exchange, replaces recorded policy/status IDs, and rolls back to the old plan if the new exchange fails.

- [ ] **Step 6: Compile and execute exact HP/status editor cases**

Verify the concrete `100/50`, average-level `5..8`, size-three case produces maximum `161`, current `81`, and bits `32,16,8,4,1`; immediate cleanup returns `100/50`. Verify damaged cleanup, zero delta, overflow, injected failed status, dead-before-apply, and death-after-apply. Inspect Action and Bonus Action resources only to prove the fork's additive `+1` appears and disappears; do not assert total normalization.

- [ ] **Step 7: Run all tests and commit**

```powershell
python -m unittest discover -s tests -v
python tests\validate_identities.py
git add story tests
git commit -m "feat: add exact native HP and additive action transactions"
```

---

### Task 8: Merged-Combat Ownership and Canonical Reconciliation

**Files:**
- Create: `story/RawFiles/Goals/AESN_60_Merge.txt`
- Modify: `story/RawFiles/Goals/AESN_30_Combat.txt`
- Modify: `story/RawFiles/Goals/AESN_40_HpTransaction.txt`
- Modify: `story/RawFiles/Goals/AESN_99_TestHarness.txt`
- Create: `tests/fixtures/merge_cases.json`
- Modify: `tests/test_poc_model.py`
- Test: Story compile; RT-17 through RT-19 editor cases

**Interfaces:**
- Consumes: `PROC_AESN_ReplanEnemy`, both combat snapshots and tracked applications.
- Produces: `PROC_AESN_MergeCombat`; `QRY_AESN_ResolveCombatOwner`; discarded-end suppression; canonical mismatch diagnostic.

- [ ] **Step 1: Add failing merge-policy/state tests**

Fixtures must cover equal snapshots, old-only snapshot, new-only snapshot, mismatch where one side has higher average and the other larger size, and a three-combat alias chain. Assert that discarded `CombatEnded` returns no cleanup commands and final surviving end returns each enemy once.

Run: `python -m unittest tests.test_poc_model -v`

Expected: FAIL until merge-state helpers and fixtures exist.

- [ ] **Step 2: Implement mark-before-migrate ownership**

The first `SwitchedCombat(_Object,_Old,_New)` rule immediately inserts `DB_AESN_MergedCombat(_Old,_New)` and `DB_AESN_CombatAlias(_Old,_New)`, then calls `PROC_AESN_MergeCombat`. That procedure migrates every application, bit, transaction, member, and participant owned by `_Old`, not just `_Object`. Alias resolution follows chains to the last survivor.

- [ ] **Step 3: Implement canonical mismatch policy and atomic enemy replan**

If both snapshots differ, build canonical fields with `max(oldAverage,newAverage)` and `max(oldEligibleSize,newEligibleSize)`, recompute level/party/action policy, union participants, call `PROC_AESN_ReplanEnemy` for all tracked enemies from both owners, and emit one diagnostic containing both source policies and the canonical fields.

- [ ] **Step 4: Suppress discarded cleanup and compile**

`CombatEnded(_Old)` with `DB_AESN_MergedCombat(_Old,_)` performs no enemy cleanup and retains the alias. `CombatEnded(_Final)` cleans records resolved to `_Final` and then removes aliases. Compile Story with zero errors.

- [ ] **Step 5: Execute equal, mismatch, and chain editor cases**

Assert record ownership, exact bit/status replans, single percentage restore, mismatch log, discarded no-op, and final cleanup.

- [ ] **Step 6: Run tests and commit**

```powershell
python -m unittest discover -s tests -v
git add story tests
git commit -m "feat: reconcile merged combat ownership"
```

---

### Task 9: Versioned Save/Load Reconciliation Gate

**Files:**
- Create: `story/RawFiles/Goals/AESN_70_Reconcile.txt`
- Modify: `story/RawFiles/Goals/AESN_00_Init.txt`
- Modify: `story/RawFiles/Goals/AESN_99_TestHarness.txt`
- Create: `evidence/capability-spikes/CAP-06-save-load.md`
- Create: `tests/fixtures/reconcile_cases.json`
- Modify: `tests/test_poc_model.py`
- Modify: `CAPABILITY-PROOF.md`
- Test: Story compile; CAP-06, RT-20 through RT-22 editor/runtime-save cases

**Interfaces:**
- Consumes: schema-1 snapshot/application/bit/transaction/alias facts; `CombatIsActive`.
- Produces: `PROC_AESN_QueueReconcile`; `PROC_AESN_ReconcileCombat`; `PROC_AESN_ReconcileEnemy`; stale inactive cleanup.

- [ ] **Step 1: Add failing reconciliation-state tests**

Fixtures must cover committed active/matching, active/missing-bit, active/extra-known-fork-bit, active/pending-apply, active/pending-remove, inactive/stale, discarded-to-active alias, and unsupported schema. The model must return one of `retain`, `rebuild`, `rollback`, `cleanup_stale`, `resolve_alias`, or `fail_closed` and never `apply_duplicate`.

Run: `python -m unittest tests.test_poc_model -v`

Expected: FAIL until reconciliation helpers exist.

- [ ] **Step 2: Implement one guarded reload generation**

`SavegameLoadStarted` marks a pending reload. `SavegameLoaded` queues reconciliation. `GameModeStarted(...,_IsStoryReload)` and `LevelGameplayStarted` allow the queued generation to execute once after gameplay is ready. Duplicate lifecycle events observe `DB_AESN_ReconcileGeneration` and no-op.

- [ ] **Step 3: Implement active and stale reconciliation**

For each snapshot, query `CombatIsActive`. Resolve discarded aliases first. Active committed records with exact known bits/statuses remain unchanged. A known-fork mismatch captures current/max, removes detected `AESN_` statuses only, preserves percentage once, and rebuilds the persisted canonical plan. Pending transactions verify and continue or rollback. Inactive records exact-clean before deleting snapshot facts. Schema values other than `1` fail closed unless an explicit version cleanup rule exists.

- [ ] **Step 4: Run CAP-06 save/load persistence proof**

In editor/runtime mode allowed without package installation, start a combat, reach `FullyCommitted`, save, reload, and record the snapshot, application, exact bit rows, schema, transaction state, active-combat query, maximum, and current HP. Repeat with a harness-paused `ApplyingHP` transaction.

Expected: facts and exact statuses persist; committed reload is idempotent; pending reload completes or rolls back once. If facts do not persist as required, mark the capability **Rejected** and stop the native path.

- [ ] **Step 5: Execute stale and alias reconciliation cases**

Use harness-injected schema-1 facts to prove stale inactive cleanup, alias-to-active retention, and unsupported-schema failure closed. Record observations in `evidence/capability-spikes/CAP-06-save-load.md`.

- [ ] **Step 6: Update proof status, run tests, and commit**

```powershell
python -m unittest discover -s tests -v
python tests\validate_identities.py
git add story tests evidence CAPABILITY-PROOF.md
git commit -m "feat: reconcile versioned combat state after reload"
```

---

### Task 10: Diagnostics, Full Editor Acceptance, and Authorship Audit

**Files:**
- Modify: `story/RawFiles/Goals/AESN_90_Diagnostics.txt`
- Modify: `story/RawFiles/Goals/AESN_99_TestHarness.txt`
- Create: `tests/validate_authorship.py`
- Create: `evidence/editor-acceptance.json`
- Create: `evidence/authorship-audit.json`
- Modify: `TEST-PLAN.md`
- Test: all host tests, Toolkit Story/Stats compile, editor acceptance matrix

**Interfaces:**
- Consumes: all production procedures and test observations.
- Produces: structured one-shot diagnostic schema; machine-readable editor acceptance and authorship reports.

- [ ] **Step 1: Write failing diagnostics and authorship tests**

Require diagnostics to default off, require each production failure state to call `PROC_AESN_RecordDiagnostic`, reject any diagnostic rule that inserts snapshot/application facts, and compare executable tokens against deny lists from the audited upstream/Tactician manifests while allowing generic engine calls and the upstream conflict UUID only in metadata.

Run:

```powershell
python tests\validate_identities.py
python tests\validate_authorship.py
```

Expected: FAIL until diagnostic coverage and audit configuration are complete.

- [ ] **Step 2: Complete structured one-shot diagnostics**

Emit keys and fields for candidate included/excluded, snapshot finalized, unsupported tier, hostility accepted/rejected, HP plan, each acknowledged bit, HP commit, rollback reason, exact cleanup, party-factor clamp, merge mismatch, alias resolution, reload retained/rebuilt/stale, schema rejection, and timeout. Test mode enables output explicitly; normal initialization leaves it disabled.

- [ ] **Step 3: Make the harness call only production interfaces**

Harness cases invoke `PROC_AESN_BuildRoster`, `PROC_AESN_ConsiderEnemy`, `PROC_AESN_PlanEnemy`, `PROC_AESN_MergeCombat`, and `PROC_AESN_QueueReconcile`. Remove any duplicated arithmetic, hostility, cleanup, or merge selection from the harness.

- [ ] **Step 4: Execute all pre-install editor rows available from TEST-PLAN**

Record pass/fail, game build, Toolkit build, fixture GUIDs, expected, observed, and log evidence for CAP-03 through CAP-07 and RT-01 through RT-25 where editor support permits. Any unavailable installed-game or multiplayer row remains explicitly `blocked_by_post_build_install_approval`, not passed.

- [ ] **Step 5: Compile and run the complete local suite**

Run:

```powershell
python -m unittest discover -s tests -v
python tests\validate_identities.py
python tests\validate_authorship.py
```

Build Stats and Story in the Toolkit. Expected: zero compiler errors, all host validators PASS, and no required pre-install editor row fails.

- [ ] **Step 6: Commit the audited editor-ready POC**

```powershell
git add story tests evidence TEST-PLAN.md
git commit -m "test: complete native POC editor acceptance"
```

---

### Task 11: Publish Local, Round-Trip Package Validation, and Mandatory Stop

**Required execution skill:** `computer-use:computer-use` for Toolkit Project Settings and Publish Local.

**Files:**
- Create: `tools/validate_package.py`
- Create: `tests/test_validate_package.py`
- Create: `artifacts/packed/AdaptiveEnemyScalingNativePOC-0.1.0.pak` (ignored)
- Create: `artifacts/reports/package-validation.json` (ignored)
- Create: `artifacts/safety/post-publish.json` (ignored)
- Create: `evidence/publish-local.json`
- Modify: `CAPABILITY-PROOF.md`
- Test: package validator, Divine round trip, live-state comparison

**Interfaces:**
- Consumes: compiled Toolkit project, LSLib Divine path, pre-build live manifest.
- Produces: hashed local `.pak`, extracted allowlist validation report, proof of no live writes.

- [ ] **Step 1: Write failing package validation tests**

Create tests using temporary fake package-extraction trees. Require exact module folder/UUID, only approved `Mods`, `Public`, and `Story` content, no Script Extender directory, all identifiers correctly namespaced, no nested archives, no Tactician IDs, and prominent upstream credit in repository metadata. Include explicit failing fixtures for an upstream UUID in executable content, a `TE_` status, a nested `.zip`, and a `ScriptExtender` directory.

Run: `python -m unittest tests.test_validate_package -v`

Expected: FAIL until `tools/validate_package.py` exists.

- [ ] **Step 2: Implement the package validator**

`tools/validate_package.py` accepts `--pak`, `--divine`, `--extract-to`, and `--report`. It rejects an extraction target outside repository `artifacts/analysis`, invokes Divine in list/extract mode, hashes the package, checks the exact allowlist and deny rules, parses `meta.lsx` identity/dependencies/conflicts, runs source identity/authorship checks on extracted content, and writes deterministic JSON with `passed`, package hash, file manifest, checks, and failures.

- [ ] **Step 3: Run all source tests immediately before publishing**

```powershell
python -m unittest discover -s tests -v
python tests\validate_identities.py
python tests\validate_authorship.py
```

Expected: PASS.

- [ ] **Step 4: Publish Local to the exact B: artifact path**

Open Project Settings in the official Toolkit, confirm name `Adaptive Enemy Scaling`, POC description, version `0.1.0`, new UUID, no mod dependencies, and Simple Enemy Scaling conflict. Select **Publish Local** and choose:

`B:\UserData\Tom\BG3ModAnalysis\AdaptiveEnemyScaling-Native-POC\artifacts\packed\AdaptiveEnemyScalingNativePOC-0.1.0.pak`

Do not choose Publish/mod.io, do not authenticate, and do not copy the package afterward.

This step is currently blocked: CAP-02 rejected the assumption that Publish Local can avoid the live player Mods directory. Do not retry it unless the design is changed to avoid the write or the user explicitly authorizes a narrowly scoped temporary-package exception.

If the Toolkit conflict UI requires installing Simple Enemy Scaling into the live Mods directory, do not install it. Attempt the conflict only through the Toolkit's supported project metadata interface using module UUID `b7e3a1d2-f4c6-4e89-9abc-d012ef345678`; if that supported path is unavailable, stop before Publish Local and report the conflict-declaration gate instead of violating the live-directory boundary.

- [ ] **Step 5: Round-trip validate the package**

Run `tools/validate_package.py` with the recorded Divine executable and output under `artifacts/analysis/package-roundtrip` and `artifacts/reports/package-validation.json`.

Expected: `passed: true`; package contains no SE tree or foreign authored identifiers.

- [ ] **Step 6: Prove Publish Local left live game state untouched**

```powershell
& .\tools\capture_live_manifest.ps1 -OutputPath .\artifacts\safety\post-publish.json
& .\tests\verify_live_directories_unchanged.ps1 -Before .\artifacts\safety\pre-build.json -After .\artifacts\safety\post-publish.json
```

Expected: PASS with no changes.

- [ ] **Step 7: Record reproducible build evidence and commit only tracked evidence**

`evidence/publish-local.json` records Toolkit/game builds, module identity, source commit, package SHA-256, validation report SHA-256, Publish Local destination, and live-manifest comparison result.

```powershell
git add tools tests evidence CAPABILITY-PROOF.md
git commit -m "build: validate native POC local package"
git status --short
```

Expected: ignored artifacts exist; tracked tree is clean.

- [ ] **Step 8: STOP FOR REVIEW**

Do not install, copy, activate, edit `modsettings.lsx`, open mod.io publishing, or begin host/client testing. Present the package path, hash, source commit, test summary, proof register, remaining post-install rows, and live-state no-change result to the user.

---

### Task 12: Post-Build Installed Runtime and Multiplayer Proof — Separate Approval Required

**Files:**
- Create after approval: `evidence/runtime-acceptance.json`
- Create after approval: `evidence/multiplayer-acceptance.json`
- Modify after approval: `CAPABILITY-PROOF.md`
- Modify after approval: `TEST-PLAN.md`
- Test: RT-01 through RT-27 in installed game, including host plus clients

**Interfaces:**
- Consumes: reviewed package from Task 11 and a new explicit installation authorization.
- Produces: final native feasibility verdict; no public upload.

- [ ] **Step 1: Obtain a separate explicit approval to install the reviewed package**

Without that approval, this task remains unstarted.

- [ ] **Step 2: Snapshot live state, install only the reviewed package, and record the reversible change**

Hash-check the package against Task 11, capture a new pre-install live manifest, install through the user-approved method, record every added/changed path, and do not upload.

- [ ] **Step 3: Execute the complete installed-game runtime matrix**

Run RT-01 through RT-25 using the exact expected values in `TEST-PLAN.md`, including mid-combat committed and pending save/load, late entrant, equal/mismatched/chain merges, dead-enemy behavior, and failure injection.

- [ ] **Step 4: Execute host-plus-client and reconnect tests**

With host and at least two clients, verify one host-authoritative application, identical observed HP/stats/statuses, exact cleanup, no client-originated duplicate, and reconnect retention. Record peer logs and observations without including account tokens or private identifiers.

- [ ] **Step 5: Issue the native verdict**

Mark each mandatory capability **Verified locally** or **Rejected**. The POC passes only if every required row passes. A rejection preserves the SE fallback and blocks publication; a pass permits a separate production-balance design and publication decision.

- [ ] **Step 6: Commit runtime evidence**

```powershell
git add evidence CAPABILITY-PROOF.md TEST-PLAN.md
git commit -m "test: record installed native POC runtime proof"
```

---

## Self-Review Record

- Spec coverage: all ten approved amendments map to Global Constraints and Tasks 4 through 12; all narrow POC proof rows map to CAP-03 through CAP-07 and RT-01 through RT-27.
- Capability gate: unsupported roster, HP, persistence, and merge assumptions each have a stop-on-rejection spike before dependent completion claims.
- Identity consistency: module UUID, module folder, namespaces, version, upstream hashes, and artifact path are identical throughout the plan.
- Safety boundary: Tasks 1, 3, and 11 capture and compare live manifests; Task 11 contains the mandatory pre-install stop.
- Copy boundary: Tasks 5, 10, and 11 mechanically reject Tactician identifiers and non-approved upstream executable reuse.
- Test-first sequencing: every executable component starts with a failing host/static test or isolated capability spike, followed by the smallest implementation and verification.
