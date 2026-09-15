# Interview deep dive

## Why this problem

A fit session already knows “too tight.” The costly question is the next pattern: which region, how many centimetres, and what else moves.

## Why VTO is the wrong product

Virtual try-on scores a still image. FitGround scores a **counterfactual edit**.

## Mechanism

`shirt.width.v` × body bust → garment bust. That identity is a feature of the pattern program, not a fake label. Physics then asks whether extra ease actually changes cloth-body clearance on a mannequin.

## Negative results as seniority

If you only show XGBoost 7.88 and CNN 6.23, you look like a tutorial. The senior story is: **learning lost to the inverse map**, so the task was upgraded; **SMPL-X missing did not freeze the physics path**; **RLVR was not forced**.

## Demo path (live)

1. Open the workspace.
2. CHEST_CASE: target = baseline + 3 cm.
3. Show intended vs realized table.
4. Show baseline vs +3 renders.
5. Show clearance/contact table (after m→cm fix).
6. Recommend +3 with waist side-effect disclosed.
7. Switch to OOD body: the system abstains.
8. Switch to shoulder: `NO_GO_FOR_CURRENT_PATTERN_FAMILY` with connecting_width evidence.

## Likely interviewer attacks

- “Is realized copied from intended?” No — after-minus-before; identity is the measured map.
- “Is this SMPL?” No. Static OBJ, labeled `SYNTHETIC_BODY_PHYSICS`.
- “Did the MLLM win?” Only if `artifacts/hero/mllm_eval.json` exists and the table says so.
- “n=3 decision accuracy?” Too small; RLVR is `NOT_JUSTIFIED`.
- “Is vision necessary?” Read `visual_disambiguation.json`. Ridge beating CNN is a negative.
- “Did you skip shoulder?” No. We published a NO-GO with a parameter scan.
