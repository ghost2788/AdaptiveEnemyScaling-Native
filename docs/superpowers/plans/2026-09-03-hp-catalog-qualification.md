# HP Catalog Qualification Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans for inline execution,
> or superpowers:subagent-driven-development if delegation is selected. Complete
> the catalog qualification gate before planning/executing production migration.

**Goal:** Generate and validate all 65,535 exact HP statuses and prepare a
reversible native capacity/behavior test without changing production HP logic.

**Architecture:** A deterministic Python generator produces a separate native
StatusData file outside production sources. Automated validation covers every
entry. An opt-in qualification fixture and staged package test native load,
boundary effects and retention; production transactions remain unchanged.

**Tech Stack:** Python standard library/unittest, native Osiris, BG3 Toolkit,
PowerShell, existing Divine/LSLib tooling for read-only save inspection.

**Spec:** `docs/superpowers/specs/2026-09-03-single-contribution-hp.md`

## Global Constraints

- Preserve supported HP delta range 0..65,535 and exact integer HP calculations.
- Zero applies no HP status; one positive delta selects exactly one total status.
- No Script Extender, global UI override or balance changes.
- Keep legacy HP status definitions and production Story unchanged for this gate.
- Preserve module UUID `a4567f52-1665-df50-b84c-3992f80fdb90` and current metadata.
- Do not copy stale repository metadata into the live Toolkit project.
- No automatic commit, merge, push, online publication or load-order changes.
- Do not write game saves; keep read-only extracts and generated output on B:.
- Protect existing uncommitted work; obtain the user's workspace choice first.
- User performs Toolkit build, Publish Local and retail verification.

## Task 1: deterministic catalog and exhaustive validator

**Files:**
- Create `tools/hp_catalog.py`.
- Create `tests/test_hp_catalog.py`.
- Generate ignored `artifacts/hp-catalog/Status_AESN_HP_Total.txt`.
- Update `evidence/capability-spikes/UI-02-hp-catalog-qualification.md` with receipts.

**Interfaces:**
- `status_id(delta: int) -> str | None`: validate 0..65,535, reject bool/non-int;
  return None for zero or `AESN_HP_TOTAL_<decimal>`.
- `render_catalog() -> str`: deterministic full catalog in ascending amount order.
- `validate_catalog(text: str) -> dict`: fail on missing/duplicate IDs, extra
  fields, incorrect amounts, unexpected inheritance or invalid display/flags;
  return count and SHA-256 of the UTF-8 bytes.
- CLI `python -m tools.hp_catalog generate --output PATH`: validate before
  writing; create a new file or accept an already-identical file. Refuse to
  overwrite differing content. Do not infer a Toolkit/live destination.
- CLI `python -m tools.hp_catalog check PATH`: read-only validation with a
  nonzero exit code and concise error on invalid data.

- [ ] Write failing selection tests with hand-derived expectations:

```python
for delta, expected in [(0, None), (1, 'AESN_HP_TOTAL_1'),
                        (111, 'AESN_HP_TOTAL_111'),
                        (32768, 'AESN_HP_TOTAL_32768'),
                        (65535, 'AESN_HP_TOTAL_65535')]:
    self.assertEqual(expected, catalog.status_id(delta))
for invalid in [-1, 65536, True, 1.0, '111', None]:
    with self.assertRaises(ValueError):
        catalog.status_id(invalid)
```

- [ ] Run `python -m unittest tests.test_hp_catalog` and observe expected failures.
- [ ] Implement selection and deterministic rendering. Each generated entry is:

```text
new entry "AESN_HP_TOTAL_111"
type "StatusData"
data "StatusType" "BOOST"
data "DisplayName" "AESNHpSourceName;1"
data "StackId" "AESN_HP_TOTAL_111"
data "Boosts" "IncreaseMaxHP(111);"
data "StatusPropertyFlags" "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"
```

- [ ] Add exhaustive independent parsing tests: 65,535 unique IDs and StackIds,
  integer coverage exactly 1..65,535, exactly one matching flat boost each,
  no zero entry, and existing XML handle resolves to Adaptive Enemy Scaling.
- [ ] Add failing validator tests by removing an entry, duplicating one,
  changing an amount, swapping a StackId and introducing another boost.
- [ ] Implement strict semantic validation; do not validate merely by comparing
  with the same renderer, which could share its bug.
- [ ] Add CLI tests using temporary directories for generate/check, identical
  rerun, refusal to overwrite differing content, and invalid-file rejection.
  Assert existing files remain unchanged on refusal.
- [ ] Implement the CLI, run tests, generate the full ignored artifact, and
  record byte length/hash/count. Generate twice and compare hashes.

## Task 2: isolated full-catalog native fixture

**Files:**
- Create `story/RawFiles/Goals/AESN_82_HpCatalogProof.txt` (disabled by default).
- Create `tests/test_hp_catalog_proof.py` using `tests/osiris_subset.py`.
- Keep `AESN_83_HpTooltipProof.txt` and its v2 proof stats as historical sources;
  exclude them from this qualification package.

**Interfaces:**
- New proof-only `DB_AESN_HpCatalog*` namespace; do not consume old tooltip DBs.
- Per fixture: NPC, amount, expected status, baseline maximum, phase.
- Recorded observations: NPC, amount, phase, expected/current/maximum.
- Explicit Complete or Failure; all observations must be queried/consumed.
- New-save setup is enabled only with the staged proof gate and out-of-combat
  host. Spawn non-combat fixtures using the already-verified setup mechanism.

- [ ] Write rule tests for sample amounts 0, 1, 111, 32768 and 65535 using
  explicit native-query outputs. Assert no HP status for zero and one exact
  catalog status per positive fixture; party members never receive test boosts.
- [ ] Observe failure before implementing the new fixture.
- [ ] Implement native application/settling/observation with permanent statuses.
  Stop at an Inspect checkpoint for separate saves and screenshots.
- [ ] Write tests that SavegameLoaded never reapplies the primary status or
  writes HP before retention validation. Missing bonus must record Failure.
- [ ] Implement reload retention, exact removal and final baseline checks;
  preserve recorded intermediate observations in the save.
- [ ] Test duplicate load/setup events, failed HP observations, disabled gate,
  no resurrection and unsupported/invalid sample selection.
- [ ] Run proof-rule and catalog tests. Treat this as source-level verification
  only; native typing, scheduling, GUI and persistence remain user-run gates.

For a fixture whose measured baseline is 20, literal independent expectations:

| Amount | Initial/reload maximum | After removal |
| --- | ---: | ---: |
| 0 | 20 | 20 |
| 1 | 21 | 20 |
| 111 | 131 | 20 |
| 32768 | 32788 | 20 |
| 65535 | 65555 | 20 |

## Task 3: safe qualification staging and native acceptance

**Files:**
- Update `tools/sync_toolkit_project.ps1` only as necessary to remove exact
  proof-only generated files during subsequent normal production staging.
- Update `tests/test_sync_toolkit_project.py` with temporary-directory behavior
  tests proving cleanup preserves production/unrelated files.
- Update `evidence/capability-spikes/UI-02-hp-catalog-qualification.md`.

- [ ] Write failing cleanup test for the exact opt-in catalog filename.
- [ ] Implement cleanup, keeping generation and test staging opt-in. No general
  sync runs against the real Toolkit because its metadata copy is stale.
- [ ] Run full unittest discovery, identity checks and whitespace validation.
- [ ] Confirm game/Toolkit exited before staging; if running, stop and ask.
- [ ] Back up exact existing staged goals/stats/metadata and installed PAK on B:.
- [ ] Prepare baseline with unchanged production code and no active throwaway
  harness. Separately prepare catalog condition with the same production code,
  full generated catalog and only the selected qualification harness.
- [ ] Verify production file and metadata hashes remain identical across the
  conditions; record intentional fixture/catalog differences.
- [ ] Ask user to build and Publish Local, never online Publish. Baseline and
  catalog conditions use the same enabled mods and original disposable save.
- [ ] Measure three comparable loads per condition; record time to controllable
  save and process memory/stability. Investigate catalog overhead exceeding
  max(2 seconds, 20% baseline) or 256 MiB steady working set.
- [ ] Verify each boundary fixture's named row and both proof saves' recorded
  maximum/current/retention/removal data. Do not infer pass from final HP alone.
- [ ] Record passed and failed capabilities separately; do not enable production
  totals or migration if catalog acceptance is incomplete.

## Subsequent implementation boundary

This is the complete plan for the first independently testable gate, not the
entire production migration. Once native catalog acceptance is recorded,
prepare the next execution plan against the approved spec's ownership,
conversion and regression sections. This explicit gate avoids implementing
production persistence on an unverified full-catalog dependency.

## Progress

- Design approved: yes.
- Workspace choice: user approved isolated B: worktree with dirty snapshot.
- Workspace: `B:/UserData/Tom/BG3ModAnalysis/worktrees/AdaptiveEnemyScaling-hp-total`, branch `codex/hp-total-catalog`.
- Baseline: 24 copied files hash-verified; 136 tests plus 8 identity checks pass.
- Catalog implementation: generator, exhaustive validator, CLI and tests implemented; artifact 65,535 entries / 18,250,946 bytes.
- Native fixture: five-sample source and lifecycle/replay regressions implemented, reviewed after two correction rounds; disabled in source.
- Source verification: 154 discovery tests plus 8 identity checks pass; catalog check and whitespace check pass.
- Staging: baseline staged after verified backup; catalog condition prepared separately with identical production inputs. Current installed PAK remains previous proof until baseline local publish.
- Native qualification: sampled retail boundary application, single-row tooltips, save/load retention, and exact removal pass; both proof saves inspected. Three fresh catalog-process memory samples recorded. User accepted Gate1 with disclosed missing controlled timings/configuration limitations and will monitor perceived performance; this is not a measured load-time pass. See UI-02 for package/save hashes and all observations.
- Final source review: approved; no actionable findings. Catalog accepted for the next implementation stage; wounded primitive proof is planned in 2026-09-03-hp-wounded-qualification.md. Production integration remains pending.
- Production migration: deliberately gated.
