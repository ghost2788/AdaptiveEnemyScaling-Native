# AESN Twin Threat Thumbnail and Repository Checkpoint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the generic balance-scale thumbnail with the approved Twin Threat Crest, preserve all intended AESN work in one verified local commit, and push that commit only to an explicitly configured remote.

**Architecture:** Compose the approved gold Hardened and cyan Relentless masters into one square raster asset using the built-in image-generation edit workflow. Preserve the previous thumbnail, install the selected output both in the repository and the live Toolkit project, validate the complete mod and staged Git snapshot, then commit. The repository currently has no configured remote, so pushing is a gated final step that requires an exact remote URL.

**Tech Stack:** Built-in image generation, PNG/RGBA assets, PowerShell/System.Drawing for deterministic sizing and previews, Python unittest contracts, Git, BG3 Toolkit project files.

---

### Task 1: Generate the Twin Threat master

**Files:**
- Read: `assets/icons/presentation-64-masters-v2/AESN_HardenedFoe_Band05-06_master.png`
- Read: `assets/icons/presentation-64-masters-v2/AESN_RelentlessFoe_Band03-04_master.png`
- Create: `assets/thumbnail-twin-threat-master.png`

- [ ] **Step 1: Inspect both approved reference masters**

Use `view_image` with original detail for both inputs. Confirm that the Hardened input is gold, the Relentless input is cyan, and both retain transparent exteriors plus dark internal infill.

- [ ] **Step 2: Generate one text-free square composite**

Use the built-in image-generation tool in `compositing` mode with both approved masters as reference images. Require the gold Hardened guardian in the lower-left, the cyan Relentless face in the upper-right, similar apparent size, slight central overlap, a near-black burgundy/navy background, and a restrained BG3-style circular gold frame. Explicitly prohibit text, scales, stat bars, arrows, particles, scenery, additional symbols, and extra characters.

- [ ] **Step 3: Inspect the generated composite at full resolution**

Use `view_image` at original detail. Reject any output with altered emblem identity, missing dark infill, lettering, transparency artifacts, or one emblem dominating more than roughly 60% of the combined crest.

- [ ] **Step 4: Save the selected master inside the repository**

Copy the selected built-in output to `assets/thumbnail-twin-threat-master.png`. Keep the generated original under the Codex generated-images directory as the generation receipt.

### Task 2: Install and verify the thumbnail

**Files:**
- Preserve: `assets/thumbnail-balance-scale-legacy.png`
- Modify: `assets/thumbnail.png`
- Modify: `B:/SteamLibrary/steamapps/common/Baldurs Gate 3/Data/Projects/AdaptiveEnemyScalingNativePOC_a4567f52-1665-df50-b84c-3992f80fdb90/thumbnail.png`
- Create: `.devspace/pro-base-preview/AESN-thumbnail-size-preview.png`

- [ ] **Step 1: Preserve the previous thumbnail**

Copy the current tracked `assets/thumbnail.png` to `assets/thumbnail-balance-scale-legacy.png` before replacement.

- [ ] **Step 2: Create the project-ready image deterministically**

Scale the approved master to exactly 1254×1254 with high-quality bicubic interpolation and save it as `assets/thumbnail.png`. The output must be a valid square PNG with a finished opaque background.

- [ ] **Step 3: Create a multi-size review sheet**

Render the new thumbnail at 256 px, 128 px, and 64 px on one dark preview sheet at `.devspace/pro-base-preview/AESN-thumbnail-size-preview.png`. Inspect it with `view_image`; both emblems must remain distinct at 64 px.

- [ ] **Step 4: Install the thumbnail in the live Toolkit project**

Copy `assets/thumbnail.png` to the exact live `Data/Projects/.../thumbnail.png` path. Verify the repository and live files have identical SHA-256 hashes.

### Task 3: Validate the complete AESN workspace

**Files:**
- Verify: `tests/`
- Verify: `toolkit/`
- Verify: `story/`

- [ ] **Step 1: Run the complete Python contract suite**

Run `python -m unittest discover -s tests -v` from the repository root. Expected result: all discovered tests pass with zero failures and zero errors.

- [ ] **Step 2: Run identity validation**

Run `python tests/validate_identities.py`. Expected result: eight tests pass.

- [ ] **Step 3: Parse the production localization XML**

Load `toolkit/Mods/AdaptiveEnemyScalingNativePOC_a4567f52-1665-df50-b84c-3992f80fdb90/Localization/English/AdaptiveEnemyScalingNativePOC.xml` as XML in PowerShell. Expected result: no parse exception.

- [ ] **Step 4: Verify the saved icon atlas**

Confirm the repository and live Toolkit copies of `AESN_ConditionIcons.dds` have identical SHA-256 hashes and that the DDS is 512×512 RGBA.

### Task 4: Create the complete local checkpoint

**Files:**
- Modify: `.gitignore`
- Stage: all intended tracked and untracked project work
- Exclude: `.devspace/`, `.superpowers/`, generated receipts outside the repository, caches, and other ignored temporary artifacts

- [ ] **Step 1: Ignore visual-companion session state**

Add `.superpowers/` to `.gitignore`; retain the existing `.devspace/`, cache, and generated-artifact exclusions.

- [ ] **Step 2: Stage all intended work**

Run `git add -A`, then inspect `git status --short`, `git diff --cached --stat`, and `git diff --cached --check`. Confirm that the staged snapshot contains the AESN Story, Stats, localization, tests, evidence, approved icon masters, atlas, thumbnail assets, docs, and tools, but no visual-companion or `.devspace` files.

- [ ] **Step 3: Create one local checkpoint commit**

Run `git commit -m "feat: implement adaptive enemy scaling production policy"`. Record the resulting commit hash.

- [ ] **Step 4: Verify the committed state**

Run `git status --short` and `git show --stat --oneline --summary HEAD`. Expected result: no unintended uncommitted project files and a commit containing the audited staged snapshot.

### Task 5: Push to the explicit remote

**Files:**
- No repository file changes

- [ ] **Step 1: Recheck configured remotes**

Run `git remote -v`. If no remote exists, stop and request the exact remote repository URL from the user; do not invent a destination or create a hosted repository.

- [ ] **Step 2: Configure only the user-supplied destination**

After the user supplies the exact URL, pass that value directly as the final argument to `git remote add origin`, without normalization or substitution, and verify the recorded destination with `git remote -v` before pushing.

- [ ] **Step 3: Push the current branch**

Run `git push -u origin codex/native-poc`. Verify the command exits successfully and report the pushed commit hash and branch.
