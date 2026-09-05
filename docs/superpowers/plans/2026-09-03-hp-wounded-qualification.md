# Wounded HP Primitive Qualification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove exact wounded HP preservation when replacing legacy bit statuses with one total status, before production depends on SetHitpoints.

**Architecture:** A disabled isolated Story fixture creates two friendly noncombat kobolds, one with a single-bit bonus and one with the six-bit111 bonus. An independent+7 reference status stays throughout. User-controlled save/reload checkpoints verify wounded legacy retention, replacement and total retention; source tests exercise real rules with explicit native observations, without claiming native behavior.

**Tech Stack:** BG3 Toolkit Osiris Story, existing BOOST catalog/legacy stats, Python unittest and tests.osiris_subset, user-driven retail saves parsed read-only with LSLib.

**Spec:** docs/superpowers/specs/2026-09-03-single-contribution-hp.md

## Global Constraints

- Preserve the current supported delta range0..65535 and policy schema2; no balance or Relentless changes.
- The absolute setter's exact wounded-migration behavior must be proved locally before it becomes a production dependency.
- No automatic commit, merge, push, online publication, duplicate mod listing or load-order change is included in this design.
- Do not copy stale repo metadata over current Toolkit metadata.
- Only disposable fixture NPCs may be mutated; source fixture disabled by default, no automatic normal-game activation.
- Catalog gate accepted with disclosed performance limitations; this plan does not implement production journal recovery or waive later regression gates.

## File structure and boundary

- Create story/RawFiles/Goals/AESN_81_HpWoundedProof.txt: independent disabled primitive probe, two cases, explicit saved phases/observations/failures.
- Create tests/test_hp_wounded_proof.py: execution tests of real source via StoryFixture, recording native calls with explicit query responses.
- Create evidence/capability-spikes/UI-03-hp-wounded-qualification.md: expected native sequence and actual results, clearly separated.
- Reuse existing catalog and legacy Status_BOOST unchanged; no additional stat definitions or production Story changes.
- Use ignored artifacts/hp-wounded/ for prepared staging, backups and save extracts.

## Task 1: Build the disabled wounded replacement probe and source tests

**Files:** create the three listed files only. Do not edit production goals, catalog or other proof goals.

**Interfaces:**
- Consumes existing AESN_HP_BIT_00001/00002/00004/00008/00032/00064 statuses and AESN_HP_TOTAL_1/7/111, confirmed in Status_BOOST. Legacy IDs use five-digit padding; catalog IDs do not.
- Native SetHitpoints(GUIDSTRING,INTEGER,STRING) from current local story_header.div; use reason `Guaranteed`.
- Produces DB_AESN_HpWoundedEnabled/Version/Started, Fixture(NPC,Amount), State(NPC,Amount,Base,Target,Wounded,Phase), Observation(NPC,Amount,Phase,ExpectedMax,Current,Maximum), Failure(NPC,Amount,Phase).
- Namespace all additional one-shot facts/timers/procedures under AESN_HpWounded. Typed CHARACTERS for NPC facts/procedure args; typed GUIDSTRING event casts consistent with existing proof.

- [ ] Write failing behavior tests before the goal exists, using empty StoryFixture when absent so failures are missing behavior assertions, not missing-file exceptions.

```python
# Real Story execution must yield these independently derived checkpoints.
cases = [(1, 20, 28, 13), (111, 20, 138, 69)]
# The +7 reference is independent of legacy/total ownership and survives cleanup.
# Assert actual ApplyStatus/RemoveStatus/SetHitpoints calls and saved states.
```

- [ ] Run `python -m unittest tests.test_hp_wounded_proof -v`; record expected RED output.
- [ ] Implement INIT with `NOT DB_AESN_HpWoundedEnabled(1);`, version1, typed seeds, sample mapping. Initial SavegameLoaded requires enabled/notStarted/host alive/out-of-combat. Sequentially spawn two Kobolds_Melee_Drunk_45e31b7d-32ec-4f3d-8067-79061aeec77b beside host/previous fixture using one-shot tokens. Set host faction, SetCanFight0, SetCanJoinCombat0. Never mutate host/ordinary enemies.
- [ ] Baseline phase requires positive full-health baseline, bounded below1000000. Apply reference AESN_HP_TOTAL_7 and exact legacy bits once. Record target=Base+7+Amount. After settle verify exact maximum and all expected statuses present; set wounded HP once to13 for amount1,69 for111 only if below target and alive/out-of-combat. Observe exact current/max and stop in LegacyInspect. A changed/missing maximum or failed setter yields Failure rather than success. Consume pending tokens before writes.
- [ ] First reload only transitions LegacyInspect to LegacyReloading; observe original current/maximum without healing or reapplication. If exact and safe, remove each recorded legacy status, preserving reference7. After settle require each removed bit absent, reference present, max=Base+7 and current positive. Observe interim HP; apply exactly matching total once. After settle require target max/reference/total present and positive current, observe native interim current, then SetHitpoints captured wounded value exactly once. Record Converted observation, require exact captured current/maximum, and stop TotalInspect.
- [ ] Second reload only transitions TotalInspect to TotalReloading. Verify captured current/max and exact total/reference statuses without writes. Remove only own total, leave reference7. After settle require max=Base+7, current positive and<=maximum, own total absent/reference present. Record Cleanup and stop Complete. Do not force final currentHP to an assumed value or remove reference7.
- [ ] Fail closed on unexpected observations, unsupported samples, dead/zero HP or combat; every delayed mutation checks fixture/version/enabled/phase/notFailure/alive/out-of-combat. Replayed timers cannot repeat writes. Reload from any transient mutation phase records Interrupted failure and performs no repair/write; this probe deliberately does not establish interrupted production recovery. Completed reloading is inert. Native events may be delayed; no test claims to simulate engine rounding/scheduling. Fixture is not a safe production converter.
- [ ] Add execution tests for both cases through legacy, replacement, total reload, cleanup; wrong maximum/current/reference or missing bit; disabled/duplicate/dead/combat continuations; interrupted save reload cannot write; zero-health cannot be restored. Validate exact statuses passed and reference never removed. Deliberately supply altered GetHitpoints responses to prove bad paths fail rather than tests merely assuming them away.
- [ ] Run focused tests GREEN, then `python -m unittest discover -s tests` and `python tests/validate_identities.py`; report full outputs and self-review. No commit.
- [ ] Write UI03 with expected checkpoints for base20: legacy13/28 and69/138, converted same, total reload same, cleanup max27 with surviving reference7. Native build/run still pending. Cite public API signature path; do not call wounded behavior verified until native save facts confirm.

## Task 2: Review and prepare user-run native qualification

**Files:** UI03 plus ignored artifacts/hp-wounded/; live Toolkit only after game+Toolkit confirmed closed.

**Interfaces:** consumes reviewed Task1 source and accepted full catalog; produces exact staged-input manifest and retained backup for user build.

- [ ] Independent task review checks actual source safety/one-shot semantics and tests against Task1 requirements. Fix/re-review substantive findings before staging.
- [ ] Confirm game/Toolkit fully exited. If open, request closure while preparing worktree artifacts; never terminate them.
- [ ] Prepare enabled copy by replacing only `NOT DB_AESN_HpWoundedEnabled(1);` with positive seed. Keep repository disabled. Validate copied catalog using `python -m tools.hp_catalog check artifacts/hp-catalog/Status_AESN_HP_Total.txt`.
- [ ] Back up current live goals/stats/meta and installed PAK to ignored artifacts/hp-wounded/pre-stage with matching hashes. Verify current moduleUUID/original PublishHandle6353123. Replace only old enabled82 proof goal with new enabled81, preserving twelve production goals, both stat files, metadata and installed PAK unchanged. Do not run general sync.
- [ ] User Generate Definitions and Build Story, Publish Local only; verify resulting PAK contains reviewed source/full catalog, original identity and no other enabled proof.
- [ ] User loads untouched out-of-combat pre-Nere save. Save AES wounded legacy and verify legacy checkpoint facts; reload then save AES wounded converted and inspect conversion; reload again and save AES wounded cleanup, inspect retention/exact cleanup. Ask one step at a time. Never overwrite campaign saves or ask user to fight/wound actors manually.
- [ ] Record native results, including intermediate native currentHP changes, failures and evidence hashes. Native gate pauses execution until user reports results. After successful wounded primitive proof, plan production ownership/journal integration against the full approved spec; this primitive test does not cover all migration interruption cases.

## Self-review and progress

- Spec coverage: this independently testable plan resolves the remaining native SetHitpoints/wounded-replacement prerequisite; production transactions, durable journal, mixed-owner transfer and recovery require the next integration plan after this gate.
- No catalog, balance, policy, Relentless or online identity changes.
- Task1 source/tests: complete, source spec/quality review approved after shared-validation refactor.168tests plus8identities pass after refactor.
- Task2 current result: corrected build1.0.0.16 compiled and published locally;
  parsed saves verify both wounded legacy/total reloads, exact replacement and
  cleanup. UI03 contains hashes, native intermediate HP and limits. User has
  now closed game/Toolkit. No production integration yet.
- Evidence limitation: these wounded checkpoints have user text confirmations
  and saved observations, not new screenshots. Full visual/retail evidence and
  normal self-healing/intervention/recovery safety remain outstanding; collect
  those in the production integration qualification before release.
- Final source review found no functional primitive blocker; evidence notes
  were corrected to distinguish historical pre-run expectations from current
  observations. The new production plan is
  `docs/superpowers/plans/2026-09-03-hp-total-production-integration.md`.
