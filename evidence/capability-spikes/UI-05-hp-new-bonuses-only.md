# UI-05 — HP total rollout: new bonuses only

## Candidate behavior

`AESN_00_Init.txt` enables `DB_AESN_HpTotalIntegrationEnabled(1)` both for a
fresh Story initialization and when `SavegameLoaded()` opens an established
campaign.  The typed declaration remains in `AESN_40_HpTransaction.txt`.
Consequently, newly planned allocations use representation 2 and the single
`AESN_HP_TOTAL_<delta>` status.

This is not automatic migration.  No activation rule enables
`DB_AESN_HpMigrationEnabled`, clears a migration hold or journal, applies or
removes a status, or writes current HP.  Existing valid representation-1 rows
remain committed and reload through the existing observation-only recovery
path.  An old campaign can therefore contain legacy committed bonuses while
later policy replans and newly encountered enemies use representation 2.

The UI-05 legacy baseline contains Nere under one owner with both a v1
`Planned` row and a v1 `HPCommitted` row, plus the exact 64+32+8+4+2+1 bit
ownership for delta 111.  The present v1 `QRY_AESN_HpCommittedIdentity` is an
unconditional compatibility query, so ordinary reconciliation does **not**
classify that duplicate-state record as an inconsistency.  This candidate does
not repair, convert, or otherwise reinterpret that historical state.

## Candidate staging gates

`tools/sync_toolkit_project.ps1` remains restricted to the exact verified
Toolkit Data root and refuses the live Mods directory.  Before it copies any
file it requires the deterministic `hp_catalog.py` semantic check and candidate
SHA-256 `F54D4F4304F46E54976D206917D1FD30FB8226009C776DB1494C85553E47817A`.
It stages the approved catalog plus production goals including `45` and `47`.
It validates existing Toolkit module UUID/PublishHandle metadata and preserves
that metadata rather than replacing it with repository metadata.

The production cleanup is an explicit inventory only: known proof goals and
proof stats (including the externally sourced `AESN_84_HpIntegrationProof`)
are removed, while unrelated Toolkit files are retained.  A missing source,
bad catalog, metadata mismatch, or wrong root stops before mutation.

## Safety boundary

Focused source tests exercise rule facts with explicit native observations;
they do not simulate or prove native engine effects.  The candidate has not
been staged to the live root, packaged, loaded, or verified in normal play.
Normal-play acceptance still requires the controller's exact candidate staging,
an untouched campaign save, Toolkit compilation, and runtime observation.
