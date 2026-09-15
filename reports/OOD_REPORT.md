# OOD report

| Split | Definition | Result |
| --- | --- | --- |
| IID person | FIT-Clean person_sha256 70/15/15 | B1 XGB MAE 7.88 cm |
| IID state | pattern lattice state_id grouped | used for SFT |
| OOD-body (planned) | train mean_all, test mean_female/male | identity map should still hold for bust centimetres; physics clearance will not |
| OOD-material (planned) | train default bending, test mid_bending | measurement-only cannot see it |
| OOD-action | intended Δ outside [-3,+4] | width clamped to [1.0, 1.3]; selector should abstain |

Failure-aware rule implemented in the workspace and `train_hero_ladder.py`: if `body_name` is outside the training support, **escalate-to-human** rather than emit a centimetre edit.

Do not report a numerical OOD win until `artifacts/hero/baseline_ladder.json` exists from the v0.2 lattice.
