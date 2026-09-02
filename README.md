# Adaptive Enemy Scaling Native

This repository contains the native Baldur's Gate 3 Toolkit implementation of **Adaptive Enemy Scaling**. The capability POC has been converted to a schema-2 production policy for the intended Honour-mode overhaul stack while retaining the exact, reversible HP transaction machinery proved during the POC.

Production Hardened scaling is enabled from level 1 through 20 using the permanent-party average and party size frozen at combat start. Relentless allocation is enabled after the hostile Action/Bonus-Action runtime proof passed locally. Test and capability goals are excluded from production Toolkit synchronization by default.

## Identity

- Module name: `AdaptiveEnemyScalingNativePOC`
- Module UUID: `a4567f52-1665-df50-b84c-3992f80fdb90`
- Persistent Story schema: `2`
- Toolkit module version: `1.0.0.4` (beta release candidate; auto-increment enabled)
- Status namespace: `AESN_*`
- Osiris database namespace: `DB_AESN_*`
- Technical mod dependencies: none
- Balance target: Honour rules with BEYOND, level 1–20/x0.5 requirements, Expanded Armoury, FATE/FED, Enemies Reworked, and Extra Encounters

## Toolkit synchronization

`tools/sync_toolkit_project.ps1` accepts only the locally verified Toolkit `Data` root and refuses the live player `Mods` directory. Its default mode copies only production goals and removes stale test/proof goals from the Toolkit project. `-IncludeTestHarnesses` is explicit; the isolated action-resource proof additionally requires `-EnableActionResourceProof` and is never included in a normal production sync.

## Documents

- [Design](DESIGN.md)
- [Test plan](TEST-PLAN.md)
- [Capability proof](CAPABILITY-PROOF.md)
- [Upstream record](UPSTREAM.md)
- [Third-party notice](THIRD-PARTY-NOTICE.md)
