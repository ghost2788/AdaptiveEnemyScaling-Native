# Adaptive Enemy Scaling Native

This repository contains the native Baldur's Gate 3 Toolkit implementation of **Adaptive Enemy Scaling**. The capability POC has been converted to a schema-2 production policy for the intended Honour-mode overhaul stack while retaining the exact, reversible HP transaction machinery proved during the POC.

Production uses world-owned Hardened scaling from level 1 through 20. Nearby active hostiles receive their HP and combat-stat tier before combat, and that tier follows the full current permanent-party average and size when the party changes. Combat-owned Relentless allocation remains encounter-scoped because its recipient cap and budgets depend on the actual combat group. Invisible and offstage actors are left untouched until they become discoverable or production combat eligibility identifies them.

The discovery-only world scan reaches 100 metres from each eligible permanent party member, repeats every three seconds, and also reacts to party, level, visibility, hostility, faction, combat-end, and load events. Active/onstage state is the render-range proxy; discovery does not require NPC perception or line of sight. Once a world-owned package commits, leaving range does not remove it. Active fights keep their current Hardened policy; a pending party-policy or external-HP replan is applied after the affected foe leaves combat.

Neutral yellow-ring actors are intentionally not pre-scaled. If one becomes hostile during an active fight, the combat hostility recheck evaluates it against the frozen encounter snapshot and applies Hardened once; Relentless remains subject to the encounter's remaining budget and recipient cap. Allied green-ring actors remain outside AES eligibility.

## Identity

- Module name: `AdaptiveEnemyScalingNativePOC`
- Module UUID: `a4567f52-1665-df50-b84c-3992f80fdb90`
- Persistent Story schema: `2`
- Toolkit module version: `1.0.0.5` (production update candidate; auto-increment enabled)
- Status namespace: `AESN_*`
- Osiris database namespace: `DB_AESN_*`
- Technical mod dependencies: none
- Balance target: Honour rules with BEYOND, level 1–20/x0.5 requirements, Expanded Armoury, FATE/FED, Enemies Reworked, and Extra Encounters

## Toolkit synchronization

`tools/sync_toolkit_project.ps1` accepts only the locally verified Toolkit `Data` root and refuses the live player `Mods` directory. Its default mode copies only production goals and removes stale test/proof goals from the Toolkit project. `-IncludeTestHarnesses` is explicit; the isolated action-resource proof additionally requires `-EnableActionResourceProof`, while the observation-only world acceptance build requires `-EnableWorldHardenedProof`. Neither proof is included in a normal production sync.

## Documents

- [Design](DESIGN.md)
- [Test plan](TEST-PLAN.md)
- [Capability proof](CAPABILITY-PROOF.md)
- [Upstream record](UPSTREAM.md)
- [Third-party notice](THIRD-PARTY-NOTICE.md)
