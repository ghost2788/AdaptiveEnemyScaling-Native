# CAP-06: Save/load persistence proof

## Classification

- Versioned Osiris database records for a fully committed application surviving a mid-combat retail-game save/load: **Verified locally**.
- Performing that proof inside Toolkit Editor Game Mode: **Rejected**.
- Active pending-transaction persistence and rollback through the production reconciler: **Verified locally** in both a focused editor fixture and a separately approved retail mid-combat save/load.
- Stale inactive-combat detection and exact production cleanup: **Verified locally**.

## Local and official evidence

The installed Patch 8 Story headers expose `SavegameLoadStarted`, `SavegameLoaded`, `GameModeStarted`, and `CombatIsActive`. Vanilla Story uses the load lifecycle events for save patching and safety cleanup. This verifies that the native APIs exist, but it does not prove that AESN's versioned snapshot, application, bit, component, and transaction facts persist with the required identities.

Larian's current Editor navigation guide warns users not to load a savegame while in Editor Game Mode because doing so can leave the Toolkit requiring a force-quit and restart:

<https://docs.baldursgate3.game/Editor%3A_Navigation#Testing_While_Playing_in_the_Editor>

The isolated editor project therefore could not safely provide the required acceptance test. After explicit user approval, a temporary retail-game activation was staged with exact preflight backups and a disposable non-Honour save.

## Verified retail-game result

On 2026-09-01, Patch 8 retail game version `4.1.1.7398727` loaded a disposable three-member, average-level-3 non-Honour save. Because no safe non-Honour level-5-to-8 save existed, the test package temporarily widened only the lower supported-policy boundary from level 5 to level 3. The production source boundary was restored to level 5 immediately after evidence capture; this was fixture setup, not a production balance decision.

The observation-only CAP-06 goal armed only after it saw schema 1, a supported snapshot, `HPCommitted`, `FullyCommitted`, target maximum equal to the live maximum, and applied-bit sum equal to the recorded delta. After saving and loading through the normal game UI, its delayed verifier found the active combat and all persisted records, confirmed every recorded bit and component status was active, rejected any known unrecorded fork-owned status, confirmed the same target/delta/applied sum and maximum, and emitted:

`AESN_CAP06 RELOAD_PASS schema=1,transaction=HPCommitted,maximumUnchanged=1,doubleApply=0`

The user observed the matching `AESN CAP-06 reload proof PASSED` notification. The committed save has SHA-256 `4EB219C24F6DBBA13325EED14EE1758F85C9EB064519623AB8DCDFCC56D629A4`. Independent extraction of its level cache confirmed persistent `AESN_HP_BIT_00004`, `AESN_HP_BIT_00002`, `AESN_HP_BIT_00001`, `AESN_TIER_LEVEL_05_08`, `AESN_EXTRA_ACTION_1`, and `AESN_EXTRA_BONUS_ACTION_1` status instances. The original QuickSave and all Honour-save names and timestamps remained unchanged.

## Verified retail pending-transaction result

On the same retail version, a second separately approved package used a dormant one-shot probe ordered before HP planning. For the first eligible hostile, it installed only `DB_AESN_HpApplicationHold`; production then created a real schema-1 `Planned` transaction with zero applied bits and left the enemy at its captured current and maximum HP. The player observed `AESN CAP-06 pending armed: save, then reload during this combat`, created a new manual save while combat remained active, and loaded that save through the normal UI.

After `SavegameLoaded`, the probe waited for production reconciliation and required `DB_AESN_ReconcileResult(..., "ROLLED_BACK", "PendingApplication")`, no transaction, hold, plan queue, recorded bit, or recorded component, no active fork-owned HP/stat/action/bonus status on the held enemy, and the exact captured current and maximum HP. It then emitted:

`AESN_CAP06_PENDING RELOAD_PASS state=ROLLED_BACK,appliedBits=0,percentageWrites=0,doubleApply=0`

The user observed the distinct `AESN CAP-06 pending reload proof PASSED` notification. The pre-reload pending save has SHA-256 `DD7C5D5984886F2EA7A44699177588A3FB5DCAC0A3180DA2CFCB638AEC6398F6`; the screenshot has SHA-256 `F6BF3B5E276F815A139EF0B8CB887F52E1E7688394A3D055718BFC76F1E52299`; and the temporary package has SHA-256 `A404B0A75BB10D21CA9129850557B6956E7AECEBED8437B88AE4DBED78D5CEF0`. The package and disposable save were moved to ignored `B:` evidence storage after the test. The live Mods manifest and `modsettings.lsx` then matched the fresh pre-test manifest exactly, and both temporary Toolkit goals were restored to hashes matching tracked production source.

## Focused production-reconciliation results

The compiled `AESN_88_ReconciliationHarness` supplied only schema-1 facts and real narrative-combat lifecycle state. It did not apply or remove a status, write HP, or call production cleanup/rollback procedures directly.

For the active pending case, the harness injected a `Planned` transaction with applied sum zero under `DB_AESN_HpApplicationHold`, then called only `PROC_AESN_OpenCombatReconciliation`. Production observed the combat as active, normalized the state to `ApplyingHP`, rolled it back with zero applied bits and zero percentage writes, deleted the transaction and hold, and emitted:

`AESN_RECONCILE_HARNESS PENDING_PASS action=rollback,appliedBits=0,percentageWrites=0,doubleApply=0`

For the stale case, the corrected harness started and ended a real narrative combat, waited for native `CombatEnded`, then injected a schema-1 committed zero-delta record against that discarded combat. The accepted trace returned `CombatIsActive(...,0)`, emitted exactly one `AESN_HP CLEANUP maximumVerified=1,percentageWrite=1,exactRecordedBits=1`, retired the transaction, snapshot, component-start guard, hold, and reconciliation result, and emitted:

`AESN_RECONCILE_HARNESS STALE_PASS action=cleanup,percentageWrites=1,exactOwnedBits=1`

The bounded stale segment contains one PASS, zero FAIL, one inactive-combat query, one exact cleanup, zero AESN `ApplyStatus` calls, and zero AESN `StatusAttemptFailed` events. Accepted trace: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\osirislog.2026-09-01T01-20-11-810456.log`, length `3,079,381`, SHA-256 `E3BB7C82D6B1074CD7164D769641D08E552B9EE80ABCDDD0F98E9F1C1633CB27`.

## Closure

The combined results close committed-state persistence, committed duplicate prevention, retail pending-state persistence and exact rollback, and stale inactive cleanup for the version-1 POC transaction model.
