# STAT-01 One-Tier Status Primitive

## Result

**Verified locally — exact resource definition, runtime ownership, and cleanup.**

- Date: 2026-08-31
- Toolkit: `4.1.1.6931813`
- Trace: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\osirislog.2026-08-31T19-02-26-991053.log` (`2,963,379` bytes when inspected)
- Commands: `oe AESN_TEST_SPAWN_AND_APPLY_STAT_TIER`, then `oe AESN_TEST_REMOVE_SPAWNED_STAT_TIER`
- Target: `Kobolds_Melee_Drunk_482aa32a-4369-cdb6-c39c-8010657008be`

The independently authored `AESN_TIER_LEVEL_05_08` Stats resource contains exactly:

```text
RollBonus(Attack,1);RollBonus(SavingThrow,1);AC(1);SpellSaveDC(1);
```

The isolated Story harness created an inert target, applied only that fork-owned status, received `StatusApplied`, and observed `HasActiveStatus(...)=1`. It then removed exactly the same status, received `StatusRemoved`, and observed `HasActiveStatus(...)=0`. The trace emitted both strict success records:

```text
AESN_STAT_TIER APPLY attack=1,saves=1,ac=1,spellDC=1,statusOwned=1
AESN_STAT_TIER REMOVE attack=1,saves=1,ac=1,spellDC=1,statusOwned=1
```

No HP bit, Action, or Bonus Action status is referenced by the harness. This proves that the one-tier resource parses, applies, remains queryable, and is exactly reversible at runtime. Osiris exposes no direct query for all four derived numeric totals, so the claim combines the exact loaded Stats definition with native status acknowledgements and active-state observations; it does not claim direct before/after measurement of those totals.

RT-08 remains open because this isolated primitive does not yet prove hostile-target selection or integrated combat cleanup.
