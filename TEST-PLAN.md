# Adaptive Enemy Scaling Native POC Test Plan

## Test stages

1. Host-side model and static tests.
2. Toolkit capability spikes and editor-mode acceptance tests.
3. Publish Local package inspection, followed by a mandatory stop.
4. Only after separate approval: installed-game, save/reload, and host/client runtime validation.

The POC is not declared complete until every required runtime row passes.

## Schema-2 production gate

The current implementation is no longer the 5–8-only balance fixture. Before a production publish:

1. Run the host-side model and source-contract suite. The Story policy harness must contain all 144 combinations of level boundaries `1,4,5,8,9,12,13,16,17,18,19,20` and party sizes `1–12`, with exact tier, HP percent, Action budget, Bonus-Action budget, and recipient ceiling.
2. Synchronize the default production allowlist and rebuild Story in the Toolkit. No CAP/test goal, TextEvent command, UI proof banner, or reload-proof notification may be present.
3. Verify Hardened I appears from level 1; the compact names, all six Hardened icons, thematic opening copy, and concise mechanics lines render cleanly in Examine. Verify the atlas also packages unused Relentless III–VI art.
4. The isolated Action-resource proof passed and production Relentless is enabled. The accepted evidence records a normal hostile at `1/1`, Relentless I at `2/1`, Relentless II at `2/2`, cleanup to `1/1` on the following turn refresh, and rejection of a target already above `1/1`. Keep the proof goal excluded from normal production synchronization; stage it only with `-IncludeTestHarnesses -EnableActionResourceProof` if a future runtime version requires requalification.
5. Re-run HP transaction, stale reconciliation, death cleanup, late entry, combat merge, save/load, and rollback under schema 2. No HP drift, AESN resource total above `2/2`, dead-recipient replacement, Toolkit crash, or game crash is acceptable.
6. Sample Honour gameplay at levels `1,5,9,13,17,19` for solo, duo, four-, six-, and twelve-member synthetic policies before changing the approved numeric table.

## Precombat Hardened acceptance gate

Runtime verification: pending. Stage the observation-only build with `-IncludeTestHarnesses -EnableWorldHardenedProof`; this changes only the staged Toolkit copy and remains excluded from production sync. Compile Story before starting the acceptance run.

The runtime trace must contain all eight production-derived checkpoints without any harness-created eligibility or ownership facts:

1. `PRECOMBAT_COMMIT`: an active, onstage, non-invisible hostile within 100 metres receives a fully committed world-owned Hardened transaction before combat without a perception or line-of-sight requirement.
2. `SINGLE_OWNER_COMBAT`: entering combat reuses that world transaction and creates no combat-owned HP transaction.
3. `RELENTLESS_COMBAT`: an eligible recipient may receive combat-owned Relentless from the frozen encounter ledger.
4. `POSTCOMBAT_RETAIN`: the valid world Hardened owner remains after combat and Relentless cleanup.
5. `POLICY_REPLAN`: a permanent-party level or size change replans an out-of-combat target once while preserving its current HP percentage.
6. `EXTERNAL_HP_REPLAN`: after another HP modifier changes maximum HP, the new base is `observed maximum - AES-owned applied sum`; the foreign modifier is preserved and AESN does not compound itself.
7. `STICKY_RETAIN`: after first commit, a missed discovery scan leaves the world-owned Hardened HP and combat-stat package intact.
8. `SAVELOAD_RETAIN`: a valid committed world transaction survives retail save/load with no duplicate application.

Any missing checkpoint, double application, HP-percentage drift, foreign-status removal, premature hidden/offstage scaling, or Story error blocks production publication of this change.

## Capability spikes

| ID | Setup | Required observation | Failure result |
|---|---|---|---|
| CAP-01 | Install official Toolkit to the `B:` Steam library | Project can be opened without writing a package into the live Mods directory | Stop |
| CAP-02 | Publish a minimal isolated probe with Publish Local | Toolkit prompts for output; package is saved under repository `artifacts/`; live manifests unchanged | Stop before publishing if live writes are unavoidable |
| CAP-03 | Inspect `DB_PartyMembers` in solo, three-player, companion, hireling, summon, familiar, and follower fixtures | Required candidates and exclusions match DESIGN.md exactly | Reject roster design |
| CAP-04 | Apply and remove one `IncreaseMaxHP(1)` status | Maximum changes by exactly one; application/removal events are observable; current HP can be restored once | Reject binary HP design |
| CAP-05 | Apply `+1`, `+4`, and `+8` statuses | Maximum changes by exactly thirteen and each exact status remains queryable | Reject binary HP design |
| CAP-06 | Save during an active combat with versioned database facts | **Verified in the retail game for both committed and pending states:** a fully committed application retained schema, snapshot, transaction, exact applied bits, component ownership, active statuses, and maximum with `doubleApply=0`; a deliberately held zero-application `Planned` transaction survived save/load and production rolled it back exactly once with no bits, components, HP writes, or duplicate application. Stale inactive cleanup is separately verified in a focused editor fixture. | Reject save/load design |
| CAP-07 | Cause or reproduce a combat switch | `SwitchedCombat` arguments and later `CombatEnded` ordering allow the discarded owner to be marked first | Reject merge design |

CAP-02 was **Rejected locally on 2026-08-31** because Publish Local wrote the package into the live player Mods directory. The exact new file was moved to ignored `B:` artifact storage, its hash was preserved, and the live manifest was restored exactly. After review, the user approved a narrow temporary-staging exception: only this POC package may be created there by Publish Local, it must be moved to ignored `B:` storage before any game launch, and the live manifest must then match exactly. CAP-04 editor execution may continue; the CAP-02 capability classification remains Rejected.

CAP-03 is partially verified as of 2026-08-31: managed Shadowheart, Gale, and Astarion fixtures each reached vanilla `DB_PartyMembers` without level mutation. AESN verified solo `size=1`, active-companion `size=2`, and three-character host-controlled `size=3,sum=3,average=1,partyPercent=140` snapshots. The latter is not yet a three-network-player result. An isolated command registered Shadowheart in vanilla `DB_Avatars`, after which Larian's built-in `hr_hire` path created and registered native hirelings. AESN verified that retained Ranger and newly created Wizard hirelings each passed summon/owner/follower exclusions, returned level `1`, and appeared exactly once in a three-member snapshot with Shadowheart. A genuine Scratch familiar then reached vanilla `DB_PartyMembers`, returned `IsSummon=1` with Shadowheart as owner, was excluded under both `Summon` and `Owned`, and left the eligible snapshot at host-only `size=1`. A native kobold added through `AddPartyFollower` likewise reached vanilla `DB_PartyMembers`; it returned `IsSummon=0`, `IsPartyFollower=1`, and owner Lae'zel, was excluded under both `Owned` and `PartyFollower`, and left the eligible snapshot at host-only `size=1`. The editor retained active party state across level re-entry, so later mutually exclusive fixtures require an editor-level reset. A prior combined fixture was retired after `SetLevel(Shadowheart,6)` encountered the off-level origin's missing Experience Component and crashed in `esv::Character::GetTotalXP`; no Gale or Astarion action executed. Level mutation is rejected for this editor-fixture context. Three-network-player and transformation fixtures remain open; further roster fixtures must be incremental and leave origin levels unchanged.

CAP-04 was **Verified locally on 2026-08-31**. The living path produced `12/12 -> 13/13 -> 12/12`, exact apply/remove acknowledgements, 100% preserved once, and applied bit `1`; the creation-frame `-1/-1` observation was resolved with a 250 ms entity-bound native timer. Native status application to a dead character is rejected, so the failure-closed policy detects `0` HP before mutation, applies no bit, performs no percentage write, preserves `0/12`, and retires the test target.

CAP-05 was **Verified locally on 2026-08-31**. Independent bits `1|4|8` produced the exact transaction `12/12 -> 25/25 -> 12/12`; each status emitted distinct apply/remove acknowledgements, all three remained individually queryable, and current HP percentage was restored once per transaction. The live manifest remained unchanged.

ACTION-01 was **Verified locally on 2026-08-31**. The fork-owned Action and Bonus Action statuses emitted distinct apply events, were simultaneously active, emitted distinct removal events, and were simultaneously inactive after cleanup. This proves additive application/ownership only; no total resource normalization is claimed.

STAT-01 was **Verified locally on 2026-08-31**. The exact loaded resource defines Attack `+1`, Saves `+1`, AC `+1`, and Spell DC `+1`. The isolated runtime harness received apply/remove acknowledgements and observed `AESN_TIER_LEVEL_05_08` active then inactive while touching no HP or action status. This proves the one-tier primitive and ownership cleanup; RT-08 remains open until hostile combat selection and integrated cleanup pass.

HOSTILITY-01 was **Verified locally on 2026-08-31**. With two controlled participants, production rejected a candidate neutral to both and accepted a candidate neutral to the first but hostile to the second. Calling the production consideration interface twice for the accepted candidate produced one considered fact and one eligible fact. This proves the existential query and duplicate guard in isolation.

COMBAT-01 was **Verified locally on 2026-08-31**. A native narrative combat emitted `CombatStarted` and `EnteredCombat`; production created one immutable snapshot and one participating member, accepted one initial hostile, then accepted one late hostile against the same snapshot. Exact additions were one snapshot, one participant, two consideration records, and two eligibility records. Two repeated production consideration calls for the late hostile added nothing. Reset removed both native memberships, destroyed the narrative combat, and cleared all combat-keyed fixture and production facts. This closes the isolated native-event proof for RT-15 and the classification-layer portion of RT-16; ordinary turn-based encounters, status-application idempotence, and the remaining RT-13/RT-14 scenarios stay open.

HP-PLAN-01 was **Verified locally on 2026-08-31**. Production captured a native `12/12`, `100%` target against a synthetic version-1 supported size-three/average-six snapshot, calculated one target maximum `19`, persisted delta `7`, and registered exactly fork-owned bits `4|2|1`. The harness confirmed HP remained `12/12` before exact plan cleanup. A separate native-combat run recorded `UnsupportedPolicy` for both level-1 enemies and produced no transaction or bit rows. Application, rollback, and exact cleanup remain open.

HP-TXN-01 was **Verified locally on 2026-08-31**. Production requested one desired status at a time and received native acknowledgements in exact `4 -> 2 -> 1` order, advancing the persisted applied sum to `7`. It verified maximum `19`, restored the captured percentage once, and committed. Cleanup captured the current percentage once, removed exactly those three recorded statuses with individual acknowledgements, verified maximum `12`, restored once, and deleted all transaction-owned rows. Forced rollback, timeout, damaged cleanup, and death-after-apply remain open.

COMPONENTS-01 was **Verified locally on 2026-08-31**. An exact production HP commit started one persistent-guarded component chain. Native acknowledgements recorded exactly one `AESN_TIER_LEVEL_05_08`, one additive `AESN_EXTRA_ACTION_1`, and one additive `AESN_EXTRA_BONUS_ACTION_1`. Cleanup removed only those ownership rows in Bonus, Action, Stat order, then removed exact HP bits `4|2|1` and restored `12/12` at `100%`. There was one start, commit, component cleanup, apply pass, and cleanup pass, with no HP/component failure addition. This closes the integrated synthetic-policy component proof; ordinary hostile encounter end-to-end behavior remains open.

CAP-07 was **Verified locally on 2026-08-31**. Two spatially separated ordinary combats received distinct native IDs. Spatial convergence emitted two `SwitchedCombat(object,old,new)` events; the harness marked the discarded owner on the first event, then observed `CombatEnded(old)` afterward and emitted its explicit pass. Each original combat dispatched once and no merge failure or dispatch loop occurred. MERGE-01 then verified RT-17 through the production goal: equal-policy ownership migrated to the survivor, `CombatEnded(old)` was suppressed, no canonical replan was queued, and the alias was removed only after the surviving combat ended. MERGE-02 verified RT-18: opposing `average=7,size=1` and `average=5,size=3` policies produced canonical `average=7,size=3`, and both tracked enemies were reconciled with one percentage restoration each. MERGE-03 verified RT-19 with a three-combat ordinary chain: both discarded owners resolved directly to the final survivor, both discarded ends were suppressed, and the final end removed both aliases.

## Host-side deterministic tests

`tests/test_poc_model.py` is the arithmetic and state-transition oracle. It covers:

- floored average and rejection of an empty/non-positive roster;
- all six Hardened level boundaries and exact solo HP values;
- `+20` HP percentage points per member through twelve and a size-12 clamp above it;
- exact solo/duo Relentless special cases and size-three-through-twelve budgets/caps;
- the per-recipient tier-II maximum and no Action/Bonus-Action total above `2/2` from AESN;
- direct target-maximum floor arithmetic and the `65,535` binary-delta limit;
- current-HP round-half-up, living/dead clamping, exact cleanup, and rollback;
- independent maximum-size/maximum-average merge policy plus monotonic spent state;
- schema-2 save/load idempotence and stale cleanup.

## Static source tests

- All custom status IDs and stack IDs begin `AESN_`.
- All custom database names begin `DB_AESN_`.
- Module UUID is exactly `a4567f52-1665-df50-b84c-3992f80fdb90`.
- Upstream and Tactician UUIDs never appear in executable Story or Stats files, except the verified Simple Enemy Scaling conflict declaration when added to metadata.
- `DB_PartOfTheTeam` occurs only in `AESN_90_Diagnostics.txt` or tests.
- Roster production rules consume `DB_PartyMembers` and no second candidate database.
- Story contains no calls that remove statuses by broad type or prefix.
- Status resources contain no reaction, Legendary Action, class resource, Action Surge, boss resource, or optional spell boost.
- No `ScriptExtender` directory or packaged entry exists.
- Source and package contain no Tactician-authored ID, UUID, localization handle, or database namespace.
- Upstream attribution includes author, distribution label, archive hash, package hash, and version discrepancy.

## Runtime acceptance matrix

| ID | Scenario | Assertions |
|---|---|---|
| RT-01 | Solo active party | Eligible size `1`; avatar appears once; no inactive companion appears |
| RT-02 | Three player avatars | Eligible size `3`; host and both clients appear exactly once |
| RT-03 | Active companion | Companion is included exactly once |
| RT-04 | Active hireling | Hireling is included exactly once |
| RT-05 | Summon and familiar | Both excluded with explicit exclusion diagnostics |
| RT-06 | Temporary party follower | Excluded through follower evidence, never reintroduced through team/player queries |
| RT-07 | Mixed levels `5, 7, 8` | Sum `20`, count `3`, average `6` |
| RT-08 | One stat tier | Eligible hostile receives exactly Attack `+1`, Saves `+1`, AC `+1`, Spell DC `+1`; cleanup removes them |
| RT-09 | Exact HP apply | Base max `100`, current `50`, size `3`, average `5-8`: target max `161`, target current `81`, delta bits `32,16,8,4,1` |
| RT-10 | Exact HP cleanup | From `81/161`, immediate cleanup yields `50/100`; only the recorded five bits are removed |
| RT-11 | Damage before cleanup | Cleanup preserves the percentage observed immediately before cleanup, using round-half-up |
| RT-12 | Additive action probe | Exactly one `AESN_EXTRA_ACTION_1` and one `AESN_EXTRA_BONUS_ACTION_1`; removing them leaves other resources unchanged |
| RT-13 | Non-hostile character in combat group | Not scaled when hostile to no participating snapshotted member |
| RT-14 | Differing hostility by member | Scaled when hostile to at least one participating snapshotted member, even if neutral to another |
| RT-15 | Late enemy entrant | Receives original combat snapshot exactly once |
| RT-16 | Duplicate events | No second application record or status copy |
| RT-17 | Equal-snapshot merge | **Verified locally:** old owner aliases to survivor; records migrate; `CombatEnded(old)` performs no cleanup; alias retires after final-owner cleanup |
| RT-18 | Mismatched-snapshot merge | **Verified locally:** higher average and larger size selected independently; both tracked enemies reconciled exactly once; one mismatch log |
| RT-19 | Merge chain | **Verified locally:** every discarded alias resolves directly to the final survivor; both discarded ends are suppressed; final end removes both aliases |
| RT-20 | Mid-combat committed save/load | **Verified locally:** same maximum, exact bit rows, stat/action statuses, and committed transaction state after retail-game load; observation-only verifier reported `doubleApply=0` |
| RT-21 | Mid-transaction save/load | **Verified locally in retail:** a one-shot production-order hold persisted a real `Planned`/zero-applied transaction through a mid-combat save/load; production reconciliation returned `ROLLED_BACK`, removed its transaction, hold, queue, bits, and components, preserved the pre-mutation HP values, and the observation-only verifier emitted `pending reload proof PASSED` with `doubleApply=0` |
| RT-22 | Stale inactive record | **Verified locally:** native `CombatEnded` preceded injection; production observed `CombatIsActive=0`, performed one exact percentage-preserving cleanup, then deleted the snapshot and application records |
| RT-23 | Enemy dead before entry | No application and no resurrection |
| RT-24 | Enemy dies while scaled | Cleanup removes exact statuses without setting HP or resurrecting |
| RT-25 | Overflow/failure injection | No partial stat/action scaling; acknowledged bits roll back; diagnostic remains |
| RT-26 | Host plus clients | One host-authoritative application; all peers observe the same HP, stats, statuses, and cleanup |
| RT-27 | Client reconnect | Rejoining client observes committed state; host does not reapply |
| RT-28 | Precombat nearby active hostile | **Partially verified in retail:** red gnolls at approximately 62 and 70 feet received precombat Hardened without NPC-perception or line-of-sight gates; single-owner combat handoff remains pending. See `evidence/capability-spikes/WORLD-HARDENED-01-discovery-sticky.md` |
| RT-29 | Dynamic party-policy change | **Pending:** out-of-combat Hardened replans once; active combat defers until exit |
| RT-30 | External maximum-HP modifier | **Pending:** recompute from `observed maximum - AES-owned applied sum`; preserve the foreign modifier and living HP percentage |
| RT-31 | Discovery-range/visibility loss | **Verified locally:** the tester retraced the route that previously removed Hardened, waited beyond the scan interval, and confirmed the committed package remained applied. See `evidence/capability-spikes/WORLD-HARDENED-01-discovery-sticky.md` |
| RT-32 | World-owned committed save/load | **Verified locally for valid commits:** retail save/reload retained the same maximum HP and exactly one Hardened status while the scanner continued scaling other loaded red gnolls. Invalid/partial recovery remains a separate fault-injection gate. See `evidence/capability-spikes/WORLD-HARDENED-01-discovery-sticky.md` |
| RT-33 | Neutral-to-hostile mid-combat flip | **Verified locally:** yellow-ring goblins remained unscaled while neutral; after the player attacked during the active retail combat and they turned red, the hostility recheck reconsidered them and applied AES under the original frozen combat policy. Relentless remains limited to any unspent budget and recipient capacity. See `evidence/capability-spikes/WORLD-HARDENED-01-discovery-sticky.md` |

## Package gate

After Publish Local:

1. Hash the `.pak`.
2. Extract it into an ignored analysis directory.
3. Compare entries with an allowlist generated from this repository.
4. Run all identity, namespace, copied-content, and Script Extender checks against extracted files.
5. Compare live Mods and `modsettings.lsx` manifests with their pre-build versions.
6. Produce `artifacts/reports/package-validation.json`.
7. Stop for user review without installing or uploading.

Latest result: the `1.0.0.5` production update package passed extraction, production-goal, authored-source, namespace, Script Extender, active-identity, and retail smoke checks. A pre-build live-manifest baseline was not captured for this iteration, so no claim is made about unrelated live Mods-directory changes. See `evidence/release-candidates/1.0.0.5.md`.
