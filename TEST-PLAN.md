# Adaptive Enemy Scaling Native POC Test Plan

## Test stages

1. Host-side model and static tests.
2. Toolkit capability spikes and editor-mode acceptance tests.
3. Publish Local package inspection, followed by a mandatory stop.
4. Only after separate approval: installed-game, save/reload, and host/client runtime validation.

The POC is not declared complete until every required runtime row passes.

## Capability spikes

| ID | Setup | Required observation | Failure result |
|---|---|---|---|
| CAP-01 | Install official Toolkit to the `B:` Steam library | Project can be opened without writing a package into the live Mods directory | Stop |
| CAP-02 | Publish a minimal isolated probe with Publish Local | Toolkit prompts for output; package is saved under repository `artifacts/`; live manifests unchanged | Stop before publishing if live writes are unavoidable |
| CAP-03 | Inspect `DB_PartyMembers` in solo, three-player, companion, hireling, summon, familiar, and follower fixtures | Required candidates and exclusions match DESIGN.md exactly | Reject roster design |
| CAP-04 | Apply and remove one `IncreaseMaxHP(1)` status | Maximum changes by exactly one; application/removal events are observable; current HP can be restored once | Reject binary HP design |
| CAP-05 | Apply `+1`, `+4`, and `+8` statuses | Maximum changes by exactly thirteen and each exact status remains queryable | Reject binary HP design |
| CAP-06 | Save during an active combat with versioned database facts | Facts, transaction state, and applied status identities are available after reload | Reject save/load design |
| CAP-07 | Cause or reproduce a combat switch | `SwitchedCombat` arguments and later `CombatEnded` ordering allow the discarded owner to be marked first | Reject merge design |

CAP-02 was **Rejected locally on 2026-08-31** because Publish Local wrote the package into the live player Mods directory. The exact new file was moved to ignored `B:` artifact storage, its hash was preserved, and the live manifest was restored exactly. After review, the user approved a narrow temporary-staging exception: only this POC package may be created there by Publish Local, it must be moved to ignored `B:` storage before any game launch, and the live manifest must then match exactly. CAP-04 editor execution may continue; the CAP-02 capability classification remains Rejected.

CAP-04 was **Verified locally on 2026-08-31**. The living path produced `12/12 -> 13/13 -> 12/12`, exact apply/remove acknowledgements, 100% preserved once, and applied bit `1`; the creation-frame `-1/-1` observation was resolved with a 250 ms entity-bound native timer. Native status application to a dead character is rejected, so the failure-closed policy detects `0` HP before mutation, applies no bit, performs no percentage write, preserves `0/12`, and retires the test target.

## Host-side deterministic tests

`tests/test_poc_model.py` is the arithmetic and state-transition oracle. It must cover:

- average: levels `[5] -> 5`, `[5, 7, 8] -> 6`, `[8, 8, 5] -> 7`;
- party factor: sizes `1 -> 100`, `3 -> 140`, `8 -> 240`, `9 -> 240` plus clamp flag;
- maximum: base `100`, average `7`, size `1 -> 115`;
- maximum: base `100`, average `7`, size `3 -> 161`;
- binary delta: `61 -> [32, 16, 8, 4, 1]`;
- delta `0` produces no bits;
- delta `-1` and `65,536` fail closed;
- current-HP round-half-up: `50/100` into maximum `115 -> 58`;
- cleanup percentage: `58/115` into maximum `100 -> 50`;
- living clamping never produces zero; dead remains zero;
- merged policy chooses the larger size and higher average independently;
- committed application plus reload is idempotent;
- discarded combat end is a no-op; surviving combat end owns cleanup.

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
| RT-17 | Equal-snapshot merge | Old owner aliases to survivor; records migrate; `CombatEnded(old)` performs no cleanup |
| RT-18 | Mismatched-snapshot merge | Higher average and larger size selected independently; every tracked enemy reconciles; one mismatch log |
| RT-19 | Merge chain | Every alias resolves to final survivor; only final end cleans |
| RT-20 | Mid-combat committed save/load | Same maximum, bit rows, stat/action statuses, and transaction state after load; no double application |
| RT-21 | Mid-transaction save/load | Pending state completes or rolls back once; never duplicates bits |
| RT-22 | Stale inactive record | Exact fork-owned cleanup completes before records are deleted |
| RT-23 | Enemy dead before entry | No application and no resurrection |
| RT-24 | Enemy dies while scaled | Cleanup removes exact statuses without setting HP or resurrecting |
| RT-25 | Overflow/failure injection | No partial stat/action scaling; acknowledged bits roll back; diagnostic remains |
| RT-26 | Host plus clients | One host-authoritative application; all peers observe the same HP, stats, statuses, and cleanup |
| RT-27 | Client reconnect | Rejoining client observes committed state; host does not reapply |

## Package gate

After Publish Local:

1. Hash the `.pak`.
2. Extract it into an ignored analysis directory.
3. Compare entries with an allowlist generated from this repository.
4. Run all identity, namespace, copied-content, and Script Extender checks against extracted files.
5. Compare live Mods and `modsettings.lsx` manifests with their pre-build versions.
6. Produce `artifacts/reports/package-validation.json`.
7. Stop for user review without installing or uploading.
