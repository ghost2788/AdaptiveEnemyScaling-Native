# MERGE-02 Mismatched-Policy Production Reconciliation

## Result

**Verified locally — mismatched combat snapshots select independent canonical maxima and reconcile every tracked enemy exactly once.**

- Date: 2026-08-31
- Toolkit: `4.1.1.6931813`
- Accepted trace: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\osirislog.2026-08-31T23-46-06-963432.log` (`5,979,661` bytes when inspected)
- Commands: `oe AESN_TEST_START_MERGE_PROBE`, `oe AESN_TEST_PREPARE_MISMATCH_MERGE`, `oe AESN_TEST_TRIGGER_MERGE_PROBE`, `oe AESN_TEST_RESET_MERGE_PROBE`
- Discarded combat: `67696fca-e784-52ef-4c84-ea2dd04e7323`
- Surviving combat: `19768822-8d1d-45f7-7c51-7cf35f6add8d`
- Reconciled enemies: `f89074d2-bbe2-8070-d18f-e9222aa7d520`, `1416a7d7-1f8c-1518-b8f6-a689b21a2f9a`

The harness seeded opposing policy dimensions only: discarded source `average=7,size=1` and surviving source `average=5,size=3`. It then called the production planner for one real `12/12` target under each source. Preparation committed the size-1 target at `13/13` with exact bit `1` and Stat only, and the size-3 target at `19/19` with bits `4|2|1` plus Stat, additive Action, and additive Bonus Action.

The native merge produced exactly one production mismatch record:

```text
DB_AESN_MergePolicyMismatch(discarded, surviving, 7, 1, 5, 3, 7, 3)
AESN_MERGE POLICY_MISMATCH canonicalIndependentMaxima=1
DB_AESN_CombatSnapshot(surviving, 1, 3, 21, 7, 115, 140, "Supported")
AESN_MERGE MIGRATION_COMPLETE markBeforeMigrate=1
```

Production queued exactly two enemies. Each old component set and HP bit set was removed through native acknowledgements, each new plan logged zero percentage writes before application, and each completed with one percentage restoration:

```text
AESN_MERGE REPLAN_NEW_PLAN percentageWrite=0  # twice
AESN_MERGE REPLAN_COMPLETE percentageWrite=1 # twice
AESN_MERGE_MISMATCH PASS canonicalAverage=7,canonicalSize=3,reconciledEnemies=2,percentageWrites=1|1
```

The trace contains exactly two `PROC_AESN_ReplanEnemy` calls. There were two initial percentage writes, exactly two writes between trigger and reset for canonical reconciliation, and exactly two writes after reset for cleanup. Both reconciled transactions were `12/12 -> 19/19`, recorded bits `4|2|1`, and owned Stat/Action/Bonus components. There was one harness PASS, zero mismatch FAIL, zero merge-probe FAIL, zero fork-status `StatusAttemptFailed`, and zero runtime `DB_AESN_HpFailure` additions.

Reset removed both component sets and both HP bit sets through exact acknowledgements, deleted the runtime mismatch diagnostic and alias only during final cleanup, and emitted one exact reset pass. The extra `AESN_MERGE FINAL_CLEANUP` log after the reset pass belongs to the separately ending discarded bookkeeping key and had no remaining owned transaction or alias.

## Rejected diagnostic runs

- `osirislog.2026-08-31T21-37-07-901318.log` is rejected. Deleting the old `DB_AESN_HpReplan` state before adding the next state exposed a synchronous no-guard gap, recursively restarted the replan, and crashed the editor. Production now inserts the next state before deleting the old one and clears the replan request before its guard.
- `osirislog.2026-08-31T23-41-29-830646.log` is rejected as evidence. Production reconciled exactly twice, but the assertion harness restarted its timer after deleting a pending row and emitted repeated PASS/FAIL records. A persistent `DB_AESN_MergeMismatchVerifyStarted` guard made the accepted run one-shot.

This verifies RT-18 in the isolated ordinary-combat fixture. It does not verify multi-hop alias flattening or save/load reconciliation; those remain RT-19 through RT-22.
