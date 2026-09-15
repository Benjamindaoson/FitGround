# Run 11 — Controlled Counterfactual Generation Contract

**Date:** 2026-09-11  
**Machine:** Windows, CPU only  
**Did not run:** GPU generation, VLM training, large downloads, FIT-Clean edits

---

## Question

Can FitGround upgrade Phase 2’s observational limitation into a **controlled intervention benchmark design** that a later GPU agent can execute as a small generation pilot — without claiming unverified FIT capabilities?

---

## Context

Read in priority order: FIT-Clean fingerprint (SHA256 match to freeze), data contract, quality rules, Phase 2 inherited counts (user freeze; v0.1 markdown not in this checkout), Experimental Contract v0.1 not overwritten.

Compact pack: `docs/context/PHASE_2_5_CONTEXT.md`

Scientific object changed from “find more released pairs” to:

`P(Y | do(measurement change), controlled context)`

---

## Evidence Used

- Frozen FIT-Clean v0.1 fingerprint and Phase 2 counts (inherited, not recomputed)
- FIT paper + project page + HF card (2026-09-11 fetch)
- Public GarmentCode @ `d449629979028123a5c4dc9e732a2ec19b7fce31`
- Absence of a public FIT generator repository (Johanna Karras GitHub + project-page “will release” language)

---

## What Was Verified

| Claim | Level |
|-------|-------|
| Released FIT-100K is not a same-cloth measurement experiment | VERIFIED (Phase 2 freeze) |
| TIER C appearance co-varies with measurements | VERIFIED (Phase 2 freeze) |
| FIT documents GarmentCode cross-drape with body/design held, size changed | VERIFIED_FROM_DOCS |
| Official `I_g` is VLM try-off from sized try-on | VERIFIED_FROM_DOCS |
| `pattern_fitter.py` can freeze design and vary bodies | VERIFIED_FROM_CODE |
| S/M/L are visualization labels, not Fit-VTO training targets | VERIFIED_FROM_DOCS |
| Measurement dimensions are correlated under resizing | VERIFIED_FROM_DOCS + Phase 2 freeze |
| Tightness poorly differentiated in GarmentCode | VERIFIED_FROM_DOCS |
| Official FIT generation code publicly released | **Not verified — not found** |

---

## What Was Rejected

- Mining released FIT-100K as the path to identification
- “Same garment design ⇒ appearance fixed”
- Univariate bust `do()` as the default intervention
- Treating unpublished Flux LoRA / Nano Banana Pro as a runnable official pipeline
- VLM self-labeling of visual fit
- Any training authorization (LoRA/RM/DPO/GRPO)

---

## Design Decision

Frozen **Experimental Contract v0.2**:

- PRIMARY Track A: measurement-isolated canonical/normalized cloth (FitGround overlay; not official FIT output)
- SECONDARY Track B: naturalistic size-specific cloth
- Unit: Controlled Fit Ladder, TIGHT → REGULAR → LOOSE, **measurement vector**
- GPU E0 Stage 1: 3×5×3 = 45 GarmentCode conditions; Stage 2 blocked
- Pre-registered GO/PARTIAL/NO-GO and shortcut attacks
- Paired/repeated-measures statistical plan locked before GPU results

Verdict: **CONTROLLED_COUNTERFACTUAL_GENERATION = PARTIAL**  
**READY_FOR_GPU_E0 = YES** (Stage 1 only)

---

## Remaining Unknowns

- Bit-exact Warp / GPU simulation reproducibility
- Whether FIT box-mesh realignment can be re-implemented without authors’ code
- Whether Track A bbox-normalized cloth still leaks size via proportions
- Photoreal Sim2Real seeds, checkpoints, identity preservation
- Human visibility of TIGHT vs REGULAR (authors expect weakness)

---

## Artifacts

- `docs/context/PHASE_2_5_CONTEXT.md`
- `reports/FIT_GENERATION_MECHANISM_AUDIT.md`
- `artifacts/control_variable_matrix_v0.2.yaml`
- `artifacts/controlled_fit_ladder_schema_v0.2.yaml`
- `artifacts/gpu_e0_pilot_v0.2.yaml`
- `docs/EXPERIMENTAL_CONTRACT_v0.2.md`
- `artifacts/experimental_contract_v0.2.yaml`
- `reports/decision_log_phase_2_5.md`
- `src/fitground/contracts/__init__.py`
- `tests/test_experimental_contract_v02.py`

FIT-Clean v0.1 and Experimental Contract v0.1 were not modified.

---

## Verification

- Mechanism audit tagged VERIFIED_FROM_CODE / DOCS / INFERRED / UNKNOWN
- Contract validator tests added
- `pytest`: **33 passed, 2 skipped** (eval shards not materialized). Windows RSS/disk defaults restored so Linux `/workspace` and `/proc` assumptions do not fail on this machine.

---

## Next Gate

**Only allowed GPU task:** GPU E0 Stage 1 — Controlled Counterfactual Generation Pilot.

Do not train. Do not download FIT-100K at scale. Do not start Stage 2 Sim2Real.
