# FitGround

FitGround is an AI fit-correction copilot for technical designers that uses body measurements, garment data, visual fit evidence, material, and fit intent to diagnose likely fit causes, predict the consequences of candidate modifications, and recommend the correction most likely to make the next sample fit correctly.

## Business Problem

A current sample has a fit problem. The expensive decision is not whether it looks tight or loose; it is what to change in the next sample, by how much, and with what risk of moving the problem somewhere else.

## Intended Workflow

```text
Current fit visual / 3D evidence + body + garment + material + fit intent
  -> likely cause hypothesis
  -> compare precise candidate corrections
  -> predict next fit state and side effects
  -> physics-based simulated verification
  -> select the lowest-regret correction
```

V0.1 candidate actions are deliberately small: bust circumference delta, shoulder width delta, and sleeve length delta. The core learning target is `(current_state, candidate_action) -> predicted_next_state`, then correction selection.

## Core AI Architecture

- **Multimodal Fit Transition Model:** predicts the next fit state after a candidate correction.
- **Cause hypothesis:** a likely explanation with evidence, validated through intervention prediction rather than declared as absolute ground truth.
- **Correction lattice:** a current state plus alternative actions, simulated outcomes, side effects, utility, and oracle correction when simulation exists.
- **Physics-based simulated verifier:** creates and checks before/modification/after evidence. It is not real-world ground truth.

The existing runtime architecture audit diagram is available at [FITGROUND_EXISTING_RUNTIME_ARCHITECTURE.html](docs/architecture/FITGROUND_EXISTING_RUNTIME_ARCHITECTURE.html).

## Existing Assets

- **FIT-Clean v0.1:** immutable observational source, quality checks, canonical measurements, image identities, provenance, and fingerprints.
- **Legacy counterfactual matching:** evidence about paired FIT observations; useful for analysis, not an intervention lattice.
- **Controlled Fit Ladder / GPU E0 contract:** retained as `LEGACY / SIMULATION SANITY / INTERVENTION FOUNDATION`. Its TIGHT/REGULAR/LOOSE sizing conditions are not direct calibrated V0.1 actions.
- **Correction foundation:** validated local schemas, deterministic lattice builder, calibration dry-run, and failure-preserving GPU smoke runner scaffold.
- **P0 synthetic-physics route:** GarmentCode is the parametric/calibration substrate and FitVTON is a candidate GarmentCodeV2/Warp pipeline bootstrap.  Its two small public companion datasets are acquired as synthetic visual bootstrap and real-visual probe assets; neither is yet a centimeter-calibrated correction lattice.

## Current Status

The local repository is prepared for pre-GPU correction work. It has **no configured GarmentCode-to-action mapping, simulator, renderer, or calibrated realized measurements**. Consequently, locally built outcomes remain `NOT_RUN`, corrections remain `NOT_VERIFIED`, and `READY_FOR_GPU` is currently `NO`.

## Evidence / Validation

- [Product Contract](docs/FITGROUND_PRODUCT_CONTRACT_v0.1.md)
- [Technical Contract](docs/FITGROUND_TECHNICAL_CONTRACT_v0.1.md)
- [Codebase Audit](reports/FITGROUND_V0_1_CODEBASE_AUDIT.md)
- [Migration Matrix](reports/FITGROUND_V0_1_MIGRATION_MATRIX.md)
- [Pre-GPU Readiness](reports/FITGROUND_V0_1_PRE_GPU_READINESS.md)
- [Data Foundation](docs/FITGROUND_DATA_FOUNDATION_v0.1.md)
- [Matching Dataset Scout](reports/FITGROUND_V0_1_MATCHING_DATASET_SCOUT.md)

## Quick Start

```powershell
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\run_fit_correction_smoke.py --dry-run --case CHEST_CASE --output-dir .\local_runs
```

The non-dry-run smoke command deliberately fails with a preserved artifact until a verified simulation backend is supplied.

## Evolution / Legacy Research Foundation

Historical reports, FIT-Clean v0.1, Experimental Contract v0.1/v0.2, GPU E0 Execution Addendum v0.2.1, and the `gpu-e0-ready-v0.2.1` baseline are preserved rather than rewritten. They document prior measurement-grounding and controlled-ladder research; they do not redefine the FitGround correction product.
