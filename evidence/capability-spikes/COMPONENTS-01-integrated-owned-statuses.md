# COMPONENTS-01 Integrated Owned Statuses

## Result

**Verified locally — guarded component commit and exact cleanup.**

- Date: 2026-08-31
- Toolkit: `4.1.1.6931813`
- Trace: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\osirislog.2026-08-31T20-49-24-19059.log` (`3,344,701` bytes when inspected)
- Commands: `oe AESN_TEST_APPLY_SUPPORTED_HP`, then `oe AESN_TEST_CLEANUP_SUPPORTED_HP`
- Target / synthetic combat key: `61bbb8a2-38e0-c113-4e16-734c9806298f`

The production transaction captured `12/12` at `100%`, planned target `19` and delta `7`, applied exact HP bits `4|2|1`, and reached `HPCommitted`. That commit started one guarded component chain. Native acknowledgement advanced it through exactly one stat tier, one additive Action status, and one additive Bonus Action status:

```text
DB_AESN_ComponentStarted(...) [add fact]
AESN_COMPONENTS COMMIT stat=1,action=1,bonus=1,additiveOnly=1
AESN_HP_APPLY_HARNESS PASS before=12/12,target=19/19,percentage=100,bits=4|2|1,stat=1,action=1,bonus=1,appliedSum=7
```

Each of `AESN_TIER_LEVEL_05_08`, `AESN_EXTRA_ACTION_1`, and `AESN_EXTRA_BONUS_ACTION_1` produced one `StatusApplied` event and one exact `DB_AESN_EnemyComponent` ownership row. The persistent `DB_AESN_ComponentStarted` guard prevented the delete/add state-transition gap from starting a second chain.

Cleanup removed only recorded component statuses, in `Bonus -> Action -> Stat` order, before re-dispatching to exact HP cleanup. The HP layer then removed only recorded bits `4|2|1`, restored the cleanup-time percentage once, and deleted the persistent component guard with the transaction records:

```text
AESN_COMPONENTS CLEANUP exactOwnedStatuses=1
AESN_HP_APPLY_HARNESS CLEANUP_PASS restored=12/12,percentage=100,exactBitsRemoved=4|2|1,stat=0,action=0,bonus=0
```

There was exactly one component start, one component commit, one component cleanup, one apply harness pass, and one cleanup harness pass. No `ComponentStatusAttemptFailed` or `DB_AESN_HpFailure` addition occurred. The post-run live Mods and `modsettings.lsx` manifest matched the pre-build baseline exactly.

This verifies the integrated synthetic supported-policy path. It does not yet prove a full ordinary hostile encounter, save/load reconciliation, combat merging, or host/client replication.
