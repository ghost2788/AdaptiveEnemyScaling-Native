# Native Capability Proof Register

Only a **Verified locally** capability may become a dependency of the full POC implementation. A documented or unsupported claim first receives an isolated acceptance spike. A rejected mandatory capability stops the native path.

| Capability | Classification | Evidence or required proof |
|---|---|---|
| Native Story signatures for `CombatIsActive`, `SavegameLoaded`, `GameModeStarted`, `EnteredCombat`, and `SwitchedCombat` exist in the installed game headers | **Verified locally** | Read-only local `story_header.div` inspection |
| Native status resources can express flat maximum HP, Attack, Saving Throw, AC, Spell DC, ActionPoint, and BonusActionPoint boosts | **Verified locally** | Read-only vanilla and installed native-mod package inspection |
| A native package can implement combat scaling without a Script Extender tree | **Verified locally** | Installed Tactician Enhanced package has native Story/Stats content and no Script Extender tree; its content is not a reuse source |
| Official Toolkit executable is installed on this machine | **Verified locally** | Steam tool app `2934770`, build `19988805`; manifest and `Glasses.exe` verified under `B:\SteamLibrary` on 2026-08-31; hashes recorded in `evidence/toolkit-install.json` |
| BG3 Toolkit Data DLC is enabled and locally complete | **Verified locally** | DLC app `2956320`, depot `2330358`, manifest `7444994150796633975`; BG3 manifest entry and `Data\Editor` verified on 2026-08-31 |
| Toolkit-generated module identity `a4567f52-1665-df50-b84c-3992f80fdb90` opens as an isolated project | **Verified locally** | Toolkit generated module UUID and folder opened successfully; project UUID is `58e90e45-f96d-379d-a71e-dbe0b8f36770`; evidence recorded in `evidence/toolkit-project-identity.json` |
| A Toolkit-generated module can be reassigned the reserved UUID `bb8bdf43-775b-4451-9ffd-69b5f3f531e8` by editing metadata and folder names | **Rejected** | The reassigned identity crashed Toolkit project scanning in `CoreLib.dll`; reverting to the generated identity restored successful opening. The generated identity was explicitly approved on 2026-08-31. |
| Toolkit Project Settings accepts a `0.1.0` module version | **Rejected** | Toolkit `4.1.1.6931813` enforces a minimum major version of `1`; the saved module is `1.0.0.0` and auto-increment is expected to produce `1.0.0.1` on first Publish Local. The repository retains `0.1.0` only as its internal POC milestone. |
| Independently authored `AESN_` Story goals compile in the isolated native project | **Verified locally** | Toolkit generated `story.div` containing `DB_AESN_SchemaVersion(1)`, `PROC_AESN_TestApplyOneHp`, and `PROC_AESN_TestRemoveOneHp`; final compiler result was `0 error(s), 0 warning(s)` on 2026-08-31. |
| Publish Local can create a native `.pak` from the isolated project | **Verified locally** | Toolkit created a `22,508,559`-byte package with SHA-256 `4248C2D5840E1E3F39EF5AFDEDE0BF4A4B0454F31AD4DD2CF583116BDE54652F`. |
| Publish Local can save directly under repository `artifacts/` without writing the live player Mods directory | **Rejected** | The local run created `AdaptiveEnemyScalingNativePOC_a4567f52-1665-df50-b84c-3992f80fdb90.pak` in the live Mods directory. It was moved to ignored `B:` artifact storage and the live manifest was restored exactly; see `evidence/capability-spikes/CAP-02-publish-local.md`. |
| Publish Local performs no upload | **Documented but unverified locally** | Official Toolkit documentation; no authentication or Publish action was used, but network non-upload was not independently instrumented. |
| `DB_PartyMembers` plus the approved exclusions produces the exact eligible roster | **Assumption/unsupported** | CAP-03 |
| One independently authored `IncreaseMaxHP(1)` status applies, acknowledges, preserves living HP percentage once, and removes with exact maxima | **Verified locally** | CAP-04 living trace: `12/12 -> 13/13 -> 12/12`, exact `StatusApplied`/`StatusRemoved`, 100% preserved, bit `1`; see `evidence/capability-spikes/CAP-04-flat-hp.md` |
| Flat-HP processing cannot resurrect a dead target | **Verified locally** | Native status application to a dead character is rejected; the implemented policy detects `0` HP before mutation, applies no bit, performs no percentage write, preserves `0/12`, and retires the target; see CAP-04 |
| Multiple binary flat-HP statuses compose to an exact larger delta and remain individually queryable | **Assumption/unsupported** | CAP-05 |
| Versioned Osiris database records survive a mid-combat save/load | **Assumption/unsupported** | CAP-06 |
| Merge event ordering supports pre-cleanup alias creation | **Assumption/unsupported** | CAP-07 |
| Host-authoritative Story application produces consistent client observations | **Assumption/unsupported** | RT-26 and RT-27 after separate install approval |

## Evidence boundary

Tactician Enhanced establishes that the broad native mechanism is feasible. No Tactician source, resource definition, localization, UUID, database name, status name, or other authored content may be copied. Every POC identifier and resource is independently authored under the `AESN_` or `DB_AESN_` namespaces.
