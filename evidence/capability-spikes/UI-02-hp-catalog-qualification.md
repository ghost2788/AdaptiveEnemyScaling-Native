# UI-02 HP catalog qualification receipt

Date: 2026-09-03

This receipt qualifies the generated source artifact only. It does not claim a
Toolkit build, stats-load, retail UI, save/load, or runtime capacity result.

- Artifact: `artifacts/hp-catalog/Status_AESN_HP_Total.txt` (ignored)
- Entries: 65,535 (`AESN_HP_TOTAL_1` through `AESN_HP_TOTAL_65535`)
- Bytes: 18,250,946 UTF-8 bytes
- SHA-256: `f54d4f4304f46e54976d206917d1fd30fb8226009c776db1494c85553e47817a`
- Two safe `generate` runs produced the identical SHA-256 above.
- `check` accepted the generated artifact. Automated tests independently
  parsed exact coverage, IDs, StackIds, boosts, and the existing localization
  handle resolving to `Adaptive Enemy Scaling`.

The artifact remains outside production staging. Native Toolkit/load and retail
qualification remain required Gate 1 work.

## Source staging status

- The catalog is not copied by default: it remains an ignored artifact until a
  controller stages it for the catalog condition.
- A normal sync now removes only the exact staged catalog path
  `Public/<module>/Stats/Generated/Data/Status_AESN_HP_Total.txt`; it does not
  remove production stats or similarly named unrelated files.
- Automated temporary-project coverage verifies that cleanup contract. This is
  source-level evidence only; no Toolkit build or runtime behavior has been
  observed.
- The controller verified the closed-process baseline staging: only the old
  `AESN_83` proof goal and `Status_AESN_HpTooltipProof.txt` were removed after
  backup; all twelve production goals, `Status_BOOST.txt`, metadata, and the
  installed PAK matched their backup hashes.
- The ignored catalog condition is prepared from those same thirteen baseline
  inputs plus the full catalog and enabled `AESN_82`; its verified difference
  is limited to those intentional catalog-condition files. It has not yet been
  built or published.

## Pending native Gate 1 test steps

1. Have the user build and **Publish Local** the prepared unchanged baseline,
   then run
   three comparable loads from the same disposable pre-combat save with the
   same enabled mods.
2. Have the controller stage the prepared catalog condition, then have the
   user build and **Publish Local** again and repeat the three comparable
   loads.
3. Record controllable-save load time, steady memory, errors/stability, each
   boundary fixture's named row, and both proof saves' maximum/current/
   retention/removal facts with screenshots. Compare production-file hashes
   between conditions, allowing only the intended fixture/catalog differences
   and any Toolkit metadata version increment.

Gate 1 remains pending until those native observations are recorded. Do not
enable production totals or migration from this source-only result.

## Baseline native build checkpoint

User reported "build succeed" after the staged baseline Story build. This
confirms the unchanged production baseline compiles; it does not test the new
catalog or harness. Baseline Publish Local has been requested, with retail
measurements still pending.

## Baseline local publish verified

User reported `baseline publish local complete`. Installed PAK verified:
25,773,484 bytes, SHA-256
`a6cd2aa2dfe87f1c0f4217d840921426b377b74292281cbe5b38db22259bd88c`,
ModuleInfo Version64 `36028797018963981`, original PublishHandle `6353123`.
Package inventory has twelve production goals and Status_BOOST only, without
the isolated tooltip/catalog proof files. Extracted goals/stats match all
thirteen baseline inputs byte-for-byte. Packaged goals.raw contains neither
old tooltip-proof nor new catalog-proof symbols. This is package/source
verification plus the user's successful native baseline build, not a catalog
build or retail pass. Retained package at ignored `artifacts/hp-catalog/baseline.pak`
and read-only extract at `artifacts/hp-catalog/baseline-package`.

Latest saved modsettings still lists GEETClassLevelProof and not AES. User must
enable AES, disable GEETClassLevelProof, keep all other mods unchanged, and use
the untouched pre-combat save for both conditions. Three comparable fresh-launch
runs will separately time launch-to-menu and load-to-controllable-save so early
catalog loading is not excluded. Record game memory after the same 60-second
idle period after each load. Baseline run 1 requested; no timing/memory results yet.

### Baseline run 1: loaded, observational memory sample

User reported loaded into the pre-Nere baseline test. On 2026-09-03 at
19:28:05 EDT, read-only process inspection found BG3 DX11 PID24868, started
19:24:51 EDT, working set 4,142.4 MiB and private bytes 9,146.1 MiB.
Saved modsettings lists Adaptive Enemy Scaling and not GEETClassLevelProof.
No changes were made to the running game or load order.

Startup/load durations were not supplied. Exact time since save loading is
unknown; process uptime is not load time and this is not a controlled 60-second
sample. This observation does not satisfy the planned three-run performance
comparison by itself. Request full exit before the next fresh baseline run;
no campaign save is needed.

### Subsequent loaded observation: load-order comparability unresolved

After reporting other-mod testing and then `loaded`, user was observed at
2026-09-03T20:12:51 EDT: DX11 PID27436, start20:03:49 EDT, working set
4,211.2 MiB, private bytes9,169.7 MiB. Installed AES package still has verified
baseline SHA-256 a6cd2aa2dfe87f1c0f4217d840921426b377b74292281cbe5b38db22259bd88c.
Saved load order contains AES and not GEETClassLevelProof, but now includes
Fade's Equipment Distribution, absent from the earlier full list captured
before baseline run1. The run1 check only enumerated AES/GEET, so this does
not prove exactly when that additional mod was enabled. Comparability with
run1 is unresolved; do not interpret the memory difference as AES overhead.
Current settings copied unchanged to ignored
`artifacts/hp-catalog/observed-load-20260903-201251.modsettings.lsx`.
Await confirmation whether Fade's Equipment Distribution was enabled in run1.

### Final baseline observation

User replied "yes i believe it was" about Fade's Equipment Distribution in
run1. Retain that qualified recollection; run1's complete load order was not
captured at measurement time. Asked user to keep current setup unchanged,
fresh-launch, load same pre-Nere save, wait about60 seconds, and report loaded.

On 2026-09-03T20:35:56 EDT: DX11 PID33596, start20:34:13 EDT,
working set4,088.6 MiB, private bytes9,055.0 MiB. Saved ModuleShortDesc nodes
(list, order, metadata) exactly match the prior captured settings. Installed
AES PAK SHA-256 remains the verified baseline. This is a distinct fresh process.

Three observed baseline working sets: 4142.4, 4211.2, 4088.6 MiB; descriptive
median4142.4 MiB. Private bytes:9146.1,9169.7,9055.0 MiB; median9146.1 MiB.
These are observational comparisons, not a fully controlled performance pass:
startup/load times were not recorded, run1 full load order is unverified, and
post-load intervals were not instrumented. No native catalog result exists yet.
Next: user fully exits game/Toolkit, then stage catalog condition without
changing production inputs, identity or mod selection; user builds/publishes
locally and tests boundaries/retention/removal before any production integration.

## Catalog condition staged — native build pending

After user confirmed full exit, fresh process checks found neither BG3 nor
Toolkit running. Verified live production inputs against the baseline, original
PublishHandle6353123, full catalog validation, and enabled-only harness change.
Backed up current goals/stats/metadata to ignored
`artifacts/hp-catalog/pre-catalog-stage/`, verifying each copied hash.

At2026-09-03T20:37:29 EDT, added only these two prepared files to the Toolkit:

- `Mods/<module>/Story/RawFiles/Goals/AESN_82_HpCatalogProof.txt` (enabled test copy),
  SHA-256 `65c1aff97b2ee1cbb1cdf03cf5133646a74a72d5f0f599aa356b1c8fcde0f7e6`.
- `Public/<module>/Stats/Generated/Data/Status_AESN_HP_Total.txt`, full65535-entry
  catalog with SHA-256 `f54d4f4304f46e54976d206917d1fd30fb8226009c776db1494c85553e47817a`.

Post-stage verification: all original production goals/stats and current meta
remain byte-identical to the immediate backup; installed baseline PAK unchanged.
Repository proof source remains disabled. Fresh catalog/proof suite:17 tests
passed in4.982s. No native catalog compilation, local publish or retail success
claimed. Next user step: Generate Definitions and Build Story in AES project.

## Catalog native build and local package verified

User reported `catalog story build success` and `catalog publish local complete`.
Installed PAK timestamp: 2026-09-03 20:41:15 EDT; size 26,773,426 bytes;
SHA-256 `01f2e0f93dbc670c223f8720535323583da8520da6cf0046845ee0b01b215948`.
Package retains module UUID a4567f52-1665-df50-b84c-3992f80fdb90 and original
PublishHandle 6353123; Version64 36028797018963982 (1.0.0.14).

Read-only extraction confirms thirteen goals (twelve production plus enabled
AESN_82_HpCatalogProof) and both stats files byte-match the prepared condition.
Independent packaged-catalog validation accepts all 65,535 entries and SHA-256
`f54d4f4304f46e54976d206917d1fd30fb8226009c776db1494c85553e47817a`.
Packaged goals.raw contains positive DB_AESN_HpCatalogEnabled(1) at line 408539;
no old HpTooltipProof symbols remain. Retained ignored catalog.pak backup and
catalog-package extraction under artifacts/hp-catalog/.

This verifies native Story build (user report) and local package contents, not
retail catalog acceptance. Next: unchanged current mod setup, untouched
out-of-combat pre-Nere save, five disposable fixtures, then inspect/save/reload
and exact proof-fact verification. Production integration remains gated.

### First catalog retail loaded observation

User reported `loaded`. At 2026-09-03T20:49:58 EDT, BG3 DX11 PID19464
(start20:44:11) used 4257.8 MiB working set and 9182.4 MiB private bytes.
Installed catalog PAK hash still matches the verified package. Relative to
observational baseline medians, differences are +115.4 MiB working set and
+36.3 MiB private bytes; not a controlled overhead result or performance pass.

Saved modsettings contains the same module UUID set; other modules' descriptor
values are unchanged, AES version/hash changed as expected. Descriptor ordering
differs: AES is now last, and Weightless Gold precedes the XP patch. Neither
snapshot has a ModOrder node. Do not claim an exactly matched load configuration
or infer catalog-caused overhead. Snapshot retained under ignored
artifacts/hp-catalog/catalog-loaded-20260903-204958.modsettings.lsx.
No load durations recorded. Next: verify five fixtures visually and save Inspect
state for fact inspection before any reload/removal. Runtime acceptance pending.

### Catalog Inspect save: all boundary amounts applied correctly

User confirmed all five expected HP values and saved a separate Inspect save:
`Lae'zel-5141260834__AES catalog inspect/AES catalog inspect.lsv`, timestamp
2026-09-03 20:51:41 EDT, 15,597,390 bytes, SHA-256
`04ebbdc1b8c624760af77bccfe9e285f6b5eb6d581091453709141148ca6d680`.
Read-only StorySave.bin extraction under artifacts/hp-catalog/inspect-save,
parsed with LSLib 1.20.4, confirms version1/enabled1/started1; five fixtures
all in Inspect with baseline20; no Failure, Spawn or FillPending facts.
All ten baseline/applying observations have expected=current=maximum:

| Bonus | Fixture UUID | Applying HP |
| --- | --- | --- |
| 0 | 9d7126a6-de6e-4007-e03c-bd120be653c2 | 20 |
| 1 | 1c850eaa-863a-bf35-b3f4-fbaa474ce776 | 21 |
| 111 | e756e7f5-31a0-a13d-a625-518884a7146e | 131 |
| 32768 | b4c11f6e-5380-3087-52b1-1f24a5e841c2 | 32788 |
| 65535 | a72e9b7d-998e-cbfe-67a7-f55c3db9176a | 65555 |

This verifies native application of the sampled boundaries with the full
catalog installed. It does not yet verify their tooltip rows or reload/removal.
Next inspect named single rows before reloading the Inspect save.

### Catalog tooltip verification

User supplied Screenshot_731.jpg and confirmed the other requested tooltip
checks. Screenshot directly shows 65555/65555 HP and exactly one
`+65535 from Adaptive Enemy Scaling` contribution, alongside separate native
difficulty contributions. The other samples' correct single rows (+1, +111,
+32768), and no AES row for zero, are user-confirmed, not independently
screenshotted. Visual source naming and single-row rendering pass for the
sampled catalog amounts on that evidence basis.

Next reload `AES catalog inspect`, wait about ten seconds, and save separately
as `AES catalog cleanup`. Harness first records retained HP without reapplication,
then removes the exact sampled statuses and expects all five fixtures at20 HP.
Retention/removal remains unverified until the new save facts are inspected.

### Catalog cleanup save: sampled retention and removal pass

User confirmed all five fixtures returned to20 HP and saved
`Lae'zel-5641260834__AES catalog cleanup/AES catalog cleanup.lsv` at
2026-09-03 20:56:40 EDT (15,585,678 bytes), SHA-256
`cd586778344a1e4edcb5b34404a51bfd284b8a1a74044fb5fe30dff70e41e6f7`.
Read-only extract retained under artifacts/hp-catalog/cleanup-save and parsed
with LSLib1.20.4. Same five fixture UUIDs as Inspect save; all five states
Complete, no Failure facts, no pending Spawn/Fill facts,25 observations.

Reloading expected/current/maximum agree for every sample:
20/21/131/32788/65555. Both Removing and Cleaning observations equal20 for
all five. The staged harness observes retention before exact status removal,
without reapplication or healing in the reload branch. Therefore sampled
save/load retention and exact removal pass; this is not inferred merely from
the user's final20-HP observation.

Functional catalog proof now passes for sampled0/1/111/32768/65535 amounts:
application, named single-row display (with stated visual evidence limits),
save/load retention and removal. Full formal cost acceptance remains pending:
only one catalog fresh-process sample, no startup/load durations, and baseline
comparability limitations remain. Production integration/migration not implemented.
Next: full game exit before remaining fresh-launch catalog observations.

### Catalog fresh-launch observation 2

After confirmed full exit and unchanged package/settings, user was asked to
fresh-launch, load the original pre-Nere save, wait60 seconds, and report loaded.
At2026-09-03T21:01:55 EDT, DX11 PID7464 (start20:59:37) used4249.7 MiB
working set and9206.1 MiB private bytes. This is a new process relative to
catalog run1. Full ModuleShortDesc values/order exactly match catalog run1;
installed catalog PAK SHA-256 remains
`01f2e0f93dbc670c223f8720535323583da8520da6cf0046845ee0b01b215948`.

Two catalog working sets4257.8/4249.7 MiB; private9182.4/9206.1 MiB.
No startup/load durations supplied; previously stated baseline comparability
limits still apply. This is another observational sample, not formal cost
acceptance. Next full exit and third fresh-launch observation; no new save needed.

### Catalog fresh-launch observation 3 and diagnostic summary

After verified full exit, user fresh-launched the same original pre-Nere save
and reported loaded following the requested60-second wait. At2026-09-03
21:06:14 EDT, DX11 PID33220 (start21:03:49) used4243.3 MiB working set and
9160.2 MiB private bytes. Saved module descriptors/order match catalogrun1;
installed catalog package SHA-256 unchanged. No game files or settings changed.

| Measurement (MiB) | Baseline observations | Catalog observations | Baseline median | Catalog median | Difference |
| --- | --- | --- | --- | --- | --- |
| Working set | 4142.4 / 4211.2 / 4088.6 | 4257.8 / 4249.7 / 4243.3 | 4142.4 | 4249.7 | +107.3 |
| Private bytes | 9146.1 / 9169.7 / 9055.0 | 9182.4 / 9206.1 / 9160.2 | 9146.1 | 9182.4 | +36.3 |

Observed working-set difference is below the256-MiB diagnostic budget, but
not an isolated catalog overhead measurement: baseline descriptor ordering
differs, baselinerun1 full configuration is unverified, and exact postload
intervals were not instrumented. Startup/save-load durations were never
captured, so the time budget cannot be evaluated. Three catalog fresh launches
were observed, but this does not retroactively satisfy all controlled-test
requirements. Functional sampled proof passed; formal cost acceptance remains
unresolved. Request explicit user acceptance of this bounded measurement
limitation before production integration, or complete a controlled timed
comparison. Do not waive wounded/migration or production smoke-test gates.

## Gate 1 acceptance with explicit performance limitation

After explanation of the65535-entry catalog and missing controlled timing,
user stated the game did not seem slower, would monitor during their playthrough,
and authorized proceeding. Catalog accepted for the next implementation stage
on functional proof and observational memory evidence. This is user acceptance
of the disclosed measurement limitation, not a measured load-time pass.
No background monitor is installed; user will observe their own playthrough.
Wounded primitive/migration and production smoke gates remain mandatory.
