# CAP-03 Eligible-Roster Capability Spike

## Static and compiler gate

**Verified locally.**

- Date: 2026-08-31
- Toolkit: `4.1.1.6931813`
- Module UUID: `a4567f52-1665-df50-b84c-3992f80fdb90`
- Compiled Story SHA-256: `A0295C8E592820A7585684532C75F811917D4C7691189C3F4E164F0B98B85D4D`
- Full registry Stats SHA-256: `43E22E97062CA974B3AB069539977A12E1AA492C9084DC898109AB240AF1510E`

Seven identity/roster validators prove that `DB_PartyMembers` is the only positive candidate database, `DB_PartOfTheTeam` appears only in diagnostics, all custom databases use `DB_AESN_`, every custom status/stack uses `AESN_`, and no Tactician identifier or module UUID occurs in executable sources. The full sixteen-bit HP registry plus the one stat tier and additive Action/Bonus Action statuses loaded through `reloadStats` without a logged error. Story compiled after every diagnostic sink received a structured reader, eliminating the four orphan warnings.

## Empty editor fixture

**Verified locally — event barrier and empty-roster failure-closed behavior only.**

- Trace: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\osirislog.2026-08-31T15-54-15-325421.log` (`2,793,129` bytes when inspected)
- Command: `oe AESN_TEST_BUILD_ROSTER`

The trace records creation of `DB_AESN_RosterAggregate(...,0,0)`, launch of the combat-keyed `AESN_SNAPSHOT_FINALIZE_*` timer for exactly 100 ms, the matching `TimerFinished` event, removal of the finalize timer fact, and:

```text
AESN_CAP03 EMPTY eligibleSize=0
```

No `DB_AESN_CombatSnapshot` was created. This proves that the asynchronous candidate barrier runs and an empty eligible roster fails closed.

## Managed solo fixture

**Verified locally — positive solo path and integer average.**

- Trace: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\osirislog.2026-08-31T16-10-52-413351.log` (`2,777,856` bytes when inspected)
- Commands: `oe AESN_TEST_MAKE_SHADOWHEART_HOST`, then `oe AESN_TEST_BUILD_ROSTER`
- Fixture: `S_Player_ShadowHeart_3ed74f06-3c60-42dc-83f6-f034cb47c679`

The hostless editor level does not create a character-creation avatar. A test-only fixture therefore called native `MakePlayer` with a null owner and inserted `DB_Players`—never `DB_PartyMembers`. The vanilla `__AAA_FirstGoal` rule derived the positive candidate fact:

```text
DB_Players(Shadowheart) [add fact]
DB_PartyMembers(Shadowheart) [add fact]
```

The native calls emitted `CharacterMadePlayer` and `CharacterJoinedParty`. AESN then enumerated only the vanilla-derived candidate, observed `IsSummon=0`, `IsPartyFollower=0`, no owner, and recorded:

```text
AESN_CAP03 ELIGIBLE member=S_Player_ShadowHeart_3ed74f06-3c60-42dc-83f6-f034cb47c679,level=1,source=DB_PartyMembers
AESN_CAP03 SNAPSHOT size=1,sum=1,average=1,levelPercent=100,partyPercent=100,state=Unsupported
```

`state=Unsupported` is expected: the deliberately narrow policy registry currently implements only average levels 5 through 8. This result verifies the solo roster count, positive-candidate source, level capture, integer aggregation, and finalization barrier; it does not yet verify a supported stat tier.

## Rejected synthetic-level fixture

**Rejected — `SetLevel` is unsafe for an off-level editor origin that lacks an Experience Component.**

- Trace: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\osirislog.2026-08-31T16-20-30-144275.log` (`2,713,965` bytes)
- Main log: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\log.2026-08-31T14-03-57-223982.txt`, lines 33653–33667
- Crash record: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\CrashDump - 08-31-2026 20h 20m 35s.dmp.txt`
- Retired command: `oe AESN_TEST_MAKE_THREE_MEMBER_PARTY`

The trace shows the command, successful native `MakePlayer`, insertion of the test-only `DB_Players(Shadowheart)` fact, and vanilla derivation of `DB_PartyMembers(Shadowheart)`. The next harness action was `SetLevel(Shadowheart,6)`. No Gale or Astarion action executed. The main log then reported:

```text
Could not find Experience Component for character S_Player_ShadowHeart
```

The object record places Shadowheart in `WLD_Main_A` while the editor fixture runs in `WLD_Campfire_E`. The crash record reports `EXCEPTION_ACCESS_VIOLATION`, read address `0x4`, with `esv::Character::GetTotalXP` at the top of the game stack. This rejects level mutation as a fixture mechanism in this context; it does not reject normal `GetLevel` reads from valid active party members. The entire combined command was removed from the repository and Toolkit mirror, and a regression test prohibits both its event name and `SetLevel` calls on origin GUIDs.

## Incremental Gale ownership probe

**Verified locally — native ownership conversion only.**

- Trace: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\osirislog.2026-08-31T16-58-01-899583.log` (`2,965,683` bytes when inspected)
- Commands: `oe AESN_TEST_MAKE_SHADOWHEART_HOST`, then `oe AESN_TEST_MAKE_GALE_OWNED_PLAYER`

The refreshed Story build executed exactly one Gale harness operation: `MakePlayer(Gale,Shadowheart,1)`. It completed without a crash, emitted `CharacterMadePlayer(Gale)` and `CharacterJoinedParty(Gale)`, changed Gale's reserved user ID from `-65536` to Shadowheart's `65537`, and returned `IsSummon=0` and `IsPartyFollower=0`. It did not add `DB_Players(Gale)` or `DB_PartyMembers(Gale)`. This verifies the isolated ownership conversion but does not yet prove Gale is an eligible roster candidate. The next isolated probe inserts only the vanilla `DB_Players(Gale)` registry fact and observes vanilla derivation.

## Incremental Gale registry probe

**Verified locally — vanilla positive-candidate derivation.**

- Trace: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\osirislog.2026-08-31T17-01-27-895499.log` (`2,985,527` bytes when inspected)
- Commands: host fixture, Gale ownership conversion, then `oe AESN_TEST_REGISTER_GALE_PLAYER_FACT`

The registry command executed exactly one harness action, `DB_Players(Gale)`. Vanilla Story matched the playable tag, inserted `DB_GLO_Playable(Gale)`, and then derived `DB_PartyMembers(Gale)`. The harness never writes `DB_PartyMembers`. This verifies that an active origin companion can reach the approved positive-candidate database through the vanilla player registry. Eligibility still depends on the production exclusion queries and is tested separately by the roster snapshot.

## Two-member eligible-roster snapshot

**Verified locally — active companion inclusion and arithmetic.**

- Trace: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\osirislog.2026-08-31T17-01-27-895499.log`
- Final command: `oe AESN_TEST_BUILD_ROSTER`

AESN enumerated Shadowheart and Gale exclusively from their vanilla-derived `DB_PartyMembers` facts. For each, `IsSummon=0`, `IsPartyFollower=0`, and `CharacterGetOwner` returned undefined; both were therefore eligible. `GetLevel` returned `1` for each. The finalized record was:

```text
AESN_CAP03 SNAPSHOT size=2,sum=2,average=1,levelPercent=100,partyPercent=120,state=Unsupported
```

This verifies active origin-companion inclusion, absence of a false ownership exclusion, exact two-member count, integer sum/average, and the two-member party factor. `Unsupported` remains expected because average level 1 is outside the deliberately narrow level-5-through-8 stat tier.

## Three-character eligible-roster snapshot

**Verified locally — three active host-controlled characters.**

- Trace: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\osirislog.2026-08-31T17-16-49-38660.log` (`3,120,776` bytes when inspected)
- Fixtures: Shadowheart, Gale, and Astarion

The Astarion probes repeated the already verified isolated sequence: native `MakePlayer`, followed separately by `DB_Players(Astarion)`, from which vanilla Story derived `DB_PartyMembers(Astarion)`. AESN then observed all three candidates from `DB_PartyMembers`; each returned `IsSummon=0`, `IsPartyFollower=0`, undefined `CharacterGetOwner`, and level `1`. The finalized record was:

```text
AESN_CAP03 SNAPSHOT size=3,sum=3,average=1,levelPercent=100,partyPercent=140,state=Unsupported
```

This verifies exact three-character active-roster counting and arithmetic under one host user. It is not evidence of three distinct network players; multiplayer host/client behavior remains an explicit later test.

## Shadowheart avatar-registry prerequisite

**Verified locally — isolated prerequisite only.**

- Trace: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\osirislog.2026-08-31T17-30-45-478133.log` (`2,928,744` bytes when inspected)
- Commands: host fixture, then `oe AESN_TEST_REGISTER_SHADOWHEART_AVATAR_FACT`

The second command executed exactly one harness action:

```text
DB_Avatars(Shadowheart) [add fact]
```

No `hr_hire` event, hireling procedure, party-join event, or player-conversion event followed the command. This verifies only the vanilla avatar fact required by Larian's built-in `hr_hire` debug rule. The hireling creation path itself remains documented but unverified locally.

## Built-in hireling creation

**Verified locally — creation and vanilla candidate registration.**

- Trace: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\osirislog.2026-08-31T17-30-45-478133.log` (`3,134,466` bytes after this run)
- Commands: host fixture, avatar-registry prerequisite, then Larian's built-in `oe hr_hire`
- Selected global: `S_GLO_Hirelings_Ranger_0488a406-402c-4bd1-ba38-63b28c112d8d`

Larian's Story selected the Ranger hireling and a random male mountain-dwarf visual, completed `PROC_Hirelings_Hire` and `PROC_Hirelings_AddToParty`, assigned a hireling faction, and then added `DB_Players(Ranger)`. The vanilla playable rule derived `DB_PartyMembers(Ranger)`; AESN did not write either fact. The path called `RequestInitialLevel` and emitted both `CharacterMadePlayer(Ranger)` and `CharacterJoinedParty(Ranger)`. Subsequent native queries returned `IsSummon=0` and `IsPartyFollower=0`.

The logged `UnlockAchievement` call failure was non-fatal: hiring and party registration continued afterward. The editor main log also emitted off-AI-grid assertions because the host fixture occupies a position without a playable grid in this blank level. Those fixture warnings do not prove production behavior and motivate keeping subsequent roster runs brief.

## Active-hireling roster snapshot

**Verified locally — active hirelings are included exactly once each.**

- Trace: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\osirislog.2026-08-31T17-30-45-478133.log` (`3,422,601` bytes after this run)
- Final command: `oe AESN_TEST_BUILD_ROSTER`
- Active candidates: Shadowheart, retained Ranger hireling, newly created Wizard hireling

The editor retained the Ranger and its vanilla Story facts across an exit and re-entry into Game Mode, then the new `hr_hire` invocation created a Wizard. AESN enumerated all three solely from `DB_PartyMembers`. Both hirelings returned `IsSummon=0`, undefined `CharacterGetOwner`, `IsPartyFollower=0`, and `GetLevel=1`. The final build segment contains exactly three `DB_AESN_SnapshotMember` additions and three eligible debug calls, with no excluded calls or duplicate member facts:

```text
AESN_CAP03 ELIGIBLE member=S_Player_ShadowHeart_...,level=1,source=DB_PartyMembers
AESN_CAP03 ELIGIBLE member=S_GLO_Hirelings_Ranger_...,level=1,source=DB_PartyMembers
AESN_CAP03 ELIGIBLE member=S_GLO_Hirelings_Wizard_...,level=1,source=DB_PartyMembers
AESN_CAP03 SNAPSHOT size=3,sum=3,average=1,levelPercent=100,partyPercent=140,state=Unsupported
```

The retained Ranger shows that leaving Game Mode is not a clean fixture reset in this editor session. Later mutually exclusive fixtures must restart or reload the editor level when stale active-party facts would alter the result. Here the retained state does not invalidate the requirement: two distinct active hirelings were each eligible and counted exactly once.

## Scratch familiar/summon exclusion

**Verified locally — a genuine native familiar remains a candidate but is excluded from the eligible snapshot.**

- Trace: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\osirislog.2026-08-31T18-09-47-599348.log` (`3,049,308` bytes when inspected)
- Commands: reset the Scratch fixture, summon Scratch through `Target_FindFamiliar_Dog`, then `oe AESN_TEST_BUILD_ROSTER`
- Familiar: `DogFamiliar_Scratch_Summon_95f8cd8b-97dc-8464-5b50-71a728ce5afd`
- Owner: Shadowheart, `3ed74f06-3c60-42dc-83f6-f034cb47c679`

The native spell created Scratch and emitted `EnteredLevel` and `CharacterJoinedParty`. Vanilla Story then inserted `DB_PartyMembers(Scratch)`, so the familiar reached the same approved positive-candidate database as the active host. Native queries independently returned `IsSummon=1` and `CharacterGetOwner(Scratch)=Shadowheart`; the harness revalidated both before the roster run.

AESN enumerated Scratch from `DB_PartyMembers` but did not create a `DB_AESN_SnapshotMember` fact for it. Instead, the production exclusion queries recorded both applicable diagnostic reasons:

```text
AESN_CAP03 EXCLUDED member=DogFamiliar_Scratch_Summon_...,reason=Summon
AESN_CAP03 EXCLUDED member=DogFamiliar_Scratch_Summon_...,reason=Owned
```

Shadowheart was the only eligible member, and the finalized snapshot remained:

```text
AESN_CAP03 SNAPSHOT size=1,sum=1,average=1,levelPercent=100,partyPercent=100,state=Unsupported
```

This verifies that candidate membership alone cannot admit a familiar: summon and ownership queries are used only to exclude and diagnose it, while `DB_PartyMembers` remains the sole positive source. The blank camp fixture still reports off-AI-grid warnings, and `FindValidPosition` returned the same invalid point; the spell nevertheless created a fully registered native summon. Navigation is therefore not claimed as verified and is irrelevant to the roster observation.

## Temporary party-follower exclusion

**Verified locally — a native party follower remains a candidate but is excluded from the eligible snapshot.**

- Trace: `B:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit\osirislog.2026-08-31T18-55-03-809323.log` (`3,125,634` bytes when inspected)
- Commands: `oe AESN_TEST_ADD_TEMP_FOLLOWER`, then `oe AESN_TEST_FOLLOWER_ROSTER`
- Follower: `Kobolds_Melee_Drunk_5e94b48c-9c39-428a-fe78-9706252f74a5`
- Owner: Lae'zel, `58a69333-40bf-8358-1d17-fff240d7fb12`

The harness created an inert native drunk kobold and called `AddPartyFollower(Kobold, Lae'zel)`. Native queries then returned `IsSummon=0`, `IsPartyFollower=1`, and `CharacterGetOwner(Kobold)=Lae'zel`. Vanilla Story responded to `CharacterJoinedParty` by inserting `DB_PartyMembers(Kobold)`; the harness never writes that positive-candidate database.

The follower-specific roster command used the newly created follower GUID only as a unique test snapshot key. Production roster construction still enumerated candidates exclusively from `DB_PartyMembers`, which contained Lae'zel and the kobold. AESN admitted Lae'zel once and recorded both applicable diagnostic exclusions for the kobold:

```text
AESN_CAP03 EXCLUDED member=Kobolds_Melee_Drunk_...,reason=Owned
AESN_CAP03 EXCLUDED member=Kobolds_Melee_Drunk_...,reason=PartyFollower
```

The trace contains exactly one `DB_AESN_SnapshotMember` addition under that key, for Lae'zel, and none for the kobold. Final arithmetic remained host-only:

```text
AESN_CAP03 SNAPSHOT size=1,sum=1,average=1,levelPercent=100,partyPercent=100,state=Unsupported
```

This verifies that a temporary follower cannot become eligible merely by entering `DB_PartyMembers`. Ownership and follower queries are exclusion and diagnostic evidence only; neither is a positive roster source.

## Remaining required fixtures

**Assumption/unsupported.**

The managed solo, active-companion, three-character host-controlled, active-hireling, native Scratch familiar/summon, and temporary-follower paths now pass. Three-network-player and transformation outcomes remain unverified. Further editor fixture construction must be incremental and must not mutate the levels of off-level origins. Official Toolkit guidance warns not to load a savegame from Editor Game Mode, so a campaign save cannot be used as an unsupported shortcut: <https://docs.baldursgate3.game/Editor%3A_Navigation>.

Official debug shortcuts document a Game Mode party editor and instant companion recruitment. Those are candidates for a further isolated editor fixture, not verified dependencies: <https://docs.baldursgate3.game/Editor%3A_Shortcuts_and_Tips>.

CAP-03 remains open until the remaining managed party facts produce the required inclusion/exclusion observations. No combat-scaling implementation may depend on the full roster result yet.

## Safety boundary

Post-runtime safety captures through `artifacts/safety/post-follower-proof-runtime.json` matched `pre-build.json` exactly: 19 live Mod files and `modsettings.lsx` SHA-256 `A2AC8F7C2238D12654846CC656F8D1CA154CA327D5901EA4095BA9EF0C6575A4` were unchanged, including after the rejected synthetic-level fixture crashed the editor.
