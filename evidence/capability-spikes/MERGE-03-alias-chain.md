# MERGE-03 Native Alias Chain

## Result

**Verified locally — a two-hop native merge chain flattens every discarded owner directly to the final survivor and cleans only when that final combat ends.**

- Date: 2026-08-31
- Toolkit: `4.1.1.6931813`
- Trace: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\osirislog.2026-08-31T23-54-27-440003.log` (`6,205,893` bytes when inspected)
- Commands: `oe AESN_TEST_START_MERGE_PROBE`, `oe AESN_TEST_TRIGGER_MERGE_PROBE`, `oe AESN_TEST_START_CHAIN_EXTENSION`, `oe AESN_TEST_TRIGGER_CHAIN_EXTENSION`, `oe AESN_TEST_RESET_MERGE_PROBE`
- First discarded combat: `d3f88b9f-79a8-623c-8e8b-9071e83f61ea`
- Intermediate survivor / second discarded combat: `3c5d7a6c-52d0-c942-5ce9-fa549520622b`
- Final surviving combat: `656e2b0c-e42d-6b1f-00d0-fe1563a6ddfd`

The first two-pair fixture merged into the intermediate owner and completed RT-17. The chain extension then created a third spatially distinct ordinary combat and converged the four existing participants onto it. The engine emitted two `SwitchedCombat` events for the first merge and four for the second merge. Production executed exactly two merge transactions and both policies were equal.

On the second merge, production first created the intermediate-to-final alias, then rewrote the existing first-to-intermediate alias and merged marker directly to the final owner:

```text
DB_AESN_CombatAlias(first, intermediate) [delete fact]
DB_AESN_CombatAlias(first, final) [add fact]
DB_AESN_MergedCombat(first, intermediate) [delete fact]
DB_AESN_MergedCombat(first, final) [add fact]
AESN_MERGE MIGRATION_COMPLETE markBeforeMigrate=1
```

At the chain assertion, both direct ownership rows existed:

```text
DB_AESN_CombatAlias(first, final)
DB_AESN_CombatAlias(intermediate, final)
NOT DB_AESN_CombatAlias(_, intermediate)
AESN_MERGE_CHAIN PASS aliasesFlattened=2,discardedCleanupSuppressed=2,finalCleanupOwner=1
```

`CombatEnded(first)` and `CombatEnded(intermediate)` each emitted exactly one `AESN_MERGE CLEANUP_SUPPRESSED discardedOwner=1`. Neither removed the surviving snapshot or aliases. `CombatEnded(final)` later removed both direct aliases and both merged markers before emitting `AESN_MERGE FINAL_CLEANUP survivingOwner=1`. A later final-cleanup log belongs to an unrelated combat ID, not any of the three chain combat IDs.

The accepted trace contains one chain PASS, zero chain FAIL, zero merge-probe FAIL, zero runtime HP failures, one exact reset pass, and no reset failure. The harness created and moved actors but never called `PROC_AESN_MergeCombat` or `PROC_AESN_FlattenCombatAliases`; all ownership behavior came from the production `SwitchedCombat` path.

This verifies RT-19 for a three-combat ordinary chain. Save/load reconciliation remains RT-20 through RT-22.
