# Ablation report

On the **calibrated bust grid**, the ablation is the result:

| Input | Model | Held-out realized-Δ MAE |
| --- | --- | --- |
| intended Δ only | identity / analytic inverse | **0.00 cm** |
| intended Δ + body | OLS | ~0 (same regime) |
| structured (s,a) | MLP SFT | 0.47 cm |
| character LM | tiny transformer | parse-rate 0.31 |

Conclusion: extra parameters and extra model class **hurt** when the mechanism is a known linear map. That is the opposite of leakage: we did not hide the inverse.

On **generated pattern drawings** (not FIT-100K):

| Input | Model | Garment bust MAE |
| --- | --- | --- |
| pixels | PCA+Ridge | **3.45 cm** |
| pixels | CNN | 6.23 cm |
| pixels + body | CNN | 6.24 cm |

Vision did not beat a linear pixel model. Multimodal body concat did not help. **VISION_NECESSITY_NOT_ESTABLISHED** on drawings.

The planned positive ablation is **same measurements, different material** (hero physics pairs). Until `visual_disambiguation.json` contains `vision_needed >= 1`, do not claim vision wins.
