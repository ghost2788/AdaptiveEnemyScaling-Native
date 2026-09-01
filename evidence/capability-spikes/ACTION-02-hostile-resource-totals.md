# ACTION-02: Hostile Action-resource totals

## Result

**Verified locally** on 2026-09-01 with Baldur's Gate 3 Toolkit `4.1.1.6931813`.

## Evidence boundary

The proof deliberately separates candidate selection from resource mutation:

- The production narrative-hostile trace established that a real `DB_AESN_EnemyEligible` hostile reports the normal `1 Action / 1 Bonus Action` personal pools at the production allocation point.
- The accepted resource trace used an ordinary disposable hostile NPC pair without fabricating production eligibility. It verified native turn-refresh behavior, both AESN status tiers, cleanup, and the production pre-existing-resource guard.

## Accepted traces

- Selection/baseline: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\osirislog.2026-09-01T16-10-11-751869.log`
- Resource lifecycle: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\osirislog.2026-09-01T16-53-28-661361.log` (`3,242,588` bytes after the Toolkit finished flushing it)

## Observed lifecycle

1. Ordinary hostile turn: `1/1`.
2. Relentless I after turn refresh: `2/1`.
3. The production guard rejects that already-enhanced target with `PreexistingActionResource`.
4. Relentless I removal followed by the next turn refresh: `1/1`.
5. Relentless II after turn refresh: `2/2`.
6. Relentless II removal followed by the next turn refresh: `1/1`.

The accepted trace contains exactly one `PASS`, zero `FAIL`, one application and removal of each Relentless status, one pre-existing-resource rejection, and zero `EnterCombatFailed` events. Its terminal marker is:

```text
AESN_ACTION_RESOURCE_PROOF PASS normal=1/1,relentlessI=2/1,relentlessII=2/2,cleanup=1/1,preexistingSkipped=1
```

## Runtime implication

Removing a resource status does not synchronously erase a point already granted for the current turn. The personal pool returns to `1/1` on the next native turn refresh. Production therefore relies on status ownership and native refresh semantics; it does not attempt an unsafe mid-turn clamp. The verified `1/1` guard prevents AESN from stacking onto candidates that already exceed the normal resource baseline.

## Production release check

After enabling `DB_AESN_RelentlessCapability(1)`, the repository passed all `76` full-suite tests and all `8` identity/namespace checks. A default production synchronization removed every test/proof goal from the Toolkit project, and the resulting clean schema-2 Story build succeeded in the Toolkit.
