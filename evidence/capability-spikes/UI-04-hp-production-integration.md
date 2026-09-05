# UI-04: first legacy-removal event trace

Status: **source-only fixture; Toolkit compilation and native user gate pending**.
This is Task4A, not a conversion proof, production activation, or release approval.
An early held conflict is useful evidence. No restoration setter is present.

## What this fixture does

The opt-in goal is `proofs/hp-total-integration/AESN_84_HpIntegrationProof.txt`.
It is outside normal production goals and defaults to disabled. It uses reviewed
production45/47, not copies of their journal or native-operation machinery.
Neither `HpMigrationEnabled(1)` nor `HpTotalIntegrationEnabled(1)` is enabled.

Two newly spawned disposable kobolds use the previously proven
`45e31b7d-32ec-4f3d-8067-79061aeec77b` template and host faction. Only recorded
returned actors can receive setup writes; host, duplicate results and actors with
existing AES ownership, queue, pending, hold or quarantine are rejected.

| Sample delta | Setup HP request | Self-healing | First recorded legacy removal |
| --- | --- | --- | --- |
| 1 | 13, only if measured maximum supports it | Fixture-only disabled control | `AESN_HP_BIT_00001` |
| 111 | 69, only if measured maximum supports it | Normal, enabled | `AESN_HP_BIT_00064` |

Both have unrelated `AESN_HP_TOTAL_7`, plus fixture `AESN_HARDENED_FOE_01`.
The reference total is not journal-owned and must survive. Delta111 owns exactly
bits64,32,8,4,2,1. These are arbitrary labeled test amounts, not a party-balance
claim. The legitimate existing WorldContext/policy is read, never replaced or
edited to make its percentage produce these amounts.

The baseline current/max are measured before statuses. With a native baseline20,
the reference external base is27 and pre-removal maxima are28/138. These numbers
are conditional examples, not assumed native results. Every sample stores its
actual baseline, Inspect and pre-entry observations. If normal healing changes111
before capture, its live value is recorded; it is not required to remain69.

## Safety and checkpoint sequence

`Baseline -> Legacy -> Wound -> Inspect -> [explicit save/reload] -> Migrate -> Journal`.

Setup checks faction, CanFight=0, CanJoinCombat=0, living/noncombat state, the
intended self-healing mode, exact live statuses and native StatusApplied
acknowledgements, measured maximum, positive current, and an observed HP event
following the one setup setter request. That HP event is an observation, not proof
of its cause. The disabled control must reach13 at Inspect; the enabled sample
may already have healed. Setup does not create production transaction, component
ownership or WorldTracked facts. No setup hold persists during native waits or
the user's Inspect/save checkpoint.

Only when both samples are Inspect does the next explicit reload arm consumable
Migrate timers. Each independently revalidates setup evidence and native state.
A short, synchronous seeding procedure records its own HpApplicationHold, seeds
tracked/bit/component facts, writes the legacy HPCommitted transaction LAST,
removes only that hold, and calls `PROC_AESN_ValidateHpMigration(Owner, Enemy)`.
There is no native wait while intentionally holding this setup barrier. It does
not use lower-level capture/store/issue helpers or synthetic eligibility tokens.
Setup evidence remains distinguishable from journal ownership.

The reviewed guarded entry captures live HP. On its first `NativeRequest` trace
for `MigrationRemoveLegacy`,84 inserts only `HpMigrationPause(Enemy)`. The first
request and acknowledgement may complete; further advancement is inhibited.
This hook never forces a phase, clears a conflict, certifies causality, or calls
an HP setter. Native DB-trigger timing is still a compiler/retail acceptance gate.
Do not remove Pause for this first experiment.

Pending/interrupted setup or a pending Migrate reload fails closed and does not
retry. Started/attempt/request tokens prevent duplicate spawns and status calls.
An interrupted short seeding marker releases only its recorded setup hold and
records failure; it never erases foreign holds, native intent, or journal evidence.
Journal reload recovery remains production47's observation-only fail-closed path.
Discard an interrupted/rejected fixture save; there is no repair/reset workflow.

## Exact user steps (only after controller review and staging)

1. Controller backs up and stages an isolated manifest: production goals including
   reviewed45/47 plus only this84 proof. Exclude81/82/83, the separate existing
   WorldHardened84 harness, and every other proof/harness. Enable only this proof's
   `DB_AESN_HpIntegrationEnabled(1)` in the isolated staged build, not the source
   default or either production activation flag. Do not copy stale metadata.
2. User performs Toolkit build/Publish Local. Controller inspects the resulting
   PAK/manifest before asking for retail testing. A source test pass is not a
   compiler pass. No staging/build/install was performed by this task.
3. Load an **untouched disposable pre-Nere save**, never an old kobold/proof
   campaign. Stay out of combat and do not attack, heal, move or otherwise
   intervene with the samples. Allow setup timers to finish (normally several
   seconds). If both actors do not reach Inspect, stop and preserve evidence.
4. Inspect both visible HP values. Identify samples using the saved
   `HpIntegrationFixture(Actor, Delta, Faction)` GUID/amount map and their distinct
   legacy status sets/maxima; do not assume spawn position is identity. Capture
   screenshots for both and save under a NEW name, e.g. `UI04-Inspect`. Do not
   overwrite the untouched save. Controller checks both persisted Inspect rows,
   native baseline values, acknowledgements and setter counts before continuation.
5. Once both baseline sets are captured, explicitly reload `UI04-Inspect` ONCE.
   This is the only action that arms migration; there is no need to enable a
   global gate or type a hidden migration command. A replay of the same save is
   a separate replay of that old state, not a continuation; do not do it casually.
6. Let the first removal callbacks/timeout settle. Capture current/max screenshots
   again and save under another NEW name, e.g. `UI04-FirstRemovalTrace`. Do not
   remove Pause, force phases, reapply statuses, restore HP, or clear conflicts.
   Keep the reference total7 visible/present. Stop even if a conflict occurs.
7. Controller extracts/inspects the saved facts and native trace. Do not continue
   this campaign for normal play. Installed version1.0.0.16 and
   `artifacts/hp-integration/task4a-before-staging/installed-proof.pak` are
   wounded-proof packages: restoring that backup is diagnostic rollback ONLY,
   not restoration to production. Normal play remains BLOCKED until the controller
   separately identifies or builds AND inspects a supported, proof-free production
   PAK and verifies it as the installed package. Only then use an untouched campaign
   save. An untouched save does not make an active proof package safe for normal play.

## Evidence to collect

Fixture facts (prefix `DB_AESN_` omitted below) persist:

- `HpIntegrationFixture(Actor, Delta, Faction)` and Sample(delta,requestedHP,mode).
- `HpIntegrationBaseline(Actor, Current, Maximum)` and
  `HpIntegrationObservation(Actor, Phase, Current, Maximum)`.
- `HpIntegrationState`, Pending, Attempt, Returned, Requested, Ack, WoundSeen,
  Failure and SetterCount. SetterCount must be exactly1 per accepted sample.
- `HpIntegrationTrace(Actor, Sequence, Event, StatusOrReason, Current, Maximum,
  FixturePhase, NativeActionID)`. It records setup requests, HP events, all status
  events, CastedSpell (including the named normal-heal spell), AttackedBy, combat,
  Dying/Died and journal conflicts. Observation continues after conflict.

Production47 supplies the authoritative journal trace:
`HpMigrationTrace(Owner, Actor, Sequence, Event, Status, Current, Maximum,
JournalPhase, PendingOperation, PendingStatus, PendingEpoch, NativeActionID)`.
Also collect journal, hold, pause, bit state, checkpoint, conflict, shared pending,
uncertain, epoch and timer rows. Its trace-before-ack procedure records callbacks
with the current native intent. Fixture and journal sequence spaces are separate;
do not sort them together or infer native ordering between independent IF rules.
`PROC_AESN_HpIntegrationDump()` is a read-only diagnostic reader, not a phase
control. Exact values are in saved facts, not the generic log captions.

The complete source fixture has two setup HP calls (one per sample) and zero
journal restoration HP calls. Any extra setter/request, removed reference7,
unrecorded actor mutation, duplicate spawn or unexpected ownership is a failed
native gate. No successful conversion is expected or claimed by this first trace.

## Known gaps and runtime capability classification

Locally inspected native Shared header supplies CreateAtObject, GetFaction,
CanFight/CanJoinCombat, status/HP/combat/death events and CastedSpell signatures.
Shared `_Disturbance_NPCRestoration` supplies SelfHealing_Disable and
QRY_SelfHealing_IsEnabled; its named heal spell/status may write HP. These are
current local source/signature evidence, not proof of scheduling or efficacy.
Prior81 spawn pattern/native observations are limited to that earlier fixture.

New84 compilation, pre-return spawn event order, immediate DB-trigger Pause
ordering, asynchronous setter/status acknowledgements, self-healing traces and
reload timing are **documented but unverified locally** or, for native ordering
without authoritative guarantees, **assumption/unsupported**. No restoration
implementation depends on those claims. The Python subset executes real rules
with explicit supplied observations and records external calls; it never simulates
engine status/HP effects and cannot promote these claims to Verified locally.

CanFight/CanJoinCombat are disabled for both benign samples. Therefore this run
does NOT qualify combat-entry, death/damage intervention coverage, a paired
healing comparison, universal causal attribution, all journal-phase interruptions,
full111 conversion, restoration/rollback, or normal-play behavior. Known event
hooks are diagnostics, not universal damage/healing detection. Those gates need
separate intervention-capable samples and Task3B design after this trace.

Compiler risks include new goal symbol/type inference, cross-goal trace DB
triggers, imported Shared query availability, persisted fact readers, and event
registration. Missing acknowledgements fail closed rather than inventing success.

## 2026-09-04: reload-prerequisite diagnostic follow-up

The first native run reached Inspect for both actors, then failed Migrate before
any journal/removal. The saved phase-only failures do not identify the failed
predicate; neither GUID formatting nor faction/combat/healing persistence is a
proven cause. See the scoped `ui04-inspect` and `ui04-first-removal` inspection
artifacts. Guards remain unchanged.

New diagnostic source captures once on the failed Migrate Step, BEFORE its Failure
row poisons Safe. Collect `HpIntegrationDiagnosticCaptured`,
`HpIntegrationPrerequisite(Actor, Check, Detail, Result)`,
`HpIntegrationDiagnosticValue(Actor, Key, Integer)` and
`HpIntegrationDiagnosticGuid(Actor, Key, GUID)` alongside existing facts.
Named checks separate returned mismatches from unavailable output-query values,
record status/ack/ownership/context blockers, and include actual HP/flags/faction.
SelfHealing is a truth-only predicate:0/1 records false/true, not a distinguishable
unavailable state. These are read-only observations, not eligibility tokens or
atomic proof of earlier native causality; queries are reread immediately before
Failure. Multiple independent failures can be recorded.

After independent review and controller-managed build/PAK inspection, use a fresh
untouched disposable pre-Nere save, repeat setup/NEW Inspect save, then reload ONCE
and save NEW prerequisite evidence. Preserve the earlier failed saves; do not
clear/reset/retry their failure state. Diagnostic compilation/query evaluation and
first-removal event ordering remain unverified. Normal play remains blocked by
step7's separately verified proof-free production-package requirement.
