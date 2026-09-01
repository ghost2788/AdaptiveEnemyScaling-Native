# HP-TXN-01 Acknowledged Exact HP Transaction

## Result

**Verified locally — sequential apply, one percentage restore, and exact cleanup.**

- Date: 2026-08-31
- Toolkit: `4.1.1.6931813`
- Trace: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\osirislog.2026-08-31T20-33-01-478537.log` (`3,278,010` bytes when inspected)
- Commands: `oe AESN_TEST_APPLY_SUPPORTED_HP`, then `oe AESN_TEST_CLEANUP_SUPPORTED_HP`
- Target / synthetic combat key: `4d6308a2-a5e4-2143-a2c6-644ca37120d6`

Production captured `12/12` at `100%`, planned target `19` and delta `7`, then requested only one desired status at a time. Native acknowledgements arrived in exact order `4`, `2`, `1`; each acknowledgement created one `DB_AESN_EnemyHpBit` row and advanced the persisted applied sum `0 -> 4 -> 6 -> 7`.

After the final acknowledgement, production verified maximum `19`, restored the captured percentage once, and persisted:

```text
DB_AESN_HpTransaction(...,1,"HPCommitted",12,12,100.0,19,7,7)
AESN_HP_APPLY_HARNESS PASS before=12/12,target=19/19,percentage=100,bits=4|2|1,appliedSum=7
```

Cleanup captured the then-current `19/19`, `100%` state once. It removed only the three recorded statuses, waited for native removal acknowledgement after each one, deleted the corresponding ownership row, verified maximum `12`, and restored the cleanup percentage once:

```text
AESN_HP CLEANUP maximumVerified=1,percentageWrite=1,exactRecordedBits=1
AESN_HP_APPLY_HARNESS CLEANUP_PASS restored=12/12,percentage=100,exactBitsRemoved=4|2|1
```

No transaction, desired-bit, plan marker, applied-bit, pending-operation, or cleanup row remained. Rollback and timeout branches compile and are statically covered but have not yet been forced at runtime. Dead-after-application and damaged cleanup also remain open.
