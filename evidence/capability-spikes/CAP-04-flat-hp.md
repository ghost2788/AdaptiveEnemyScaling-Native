# CAP-04 Flat-HP Capability Spike

## Static and compiler gate

- Date: 2026-08-31
- Toolkit: `4.1.1.6931813`
- Module UUID: `a4567f52-1665-df50-b84c-3992f80fdb90`
- Probe status: `AESN_HP_BIT_00001`
- Boost: `IncreaseMaxHP(1);`
- Story entry points: `PROC_AESN_TestApplyOneHp` and `PROC_AESN_TestRemoveOneHp`
- Result: `story.div` contains both procedures and `DB_AESN_SchemaVersion(1)`.
- Compiler result: `0 error(s), 0 warning(s). Compilation ended.`
- Intentional orphan records ignored for this narrow spike: `DB_AESN_SchemaVersion/1` and `DB_AESN_TestObservation/7`. The former is consumed by the later reconciliation implementation; the latter is a test-only observation sink.
- Live-state boundary: live Mods and `modsettings.lsx` matched the pre-build manifest after compilation.

## Runtime gate

**Verified locally — living one-bit apply/cleanup path.**

- Runtime date: 2026-08-31
- Execution surface: Toolkit editor Game Mode in `WLD_Campfire_E`; no package installation or activation
- Target: harness-owned vanilla kobold, disabled from fighting and joining combat
- Trace: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\osirislog.2026-08-31T15-22-32-781244.log` (`2,652,907` bytes when inspected)
- Living-probe compiled Story SHA-256: `283A32E0F09A2838EB79F4FF913980830EE55AC1F1C2DC9EFE3DEA08698606C4`
- Probe Stats SHA-256: `0665E43AB24D7A92CF45AF2172379FA322E390C19F3B7C1DCF81A5E9DF8CE606`

The first creation-frame attempt failed closed because native HP queries returned `-1/-1`. The independently authored harness was changed to wait for a 250 ms entity-bound `RealtimeObjectTimerLaunch`/`ObjectTimerFinished` pair before capturing the baseline. The strict rerun recorded:

```text
AESN_CAP04 APPLY beforeCurrent=12,beforeMax=12,afterCurrent=13,afterMax=13,percentagePreserved=1,bit=1
AESN_CAP04 REMOVE beforeCurrent=13,beforeMax=13,afterCurrent=12,afterMax=12,percentagePreserved=1,bit=1
```

The trace also contains the matching `StatusApplied` and `StatusRemoved` acknowledgements. The harness emits these records only after exact maximum arithmetic, exact percentage equality, and the applied-bit identity all pass. The target was retired after `REMOVE_POST`, and the later Game Mode exit did not report the AESN status as retained.

## Dead-target failure-closed gate

**Verified locally — skip before mutation.**

Native `ApplyStatus` rejected the initial dead-target attempt with `StatusAttemptFailed`. That establishes the engine constraint rather than a valid transaction. The harness was therefore changed to implement the production-safe policy: if captured current HP is zero, apply no HP bits, perform no percentage write, and retire the test target after proving its state is unchanged.

- Trace: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\osirislog.2026-08-31T15-33-04-0201.log` (`2,663,102` bytes when inspected)
- Final compiled Story SHA-256: `F179B34596B8CB2BEBC04B34BA64B5A5EF7ADCCBC1CBE41115B58A3F86EB855B`

```text
AESN_CAP04 SKIP_DEAD current=0,max=12,statusApplied=0,percentageWrite=0
```

The same trace contains `SKIP_DEAD(0,12,12,0,0.0)`, `SKIP_DEAD_POST(0,12,12,0,0.0)`, no `ApplyStatus` call for `AESN_HP_BIT_00001`, and deletion of the harness-owned `DB_AESN_TestSpawnedTarget` fact after `PROC_SetOnStage(..., 0)`.

CAP-04 is complete: the living apply/cleanup primitive and the dead-target failure-closed policy are both Verified locally.

Post-runtime safety capture `artifacts/safety/post-cap04-runtime.json` matched `pre-build.json` exactly: 19 live Mod files and `modsettings.lsx` SHA-256 `A2AC8F7C2238D12654846CC656F8D1CA154CA327D5901EA4095BA9EF0C6575A4` were unchanged.
