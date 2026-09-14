# FitGround Technical Contract v0.1

**Status:** FROZEN FOR PRE-GPU CORRECTION FOUNDATION
**Machine-readable schema:** `schemas/fit_correction_v0.1.schema.json`
**Reference implementation:** `src/fitground/correction/`

## Shared semantics

- `NOT_RUN`: no simulation was executed; it has no extracted after-state, utility, or oracle.
- `NOT_VERIFIED`: a planned action or hypothesis has not been confirmed by a calibrated simulator/backend.
- `SIMULATED`: a backend has emitted an after-state; this status is reserved for a future verified runner.
- `FAILED`: an attempted execution failed; the failure artifact must be preserved.
- `intended_delta_cm` and `realized_delta_cm` are distinct. The latter is `null` until measured after an actual pattern/backend operation.
- A physics result is a **simulated outcome**, never real-world ground truth.

## CurrentFitState

Represents `s = (I, B, G, M, F)` for an already-observed sample.

| Field | Meaning |
|---|---|
| `state_id` | Stable caller-supplied state identifier |
| `body` | Body measurements and related metadata |
| `garment` | Garment measurements/geometry metadata |
| `visual_assets` | At least one image, render, mesh, or visual-evidence reference |
| `material` | Material properties/metadata |
| `garment_type` | Explicit garment type |
| `fit_intent` | Intended fit, such as regular or structured |
| `region_fit_state` | Current observed regional fit state |
| `provenance` | Source, hashes/IDs, and lineage references |

The schema requires visual evidence so a correction data asset cannot silently collapse into a measurement-only dataset.

## CauseHypothesis

| Field | Meaning |
|---|---|
| `cause` | A likely causal explanation, not an asserted absolute label |
| `supporting_evidence` | Observable visual, measurement, material, or intervention evidence |
| `confidence` | Optional calibrated confidence in `[0, 1]` |
| `verification_status` | Whether intervention evidence supports the hypothesis |

Diagnosis credibility is evaluated through intervention predictive validity: suitable actions should improve the predicted/simulated state more than unsuitable controls.

## CandidateCorrection

V0.1 permits only the following precise action families:

1. `bust_circumference_delta_cm`
2. `shoulder_width_delta_cm`
3. `sleeve_length_delta_cm`

| Field | Meaning |
|---|---|
| `action_family` | One V0.1 action family |
| `intended_delta_cm` | Requested non-zero change in centimetres |
| `realized_delta_cm` | Measured garment change in centimetres, or `null` |
| `source_pattern_parameters` | Future pattern mapping inputs; empty is allowed before calibration |
| `candidate_id` | Deterministic ID derived from state/action/intended delta |
| `verification_status` | `NOT_VERIFIED`, `VERIFIED`, or `FAILED` |

`apply_correction(garment, action_family, intended_delta_cm)` is a planning API only in this repository. It does not mutate a garment, map to GarmentCode, or imply a realized delta.

## PredictedFitOutcome

| Field | Meaning |
|---|---|
| `candidate_id` | Candidate correction that produced the entry |
| `region_before` | Current regional state |
| `region_after` | Predicted/extracted next state; required only for `SIMULATED` |
| `direction` / `magnitude` | Interpretable effect summary when available |
| `side_effects` | Explicit affected regions and issues |
| `confidence` | Optional model confidence |
| `simulation_status` | `NOT_RUN`, `SIMULATED`, or `FAILED` |
| `render_status` | `NOT_RUN`, `RENDERED`, `FAILED`, or `NOT_APPLICABLE` |
| `reproducibility` | Seed/environment/replay information; explicitly `NOT_RUN` before execution |
| `hashes` | Hashes of produced assets when present; empty only when no output artifact exists |
| `provenance` | Backend/version/hash lineage |

For `NOT_RUN`, `region_after`, `direction`, `magnitude`, side-effect claims, confidence, utility, and oracle remain unavailable rather than synthesized.

## CorrectionLattice

A `CorrectionLattice` binds one `state_id` to a unique set of candidate actions, one outcome entry per candidate, per-candidate utilities, an optional oracle action, optional ranking, verification status, and provenance. Its provenance always records `git_sha`, `environment`, `seed`, `source_assets`, and `artifact_paths`; `UNAVAILABLE_AT_CHECKOUT` and `NOT_RUN` are explicit non-claims rather than invented execution metadata.

The builder deterministically creates entries with:

```text
candidate action -> PredictedFitOutcome(simulation_status=NOT_RUN)
```

The validator distinguishes a structurally valid planned lattice from a complete simulated lattice. `--require-complete-outcomes` fails if any action lacks a `SIMULATED` outcome.

## Utility

When a future simulated after-state exists, selection uses:

```text
U(s', a) = - target_fit_error(s') - λ1 * modification_magnitude(a) - λ2 * side_effect_penalty(s')
```

No utility or `oracle_action` is valid for a `NOT_RUN` lattice.

## Calibration and verification boundary

`scripts/calibrate_correction_action.py` defines the future measurement loop:

```text
intended delta -> named pattern parameter change -> extracted realized delta
               -> error + cross-region effects
```

The script's local dry-run writes `realized_delta_cm: null`. `scripts/run_fit_correction_smoke.py` writes a plan under `--dry-run`, and otherwise preserves a `SIMULATION_BACKEND_NOT_CONFIGURED` failure artifact until a verified backend is configured.
