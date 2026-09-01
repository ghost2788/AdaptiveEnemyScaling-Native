# ACTION-01 Additive Action-Resource Status Spike

## Result

**Verified locally — exact fork-owned status application and cleanup.**

- Date: 2026-08-31
- Toolkit: `4.1.1.6931813`
- Trace: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\osirislog.2026-08-31T17-24-35-595513.log` (`2,944,756` bytes when inspected)
- Fixture: managed host Shadowheart
- Commands: `oe AESN_TEST_APPLY_ACTION_PAIR`, then `oe AESN_TEST_REMOVE_ACTION_PAIR`

The apply transaction first proved both fork-owned statuses inactive, then called only:

```text
ApplyStatus(...,"AESN_EXTRA_ACTION_1",...)
ApplyStatus(...,"AESN_EXTRA_BONUS_ACTION_1",...)
```

Native Story emitted distinct `StatusApplied` events for both. `HasActiveStatus` returned `1` for each before `DB_AESN_ActionPairApplied` was committed. The apply-side diagnostic `DebugLog` returned a non-fatal call failure; the status events, active queries, and committed transaction fact are the authoritative evidence.

Cleanup called `RemoveStatus` for exactly the same two identifiers. Native Story emitted distinct `StatusRemoved` events, both active queries returned `0`, and the harness removed its target/application facts once. No total ActionPoint or BonusActionPoint normalization call occurred, and no reaction, Legendary Action, class resource, Action Surge-like ability, or boss resource was touched.

This proves additive status ownership and reversible application. It does not claim exact total resource normalization or a combat-turn refresh policy.
