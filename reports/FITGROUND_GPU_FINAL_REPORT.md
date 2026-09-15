# FitGround GPU final report (v0.1 execution)

## Executive summary

FitGround v0.1 on this RTX 4090 machine now has a measured `(s, a) -> s` path for bust circumference on a GarmentCode t-shirt:

shirt.width.v mutation -> 2D panel measurement (realized_delta_cm) -> Warp XPBD on mean_all.obj -> PNG render -> utility ranking.

Oracle on the enumerated CHEST_CASE (target = baseline bust + 3 cm) is bust_plus_3cm. Shoulder/sleeve controls are NOT_VERIFIED. Overall bust gate is PARTIAL because shirt.width.v scales full torso girth (waist tracks bust).

PyTorch CUDA is PARTIAL (NVIDIA CDN). SMPL-X parametric bodies are BLOCKED (licensed files absent). MLLM SFT/RLVR are NOT_JUSTIFIED.

## Environment

- Host daka5svhri0c73etu4ug-fitground, RTX 4090 24GB, driver 580.95.05
- fitground-core Python 3.11.16: pytest 58 passed, 2 skipped, pip check PASS
- flux Python 3.10.21, nvcc 12.6.85, numpy 2.2.6
- Warp 1.0.0-beta.6, warp.so SHA256 9e61637a8868fd7813e75d1601119c8aa91b76f0d2e766a6296fcfee8edb2c8c
- FitGround source archive commit c1dcca938e1e5d0f308ca496a12574a024831ab1 (no .git)
- FitVTON 17078c64cc6f6984466bc31916e40421d97f3280
- GarmentCode d449629979028123a5c4dc9e732a2ec19b7fce31

## Data provenance

- data/processed/fit_clean_v0.1.parquet: 105000 rows observational FIT-derived table. Images not on disk.
- No FIT-100K download.
- Frozen FIT-Clean / E0 artifacts were not modified.

## Physics backend

Static-body Warp XPBD in FitVTON GarmentCodeV2. Smoke PASS. Lattice +1/+2/+3 each SIMULATED+RENDERED in about 11s after kernel cache. Body-cloth intersections 0.

## Calibration

See reports/BUST_ATOMIC_CALIBRATION.md. Inverse map: delta(width.v) = delta_cm / body_bust_cm.

## Correction lattice

artifacts/correction_lattice_chest_case.json. Utility = -target_error - 0.15*|edit| - 0.5*(|sleeve|+|length|). Oracle: bust +3 cm.

## Baselines

Observational forward prediction of garment_bust_cm (person-grouped split, not intervention):

- B0: test MAE 8.11 cm, RMSE 10.94 cm
- B1 OLS: test MAE 8.08 cm, RMSE 10.27 cm
- B2/B3: NOT_RUN (no local images)

## Vision necessity

MLLM NECESSITY NOT ESTABLISHED. No visual-disambiguation experiment with images on disk.

## MLLM / RLVR

NOT_JUSTIFIED: 3 verified bust actions is not an SFT corpus. Physics verifier exists but residual optimization gap is not characterized.

## Failure cases

- Torch 2.11+cu126 depends on pypi.nvidia.com (timeout).
- FitVTON Cloth assumed SMPL-X body_sequence; patched for static OBJ.
- libigl 2.6 facet_components API change; patched.
- 80-step smoke did not fully settle; 300-step lattice did (0 non-static verts).

## Limitations

- One garment program (straight Shirt), one body (mean_all).
- Bust edit is a girth multiplier, not a dart.
- No SMPL-X body library.
- Observational table is not counterfactual ground truth.
- No MLLM.

## VERIFIED

Warp CUDA kernel; pattern bust realized_delta; physics+render for baseline/+1/+2/+3; FitGround core tests; observational B0/B1 numbers.

## NOT VERIFIED

Shoulder/sleeve mappings; vision necessity; SFT; real-world first-pass improvement.

## Blocked

Licensed SMPL/SMPL-X model files; NVIDIA pip CDN for full PyTorch CUDA stack.

## Resume claims that are supported

- GPU Warp XPBD correction backend for GarmentCode shirts with measured bust deltas and before/after renders.
- Calibrated shirt.width.v to centimetres with monotonic, reproducible pattern measurements.
- Ranked enumerated CHEST_CASE actions with an explicit utility; did not fabricate physics.

## Resume claims that are not supported

- production-ready
- real-world first-pass improvement
- sample reduction
- industry validated
- vision-critical MLLM
