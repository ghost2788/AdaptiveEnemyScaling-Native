# Single-contribution AES HP design

Date: 2026-09-03
Status: Approved for implementation by the user's "implement it" instruction.
Classification: Architectural; saved HP ownership and migration change.

## Outcome and unchanged behavior

Represent each supported positive AES HP bonus as one permanent, named BOOST
status, yielding one `+N from Adaptive Enemy Scaling` contribution. A zero
bonus applies no HP status. Preserve the current supported delta range
0..65,535, policy percentages, integer target calculation, and all Hardened
combat bonuses and Relentless allocation/budgets. No rounding to a smaller
catalog, fallback to multiple rows for large newly applied bonuses, Script
Extender dependency, global UI override, or new mod listing.

The current formula remains `floor(externalBase * targetPercent / 100)`;
delta is target maximum minus external base. Existing range and overflow
guards remain. Changes in policy continue to use the existing wounded-HP
percentage behavior. Merely converting representation must not change either
the maximum or current HP, and must not recalculate policy.

## Evidence and limits

The accepted version-2 +111 fixture displayed one correctly named row and its
saved observations verified 20 -> 131 -> reload 131 -> reference 242 -> removal
131 -> cleanup 20. Its final state was Complete with zero failures. See
`evidence/capability-spikes/UI-01-hp-tooltip-feasibility.md` for save identities.

Verified locally: the specific permanent BOOST status, label, full-health
handling, reload persistence without reapplication, and exact-status removal.
Rejected: the earlier direct AddBoosts implementation's retention/attribution.
Not yet verified: the capacity/cost of 65,535 added status definitions,
boundary amounts, representation migration, wounded migration and interrupted
migration recovery. These are release gates, not assumed capabilities.

The current Toolkit header exposes SetHitpoints(GUIDSTRING, INTEGER, STRING)
and SetHitpointsPercentage(GUIDSTRING, REAL, STRING). The absolute setter's
exact wounded-migration behavior must be proved locally before it becomes a
production dependency. No reapplication or healing-on-load workaround is allowed.

## Alternatives considered

1. Full exact catalog (selected): preserves all existing supported integer
   amounts using the proven status mechanism; carries build/load/memory cost
   that must be measured before production wiring.
2. Smaller catalog with binary fallback: lower cost but not one contribution
   for every supported new bonus; not selected by the user.
3. Direct dynamically constructed boost: fewer definitions, but the tested
   version failed persistence and attribution; not selected.

## Catalog and selection

Generate definitions deterministically for integers 1..65,535:

- ID and StackId: `AESN_HP_TOTAL_<decimal>` (no leading zero padding).
- Type: StatusData; StatusType: BOOST.
- DisplayName: `AESNHpSourceName;1` (existing localization).
- Boosts: exactly one `IncreaseMaxHP(N);`, with N matching the ID.
- StatusPropertyFlags: DisableOverhead;DisableCombatlog;DisablePortraitIndicator.
- No inherited boosts, damage, action resources, or duration/removal conditions.

Retain legacy AESN_HP_BIT definitions for decoding/removing existing saves.
Use a generator plus exhaustive artifact validation; do not hand-maintain the
catalog. Runtime selection constructs one ID from a validated delta instead
of adding 65,535 Story database rows or scanning every possible status.
Zero remains status-free. A missing or failed status must fail the transaction,
not silently select another amount.

Only one total status is committed for a given enemy/owner. Distinct IDs use
distinct StackIds; sequencing and acknowledgement enforce exclusivity during
replacement rather than assuming StackId collisions safely implement migration.

## Gate 1: catalog qualification before production integration

Implement and test the deterministic catalog generator first. Keep its output
outside production staging by default until qualification. Test complete ID
coverage, no duplicates, exact values, label resolution, no zero entry,
determinism, invalid arguments and no modifications of legacy status content.

Prepare explicit baseline and catalog qualification packages with unchanged
production Story logic. Disable/exclude old throwaway fixture goals except for
the explicitly selected qualification harness. Back up staged/installed files;
preserve module UUID and the original mod.io identity. Do not copy stale repo
metadata over current Toolkit metadata. The user performs Toolkit build,
Publish Local and retail launch. Never Publish online at this stage.

Compare same-machine, same-save baseline and catalog conditions: build result,
stats-load errors, time to controllable save, working-set/commit observations,
and stability. Run three comparable loads per condition and report medians;
do not call one cold run and one warm run a valid performance comparison.
Investigate an added median load time above max(2 seconds, 20% of baseline)
or an added steady game working set above 256 MiB. A crash, unresolved status,
or build/load error blocks integration. Performance figures are diagnostic
budgets, not permission to silently reduce the supported delta range. If a
budget is exceeded, present measured costs to the user before proceeding.

In the isolated fixture verify amounts 1, 111, 32768 and 65535, plus status-free
zero selection. Check exact maximums, named contribution, save/load retention
and removal. Keep these saves separate from the campaign. Catalog acceptance
must be recorded before migrating or applying totals to production enemies.

## HP ownership and transaction integration after Gate 1

Keep policy schema 2 and the existing combat/world ownership separation.
Use HP representation version 2 for new transactions; retain explicit readers
and cleanup paths for legacy HP version 1. Do not globally reinterpret old
bit-value facts as new total statuses or remove legacy definitions.

New ownership facts track (owner, enemy, delta, exactStatusId) independently
of legacy DB_AESN_EnemyHpBit. Application records pending intent before the
native ApplyStatus call, waits for acknowledgement, verifies the live maximum,
then commits ownership and restores wounded percentage under the same policy
rules as today. Zero commits without an HP status or unnecessary HP write.
Timeouts and failed attempts cannot create a success record; reconcile any
late status acknowledgement against saved intent before further mutation.

Cleanup removes only the recorded AES status and preserves unrelated sources.
World replanning and combat merging transfer both representation/version and
ownership facts. They must never attach a second HP owner to the same enemy.
Fully committed valid version-2 saves are observation-only on reload: no
reapplication, healing or recalculation merely because the game loaded.

## Legacy-save conversion

Convert only validated, fully committed legacy HP records. Do not infer
ownership from an HP difference or a shared display label. Confirm each
recorded bit is present, its sum equals the stored delta, and live maximum
matches the stored target. Inconsistent or interrupted pre-existing records
use their exact legacy recovery path instead of blind conversion.

Defer conversion while the NPC is in combat, while a merge/replan/cleanup is
pending, or while the NPC is dead. Existing valid effects remain intact during
that deferral; consequently an old active-combat save can temporarily retain
multiple tooltip rows. New eligible targets use the new representation once
production integration is enabled. Recheck deferred living targets when out
of combat, including sticky world-tracked targets outside discovery range.

At a safe conversion point, acquire an enemy-level mutation hold and capture
live current HP, maximum HP, exact legacy set and delta in a durable migration
journal. Preserve the frozen target; do not change tiers or Relentless facts.
Remove only the recorded old HP statuses with acknowledgements, then apply the
matching total status and verify the original maximum. Restore exact captured
current HP once, verify it, and only then commit new ownership and release the
hold. This must not turn wounded NPCs into full-health NPCs or revive a dead NPC.

Conversion occurs while the NPC is out of combat; if combat begins, another
mutation intervenes, or the NPC dies during conversion, stop advancement and
reconcile the recorded transition. Never overwrite intervening damage with an
old HP snapshot. Migration eligibility is rechecked before each mutation.

The durable journal distinguishes pending and acknowledged removals, pending
application, verification and commit. Interrupted saves are not treated as
fresh legacy or committed v2 saves. On reload, compare exact journal-owned
statuses and live HP to the recorded checkpoint. Resume or roll back only a
validated checkpoint. Ambiguous state fails closed with diagnostic evidence,
not guessed healing, broad removal or duplicate application. A failed normal
conversion should restore the recorded legacy representation when that can
be verified safely; uncertain recovery remains blocked and visible in logs.

## Required regression and retail checks

- Exhaustive catalog coverage, exact ID/value/label mapping and generation.
- New application for zero, 1, 111, 32768, 65535; invalid/overflow rejection.
- Full and wounded HP behavior; death during application/conversion.
- Legacy one-bit and many-bit conversion, including Nere's +111.
- Same current/maximum before and after representation-only conversion.
- Deferred conversion in combat; retry after combat; no Relentless reallocation.
- Unrelated HP status survives application, conversion and exact cleanup.
- Party/level changes and world retention beyond discovery range.
- Combat merge/owner transfer with mixed legacy and new actors.
- Duplicate, failed and late status acknowledgements; apply/remove timeouts.
- Save/reload at each mutation checkpoint and repeated committed reloads.
- No test spawn code or proof statuses in the final production package.

Automated tests exercise real Story rules and generated artifacts but do not
substitute for native status scheduling/rounding or GUI tests. Retail proof
requires save facts plus screenshots, not an endpoint HP screenshot alone.

## Files and delivery boundaries

Expected additions: catalog generator and tests; generated catalog; isolated
catalog/migration qualification fixtures; a focused HP conversion goal and
regression fixtures. Production integration touches HP planning/application,
merge fact transfer, reconciliation and world mutation holds, with targeted
model/identity/staging tests. Keep unrelated dirty worktree changes intact.

Remove the temporary kobold harness and its two +111 proof definitions from
final staging. Keep proof sources/evidence separately for reproducibility.
Backups, save extracts and transient tooling stay on B: under ignored paths.
No automatic commit, merge, push, online publication, duplicate mod listing or
load-order change is included in this design. Normal play must use the restored
production package and an untouched campaign save, not a proof save.

## Approval and execution boundary

This written design is the review artifact. After approval, create the
implementation plan and execute catalog qualification first. Stop at its
user-run Toolkit/retail gate before production HP migration. Catalog success
does not waive the later wounded/migration and production smoke-test gates.
