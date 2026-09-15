# Resume claims (evidence-linked)

Every bullet below is allowed only with the linked artifact. Do not upgrade wording.

## 中文 · 可以说

1. 构建了面向技术设计师的合体修正流水线：样衣 fit 问题 → 可执行服装参数干预 → **实测** `realized_delta_cm`（二维样板几何）→ Warp XPBD 静态人台碰撞 → 区域 clearance/contact 指标 → 效用排序推荐下一版修改；胸围 `shirt.width.v` 在 +1/+2/+3 cm 上实测误差约 1e-14 cm（`artifacts/bust_atomic_calibration.json`，`artifacts/hero/existing_physics_outcomes.json`）。
2. 在缺失 SMPL-X 权重时没有停机：使用 GarmentCode 仓库内静态 OBJ 人台（米制缩放为厘米），标记 `SYNTHETIC_BODY_PHYSICS`，并完成 before/after 模拟与渲染（`src/fitground/physics/outcomes.py`）。
3. 训练并对比了观测基线与干预学习：FIT-Clean B0/B1/XGB MAE 8.11/8.08/7.88 cm；纸样 Ridge 3.45 cm 优于 CNN 6.23 cm；Transition SFT 在恒等校准格子上 **未能打过解析逆映射**（0.47 vs 0.00 MAE），并据此把任务升级为物理 next-state（`artifacts/training/`，`reports/TRAINING_RUN.md`）。

## English · allowed

1. Built a physics-grounded counterfactual fit-correction pipeline: named garment edits → measured panel `realized_delta_cm` → Warp XPBD on a static mannequin → regional clearance/contact → utility-ranked next-sample recommendation (`artifacts/correction_lattice_chest_case.json`).
2. Did not halt on missing SMPL-X weights; shipped a documented `SYNTHETIC_BODY_PHYSICS` fallback using in-repo OBJ mannequins with metre-to-centimetre alignment (`src/fitground/physics/outcomes.py`).
3. Showed that a learned transition model loses to the analytic inverse on the calibrated bust grid (0.47 vs 0.00 cm MAE), and that pixel Ridge beats a small CNN on 192 pattern drawings — negative results that forced a harder physics/material split (`artifacts/training/transition_sft.json`).

## 不能说 / not allowed

- Production-ready, deployed, or used by brands
- Real-world first-pass sample reduction or return-rate impact
- “Vision is necessary” until the material-pair disambiguation set has `vision_needed >= 1` with hashes
- Pretrained MLLM LoRA success (download/train must exist in `artifacts/hero/mllm_status.json`)
- Shoulder centimetre GO without G2 PASS
- RLVR improved decisions (holdout regret was already 0)
- FIT-100K image training

## 30-second pitch

FitGround answers: the sample is wrong — what do we change next, by how many centimetres, and what else moves? It is a correction engine with measured interventions and a static-body cloth sim, not a dressing-room VTO.

## 2-minute pitch

Technical designers already see tightness. The expensive part is the next pattern edit. FitGround enumerates bust/sleeve candidates, measures realized geometry instead of trusting intended deltas, drapes on a legal static mannequin when SMPL-X files are missing, scores chest clearance and contact, and ranks corrections with an explicit utility. Simple rules win on the trivial calibrated grid; the research claim is to push the task into material and body regimes where measurements collide.

## 5-minute deep dive

Start from `shirt.width.v = desired_cm / body_bust`. Show identity calibration, waist coupling, physics clearance table, the measurement-bug on sleeve Y vs X, why shoulder is NO-GO on Shirt, why SFT < identity, why RLVR was not justified, then the hero workspace recommending Bust +3 cm for CHEST_CASE with alternatives and provenance.
