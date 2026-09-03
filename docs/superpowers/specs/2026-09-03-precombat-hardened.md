# Precombat Hardened Specification

## Outcome

Adaptive Enemy Scaling applies its real Hardened HP and combat-stat statuses to nearby active hostile enemies before initiative. Relentless remains combat-scoped and is allocated only after native combat membership is known.

## Policy ownership

- Preserve the released schema-2 party policy matrix and Relentless budgets.
- Maintain one durable world-policy owner with its own schema-2 roster snapshot.
- Store precombat Hardened HP bits and the Hardened tier status under that world owner using the existing acknowledged transaction engine.
- Treat a fully committed world Hardened transaction as satisfying a combat enemy's Hardened prerequisite. Never start a second combat-owned HP transaction for that enemy.
- A combat-owned transaction remains the fallback for an enemy first discovered by `EnteredCombat`, including hidden or offstage entrants.

## Candidate rules

A precombat candidate must be a living character within 100 metres of an eligible permanent party member and must be active, on stage, not invisible, hostile to at least one eligible party member, outside combat, and not a party member. Active/onstage state is the render-range proxy; neither NPC perception nor line of sight is required.

Candidates are discovered every three seconds. `WentOnStage`, permanent-party join/leave, level-up, respec, faction/relation changes, temporary-hostility changes, gameplay start, save load, and leaving combat request an earlier scan or policy refresh as applicable. These are discovery-only gates: a completed tracked package remains committed after range, visibility, stage, or hostility changes. Party-policy changes replan all tracked targets from the full permanent roster. Invalid or failed transactions still use the existing acknowledged component-first and HP-second cleanup path.

## Dynamic refresh

- Rebuild the durable world snapshot when the permanent roster or its levels change.
- If the Hardened tier or target HP percentage changes, replan every committed world-owned enemy that is not in combat.
- Defer replanning for an enemy in combat until `LeftCombat` or the surviving `CombatEnded` path releases it.
- During every eligible scan, compare the observed maximum HP with the transaction's recorded target. A mismatch indicates an external HP change and queues an exact replan outside combat.
- Replanning must remove only AES-owned HP bits, derive `externalBase = observedMaximum - ownedAppliedSum`, calculate `target = floor(externalBase * targetHpPercent / 100)`, and restore the captured HP percentage after the new exact bit set commits.

## Combat lifecycle

- Combat snapshots remain immutable and continue to own Relentless budgets.
- Relentless may start after either a combat-owned Hardened transaction or a world-owned Hardened transaction is fully committed.
- World-owned Hardened statuses remain applied during and after combat.
- Combat cleanup removes combat-owned Hardened fallbacks and all Relentless state. It must also clean Relentless-only component records for enemies whose Hardened owner is the world context.
- Combat merging continues to migrate combat-owned fallback and Relentless state. World-owned Hardened state is not re-owned during a merge.

## Save/load and compatibility

- Existing schema-2 combat transactions keep their current behavior and reconcile normally.
- A valid world-owned committed transaction is retained on save load even though the world owner is not an active combat GUID.
- Invalid or partial world transactions use the same exact rollback/cleanup machinery as combat transactions.
- No third-party code, identifiers, localization, assets, or UUIDs are copied.

## Runtime proof gate

The local current `story_header.div` and installed Toolkit verify the required call/event signatures. Production release remains blocked until an isolated Toolkit compile and in-game acceptance test confirm the world scan, precombat status application, combat handoff, deferred refresh, external-HP replan, cleanup, and save/load retention.
