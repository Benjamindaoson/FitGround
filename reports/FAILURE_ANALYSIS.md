# Failure analysis

| Failure | Symptom | Cause | Mitigation |
| --- | --- | --- | --- |
| Sleeve realized Δ = 0 | `sleeve.length.v` 0.3→0.4 did not change panel **Y** | Length is constructed on panel **X** in sleeves.py | Measure sleeve dx; recalibrate |
| Shoulder NOT_VERIFIED | No `realized_delta_cm` | Shirt has no independent garment shoulder width; body `shoulder_w` is not an action | Probe `sleeve.connecting_width`; else NO-GO |
| SFT worse than identity | 0.47 vs 0.00 MAE | Task was the inverse of a linear pattern map | Upgrade target to physics next-state |
| CNN < Ridge | 6.23 vs 3.45 MAE | 192 line drawings, small CNN overfit | Keep Ridge; use renders + materials for vision |
| RLVR no gain | regret 0 before and after | Decision SFT already oracle on n=3 | RLVR_NOT_NEEDED on that lattice |
| Clearance ~105 cm | first physics metrics | Body OBJ in metres, cloth in centimetres | ×100 alignment in `cloth_body_outcomes` |
| Waist tracks bust | G4 PARTIAL | `flare=1` Shirt width scales full girth | Price waist in utility or change flare |
| FIT-100K vision | NOT_RUN | Images not on disk; 197GB not downloaded | Generated-pattern / sim-render substitutes |
| SMPL-X | no parametric pose | Licensed files absent | SYNTHETIC_BODY_PHYSICS mannequin OBJs |
