# MERGE-01 Equal-Policy Production Merge

## Result

**Verified locally — equal-policy combat ownership migrates to the native survivor and discarded-combat cleanup is suppressed.**

- Date: 2026-08-31
- Toolkit: `4.1.1.6931813`
- Trace: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\osirislog.2026-08-31T21-28-43-219244.log` (`4,519,010` bytes when inspected)
- Commands: `oe AESN_TEST_START_MERGE_PROBE`, `oe AESN_TEST_TRIGGER_MERGE_PROBE`, `oe AESN_TEST_RESET_MERGE_PROBE`
- Discarded combat: `d6729e4c-24ae-61dc-e81d-54e619d20aa7`
- Surviving combat: `d308797c-57b8-1899-304d-602fbc69e733`

The ordinary-combat fixture captured two distinct native combat IDs. When spatial convergence produced the first `SwitchedCombat`, the production merge goal created the discarded-to-survivor marker and alias before migrating the combat-owned snapshot and bookkeeping. Both source snapshots were equal, so the production path retained the surviving policy and did not schedule canonical reconciliation:

```text
DB_AESN_MergedCombat(discarded, surviving) [add fact]
DB_AESN_CombatAlias(discarded, surviving) [add fact]
AESN_MERGE POLICY_EQUAL canonicalReplan=0
AESN_MERGE MIGRATION_COMPLETE markBeforeMigrate=1
CombatEnded(discarded)
AESN_MERGE CLEANUP_SUPPRESSED discardedOwner=1
AESN_MERGE_EQUAL PASS ownershipMigrated=1,discardedCleanupSuppressed=1,canonicalReplan=0
```

The discarded snapshot was absent and the surviving snapshot remained present at the RT-17 assertion. There was no `DB_AESN_MergePolicyMismatch` addition, no `DB_AESN_MergeReplanRequired` addition, no merge failure, and no HP failure. The trace contained exactly one runtime add and one final delete for both `DB_AESN_MergedCombat` and `DB_AESN_CombatAlias`; the apparent extra occurrence for each was only its INITSECTION null-row database declaration.

The alias and merged marker survived the discarded combat's end. They were deleted only after `CombatEnded(surviving)`, which emitted:

```text
AESN_MERGE FINAL_CLEANUP survivingOwner=1
```

This verifies RT-17 for the equal-policy ordinary-combat fixture: ownership migrates once, the discarded end cannot clean the survivor, and final-owner cleanup retires the alias. It does not verify mismatched-policy canonical reconciliation or multi-hop alias chains; those remain RT-18 and RT-19.
