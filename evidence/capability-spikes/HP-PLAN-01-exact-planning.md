# HP-PLAN-01 Exact Persisted Planning

## Result

**Verified locally — one captured target and exact desired-bit registry without mutation.**

- Date: 2026-08-31
- Toolkit: `4.1.1.6931813`
- Trace: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\osirislog.2026-08-31T20-26-55-377837.log` (`3,236,455` bytes when inspected)
- Commands: `oe AESN_TEST_PLAN_SUPPORTED_HP`, then `oe AESN_TEST_RESET_SUPPORTED_HP_PLAN`
- Target / synthetic combat key: `cc0ef7c2-e9fa-0c17-85de-c4620bc7bc50`

The disposable native target initialized at `12/12`, `100%`. The harness supplied only a version-1 supported snapshot representing eligible size `3`, level sum `18`, average level `6`, level percent `115`, and party percent `140`, then called production `PROC_AESN_PlanEnemy`.

Production persisted exactly:

```text
DB_AESN_HpTransaction(...,1,"Planned",12,12,100.0,19,7,0)
DB_AESN_HpDesiredBit(...,4,"AESN_HP_BIT_00004")
DB_AESN_HpDesiredBit(...,2,"AESN_HP_BIT_00002")
DB_AESN_HpDesiredBit(...,1,"AESN_HP_BIT_00001")
```

No other desired-bit row was present. The verification gate re-read current and maximum HP as `12/12` and emitted:

```text
AESN_HP_PLAN_HARNESS PASS base=12,target=19,delta=7,bits=4|2|1,mutation=0
```

Reset deleted the transaction, all three desired-bit rows, plan-queued marker, and synthetic snapshot before staging off the target.

The earlier native narrative-combat trace `osirislog.2026-08-31T20-22-11-364434.log` separately verified that two level-1/unsupported enemies each recorded `UnsupportedPolicy` and created zero transactions or desired bits.

This proves deterministic versioned planning, exact 16-bit decomposition at runtime for delta `7`, unsupported-policy failure closure, and a strict plan-before-mutation boundary. It does not yet prove acknowledgement-driven application, rollback, cleanup, or save/load persistence.
