# Native Capability Proof Register

Only a **Verified locally** capability may become a dependency of the full POC implementation. A documented or unsupported claim first receives an isolated acceptance spike. A rejected mandatory capability stops the native path.

| Capability | Classification | Evidence or required proof |
|---|---|---|
| Native Story signatures for `CombatIsActive`, `SavegameLoaded`, `GameModeStarted`, `EnteredCombat`, and `SwitchedCombat` exist in the installed game headers | **Verified locally** | Read-only local `story_header.div` inspection |
| Native status resources can express flat maximum HP, Attack, Saving Throw, AC, Spell DC, ActionPoint, and BonusActionPoint boosts | **Verified locally** | Read-only vanilla and installed native-mod package inspection |
| A native package can implement combat scaling without a Script Extender tree | **Verified locally** | Installed Tactician Enhanced package has native Story/Stats content and no Script Extender tree; its content is not a reuse source |
| Official Toolkit is installed on this machine | **Rejected** | Steam library and app-manifest inspection found no Toolkit installation before this project |
| Publish Local asks where to save a `.pak` and does not upload | **Documented but unverified locally** | Official Toolkit publishing documentation; local acceptance required after installation |
| `DB_PartyMembers` plus the approved exclusions produces the exact eligible roster | **Assumption/unsupported** | CAP-03 |
| Binary flat-HP statuses apply, acknowledge, query, and remove with exact maxima | **Assumption/unsupported** | CAP-04 and CAP-05 |
| Versioned Osiris database records survive a mid-combat save/load | **Assumption/unsupported** | CAP-06 |
| Merge event ordering supports pre-cleanup alias creation | **Assumption/unsupported** | CAP-07 |
| Host-authoritative Story application produces consistent client observations | **Assumption/unsupported** | RT-26 and RT-27 after separate install approval |

## Evidence boundary

Tactician Enhanced establishes that the broad native mechanism is feasible. No Tactician source, resource definition, localization, UUID, database name, status name, or other authored content may be copied. Every POC identifier and resource is independently authored under the `AESN_` or `DB_AESN_` namespaces.

