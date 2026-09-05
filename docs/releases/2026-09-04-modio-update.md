# Adaptive Enemy Scaling — cleaner HP tooltips and Relentless priority

## Changelog — paste into the new mod.io file

- Newly applied AES health bonuses now appear as one clearly named HP tooltip line instead of several separate entries.
- Relentless now prioritizes eligible bosses and designated elite enemies, including Nere, within the existing encounter limits.
- Fixed a budget-accounting issue that could allow more Relentless recipients than intended.
- Ensured Relentless works with the new single-line HP bonus format.
- HP scaling amounts and Hardened combat bonuses are unchanged.

## Maintainer upload checkpoint

- Upload through the existing Adaptive Enemy Scaling Toolkit project, not a new project/listing.
- Verified original module UUID: a4567f52-1665-df50-b84c-3992f80fdb90.
- Verified original mod.io PublishHandle: 6353123.
- Tested local version: 1.0.0.19. Record the version actually produced by online Publish; auto-increment may advance it.
- Tested package SHA256: 885B13BA866ED30FC3D81A268875F6E5B0A8ECF86736CCFF90F4FBDD895105E6.
- Compiled Story SHA256: D159A0FED49938E61BECF5D79B933EF7A1C90AF5E4E8FBB22ACC621B27DFB96C.
- Compilation: 0 errors, 0 warnings. 14 production goals, no test harness goals.
- Source suite: 273 tests passed after the Relentless compatibility correction; independent scoped review approved.
- Retail evidence: one +111 AES HP line at212max on Nere, retained after reload; RelentlessI confirmed after the compatibility fix.
- Automatic cosmetic migration is not enabled. Legacy-format preservation was not conclusively tested; the user explicitly waived further old-save testing. Do not advertise a tested migration or universal save-compatibility guarantee.
- Before making the new file live, confirm it appears alongside the previous release on the original listing (with the existing subscribers/comments), not as a separate mod.
- Source work remains uncommitted in the isolated worktree; no merge or push performed by this upload-preparation step.
