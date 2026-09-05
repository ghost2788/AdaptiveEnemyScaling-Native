# BOSS-01: Native boss classification

## Result

Observed in retail savegames on 2026-09-03 using the gated, observation-only
`AESN_85_BossPriorityHarness`.

- **Verified locally:** the native `IsBoss` query can classify eligible enemies
  when `DB_AESN_CombatHardenedReady` fires and persist the result in Story facts.
- **Rejected:** native `IsBoss` alone identifies every intended encounter boss.
  In particular, Nere returned `0` in the tested mod configuration.
- **Assumption/unsupported:** these results establish universal classification
  across other load orders or every boss in the game. They do not.

## Evidence

The user created `AES Nere proof.lsv` at 14:54:39 local time. Its Story data was
extracted read-only into ignored `artifacts/boss-proof-nere-confirm-20260903/`.
The original save was not modified. LSLib 1.20.4 successfully read its Osiris
v1.15 Story data; the older installed LSLib 1.19.5 reader rejected that format.

`DB_AESN_BossPriorityHarnessObserved` contains:

```text
97693f56-6ba9-d858-d3ac-287cad18d902 | S_UND_TheDrowNere_06bf05c5-216b-4eaf-91f5-8f1dd3d57f30 | NonBoss
435224e2-411c-cf51-eaa4-7e980bfed240 | S_UND_KethericCity_AdamantineGolem_2a5997fc-5f2a-4a13-b309-bed16da3b255 | Boss
```

The same save records six duergar in Nere's combat as `NonBoss`. Its existing
Relentless recipient facts identify `S_UND_DuergarRaftCaptain` and
`S_UND_DuergarLoyalWry`, both at tier I. This observation is from this save,
not a reinterpretation of the earlier Fonmara screenshot.

## Implementation consequence

Boss-first allocation needs an explicit identity override for Nere in addition
to native classification. Do not use the Honour-mode tutorial boss database as
proof of the native query's result. Priority must remain subordinate to hostile
eligibility, resource-safety checks, existing recipient caps, and remaining
budgets. This proof does not implement or validate ranked allocation itself.
