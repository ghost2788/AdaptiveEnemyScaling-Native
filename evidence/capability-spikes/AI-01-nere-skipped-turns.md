# AI-01: Nere skipped turns and allied Hardened — investigation

## Evidence and scope

User reports numerous duergar skipping turns, including hostile and allied
actors, after reloading the budget proof and continuing combat. Some green
duergar acquired Hardened II while others did not. No cause is established.
No executable changes or deployment were made during this investigation.

Read-only extraction of `AES skipped turns.lsv`, saved 2026-09-03 16:58:32
local, is under ignored `artifacts/nere-skipped-turns-20260903-165832/`.
Comparison is `AES Nere budget fix.lsv`, saved 16:43:58, extracted under
`artifacts/nere-budget-fix-20260903-164358/`. Story facts were read with LSLib
1.20.4; Globals and WLD_Main_A resources were converted to LSX for inspection.
The original saves were not changed.

## Confirmed findings

- Same Nere combat: `de21ff95-aa5d-e07e-31fe-e82ce025bf86`.
- Relentless remains exactly one committed tier-I recipient, Nere. Ledger
  remains budget 1/0, cap 2, spent 1/0/1. Reload did not overgrant.
- Three actors were initially `HostileToNoParticipant` rejections, but now
  have combat-owned FullyCommitted Hardened and HPCommitted transactions:
  - RebelGuard_03: `baac0ae3-7b2e-47e6-85e4-579f70d4b4fa`.
  - RebelGreedy: `379fd131-79ab-4588-a8f0-28cdb51546e3`.
  - RebelBored: `30fb7e6e-40d2-4e77-b5ea-887f8eb345c9`.
- RebelPatroller_01 (`0c7758f9-ed35-49cb-926c-8b24195ee978`) also has a new
  combat-owned FullyCommitted application. The two Rebel_AtPier actors
  (`5ff28d97-e070-4805-a856-3112df670e1f`,
  `2dd2a840-35ff-4ed6-bf43-f9aae0e69c32`) remain rejected and unbuffed.
- Actual saved status lists agree: four rebels have AESN_HARDENED_FOE_02 and
  the appropriate HP-bit statuses; the two pier rebels do not.
- Therefore the reported ally buffs came through combat classification or
  reclassification, not world-preview ownership. The stored facts do not
  identify which party member was the hostility witness or when relations
  changed. Current source accepts hostility to any snapshotted participant;
  it is not a ring-color test and does not continuously revoke accepted
  combat eligibility when a relation later changes.
- No HP pending apply, component pending apply/remove, Relentless selection,
  hostility-recheck, or enemy-reconciliation pending facts exist in either
  snapshot. The original seven Nere combatants have ValidActiveCommit RETAIN
  reconciliation results in the later save.
- Fourteen HP failure/cleanup records refer to older skeleton/armor/Grym
  combats and exist in both snapshots. Do not attribute the new skipped turns
  to these old records without a causal trace.
- World policy state is Building with one finalize-pending fact in both
  snapshots. This warrants separate scheduler scrutiny; a snapshot does not
  prove a loop, and it cannot be summarized as all AES state being idle.
- Dalthar's saved statuses contain HEALTHBOOST_HARDCORE plus AES HP bits and
  Hardened II, not Relentless or an obvious named incapacitation status.
  No active domination/charm status was found in the inspected party status
  lists. Expired control effects are not ruled out by this observation.
- The staged project contains 12 production goals, not the test harnesses
  that issue EndTurn/SetCanFight. Their presence in repository source alone
  must not be mistaken for deployment.
- Saved mod list includes 5.5e NPC Combat Overhaul (GhostsEnhancedEnemyTactics)
  and DnD 5.5e All-in-One BEYOND alongside AES. The local NPC-overhaul Character
  definitions modify duergar passives/resources. This is an interaction axis,
  not evidence that either mod caused the symptom.

## Limits and next diagnostic step

The save is not a turn-by-turn AI trace. Saved AI-request/fallback fields,
empty behaviour nodes, or zero path movement speed are not decoded sufficiently
to diagnose skipped turns. No claim is made that AES is exonerated or that a
vanilla/other-mod bug is responsible.

Ask whether a party member was mind-controlled/charmed or hit allied duergar
with an attack/area spell before their buffs appeared. A temporary hostility
witness is a hypothesis, not a finding. If necessary, instrument witness and
relation transitions in an explicitly scoped diagnostic build, and perform a
controlled comparison from the same pre-fight save with one variable changed.
Do not remove mods from the only campaign save or overwrite the proof saves.

Public release remains on hold pending investigation of these encounter issues.

## User clarification and priority

The user subsequently confirmed Karlach was coerced, appeared hostile to the
party, and may have attacked an allied duergar. Lae'zel fled after Dissonant
Whispers without attacking allies. Karlach remaining a snapshot participant
while temporarily opposing allies is a strong explanation for the observed
Hardened reclassification; the specific IsEnemy witness was not recorded.

The user explicitly deferred this coercion/ally-buff eligibility issue as
lower priority. Do not change this behavior in the skipped-turn investigation.
The user also reports similar immobile/skipping NPCs in an earlier Underdark
beach fight before development of these mods. This expands the investigation
to the existing loadout but does not exonerate AES or establish another culprit.
Authorized next steps: audit installed combat-mod files, then a controlled
comparison from PRE-NERE-FIGHT; isolate BEYOND separately only if needed.
