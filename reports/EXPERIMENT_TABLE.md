# Experiment table

| Experiment | n | Split | Metric | Result | Artifact |
| --- | --- | --- | --- | --- | --- |
| B0 ease heuristic | 15752 test rows | person_sha256 | MAE cm | 8.11 | artifacts/training/observational_and_vision_baselines.json |
| B1 OLS | same | person | MAE cm | 8.08 | same |
| B1 XGBoost | same | person | MAE cm | 7.88 | same |
| B2 pattern Ridge | 29 test drawings | state_id | MAE cm | 3.45 | same |
| B2 pattern CNN | 29 | state_id | MAE cm | 6.23 | same |
| B3 CNN+body | 29 | state_id | MAE cm | 6.24 | same |
| Transition SFT MLP | 16 test | state_id | realized MAE | 0.47 vs identity 0.00 | artifacts/training/transition_sft.json |
| Decision SFT MLP | 3 test | state_id | accuracy | 1.0 | artifacts/training/decision_sft.json |
| RLVR REINFORCE | 3 test | state_id | regret | 0 → 0 | artifacts/training/rlvr.json |
| Bust pattern calibration | +1/+2/+3 + repeat | — | max abs error | ~1e-14 cm | artifacts/bust_atomic_calibration.json |
| Physics clearance (unit-fixed) | 4 drapes | — | chest p10 cm | 0.47 → 0.50 at +3 | artifacts/hero/existing_physics_outcomes.json |
| FIT-100K B2/B3 | 0 images | — | — | NOT_RUN | same observational json |
| Shoulder GO | probes | — | — | pending/NO-GO unless connecting_width maps | artifacts/hero/atomic_calibration.json |
