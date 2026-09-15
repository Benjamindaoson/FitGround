# FitGround training run

Training on the RTX 4090 **did run to completion**. Jobs: B0, B1, B1-Ridge, B1-XGBoost, generated-pattern B2/B3, Transition SFT, Decision SFT, RLVR.

| Task | Status | Headline metric |
| --- | --- | --- |
| B0 ease heuristic | PASS | test MAE 8.11 cm (FIT-Clean, not intervention GT) |
| B1 OLS | PASS | test MAE 8.08 cm |
| B1 XGBoost | PASS | test MAE 7.88 cm |
| B2 FIT-100K vision | NOT_RUN | images not on disk |
| B2 generated-pattern Ridge | PASS | test MAE 3.45 cm (192 drawings) |
| B2 generated-pattern CNN | PASS | test MAE 6.23 cm on CUDA; Ridge wins |
| B3 generated-pattern CNN+body | PASS | test MAE 6.24 cm |
| Transition SFT MLP | PASS | realized-delta MAE 0.47 cm; identity map is 0.00 on this grid |
| Decision SFT MLP | PASS | holdout accuracy 1.0, regret 0.0 (n=3) |
| RLVR REINFORCE | COMPLETED_NOT_JUSTIFIED | 300 CUDA steps; no residual gap after SFT |

This run trains B0–B3, Transition SFT, Decision SFT, and RLVR on **measured** GarmentCode panel geometry.
FIT-100K images were not downloaded. Vision models use rasterized pattern drawings.
No `intended_delta_cm` was copied into `realized_delta_cm`.

```json
{
  "lattice": {
    "task": "measured_training_lattice",
    "n_transitions": 88,
    "n_vision_samples": 192,
    "n_decision_cases": 24,
    "n_unique_patterns_generated": 289,
    "cache_hits": 19,
    "families": [
      "bust_circumference_delta_cm",
      "shirt_length_delta_cm"
    ],
    "probes": [
      {
        "parameter": "shirt.width",
        "measure_key": "bust_circumference_cm",
        "v0": 1.05,
        "v1": 1.0800478662509378,
        "before_cm": 104.83273500000001,
        "after_cm": 107.83273500000001,
        "realized_delta_cm": 3.0,
        "cm_per_unit": 99.8406999999998,
        "body_name": "mean_all"
      },
      {
        "parameter": "sleeve.length",
        "measure_key": "sleeve_length_cm",
        "v0": 0.3,
        "v1": 0.4,
        "before_cm": 21.06146554666354,
        "after_cm": 21.06146554666354,
        "realized_delta_cm": 0.0,
        "cm_per_unit": 0.0,
        "body_name": "mean_all"
      },
      {
        "parameter": "shirt.length",
        "measure_key": "length_cm",
        "v0": 1.2,
        "v1": 1.4,
        "before_cm": 49.94076049824885,
        "after_cm": 57.319020502922655,
        "realized_delta_cm": 7.378260004673805,
        "cm_per_unit": 36.891300023369034,
        "body_name": "mean_all"
      },
      {
        "parameter": "shirt.width",
        "measure_key": "bust_circumference_cm",
        "v0": 1.05,
        "v1": 1.0800478662509378,
        "before_cm": 102.27798000000001,
        "after_cm": 105.20487053662484,
        "realized_delta_cm": 2.926890536624825,
        "cm_per_unit": 97.40759999999918,
        "body_name": "mean_female"
      },
      {
        "parameter": "sleeve.length",
        "measure_key": "sleeve_length_cm",
        "v0": 0.3,
        "v1": 0.4,
        "before_cm": 21.03115951756412,
        "after_cm": 21.03115951756412,
        "realized_delta_cm": 0.0,
        "cm_per_unit": 0.0,
        "body_name": "mean_female"
      },
      {
        "parameter": "shirt.length",
        "measure_key": "length_cm",
        "v0": 1.2,
        "v1": 1.4,
        "before_cm": 48.299235718793796,
        "after_cm": 55.450215700747265,
        "realized_delta_cm": 7.150979981953469,
        "cm_per_unit": 35.75489990976735,
        "body_name": "mean_female"
      }
    ],
    "max_bust_calibration_error_cm": 2.842170943040401e-14,
    "realized_source": "panel_geometry_after_minus_before",
    "note": "FIT-100K images were not downloaded. Vision samples are GarmentCode pattern drawings.",
    "paths": {
      "transitions": "/root/workspace/projects/FitGround/artifacts/training/transition_lattice.jsonl",
      "vision": "/root/workspace/projects/FitGround/artifacts/training/vision_pattern_samples.jsonl",
      "decisions": "/root/workspace/projects/FitGround/artifacts/training/decision_cases.json",
      "png_dir": "/root/workspace/projects/FitGround/artifacts/training/pattern_pngs"
    },
    "runtime_s": 932.5117683410645
  },
  "B0_test_mae_cm": 8.110471560302393,
  "B1_test_mae_cm": 8.080634882812335,
  "B1_xgboost_test_mae_cm": 7.875043460716143,
  "B2_cnn_test_mae_cm": 6.234292807802393,
  "B3_cnn_test_mae_cm": 6.236495861243934,
  "transition_sft_realized_mae_cm": 0.47328024404123425,
  "decision_sft_accuracy": 1.0,
  "rlvr": {
    "status": "COMPLETED_NOT_JUSTIFIED",
    "before_test": {
      "accuracy": 1.0,
      "mean_utility_regret": 0.0,
      "n": 3
    },
    "after_test": {
      "accuracy": 1.0,
      "mean_utility_regret": 0.0,
      "n": 3
    }
  }
}
```

## Matrix

- FitGround Core: PASS
- Warp CUDA: PASS
- PyTorch CUDA: PASS
- SMPL assets: BLOCKED
- Parametric garment geometry: PASS
- Warp synthetic-body physics: PASS (`SYNTHETIC_BODY_PHYSICS`)
- SMPL/SMPL-X body physics: HARD_BLOCKED_LICENSE
- Real-human validation: HARD_BLOCKED_LICENSE
- Bust calibration: PARTIAL
- Shoulder calibration: NOT_RUN
- Sleeve calibration: NOT_RUN
- Correction lattice: PARTIAL
- Classical baseline: PASS
- Vision baseline: PASS
- Multimodal baseline: PASS
- Transition SFT: PASS
- Decision SFT: PASS
- RLVR: COMPLETED_NOT_JUSTIFIED
- Demo: PASS

## Honesty

- Observational B0/B1 remain FIT-Clean measurement prediction, not intervention GT.
- B2/B3 FIT-100K: NOT_RUN. B2/B3 generated-pattern: trained.
- Tiny LMs are from-scratch character transformers, not pretrained MLLMs.
- RLVR reward is cached measured utility from the lattice, not a live Warp loop.
