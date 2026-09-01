# COMBAT-01 Native Combat Events and Late Entry

## Result

**Verified locally — narrative-combat event integration and late-enemy dispatch.**

- Date: 2026-08-31
- Toolkit: `4.1.1.6931813`
- Trace: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\osirislog.2026-08-31T20-15-29-193451.log` (`3,743,937` bytes when inspected)
- Commands: `oe AESN_TEST_START_NARRATIVE_COMBAT`, `oe AESN_TEST_ADD_LATE_NARRATIVE_HOSTILE`, `oe AESN_TEST_RESET_NARRATIVE_COMBAT`
- Native combat: `a28e90ed-4453-9ac3-50f8-905c28625eac`
- Participating snapshot member: Gale, `ad9af97d-75da-406a-ae13-7071c563f604`
- Initial hostile: `76416231-ba47-72c3-5be0-6dcf93d8d884`
- Late hostile: `7d3e2900-d7a9-eaca-d2cd-a04dbe5c15d3`

The harness created a native narrative combat and inserted its entities only through `SetInNarrativeCombat`. It did not insert any production roster, snapshot, participant, consideration, eligibility, or rejection facts.

Native events and production facts were observed in this order:

```text
initial EnteredCombat
CombatStarted
one DB_AESN_CombatSnapshot
one DB_AESN_CombatParticipant for Gale
one consideration and eligibility record for the initial hostile
AESN_NARRATIVE START_PASS nativeCombatStarted=1,initialEligible=1
late EnteredCombat
one consideration and eligibility record for the late hostile
AESN_NARRATIVE LATE_PASS nativeEnteredCombat=1,lateEligible=1,duplicateSafe=1
```

Exact additions for this combat were:

```text
snapshotAdds=1
participantAdds=1
consideredAdds=2
eligibleAdds=2
rejectedAdds=0
```

The late verification deliberately called production `PROC_AESN_ConsiderEnemy` twice after the native late-entry path had already accepted the enemy. No additional consideration or eligibility fact was added. The late entrant therefore reused the original snapshot and remained duplicate-safe.

Reset removed the two native combat memberships, destroyed the narrative combat, cleared both individual relation overrides, staged off both disposable enemies, and removed all fixture-owned and production facts for the combat.

This verifies the native `CombatStarted` snapshot path, participant intersection, initial dispatch, native `EnteredCombat` late dispatch, original-snapshot reuse, and integrated duplicate suppression in an isolated narrative combat. It does not yet prove ordinary turn-based encounter behavior, hostile-summon exclusion, merge handling, or save/load reconciliation.
