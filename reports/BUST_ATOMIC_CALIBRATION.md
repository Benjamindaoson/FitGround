# Bust atomic calibration

**Decision: PARTIAL**

Garment: GarmentCodeV2 `assets/design_params/t-shirt.yaml` (`meta.upper = Shirt`) on `mean_all` (bust 99.8407 cm).

**Controlling parameter (measured, not guessed):** `design[shirt][width][v]`.

From `tee.py`: `m_width = width.v * body[bust]`. Front+back torso panel x-spans sum to `m_width`. Empirical:

| action | intended_cm | realized_cm | error_cm | waist_delta | shoulder_delta | sleeve_delta | length_delta |
| --- | --- | --- | --- | --- | --- | --- | --- |
| +1 | 1 | 1.000000 | ~0 | 1.00 | 0.48 | 0.10 | 0.10 |
| +2 | 2 | 2.000000 | ~0 | 2.00 | 0.96 | 0.23 | 0.20 |
| +3 | 3 | 3.000000 | 0 | 3.00 | 1.43 | 0.28 | 0.30 |
| +3 repeat | 3 | 3.000000 | 0 | 3.00 | 1.43 | 0.28 | 0.30 |

Inverse calibration: `parameter_delta = desired_cm / body_bust_cm`. Baseline `width.v = 1.05`.

## Gates

| Gate | Status | Evidence |
| --- | --- | --- |
| G1 executability | PASS pattern; PASS physics+render for +1/+2/+3 (300 steps) | meshes + PNGs under `artifacts/gpu/physics_lattice/` |
| G2 measurement accuracy | PASS | max abs error 2.8e-14 cm |
| G3 monotonicity | PASS | 1 < 2 < 3 |
| G4 locality | PARTIAL | `shirt.width.v` is full-girth; waist tracks bust 1:1 when `flare=1.0`. Sleeve/length side effects ~0.1 cm per 1 cm bust |
| G5 sensitivity | PASS | unique spec hashes; physics renders differ |
| G6 reproducibility | PASS | +3 vs +3 repeat realized diff 0 |

**Why not GO:** G4 waist coupling is structural for this Shirt program. A dart-based `FittedShirt` mapping was not calibrated in this run. Do not claim a bust-only local edit.

`realized_delta_cm` is **measured** from panel geometry. It is not copied from `intended_delta_cm`.

Figures: `reports/figures/bust_calibration_curve.png`, `bust_intended_vs_realized.png`, `bust_side_effects.png`, `baseline_render_front.png`, `bust_plus_{1,2,3}cm_render_front.png`.
