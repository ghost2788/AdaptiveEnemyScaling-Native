# CAP-02 Publish Local Isolation

## Result

**Rejected.**

On 2026-08-31, Baldur's Gate 3 Toolkit `4.1.1.6931813` successfully built the isolated native project with **Publish Local**, but wrote the resulting package directly to the live player Mods directory:

`C:\Users\Tom Girard\AppData\Local\Larian Studios\Baldur's Gate 3\Mods\AdaptiveEnemyScalingNativePOC_a4567f52-1665-df50-b84c-3992f80fdb90.pak`

This contradicted the POC's no-live-write isolation dependency. The pre/post manifest showed exactly one live-state difference: that newly created package. `modsettings.lsx` and every pre-existing mod remained unchanged.

## Remediation

The exact new package was moved, without modification, to the ignored artifact path:

`B:\UserData\Tom\BG3ModAnalysis\AdaptiveEnemyScaling-Native-POC\artifacts\capability-spikes\CAP-02-minimal.pak`

- Length: `22,508,559` bytes
- SHA-256: `4248C2D5840E1E3F39EF5AFDEDE0BF4A4B0454F31AD4DD2CF583116BDE54652F`
- Post-remediation comparison: live Mods and `modsettings.lsx` exactly matched the pre-publish manifest.

The package was not activated, added to `modsettings.lsx`, or uploaded. Per the approved Task 4 gate, work stops before CAP-04 runtime execution. Continuing requires either a design that avoids Publish Local writing to the live Mods directory or an explicit, separately scoped exception from the user.
