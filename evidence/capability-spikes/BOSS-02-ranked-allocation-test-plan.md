# BOSS-02: Ranked Relentless allocation — local test candidate

## Implementation scope

- Select rank 2 (native bosses and Nere's exact identity override), then rank 1
  (curated elite overrides), then rank 0 (ordinary eligible hostiles).
- Nere is the only seeded override in this candidate. The rank-1 mechanism is
  tested with fixtures; no campaign-wide elite roster is claimed or seeded.
- A 500ms barrier follows combat dispatch/readiness. Each pass classifies all
  known eligible enemies before spending any budget. A higher-ranked candidate
  still awaiting Hardened holds lower ranks back until it is ready or ceases to
  qualify. Pending work is retried while budget and candidates remain.
- Equal-rank tie order is not a guaranteed ranking by HP, level, or identity.
- Retain the existing resource guard and frozen caps/budgets. Relentless II
  consumes an available bonus-action upgrade before later tier-I grants.
- Existing recipients and spent counters are never reset to favor a late boss.
  Death/status failure does not refund budget. Reload restarts pending selection;
  merging rebuilds derived ranks after combining spent ledgers; cleanup cancels
  selection timers and deletes ranks.
- No changes to Hardened, HP amounts, hostility eligibility, or policy budgets.

## Local verification boundary

`tests/test_relentless_story.py` executes the checked-in allocation/lifecycle
rules using `tests/osiris_subset.py`, with explicit native query fixtures. This
checks rule decisions and effects rather than just matching source text. It is
not an Osiris compiler or runtime and does not prove native event ordering,
type inference, timers, or status behavior. Toolkit build and retail tests are
still required. BOSS-01 is the accepted native classifier evidence.

Local checks on 2026-09-03: 120 discovery-suite tests passed (including 20
source-rule allocation tests), plus 8 identity checks. Independent read-only
review found a delayed merge-replan readiness hazard; a failing regression was
added and the fix requires current HP/component commit plus absence of active
replan/cleanup/hold markers. The reviewer rechecked that fix successfully.

All 12 staged production goals match source hashes and pass LSLib 1.20.4 goal
syntax parsing. Its full command-line StoryCompiler check could not parse the
Toolkit-generated story header, so no full compilation success is claimed.
The user must run the Toolkit Story build. The staged project retains original
publish handle `6353123`, module UUID `a4567f52-1665-df50-b84c-3992f80fdb90`,
and existing local version `1.0.0.8`. Temporary proof goals were removed from
the staged project; their repository sources remain available.

## Manual acceptance

1. Build the staged Adaptive Enemy Scaling Story and Publish Local only.
2. Load a save BEFORE the Nere fight. Do not use the in-combat classifier-proof
   save to assess a new allocation: its existing recipients must remain intact.
3. Start combat with Nere hostile. After Hardened and the collection barrier,
   Nere should receive Relentless I for a qualifying tier-II party provided his
   personal action/bonus pools do not already exceed the safe baseline.
4. Create a new in-combat `AES Nere priority` save for database inspection.
   Confirm other recipients, if any, fit the unchanged combat allowance.
5. Reload that save: no additional recipients or extra budget spend.
6. End combat: Relentless is removed through existing owned-status cleanup;
   sticky world-owned Hardened behavior is unchanged.
7. Follow-up coverage: native-flagged boss; late hostile entrant with remaining
   versus exhausted budget; merged combats; tier-II Relentless on a qualifying
   higher-level party. Never force extra budget into the public production build.

This candidate is for local testing, not a confirmed public release.

## Retail result — budget failure, do not release

The user reported successful Toolkit Story build and Publish Local. The
`AES Nere priority.lsv` save (2026-09-03 15:46:25 local) was extracted read-only
to ignored `artifacts/nere-priority-20260903/` and inspected with LSLib 1.20.4.

Combat `a47a9051-d102-319e-c1f4-1f2991711fc1` records:

- Four level-5 snapshot members; Hardened II; action budget 1, bonus budget 0,
  recipient cap 2.
- Nere rank 2 and six other candidates rank 0.
- Two committed Relentless-I applications and recipients: Nere and
  `S_UND_DuergarLoyalGuard_02_cc942779-3d2d-4327-9704-c6c385c12c82`
  (the user identified the second recipient as Dalthar).
- Ledger action spent 1, bonus spent 0, recipients spent 1.
- No rejected candidates or pending selection timer.

Nere priority is demonstrated, but two committed grants against action budget
1 is an allocation/accounting failure. Recipient cap 2 does NOT authorize a
second grant. Local source-interpreter tests did not reproduce native behavior.

The earlier observation-only `AES Nere proof` save also has two recipients
against a 1/0 budget and spent counts 1/0/1. The pre-fight save contains no
Relentless recipients. Thus this mismatch predates ranked selection and is not
explained by inherited pre-fight recipient records. It was missed during the
earlier classifier-only inspection.

## Budget fix — reproduced locally, retail retest pending

The previous snapshot-triggered IF included `NOT DB_AESN_RelentlessLedger`.
Removing the old ledger row while spending therefore triggered initialization
again, creating a zero-spent row alongside the subsequently inserted spent row.
A second grant consumed the zero row; identical spent rows collapsed, producing
the observed two recipients with only one recorded spend. This is a reactive
absence-check defect, not evidence of concurrent execution.

[Larian's Osiris trigger documentation](https://docs.larian.game/Osiris_Overview#Trigger_Conditions)
documents removal triggers for negative database conditions in IF rules.
The source-rule interpreter previously omitted these triggers. It now models
them, and the new persisted-snapshot regression failed before the production
fix with precisely Nere plus a second recipient against budget 1.

The snapshot IF now calls `PROC_AESN_InitializeRelentlessLedger`; WorldContext
and ledger-absence checks live inside that procedure. They are evaluated only
when called, so spending cannot independently reinitialize the ledger. No caps,
budgets, status bonuses, or existing-recipient migration were changed.

Fresh local checks on 2026-09-03: 123 discovery tests passed, including 23
source-rule allocation tests, plus 8 identity checks. Allocation fixtures now
retain the snapshot during spending. Checks include tier-II upgrades, multiple
slots, late entrants, initial creation, repeated snapshot delivery, world-context
exclusion, save/load, and the exact one-action/two-cap regression.
Independent read-only review found no blocking issue; focused probes also
preserved combined merge spending and removed cleanup ledgers without reseeding.
These remain subset-interpreter checks, not native engine acceptance.

All 12 production goals were synchronized to the Toolkit, hash-matched, and
passed LSLib goal syntax parsing. Original handle `6353123` and module UUID were
preserved, including the Toolkit's current auto-incremented local version
`1.0.0.9`. No public upload was performed. Actual Toolkit Story build and retail
retest are still pending.

Retest from the save BEFORE the Nere fight, with the same four level-5 party.
Expected: Nere receives Relentless I; Dalthar and other enemies receive no
Relentless once that single action allowance is spent. Save the new combat for
inspection: exactly one recipient/application and ledger spent counts 1/0/1.
Reload must not grant another recipient. Already-overgranted combat saves are
not repaired or stripped of existing buffs by this fix and are not suitable for
fresh-allocation acceptance.

## Retail budget-fix acceptance — fresh allocation passed

The user reported successful budget-fix Toolkit Story build and Publish Local,
then observed only Nere receiving Relentless. The new `AES Nere budget fix.lsv`
(2026-09-03 16:43:58 local) was extracted read-only to ignored
`artifacts/nere-budget-fix-20260903-164358/` and its StorySave.bin inspected with
LSLib 1.20.4.

Combat `de21ff95-aa5d-e07e-31fe-e82ce025bf86` records:

- Four level-5 party members; Hardened II; action budget 1, bonus budget 0,
  recipient cap 2.
- Exactly one recipient: Nere, tier I, with one matching Committed application
  of `AESN_RELENTLESS_FOE_01`.
- Exactly one ledger row for this combat: action spent 1, bonus spent 0,
  recipients spent 1. No zero-spent duplicate for this combat.
- Nere rank 2 and six other candidates rank 0, including the guard the user
  identified as Dalthar. No second recipient, rejected candidate, or pending
  selection timer.

This verifies fresh Nere priority and correct one-action accounting in retail.
Post-fix reload/no-extra-grant and combat-end cleanup acceptance remain pending;
this result does not establish those lifecycle cases or a public release.
