# Adaptive Enemy Scaling Native POC

This repository contains the isolated, native Baldur's Gate 3 Toolkit proof of concept for **Adaptive Enemy Scaling**. The native path is primary; the existing Script Extender implementation remains untouched as a fallback.

The POC is intentionally narrow. It must prove native roster selection, deterministic party-level and party-size policy, exact reversible HP mutation, one stat tier, additive Action and Bonus Action statuses, late entrants, merged combats, save/load reconciliation, and host/client behavior before the production balance table or optional spell injection is considered.

## Identity

- Module name: `AdaptiveEnemyScalingNativePOC`
- Module UUID: `a4567f52-1665-df50-b84c-3992f80fdb90`
- Internal POC milestone: `0.1.0`
- Toolkit module version: `1.0.0.0` (first Publish Local is expected to auto-increment to `1.0.0.1`)
- Status namespace: `AESN_*`
- Osiris database namespace: `DB_AESN_*`
- External mod dependencies: none

## Safety boundary

Until a separate post-build approval is given, this project must not write to the live Baldur's Gate 3 `Mods` directory, change `modsettings.lsx`, install a built package, or upload to mod.io. Toolkit **Publish Local** output is saved under ignored `artifacts/` storage on `B:` and then work stops for review.

## Documents

- [Design](DESIGN.md)
- [Test plan](TEST-PLAN.md)
- [Capability proof](CAPABILITY-PROOF.md)
- [Upstream record](UPSTREAM.md)
- [Third-party notice](THIRD-PARTY-NOTICE.md)
