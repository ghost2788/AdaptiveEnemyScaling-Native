# AI-02: installed combat-mod audit and comparison plan

Date: 2026-09-03. Status: static audit complete for the scope below; runtime
cause unconfirmed. No installed packages, load order, campaign saves, or
gameplay source were changed by this audit.

## Scope and provenance

Exact installed packages were extracted into ignored
`artifacts/ai-audit-20260903/`: AES, 5.5e NPC Combat Overhaul,
DnD 5.5e All-in-One BEYOND, Expanded Armoury, Extra encounters and Minibosses,
Fade's Equipment Distribution, and Fade's Assorted Treasure Expansion.
Their module UUID/version metadata agrees with the skipped-turn save's active
module list. PAK presence alone is not evidence of activation; old proof PAKs
and Enemies Reworked were not treated as enabled mods.

Key installed fingerprints:

| Module | Version64 | SHA-256 of PAK |
| --- | --- | --- |
| AES | 36028797018963978 | 4ED446243B9E209093CC66EC677D55C2245A0E165449047F292E3F377108CCC3 |
| NPC Combat Overhaul | 36028797018963978 | 92ED2AD28CD8B593DE8C02A23FBE956A009D649F918C1BD030A46A843405772D |
| BEYOND | 145804063705923585 | F9C86F9375AE6FE42E5D3ED24A5329F630DFC2F03DB7FC7893BF7E9A697AA1DA |

Read-only reproduction helper: `.devspace/audit_combat_stats.py` (ignored).
Divine converted the NPC overhaul's six level-character LSFs into adjacent
derived LSX files in the audit artifacts, without touching the originals.

## Findings

### No demonstrated forced-turn-ending mechanism

The inspected extracted text did not reveal a direct forced EndTurn,
SetCanFight, or movement-disable call explaining encounter-wide skips.
The deployed AES production-goal list excludes its test harnesses. This is
not a decompilation of every compiled script or a proof that AES cannot
affect AI indirectly. Saved AES pending-state limitations remain documented
in AI-01, including the world-policy Building/finalize-pending observation.

### NPC overhaul and BEYOND are a concrete interaction axis

The installed NPC overhaul changes the kits of actors in this fight:
Thudd and several other duergar gain Push, Brithvar gains Sap, Drar gains
Push/Archery, and the sergeant gains Nick/Dual Wielder. Generic kit variants
also add Second Wind and its resource. These are full Passives/DefaultBoosts
field overrides, so inherited semantics matter even without duplicate names.

BEYOND supplies those mechanics and modifies common main/offhand attacks,
Nick's attack override and offhand-block condition, Second Wind costs,
rage behavior, spell-slot restrictions, and jumping. Specifically:

- `Projectile_Jump` uses `Movement:Distance`; this is the movement action,
  distinct from the `Target_Jump` spell.
- HeavyArmor's -3 movement is conditional on heavy armor and Strength below
  13, with an Armorer exemption. It is not a universal immobilization rule.
- Nick's helper story removes its status on a short timer after casting;
  the inspected helper does not call EndTurn.

These interactions justify a controlled test, not an accusation against either
mod. Dalthar's inspected saved status list lacks Relentless or an obvious
incapacitation status; the observed problem is not confined to Nere's grant.

### NPC level overrides preserve the inspected AI-related fields

Compared all six installed level-character overrides against the local vanilla
extract at `GhostsEnhancedEnemyTactics/.devspace/grymforge-census-source/`.
The substantive top-level change is each actor's Stats reference. Archetype,
AnubisConfigName, faction, spell-set/readiness fields where present, skill
lists, and transforms match that baseline. Other differences are translated
string version increments, Flag serialization type, omitted original-file
metadata, and one LayerList node's `key="MapKey"` serialization annotation.
Five child trees are structurally identical; the sixth differs only by that
annotation. No changed AI field was found in this comparison.

This baseline is a prior local extract, not a fresh verification against every
currently mounted base-game patch archive.

### Limited explicit stat-name collisions

Across the seven extracted packages, explicit shared stat-entry names were:
`MAG_WATCHER_Human_Crossbow`, `MAG_WATCHER_Human_Greataxe`, and `Throw_Throw`
(BEYOND versus Expanded Armoury). No AES entry-name collision was found.
This does not rule out inherited, resource, spell, equipment, or story
interactions. None of these collisions is established as the Nere failure.

### Installed BEYOND differs from recorded compatibility baseline

NPC overhaul's `config/upstream_lock.json` records BEYOND 4.12.10.7,
Version64 145804059410956295. The installed/save version is newer.
Compared generated Stats text against the local 4.12.10.7 census extract:
the focused common attacks, Nick/mastery markers, Second Wind, HeavyArmor,
normal jump, rage, and Dissonant Whispers definitions inspected here are
unchanged. Nine other existing non-section-marker definitions differ, and
new definitions include Conjurer/Enchanter features. This comparison does not
cover all non-Stats resources or establish whether a new feature participated
in this fight. Do not equate version drift with causation or recommend an
automatic downgrade.

## Controlled runtime comparison

The earlier symptom occurred after a saved budget proof was loaded and combat
continued. Test both fresh combat and reload, not only one round of a fresh
fight. The current bugged combat save is evidence, not the starting baseline.

1. **A: reproduce with current setup unchanged.** Start from PRE-NERE-FIGHT,
   keep the same difficulty, party, equipment, dialogue side, and opening
   approach. Keep Nere and enough duergar alive to observe at least four
   rounds, or the original failure point if later. Record the first skipped
   actor, round, approximate wait before the skip, visible conditions,
   coercion/fear events, and whether others still act. Do not deliberately
   add new crowd control as a diagnostic variable.
2. Save separately as `AI-A current fresh`. Reload that disposable save and
   continue two rounds (or until the symptom recurs), then save separately
   as `AI-A current reload`. Never overwrite PRE-NERE-FIGHT or previous proofs.
   A short recording of the first failure is better than only a final state.
3. **B: isolate AES behavior**, from the same untouched pre-fight save, with
   all other mods fixed. Prepare and verify a reversible diagnostic only
   after A's result. No existing on/off capability is assumed. An inert
   build must account for persisted AES facts/statuses and queued timers;
   merely omitting a goal or disabling the mod is not automatically a clean
   comparison. Preserve package/identity backups and verify the changed
   variable at runtime before interpreting B.
4. If skips persist without AES behavior, compare the NPC overhaul's kit
   changes next. Then isolate BEYOND if still needed. Keep dependent mods
   consistent with their dependency requirements; BEYOND removal can affect
   this party's subclasses/resources and should use a disposable compatible
   setup, not an in-place campaign uninstall.
5. Restore A to test reproducibility if a changed setup appears to fix the
   problem. One clean run is not proof of absence; one changed setup can
   alter encounter choices without removing the underlying bug.

Runtime A/B results are pending user-operated gameplay. Public release of
the current unshipped changes remains on hold. Coercion-related ally Hardened
is documented in AI-01 and deliberately deferred at the user's direction.

## A: live narration, not yet a completed/reloaded proof

The user narrated an unchanged fresh fight with numerous successful NPC turns:
Drar attacked/pushed Thudd into lava; Dalthar attacked twice; Thrinn attacked
and Action Surged; Greymaw enlarged/moved/dashed and attacked on a later turn;
Kur and Brithvar attacked; Nere attacked/cast/moved; the Mind Masters cast.
No encounter-wide skipped-turn failure was reported in this narrated segment.
One movement-only turn under Mind Mastery is not sufficient evidence of the
same failure. Exact round counts and engine events are not verified by a save.

Karlach was coerced again and acted against the party; Lae'zel was affected by
Dissonant Whispers and later Mind Mastery. Danna reportedly acquired Hardened
II while green. This remains consistent with the deferred hostility-witness
hypothesis, not proof of its precise transition.

User additionally raised separate balance/UI concerns: Nere at 212 HP,
Greymaw at 157 HP, desired trial targets about 150 and 100; six HP-tooltip
lines of 64/32/8/4/2/1 on Nere. Those sum to 111 flat added HP, consistent
with 101 before AES and floor(101 * 210 / 100) = 212. No balancing or tooltip
change was made during the AI baseline. Reload comparison remains pending.

## A: user-reported reload result

The user subsequently confirmed the unchanged mid-combat reload test was
completed: everyone continued taking turns normally, with Karlach coerced
twice and no skipped turns reported. Thus the symptom did not reproduce in
this fresh/reloaded comparison; its cause remains unidentified. This does not
exonerate any individual mod or prove an intermittent issue fixed. No AES-off
or BEYOND-off comparison was performed. Evidence saves remain available.
The user withdrew the HP-reduction proposal and explicitly retained current
balance. Coercion eligibility remains deferred. After confirming game exit,
the user authorized the separate UI-01 isolated boost proof preparation.
