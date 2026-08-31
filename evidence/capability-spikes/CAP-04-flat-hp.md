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

**Assumption/unsupported — blocked by the rejected CAP-02 isolation gate pending user review.**

CAP-04 is not verified until a living target demonstrates maximum HP `N -> N+1`, percentage restoration once, exact status acknowledgement, removal `N+1 -> N`, and percentage restoration once without package installation.
