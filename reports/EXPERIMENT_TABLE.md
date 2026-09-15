# Experiment table

| Track | Status | Evidence |
| --- | --- | --- |
| Core | PASS | pytest |
| Warp CUDA | PASS | artifacts/gpu/warp_smoke.json |
| PyTorch CUDA | PASS | torch 2.5.1+cu124 on RTX 4090 |
| Parametric garment geometry | PASS | GarmentCode Shirt serialize + panel measures |
| SYNTHETIC_BODY_PHYSICS | PASS | Warp XPBD vs static OBJ, m→cm |
| SMPL/SMPL-X body physics | HARD_BLOCKED_LICENSE | weights absent, not pirated |
| Real-human validation | HARD_BLOCKED_LICENSE | requires licensed/consented capture |
| Bust | PASS | MAE ~0, monotonic, 3× repeat exact |
| Shoulder | NO_GO_WITH_EVIDENCE | SHOULDER_ACTION = NO_GO_FOR_CURRENT_PATTERN_FAMILY |
| Sleeve | PASS | panel X geodesic/construction axis, MAE 0 on ±2 cm |
| Large lattice | PASS | 636 transitions, dup=0 |
| Visual disambiguation | PASS | VISION_NECESSITY_NOT_ESTABLISHED n_pairs=33 |
| Classical baselines | PASS | B0/B1/XGB on FIT-Clean |
| Vision baseline | PASS | Ridge 3.45 < CNN 6.23 on 192 drawings |
| Multimodal baseline | PASS | CNN+body 6.24, no gain |
| Pretrained MLLM | PASS | Qwen/Qwen2-VL-2B-Instruct |
| Transition | PASS | SFT 0.47 cm; analytic better |
| Decision | PASS | analytic ranking; SFT n=3 too small to boast |
| OOD | PASS | artifacts/hero/ood_results.json |
| Failure-aware | PASS | artifacts/hero/failure_aware.json |
| RLVR | NOT_JUSTIFIED | no residual gain, n=3 |
| Demo | PASS | studio/ |
| Reproducibility | PASS | artifacts/REPRODUCIBILITY.json |
