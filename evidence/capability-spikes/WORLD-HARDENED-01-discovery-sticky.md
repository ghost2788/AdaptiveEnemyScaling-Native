# WORLD-HARDENED-01: Precombat Discovery and Sticky Retention

Date: 2026-09-03

Environment: retail Baldur's Gate 3, Risen Road pre-gnoll save, local Toolkit proof package built from `codex/precombat-hardened`.

## Package controls

- Corrected Story built successfully in the official Toolkit.
- Publish Local produced `AdaptiveEnemyScalingNativePOC_a4567f52-1665-df50-b84c-3992f80fdb90.pak` at 02:05:38.
- The active load-order entry used the module UUID with `PublishHandle="0"`, identifying the local Toolkit package.
- The staged discovery query used a 100-metre radius and contained no `CanSee` or `HasLineOfSight` gate.

## Retail observations

1. With the prior perception-gated build, a red gnoll at approximately 62 feet received Hardened while red gnolls behind it at approximately 70 feet did not.
2. Base-game Story source showed `CanSee` used as an actor-perception condition (for example, an NPC noticing a player interaction), confirming it was not a camera-rendering test.
3. After removing both `CanSee` and `HasLineOfSight`, the same loaded red gnolls at approximately 70 feet received precombat Hardened.
4. Nearby yellow-ring hyenas remained unchanged while neutral, as required by the `IsEnemy` gate.
5. The tester retraced the route where Hardened had previously disappeared, waited beyond the three-second scan interval, and confirmed that the committed Hardened package remained applied.
6. The tester saved with a precombat world-owned package committed, reloaded that retail save, and confirmed the same maximum HP, exactly one Hardened status, and continued scaling of the other loaded red gnolls.
7. In the goblin encounter, yellow-ring goblins correctly remained unscaled before hostility. After the player attacked during the active combat and the goblins turned red, the hostility recheck reconsidered them and applied AES under the existing combat snapshot.

## Result

- Nearby active-hostile discovery without character perception/line of sight: **Verified locally**.
- Sticky retention after leaving the discovery conditions: **Verified locally**.
- Neutral precombat exclusion: **Verified locally**.
- Neutral-to-hostile reconsideration during an active retail combat: **Verified locally**.
- Valid committed save/load retention without duplicate application: **Verified locally**.
- Dynamic permanent-roster replanning, external-HP replanning, and single-owner combat handoff remain separate runtime gates.
