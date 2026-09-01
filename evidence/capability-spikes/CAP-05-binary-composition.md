# CAP-05 Binary Flat-HP Composition Spike

## Gate result

**Verified locally.**

- Date: 2026-08-31
- Toolkit: `4.1.1.6931813`
- Module UUID: `a4567f52-1665-df50-b84c-3992f80fdb90`
- Exact fork-owned bits: `AESN_HP_BIT_00001`, `AESN_HP_BIT_00004`, `AESN_HP_BIT_00008`
- Expected delta: `1 + 4 + 8 = 13`
- Execution surface: Toolkit editor Game Mode in `WLD_Campfire_E`; no package installation or activation
- Trace: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\osirislog.2026-08-31T15-39-11-814116.log` (`2,855,069` bytes when inspected)
- Compiled Story SHA-256: `58182BC1EF5E26524168A39C927A70386E1B1F631FCD61E32B4DAFADB0CAADFB`
- Probe Stats SHA-256: `489738F26FE903955DDCDF4CF6E3BB2B734C738F1AD6FF6DABA75EEFB1635C13`

The harness captured one pre-mutation baseline, applied the three statuses, waited until all three were active, restored current HP percentage once, and emitted a pass record only after exact arithmetic and status queries succeeded:

```text
AESN_CAP05 APPLY13 beforeCurrent=12,beforeMax=12,afterCurrent=25,afterMax=25,percentagePreserved=1,bits=1|4|8
AESN_CAP05 REMOVE13 beforeCurrent=25,beforeMax=25,afterCurrent=12,afterMax=12,percentagePreserved=1,bits=1|4|8
```

The same trace contains distinct `StatusApplied` and `StatusRemoved` events for each of `00001`, `00004`, and `00008`. Cleanup waited until all three status queries returned inactive, restored the captured percentage once, and retired the harness-owned target.

## Safety boundary

Post-runtime safety capture `artifacts/safety/post-cap05-runtime.json` matched `pre-build.json` exactly: 19 live Mod files and `modsettings.lsx` SHA-256 `A2AC8F7C2238D12654846CC656F8D1CA154CA327D5901EA4095BA9EF0C6575A4` were unchanged.

CAP-05 verifies exact multi-bit composition for a positive delta. Overflow, zero/negative delta, and full-bank decomposition remain governed by the deterministic model and require the complete registry/static gate before production use.
