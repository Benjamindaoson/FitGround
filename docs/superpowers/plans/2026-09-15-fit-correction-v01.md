# FitGround v0.1 Correction Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reposition FitGround as a technical-designer correction copilot and supply a tested, dry-run-safe V0.1 correction contract without changing frozen legacy evidence.

**Architecture:** FIT-Clean remains an immutable source/provenance asset. A new pure-Python `fitground.correction` boundary validates state and actions, generates deterministic lattice entries with `NOT_RUN` outcomes, and leaves GarmentCode mapping and physics execution explicitly unverified. Small CLIs serialize only plans or preserved failure artifacts.

**Tech Stack:** Python 3.11+, standard-library dataclasses/JSON/hashlib, PyYAML already installed, pytest.

**Spec:** `openspec/changes/migrate-fit-correction-v01/`

## Global Constraints

- Do not modify FIT-Clean v0.1, Experimental Contract v0.1/v0.2, GPU E0 v0.2.1, or generated historical evidence.
- Do not start GPU/physics work, download data, train a model, or fabricate realized deltas/outcomes.
- V0.1 action families are exactly `bust_circumference_delta_cm`, `shoulder_width_delta_cm`, and `sleeve_length_delta_cm`.
- Default local output status is `NOT_RUN` / `NOT_VERIFIED`.
- Use no new runtime dependency.

---

### Task 1: Make the current source tree installable

**Files:**
- Create: `pyproject.toml`
- Test: `tests/test_project_install.py`

**Interfaces:**
- Produces: editable package discovery for `src/fitground`.

- [ ] **Step 1: Write the failing test**

```python
def test_project_metadata_declares_src_package() -> None:
    assert (ROOT / "pyproject.toml").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_project_install.py -q`

- [ ] **Step 3: Write minimal implementation**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
```

- [ ] **Step 4: Run install and test**

Run: `python -m pip install --no-deps -e .; python -m pytest tests/test_project_install.py -q`

### Task 2: Add pure correction contracts

**Files:**
- Create: `src/fitground/correction/__init__.py`
- Create: `src/fitground/correction/schema.py`
- Create: `src/fitground/correction/api.py`
- Test: `tests/test_correction_schema.py`

**Interfaces:**
- Produces: `CurrentFitState`, `CandidateCorrection`, `PredictedFitOutcome`, `CauseHypothesis`, `CorrectionLattice`, `apply_correction()`.

- [ ] **Step 1: Write failing tests**

```python
def test_candidate_preserves_missing_realized_delta() -> None:
    candidate = apply_correction({}, "bust_circumference_delta_cm", 3.0)
    assert candidate.intended_delta_cm == 3.0
    assert candidate.realized_delta_cm is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_correction_schema.py -q`

- [ ] **Step 3: Write minimal implementation**

```python
SUPPORTED_ACTION_FAMILIES = ("bust_circumference_delta_cm", "shoulder_width_delta_cm", "sleeve_length_delta_cm")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_correction_schema.py -q`

### Task 3: Add lattice, calibration, and runner dry-run boundaries

**Files:**
- Create: `src/fitground/correction/lattice.py`
- Create: `src/fitground/correction/validation.py`
- Create: `scripts/build_correction_lattice.py`
- Create: `scripts/validate_correction_lattice.py`
- Create: `scripts/calibrate_correction_action.py`
- Create: `scripts/run_fit_correction_smoke.py`
- Create: `artifacts/fit_correction_smoke_plan_v0.1.yaml`
- Test: `tests/test_correction_scripts.py`

**Interfaces:**
- Produces: deterministic `NOT_RUN` lattice entries, non-fabricated calibration dry-runs, and resume-safe failure artifacts.

- [ ] **Step 1: Write failing tests**

```python
def test_smoke_runner_dry_run_never_claims_simulation(tmp_path: Path) -> None:
    payload = run_script("--dry-run", "--case", "CHEST_CASE")
    assert payload["simulation_status"] == "NOT_RUN"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_correction_scripts.py -q`

- [ ] **Step 3: Write minimal implementation**

```python
if args.dry_run:
    return {"simulation_status": "NOT_RUN", "backend_status": "NOT_VERIFIED"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_correction_scripts.py -q`

### Task 4: Publish contracts, migration evidence, and README

**Files:**
- Create: `docs/FITGROUND_PRODUCT_CONTRACT_v0.1.md`
- Create: `docs/FITGROUND_TECHNICAL_CONTRACT_v0.1.md`
- Create: `reports/FITGROUND_V0_1_CODEBASE_AUDIT.md`
- Create: `reports/FITGROUND_V0_1_MIGRATION_MATRIX.md`
- Create: `reports/FITGROUND_V0_1_PRE_GPU_READINESS.md`
- Create: `README.md`
- Test: `tests/test_legacy_preservation.py`

**Interfaces:**
- Produces: frozen product scope and a hash check over historic contract artifacts.

- [ ] **Step 1: Write the failing preservation test**

```python
def test_frozen_legacy_bytes_are_unchanged() -> None:
    assert sha256(FROZEN_PATH) == EXPECTED_SHA256
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_legacy_preservation.py -q`

- [ ] **Step 3: Write required documentation without editing protected files**

```markdown
## Evolution / Legacy Research Foundation
FIT-Clean and GPU E0 are preserved as historical evidence and simulation sanity foundations.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_legacy_preservation.py -q`

### Task 5: Verify migration boundaries

**Files:**
- Modify: `openspec/changes/migrate-fit-correction-v01/tasks.md`

- [ ] **Step 1: Install from current workspace**

Run: `python -m pip install --no-deps -e .`

- [ ] **Step 2: Run complete local suite**

Run: `python -m pytest -q`

- [ ] **Step 3: Run smoke dry-run and lattice validation**

Run: `python scripts/run_fit_correction_smoke.py --dry-run --case CHEST_CASE --output-dir <temporary-dir>`

- [ ] **Step 4: Verify frozen hashes and final file review**

Run: `python -m pytest tests/test_legacy_preservation.py -q; git status --short`
