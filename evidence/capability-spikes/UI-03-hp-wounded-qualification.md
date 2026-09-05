# UI-03: wounded HP primitive qualification

Date: 2026-09-03

Status: Controlled two-sample wounded replacement, legacy/total reload retention
and exact cleanup PASSED for the two isolated fixtures. Production integration/recovery
remains unimplemented. This is not completion of the full retail-evidence or release
contract. Latest wounded checkpoints were verified through user text plus parsed save
facts; no new wounded screenshots were collected, although the full specification
requests them. Screenshot evidence remains incomplete.

Historical first-run result: fixtures initially reached wounded checkpoints, then
returned to full health. That run did not pass; the corrected run is recorded below.

Historical correction staging receipt (2026-09-03 21:57:24 EDT): one Setup call disables
self-healing only on disposable fixtures before HP/status mutations. Scoped
independent source review approved; controller fresh169tests and8identity
checks passed. Backup `artifacts/hp-wounded/selfheal-pre-stage` retained.
Corrected enabled81 SHA256
`b33f1b4ce5b2832de82f1b1fa3a584037a7a26c20b82b83e54da9c094832ffab`.
All12productiongoals,2stats,metadata and installed1.0.0.15PAK unchanged;
original6353123 identity retained. Repository source remains disabled.
At this staging checkpoint, build, local publish, package verification and retest
were still pending. The completed corrected run below supersedes that status;
these are not current rebuild instructions.

Corrected package receipt (before retail retest): user build and PublishLocal succeeded; installed
timestamp2026-09-03 22:04:06 EDT,size26,778,674bytes,version1.0.0.16, SHA256
`9f43385058f14da4b467efcec69135cd39efb22d2d32a5e71319978b0e815205`.
All13goals byte-match reviewed inputs; both stats match accepted inputs and
full catalog validates. Compiled goals.raw includes enabled81 and its Setup
SelfHealing disable call. OriginalUUID/handle6353123 retained, no82/83goals.
Extract/backup: ignored selfheal-package/ and selfheal-corrected.pak under
artifacts/hp-wounded. At this package checkpoint, the fresh pre-Nere load and
inspection were still pending. The following receipts supersede that uncertainty.

## Corrected legacy inspection save

User observed both fixtures remain13/28 and69/138 after waiting and saved
`AES wounded legacy` (Lae'zel-124126283__AES wounded legacy),
2026-09-03 22:12:09 EDT,15,575,309bytes, SHA256
`6e127af51ddd3dd987fa5707f5c992b76a534f3741f3b43af6351228b93f6a08`.
Read-only extraction: ignored artifacts/hp-wounded/legacy-save/StorySave.bin.
Both saved states LegacyInspect; Failure0,Pending0,Spawn0,OwnedBit7,
RemovedBit0,Observation6. Baselines20/20; legacy maxima28/138;
historical LegacyWounding observations13/28 and69/138 as intended.
Fixtures9c1d56ec-5a55-bf56-61be-f836892e932e (1) and
6130d72e-138b-8dc9-7ed6-056992d37446 (111) both have saved
DB_CharacterCrimeDisabled(NPC,"SelfHealing") facts, independently confirming
the fixture-only helper's saved effect. Stable inspection is user-confirmed;
at this checkpoint, save/reload retention and replacement were still pending.
The next step then was reloading this legacy save to reach TotalInspect with
unchanged13/28,69/138. The converted-save receipt records that completed step.

## Converted inspection save

User confirmed13/28 and69/138 after reloading legacy once and saved
`AES wounded converted` (Lae'zel-1541262846__AES wounded converted),
2026-09-03 22:15:53 EDT,15,624,400bytes,SHA256
`715a956e77d958959b3d79e4ed4a5ad37cf5e818cac0d97194976618cd26bf8f`.
Read-only extract retained in artifacts/hp-wounded/converted-save/.
Both states TotalInspect,Failure0,Pending0,14observations,7exact RemovedBit facts.
Saved observations (current/maximum):

| Phase | Amount1 | Amount111 |
| --- | --- | --- |
| LegacyReloading, before mutation | 13/28 | 69/138 |
| LegacyRemoving | 13/27 | 27/27 |
| TotalApplying, before absolute restoration | 14/28 | 138/138 |
| Converted | 13/28 | 69/138 |

This proves legacy wounds retained across this reload and exact current/max
restored after this controlled replacement. Native removal clamps the larger
sample's current HP and adding the total increases it; absolute restoration is
therefore necessary for this replacement sequence. Intermediate observations
are measurements for these cases, not a universal rounding claim. Final phase
guards validated surviving reference7, removed legacy bits and matching total.
OwnedBit facts remain as historical fixture records, not evidence of live bits.
At this checkpoint, the next step was reloading the converted save to observe
TotalReloading and then exact-total removal. The cleanup receipt records that
completed step with maximum27 and retained reference7.
No interrupted recovery or production integration proof is established here.

## Cleanup save: total reload retained wounds before removal

User observed13/27 and27/27 after cleanup and saved `AES wounded cleanup`
(Lae'zel-214126280__AES wounded cleanup),2026-09-03 22:21:08 EDT,
15,646,350bytes,SHA256
`c1f48e8eb646e4e2d61965efdb7d981812f75c939f587aad1d578bfc2789c712`.
Read-only extract retained under artifacts/hp-wounded/cleanup-save/.
Both State rows Complete; Failure0,Pending0,Observation18,RemovedBit7.
Saved TotalReloading observations are13/28 and69/138, recorded before
matching-total removal. Cleanup observations are13/27 and27/27, matching the
user's display. Complete requires reference7 present, matching total absent,
legacy bits absent and positive bounded currentHP. Reference7 deliberately
remains; OwnedBit records are historical fixture bookkeeping.

Qualified locally for these controlled samples: absolute wounded restoration
after exact bit-to-total replacement, unchanged maximum, legacy and total
save/reload retention without reapplication, and exact removal preserving an
independent HP contribution. No universal timing/rounding or crash-recovery
claim follows. Repeated Complete reload inertness has source-test coverage;
an additional post-cleanup native reload has not been performed. Normal NPC
self-healing remains unchanged outside the disposable test fixtures. Migration
with normal NPC SelfHealing enabled, migration interruptions/recovery and mixed-owner
behavior remain unqualified by this isolated probe.

The installed package is still a proof build. Do not continue the campaign
from a proof save or publish it online. Next close game/Toolkit for review and
the separately planned production integration; final production smoke and
interruption/mixed-owner/regression gates remain outstanding.

Scope: Disposable two-kobold prerequisite probe only; no production migration or recovery.

## Capability gate

- Verified locally: the installed public Story header at
  `B:/SteamLibrary/steamapps/common/Baldurs Gate 3/Data/Mods/Shared/Story/RawFiles/story_header.div`
  contains `call SetHitpoints((GUIDSTRING)_Entity, (INTEGER)_HP, (STRING)_HealTypes)`.
  Read-only inspection also confirmed GetHitpoints, GetMaxHitpoints, HasActiveStatus,
  ApplyStatus, RemoveStatus, CreateAtObject and ObjectTimerFinished signatures.
- Verified locally for this corrected package and two isolated samples: user-confirmed
  compilation, independently checked package contents, exact wounded restoration,
  measured intermediate current HP, and legacy/total save-load retention recorded above.
  Typed CHARACTER seeds/arguments and GUIDSTRING event casts compiled in this package.
  These claims were unverified before the corrected run, not at the current checkpoint.
- Assumption/unsupported beyond these measurements: generalized timing/rounding,
  migration with normal NPC SelfHealing enabled, interrupted recovery and mixed-owner
  production behavior. Controlled results do not qualify these as production dependencies.
- No production-safety, interrupted-recovery, timing or rounding claim is established here.

## Fixture contract

Source: `story/RawFiles/Goals/AESN_81_HpWoundedProof.txt`.

Checked-in INIT explicitly removes the enabled fact. Start requires deliberate staging
activation, a living out-of-combat host and no Started fact. It spawns two disposable
Kobolds_Melee_Drunk fixtures sequentially beside the host/previous fixture, adopts the
host faction and disables fighting/combat joining plus fixture-only SelfHealing before
HP/status mutations. No host or ordinary enemy HP/status
mutation is performed.

Version 1 fixture records:

- `DB_AESN_HpWoundedFixture(NPC, Amount)`
- `DB_AESN_HpWoundedState(NPC, Amount, Base, Target, Wounded, Phase)`
- `DB_AESN_HpWoundedObservation(NPC, Amount, Phase, ExpectedMax, Current, Maximum)`
- `DB_AESN_HpWoundedFailure(NPC, Amount, Phase)`
- Exact owned/removed legacy statuses and phase-specific one-shot pending facts.

The reference `AESN_HP_TOTAL_7` belongs to neither legacy-bit nor matching-total cleanup.
It survives the entire experiment.

## Expected checkpoints, assuming measured baseline 20

| Checkpoint | Amount 1 | Amount 111 | Required evidence |
|---|---|---|---|
| Baseline | 20 / 20 | 20 / 20 | Full positive baseline below 1,000,000 |
| LegacyInspect | 13 / 28 | 69 / 138 | Reference7 and every exact legacy bit present |
| LegacyReloading observation | 13 / 28 | 69 / 138 | No HP/status write before observation |
| LegacyRemoving observation | native current / 27 | native current / 27 | All owned legacy bits absent, reference7 present, current positive |
| TotalApplying observation | native current / 28 | native current / 138 | Matching total and reference7 present, bits absent, current positive |
| Converted / TotalInspect | 13 / 28 | 69 / 138 | Exactly one absolute restore of captured wounded value |
| TotalReloading observation | 13 / 28 | 69 / 138 | No reload reapplication or HP repair |
| Cleanup / Complete | native current / 27 | native current / 27 | Own total absent, reference7 retained, 0 < current <= maximum |

Slash notation is current / maximum HP. Interim and final native current HP are
observed, not predicted or forced. The source accepts another positive full-health
baseline below the bound and derives targets as measured Base + 7 + Amount, but a
baseline different from 20 must be disclosed when comparing this table.

Amount 1 uses only `AESN_HP_BIT_00001`. Amount 111 uses
`AESN_HP_BIT_00001/00002/00004/00008/00032/00064` (1+2+4+8+32+64=111).
Replacement totals are plain `AESN_HP_TOTAL_1` and `AESN_HP_TOTAL_111`.

## Original native acceptance procedure — historical plan

The corrected run above completed the initial build, inspection, replacement and cleanup
sequence. Retain this plan for comparison, not as a current instruction to repeat it.
Its latest-run screenshot requests remain unfulfilled. An additional Complete reload
and final production restoration/release checks are not established by these receipts.

1. Controller separately prepares/reviews an opt-in proof build, preserving current
   metadata and mod identity and excluding competing proof fixtures. User performs
   Toolkit build and Publish Local only. Do not publish online or use a campaign save.
2. Load a fresh disposable, out-of-combat save. Wait for both LegacyInspect checkpoints.
   Make a separate save and capture both NPC HP/tooltips. Extract actual saved
   State/Observation/Failure facts; require zero failures.
3. Reload that inspection save once. Require saved LegacyReloading observations to
   retain 13/28 and 69/138 before removals. Let replacement finish at TotalInspect.
   Save separately, capture HP/tooltips and extract both native interim observations,
   Converted observations and exact ownership records. Require zero failures.
4. Reload the TotalInspect save once. Let exact-total cleanup reach Complete. Save,
   capture remaining reference contribution and extract TotalReloading/Cleanup facts.
   Require maximum 27, positive bounded current HP, reference7 retained and no matching total.
5. Repeated Complete reloads must be inert. Restore the supported production package
   through the controller's separately reviewed procedure and leave proof saves isolated.

Any dead/zero-HP/combat/disabled/invalid-version/missing-status/wrong-HP continuation
fails closed. Replayed timers cannot repeat writes. A save loaded during any transient
phase records Interrupted and does no repair, restoration or resumption. The proof's
short settle timers are observational attempts, not a claim of guaranteed native event
completion; a delayed native response may fail this run rather than be silently repaired.

## Source validation and actual results

The Python execution suite runs the actual checked-in Story rule bodies using
`tests.osiris_subset.StoryFixture`. Native HP/status answers are explicitly supplied;
actions do not simulate status effects or mutate those supplied answers. Tests exercise
both samples, changed maximum/current/reference/bit answers, missing native responses,
zero/dead/combat/disabled/version failures, exact write counts, replay and interruption.

Initial RED: 11 tests, 37 expected missing-behavior assertion failures; no missing-file
errors (empty fixture when goal absent). Focused GREEN: 14 tests passed. Full repository
test and identity results are recorded in the task report.

Historical pre-run status was: compile pending, no saves/screenshots or native HP
observations yet, and wounded behavior unverified. The corrected package and three
save receipts above supersede that status. Current evidence includes user text and
parsed save facts, including intermediate current-HP measurements. No new wounded
screenshots were collected. The controlled two-sample gate passed with these disclosed
limits; the full screenshot/retail-evidence and production release contract is incomplete.

## Historical source review and initial staging receipt

Independent Task1 review approved functional source compliance, requested
consolidation of duplicated validation, then approved the scoped refactor with
no new findings. Shared read-only invariants retain explicit per-phase checks.
Controller fresh verification after refactor:168 discovery tests passed9.196s,
8 identity tests passed0.057s; catalog independently validates65535 entries
with accepted hashf54d4f4304f46e54976d206917d1fd30fb8226009c776db1494c85553e47817a.

With game and Toolkit confirmed closed, current catalog condition was backed
up at ignored artifacts/hp-wounded/pre-stage (13goals,2stats,meta,installedPAK).
Every live input was checked against backup immediately before staging.
At2026-09-03T21:21:59 EDT, replaced only the enabled AESN_82_HpCatalogProof
goal with reviewed AESN_81_HpWoundedProof, enabled only in prepared/staged copy.
The old catalog probe remains recoverable from backup and repository source.
New staged81 SHA-256:
`88e6c435bdd4e6ecaf8e6514b8cba0dd5e3571f2b8315d7cf0c520dc59d21f0d`.
Post-stage inventory13goals; all twelve production goals, both stats files,
current metadata and installed catalogPAK are byte-identical to backup.
Original moduleUUIDa4567f52-1665-df50-b84c-3992f80fdb90,
PublishHandle6353123, metadataVersion64 36028797018963982 preserved.
At this initial staging checkpoint, the installed PAK was still the previous catalog
test. Build, local publish and package verification were the next steps then; later
receipts supersede those pending instructions. No online Publish was authorized.
Production integration remains unimplemented.

## Historical first native build and local package verification

User reported `wounded story build success`, then `wounded publish local complete`.
Installed PAK timestamp2026-09-03 21:29:06 EDT, size26,778,610 bytes, SHA256
`f60a21913013bc1cafeb06b1fa846ccbbb5b6af74db656e77398cac9887b9243`.
Read-only extract artifacts/hp-wounded/package and backup wounded.pak retained.
Package includes exactly12 unchanged production goals plus reviewed enabled81;
all13 goals and both stat files byte-match prepared/backup inputs. goals.raw
has positive HpWoundedEnabled at408539 and no old catalog/tooltip enable symbols.
Independent packaged catalog validation:65535 entries, accepted hash unchanged.
Original UUID/PublishHandle6353123 retained; Version64 36028797018963983 (1.0.0.15).
Native Story compilation is user-confirmed; package contents independently
verified. At this first-build checkpoint, runtime behavior and retention were still
pending, with a fresh pre-Nere load next. Later failed and corrected-run receipts
supersede that uncertainty; this is not a current retest instruction for version1.0.0.15.

## Historical first retail diagnostic: wounds did not persist

User saved `AES wounded diagnostic` and confirmed current HP28/28 and138/138.
Save timestamp2026-09-03 21:49:48 EDT,15,585,041bytes, SHA256
`a5830f48c7d4254f7cb29f63afc55669dd260b7d08cca987e73e8cca24f3ac1c`.
Read-only StorySave extraction retained under ignored
`artifacts/hp-wounded/diagnostic-save/`.

Both saved states are LegacyInspect, with zero Failure facts and no pending timers.
Historical LegacyWounding observations are13/28 (fixture amount1) and69/138
(amount111). Thus SetHitpoints produced the intended wounds at the short
checkpoint; these historical facts are not evidence of current wounded HP.
The later user-observed full health contradicts stable wounded persistence.

Installed package goals.raw, base-game `_Disturbance_NPCRestoration` goal39,
contains HitpointsChanged -> out-of-combat SelfHealing checks and an NPC
regain-HP path. It explicitly provides PROC_SelfHealing_Disable and
PROC_SetHitpoints_BlockSelfHealing helpers. The first-run probe disabled combat
participation but did not disable SelfHealing. Normal NPC self-healing is
therefore the leading source-supported explanation; no particular healing
cast has been directly observed in this diagnostic.

The correction selected then was fixture-only SelfHealing isolation before wounding,
followed by fresh-save retesting. It was implemented and the controlled result appears
above. No repeated wound forcing or production healing/balance/migration change was
authorized. This healed diagnostic remains a failed run, not passing evidence.

## Probe-only self-healing isolation correction

Implemented correction (rebuild/retest was pending at this historical checkpoint): Setup calls
`PROC_SelfHealing_Disable(_NPC)` once, immediately after adopting each disposable
fixture and before its baseline timer or any probe HP/status mutation. No call was
added on reload, no new timer was added, and no repeated wound enforcement was added.

Exact local source evidence is the installed package extraction:
`artifacts/hp-wounded/package/Mods/AdaptiveEnemyScalingNativePOC_a4567f52-1665-df50-b84c-3992f80fdb90/Story/goals.raw`,
lines 28608–28612, within base-game goal39:

```text
PROC
PROC_SelfHealing_Disable((CHARACTER)_Char)
THEN
PROC_CharacterDisableCrime(_Char, "SelfHealing");
//NOT DB_SelfHealing_Perform(_Char);
```

Verified locally: this procedure definition and its CHARACTER signature exist in the
installed package's base-game Story source. The correction's execution test records
the exact external procedure boundary for npc1 and npc111 before HP/status writes.
It neither executes nor simulates the base game's self-healing outcome.

TDD: the focused suite first ran 15 tests with one expected failure (no disable calls);
after the one-line Setup correction, all 15 passed. Prior no-write reload, replay,
zero-health, wrong-observation and exact-status tests remain unchanged and passing.

At this correction-writing checkpoint, native efficacy was unverified. Subsequent
corrected-package verification, saved SelfHealing-disabled facts and controlled
inspection/reload receipts above establish the isolated two-sample result. The first
healed diagnostic does not count as a pass. No new wounded screenshots accompanied
the latest text/save evidence. General migration with normal NPC SelfHealing,
interrupted recovery and mixed-owner behavior remain unqualified. This correction
changes no production healing, stats or migration logic.
