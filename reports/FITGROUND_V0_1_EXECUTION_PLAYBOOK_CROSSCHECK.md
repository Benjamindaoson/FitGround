# FitGround V0.1 Execution Playbook Cross-Check

**Checked:** 2026-09-15
**Reference:** `FitGround_企业AI_Fit_Correction_完整执行方案_v0.1.pdf`
**Method:** repository source and tests were checked against the playbook's product, action-space, lattice, evidence, local/GPU-boundary, and Phase-1-gate requirements. The PDF is a reference specification; it did not authorize a simulation run, a model-training run, or replacement of frozen historical evidence.

## Result

The local correction-contract implementation now matches the playbook's local, pre-GPU requirements. It is deliberately **not a runnable GarmentCode/Warp/Blender correction backend**. Consequently, it can safely plan, validate, and preserve a V0.1 smoke run, but it cannot yet execute or simulate a correction on a GPU.

| Playbook requirement | Local status | Evidence / result |
|---|---|---|
| Current-sample-to-next-correction product framing | PASS | Product contract and README describe `(s, a) -> s'`, not a tight/regular/loose classifier. |
| Three exact V0.1 action families; no ambiguous armhole action | PASS | `SUPPORTED_ACTION_FAMILIES` and tests reject unsupported `armhole_delta_cm`. |
| Intended delta distinct from realized delta | PASS | Planning API always emits `realized_delta_cm: null`; calibration dry-run does the same. |
| CurrentFitState carries body, garment, visual, material, type, intent, regional state, provenance | PASS | `CurrentFitState` validates all fields and rejects missing visual evidence. |
| CauseHypothesis is hypothesis rather than absolute physical truth | PASS | Explicit confidence, supporting evidence, and verification status are represented. |
| Correction Lattice carries candidate action, outcome, utility/oracle/ranking, verification, provenance | PASS after repair | `ranking` is now explicit and must be a unique permutation of candidates. |
| Outcome carries simulation, render, reproducibility, and hash evidence | PASS after repair | `PredictedFitOutcome` now has `simulation_status`, `render_status`, `reproducibility`, and `hashes`; unrun entries remain explicit `NOT_RUN`. |
| Machine-readable schemas cover all five required schema objects | PASS after repair | JSON Schema now declares `CurrentFitState`, `CauseHypothesis`, `CandidateCorrection`, `PredictedFitOutcome`, and `CorrectionLattice` (plus status enums). |
| No fabricated simulation/realized measurement | PASS | Dry-run output has `simulation_status: NOT_RUN`, `render_status: NOT_RUN`, and `realized_delta_cm: null`. |
| Chest / shoulder / sleeve smoke plan with treatment and control actions | PASS | `artifacts/fit_correction_smoke_plan_v0.1.yaml`; CHEST dry-run emitted 5 planned actions. |
| Failure preservation and resume | PASS | Runner writes a `SIMULATION_BACKEND_NOT_CONFIGURED` artifact when invoked without `--dry-run`; regression test confirms resume does not overwrite it. |
| Phase-1 action executability, measurement accuracy, monotonicity, locality, outcome sensitivity, reproducibility | NOT YET EXECUTABLE | These are GPU empirical gates. No result has been claimed. |
| GarmentCode/Warp/Blender action backend | MISSING | This checkout has no public-GarmentCode integration, named pattern-parameter mapping, realized-measurement extraction, simulator, renderer, or outcome extractor. |
| Complete GPU one-command execution | BLOCKED | The runner intentionally stops with a preserved failure artifact until the backend above is implemented and calibrated. |
| Frozen FIT-Clean / experimental / GPU-E0 evidence | PASS | `tests/test_legacy_preservation.py` verifies all 12 protected SHA-256 values. |
| Git traceability | BLOCKED BY CHECKOUT | `D:\FitGround` has no `.git`; branch, commit SHA, and clean state cannot be established locally. Lattice provenance records `UNAVAILABLE_AT_CHECKOUT` rather than inventing a SHA. |

## Repair made during this cross-check

The previous correction implementation omitted several required playbook fields despite otherwise having the right safety boundary. The following minimal, non-simulation changes were made:

- Added `render_status`, `reproducibility`, and `hashes` to `PredictedFitOutcome`.
- Added `ranking` to `CorrectionLattice` and validated it as a unique full candidate ordering.
- Required lattice provenance keys: `git_sha`, `environment`, `seed`, `source_assets`, and `artifact_paths`.
- Expanded the JSON Schema to include all V0.1 contract objects.
- Added regression tests for these contract fields and for schema coverage.

No frozen artifact, simulator output, realized measurement, or historical report was changed.

## Verification evidence

| Check | Result |
|---|---|
| `python -m pytest -q` | **58 passed, 2 skipped** (the two skips are existing absent local evaluation shards) |
| Correction code and tests Ruff check | PASS |
| `openspec validate migrate-fit-correction-v01 --strict` | PASS |
| `python -m pip check` | PASS |
| `run_fit_correction_smoke.py --dry-run --case CHEST_CASE ...` | PASS; only planned/`NOT_RUN` output written |
| Legacy protection test | PASS as part of full suite |
| `ruff check .` | **82 pre-existing repository-wide lint findings**; the V0.1 correction code, its CLIs, and its tests are clean. These legacy findings were not auto-fixed because they span historical modules and may alter frozen research paths. |

## Data download decision

The repository's declared source is **Hugging Face**, not DHub:

```text
Yuanhao-Harry-Wang/fitvto-100k
revision: 5563646729edf148ed2b32c4b9c794d51a1bc828
```

Live metadata check returned 428 files totaling **211,503,595,815 bytes (196.98 GiB)**. The current local `data/` tree is only **52,300,374 bytes** and contains processed/sample material, not a complete raw dataset. The full source was **not downloaded**: it is neither small nor part of the newly frozen correction smoke gate, and downloading it would conflict with the repository's established streaming/ephemeral strategy.

## GPU handoff decision

`READY_FOR_GPU = NO` for the V0.1 correction smoke. The only product blocker is a calibrated atomic simulation backend that can, for one exact V0.1 action family:

```text
named pattern parameter mutation
-> realized garment measurement
-> physics simulation
-> render
-> regional outcome and side-effect extraction
-> hashes and reproducibility evidence
```

The old `gpu-e0-ready-v0.2.1` history is preserved as a legacy controlled-ladder execution baseline. It does not make the new correction backend exist and must not be relabeled as a V0.1 correction result.
