# HOSTILITY-01 Existential Party-Member Hostility

## Result

**Verified locally — isolated existential query and duplicate guard.**

- Date: 2026-08-31
- Toolkit: `4.1.1.6931813`
- Trace: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\osirislog.2026-08-31T19-16-45-117561.log` (`3,353,284` bytes when inspected)
- Commands: `oe AESN_TEST_EXISTENTIAL_HOSTILITY`, then `oe AESN_TEST_RESET_EXISTENTIAL_HOSTILITY`
- Fixture combat key / first participant: `896d4a9a-4e37-bd62-317e-45d0a09b8971`
- Second participant: Lae'zel, `58a69333-40bf-8358-1d17-fff240d7fb12`
- Neutral candidate: `fe57324a-a078-67d1-5b19-f4d7f807c3c9`
- Second-participant-only hostile: `44e5ebcf-4102-b441-3df5-5e51c12d218f`

The fixture used disposable native characters and per-entity relation overrides only. Both candidates were neutral to the first participant. The neutral candidate was also neutral to Lae'zel, while the hostile candidate was hostile to Lae'zel:

```text
neutral -> first  = 0
neutral -> second = 0
hostile -> first  = 0
hostile -> second = 1
```

The harness controlled only those inputs and called production `PROC_AESN_ConsiderEnemy`. Production `QRY_AESN_IsEligibleHostile` enumerated both `DB_AESN_CombatParticipant` rows and called `IsEnemy` independently for each member. It rejected the neutral candidate with `HostileToNoParticipant` and accepted the candidate hostile only to the second participant:

```text
AESN_HOSTILITY REJECT enemy=fe57324a-...,combat=896d4a9a-...
AESN_HOSTILITY ACCEPT enemy=44e5ebcf-...,combat=896d4a9a-...
AESN_HOSTILITY_HARNESS PASS neutralRejected=1,firstNeutral=1,secondHostile=1,eligible=1
```

The harness deliberately invoked `PROC_AESN_ConsiderEnemy` twice for the hostile candidate. The trace contains two procedure calls but exactly one `DB_AESN_EnemyConsidered` addition and one `DB_AESN_EnemyEligible` addition, verifying duplicate suppression at the production interface.

Reset cleared both individual relations, all fixture-owned consideration/eligibility/rejection/participant/snapshot facts, and staged off all disposable targets.

This is an isolated query proof. It verifies that classification is existential and does not use one representative party member. RT-13 through RT-16 remain open until native combat events establish the participant intersection, late-entry dispatch, and integrated duplicate behavior.
