# CAP-07 Native Merge Ordering

## Result

**Verified locally — native combat switching marks the discarded owner before its combat-end event.**

- Date: 2026-08-31
- Toolkit: `4.1.1.6931813`
- Trace: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\osirislog.2026-08-31T21-15-57-853026.log` (`4,652,431` bytes when inspected)
- Commands: `oe AESN_TEST_START_MERGE_PROBE`, `oe AESN_TEST_TRIGGER_MERGE_PROBE`, `oe AESN_TEST_RESET_MERGE_PROBE`
- Discarded combat: `55e41344-3bd7-1f37-ac3f-1a32f16b91ef`
- Surviving combat: `398f5e5c-1680-034d-1807-b815d7fa8e0b`

The harness created two spatially separated ordinary combats, each with two disposable actors. All four remained combat-capable and received temporary vanilla invulnerability only after two distinct native combat IDs were captured. Moving the old pair beside the new pair caused the engine to merge the combats before the delayed explicit join request was needed.

The native sequence was:

```text
AESN_MERGE_PROBE SETUP_PASS distinctOrdinaryCombats=1
SwitchedCombat(first old actor, discarded, surviving)
DB_AESN_MergeProbeMarked(discarded, surviving)
AESN_MERGE_PROBE EVENT firstSwitched=1,markedBeforeMigration=1
SwitchedCombat(second old actor, discarded, surviving)
AESN_MERGE_PROBE EVENT additionalSwitched=1
CombatEnded(discarded)
AESN_MERGE_PROBE EVENT discardedCombatEndedAfterMarker=1
AESN_MERGE_PROBE PASS switchedObserved=1,markedFirst=1,discardedEndedAfterMarker=1
```

There was no merge-probe failure record. Each original combat scheduled and completed one `AESN_COMBAT_DISPATCH_*` timer; no recurring or trailing dispatch loop occurred. Reset removed the temporary invulnerability, cleared the relation overrides, removed all four actors from the surviving combat, retired both recorded source combats, cleared fixture facts, and emitted one exact reset record.

An earlier run was invalid because `SetCanFight(...,0)` immediately emitted `LeftCombat` for all four actors and ended both source combats. That guard was replaced with `PROC_SetInvulnerable(...,1)` and exact reset removal before this accepted run. Narrative reassignment and direct cross-combat `EnterCombat` fixtures were separately rejected because they did not emit `SwitchedCombat`.

This proves the event-order dependency required for mark-before-migrate ownership and discarded-combat cleanup suppression. It does not by itself prove production record migration, canonical mismatch reconciliation, alias chains, or final-owner cleanup; those remain RT-17 through RT-19.
