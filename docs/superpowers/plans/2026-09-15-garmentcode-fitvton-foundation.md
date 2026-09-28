# GarmentCode and FitVTON Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prepare and acquire the smallest verified public data/source foundation needed to begin the future GPU correction-validation phase.

**Architecture:** Keep external upstream code and upstream dataset bytes outside FitGround's generated evidence.  Use the existing Hugging Face client to download two revision-pinned, public datasets; retain a machine-readable acquisition receipt.  The existing correction schema remains the source of truth and no source is promoted to a calibrated action lattice without GPU calibration.

**Tech Stack:** Git, existing Python `.venv`, `huggingface_hub`, PowerShell, OpenSpec.

**Spec:** `openspec/changes/adopt-garmentcode-fitvton-foundation/`

## Global Constraints

- Do not use, print, save, or embed a credential; all selected sources are public.
- Do not download full GarmentCodeData v2, FIT-100K, Dress-ED, CLOTH3D, TailorNet, or VITON-HD.
- Do not run GPU physics, training, or create an outcome/realized measurement.
- Preserve all frozen historical evidence byte-for-byte.
- The repository has no `.git` directory; no worktree or commit operation is possible.

---

### Task 1: Lock the P0 route in project documentation

**Files:**
- Create: `docs/FITGROUND_DATA_FOUNDATION_v0.1.md`
- Modify: `README.md`
- Create: `openspec/changes/adopt-garmentcode-fitvton-foundation/*`

**Interfaces:**
- Consumes: public source metadata recorded in `reports/FITGROUND_V0_1_MATCHING_DATASET_SCOUT.md`
- Produces: P0 roles and exclusion boundary used by the acquisition receipt

- [ ] **Step 1: State the role and ceiling of each P0 source**

Document GarmentCode as the parametric substrate, FitVTON as a candidate pipeline bootstrap, GarmentCodeVTONDataset as a synthetic visual asset, FittingEffectDataset as a real visual probe, and FIT-Clean as auxiliary evidence.  State that none yet proves a centimeter-level correction action.

- [ ] **Step 2: State exclusions and storage locations**

Document `external/FitVTON-source`, `external/GarmentCode`, `data/external/GarmentCodeVTONDataset`, and `data/external/FittingEffectDataset`.  Name every prohibited full download.

- [ ] **Step 3: Review documentation assertions**

Run: `rg -n "GarmentCode|FitVTON|GarmentCodeVTONDataset|FittingEffectDataset|calibrated" README.md docs/FITGROUND_DATA_FOUNDATION_v0.1.md`

Expected: Every P0 assertion contains an explicit source role and limit.

### Task 2: Acquire the two source trees at auditable revisions

**Files:**
- Create: `external/FitVTON-source.zip` and `external/FitVTON-source-tree/` (fixed-commit archive and extracted tree)
- Create: `external/GarmentCode-source.zip` and `external/GarmentCode-source-tree/` (fixed-commit archive and extracted tree)

**Interfaces:**
- Consumes: public GitHub URLs
- Produces: local source archives and extracted trees whose fixed commits and SHA-256 hashes are written to the receipt

- [ ] **Step 1: Resolve remote heads**

Run: `git ls-remote https://github.com/ZenoNing/FitVTON.git HEAD` and `git ls-remote https://github.com/maria-korosteleva/GarmentCode.git HEAD`.

Expected: One immutable SHA per remote.

- [ ] **Step 2: Acquire only the declared fixed-commit source archive**

Run: `Invoke-WebRequest https://api.github.com/repos/ZenoNing/FitVTON/zipball/<fitvton-commit> -OutFile external/FitVTON-source.zip` and the equivalent GarmentCode fixed-commit URI.

Expected: Both ZIPs pass `tar -tf`, extract into fresh directories, and have SHA-256 values in the receipt.  Do not initialize recursive submodules or LFS blobs.

- [ ] **Step 3: Check archive hashes**

Run: `Get-FileHash -Algorithm SHA256 external/FitVTON-source.zip,external/GarmentCode-source.zip`.

Expected: The receipt and locally calculated hashes match; archive acquisition creates no Git remote.

### Task 3: Download exactly the two approved public datasets

**Files:**
- Create: `data/external/GarmentCodeVTONDataset/` (downloaded external source)
- Create: `data/external/FittingEffectDataset/` (downloaded external source)

**Interfaces:**
- Consumes: `huggingface_hub.snapshot_download(repo_id, repo_type="dataset", revision, local_dir)`
- Produces: resumable, revision-pinned local snapshots

- [ ] **Step 1: Preflight destinations and free storage**

Run PowerShell `Test-Path` checks for both target directories and `Get-PSDrive D`.

Expected: Target directories do not already exist and free storage materially exceeds 5,448,355,528 bytes.

- [ ] **Step 2: Download GarmentCodeVTONDataset**

Run the project venv's Python with `snapshot_download(repo_id="ZenoNing/GarmentCodeVTONDataset", repo_type="dataset", revision="f51b54db869fc4b1a7f32b017cdbfa80cb22956a", local_dir="data/external/GarmentCodeVTONDataset", token=False, max_workers=32)` after setting a repository-local HF cache.

Expected: The command exits successfully and records Hugging Face local download metadata for resume.

- [ ] **Step 3: Download FittingEffectDataset**

Run the project venv's Python with `snapshot_download(repo_id="ZenoNing/FittingEffectDataset", repo_type="dataset", revision="a1de636764dd7ce848737752e918ab3eec02ff03", local_dir="data/external/FittingEffectDataset")`.

Expected: The command exits successfully and records Hugging Face local download metadata for resume.

### Task 4: Produce the receipt and verify the unchanged codebase

**Files:**
- Create: `artifacts/FITGROUND_V0_1_P0_SOURCE_ACQUISITION.json`

**Interfaces:**
- Consumes: repository `HEAD`, Hugging Face revisions, and regular-file byte counts
- Produces: external-source receipt for GPU-machine recreation

- [ ] **Step 1: Measure only regular payload files**

Run PowerShell `Get-ChildItem -File -Recurse` counts and lengths for each data source, excluding neither payloads nor partials without recording the rule.

Expected: Both observed totals are non-zero; values are compared to the public API totals, allowing local metadata overhead.

- [ ] **Step 2: Write receipt with actual values**

Record canonical URLs, revisions, expected and observed totals, local paths, non-gated/public acquisition condition, role, and the explicit no-calibration limitation.

- [ ] **Step 3: Run regression checks**

Run: `.\\.venv\\Scripts\\python.exe -m pytest -q`

Expected: `58 passed, 2 skipped` or a failure explained as unrelated pre-existing environment drift.

## Plan Review

- Spec coverage: Task 1 covers source roles and exclusions; Tasks 2–3 cover revision-pinned acquisition; Task 4 covers receipt and regression evidence.
- Placeholder scan: no `TBD`, `TODO`, or deferred implementation terms remain.
- Type consistency: no new runtime interfaces are introduced; the only API call is the documented `snapshot_download` signature.
