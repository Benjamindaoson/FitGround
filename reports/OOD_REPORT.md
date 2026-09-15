# OOD report (quantitative)

**Label:** `SYNTHETIC_BODY_OOD`. These numbers are not real-human generalization.

| Split | Metric | n | mean | std | 95% CI |
| --- | --- | --- | --- | --- | --- |
| IID trivial geometry | MAE cm (analytic) | 88 | 9.85070610940139e-15 | 1.0413410181229966e-14 | [7.751375299201092e-15, 1.1954074094236682e-14] |
| OOD synthetic body | MAE cm (analytic) | 402 | 8.271990058102659e-15 | 9.879042759756583e-15 | [7.282179281919435e-15, 9.262684593907475e-15] |
| OOD garment/sleeve | MAE cm | 36 | 0.0041775303869670604 | | |
| OOD material | meas-only disagreement | 33 | 0.21212121212121213 | 0.41514875026728054 | [0.09090909090909091, 0.36363636363636365] |

Decision regret (analytic vs oracle utility): {"n": 160, "mean": 0.0, "std": 0.0, "lo": 0.0, "hi": 0.0}

Action-magnitude policy: intended |Δ| outside [-3, +3] cm **abstain**. Width is clamped to [1.0, 1.3].

Side-effect rate on ±3 cm bust edits (waist tracks bust on flare=1): {"n": 162, "mean": 1.0, "std": 0.0, "lo": 1.0, "hi": 1.0}
