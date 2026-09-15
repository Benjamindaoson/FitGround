# Resume claims (evidence-linked)

Every bullet is allowed only with the linked artifact. Status words are only
`PASS`, `NO_GO_WITH_EVIDENCE`, `NOT_JUSTIFIED`, `HARD_BLOCKED_LICENSE`.

Do not say “GarmentCode physics PASS”. Split:

| Layer | Status |
| --- | --- |
| Parametric garment geometry | PASS |
| Warp synthetic-body physics | PASS (`SYNTHETIC_BODY_PHYSICS`) |
| SMPL/SMPL-X body physics | HARD_BLOCKED_LICENSE |
| Real-human validation | HARD_BLOCKED_LICENSE |

## 中文简历 3 bullet

1. 从纸样参数干预做到可测几何与可测物理后果：修改 `shirt.width.v` 后用二维样板 **after−before** 得到 `realized_delta_cm`（胸围 ±3 cm 网格 MAE≈0、三次重复完全一致），再跑 Warp XPBD 静态人台，胸围 clearance p10 从 0.47 cm 升到 0.50 cm，contact 从 0.027 降到 0.022（`artifacts/hero/atomic_calibration.json`，`artifacts/hero/existing_physics_outcomes.json`）。
2. 用对照实验画出学习边界：在平凡几何格子上解析逆映射 MAE=0，Transition SFT 为 0.47 cm；纸样 Ridge 3.45 cm 优于 CNN 6.23 cm。结论是 trivial geometry 不需要学习，而不是“模型都很好看”（`reports/WHEN_IS_LEARNING_NECESSARY.md`）。
3. 做成技术设计师工作台而不是 chatbot：候选修正按效用排序，OOD/人台外推时 **拒答并升级人工**；当前 Shirt 肩宽动作为 `NO_GO_WITH_EVIDENCE`（`connecting_width` 只带动袖长、肩宽 Δ=0 cm）。SMPL-X 权重未获取，未停机，未盗版。

## English resume 3 bullets

1. Built a physics-grounded counterfactual correction loop: named pattern intervention → measured panel `realized_delta_cm` (bust ±3 cm identity map, MAE ~0) → Warp XPBD on a static mannequin → regional clearance/contact → utility-ranked next-sample edit (`artifacts/hero/`).
2. Showed when learning is unnecessary: analytic inverse MAE 0.00 cm vs Transition SFT 0.47 cm on the trivial Shirt grid; pattern Ridge 3.45 cm beats a CNN 6.23 cm on 192 drawings. Vision necessity is reported only from a grouped-split material-pair experiment, not assumed (`reports/WHEN_IS_LEARNING_NECESSARY.md`).
3. Shipped a Technical Designer workspace that recommends the next sample change, abstains on OOD bodies, and records shoulder as `NO_GO_WITH_EVIDENCE` for this pattern family. SMPL-X remains `HARD_BLOCKED_LICENSE`; physics continues as `SYNTHETIC_BODY_PHYSICS`.

## 30-second pitch

FitGround answers: the sample is wrong — what do we change next, by how many centimetres, and what else moves? It is a measured intervention + cloth-body physics engine for technical designers, not a dressing-room VTO and not a chatbot.

## 2-minute pitch

Technical designers already see tightness. The expensive question is the next pattern edit. FitGround enumerates centimetre actions, measures realized geometry instead of trusting intended deltas, drapes on a legal static mannequin when SMPL-X files are missing, scores chest clearance and contact, and ranks corrections with an explicit utility. On this Shirt, bust and sleeve maps are millimetre-class; shoulder is a documented NO-GO. Simple analytic rules win on the trivial grid. The research question is when material and drape actually change the best correction — and the system is allowed to abstain.

## 5-minute deep dive

1. Product sentence: next-sample correction, not try-on.
2. Intervention: `shirt.width.v = desired_cm / body_bust`; realized = after−before; never copy intended.
3. Bust gate PASS; waist coupling PARTIAL (`flare=1`); sleeve PASS on panel X; shoulder NO-GO (`connecting_width` Δshoulder=0, Δsleeve≠0).
4. Physics: static OBJ, m→cm, clearance/contact table for baseline/+1/+2/+3.
5. Learning ladder: observational MAE ~8 cm is not intervention GT; Ridge > CNN; analytic > SFT; RLVR NOT_JUSTIFIED (n=3).
6. Visual disambiguation: same measurements, different bending; grouped split; verdict is whatever the numbers say.
7. OOD: synthetic-body numbers only; abstain on unseen body/material/unstable sim.
8. Demo: `studio/` — “What should change in the next sample?”
9. Limitations: no SMPL-X, no real humans, Shirt family only, physics n is a subset of the 636-row lattice.

## 10 interview questions + answers

1. **Why isn’t this a VLM demo?** Because the unit of work is a centimetre pattern intervention with a measured realized delta and a cloth-body sim. A VLM is one optional ranker, not the product.
2. **How do you know realized_delta is real?** It is panel after-minus-before with provenance `panel_geometry_after_minus_before`. Tests reject intended-copy.
3. **Why did the sleeve probe first look dead?** Length is constructed along panel X in `sleeves.py`. Measuring mean dy was a bug. After switching to dx, ±2 cm is exact.
4. **Why NO-GO the shoulder instead of forcing a model?** Shirt has no independent garment shoulder width. `connecting_width` moves sleeve length. Body `shoulder_w` is not an action.
5. **When is ML necessary?** Not on the calibrated bust identity map. Possibly when material/drape changes next-state utility at matched measurements. That is an experiment, not a slogan.
6. **Did vision win?** Only if `visual_disambiguation.json` says `VISION_NECESSITY_ESTABLISHED` with n, CI, and a grouped split. Ridge beating CNN is evidence against naive visual necessity.
7. **What happens on a new body?** The failure-aware policy abstains if `body_name` is outside support. Those numbers are `SYNTHETIC_BODY_OOD`, not real-human generalization.
8. **Why not SMPL-X?** Licensed weights are absent. We did not pirate them. Physics continued on in-repo OBJ mannequins.
9. **Did RLVR help?** No. Holdout regret was already 0 with n=3. Status: `NOT_JUSTIFIED`.
10. **What would you do next with a licensed body?** Re-run the same lattice on SMPL-X, keep the analytic inverse as the trivial-regime baseline, and only then test whether a pretrained VLM beats drape-evidence on the complex split.

## Not allowed

- Production-ready, brand-deployed, return-rate impact
- Real-world first-pass sample reduction
- “Vision is necessary” without the ESTABLISHED verdict
- Pretrained MLLM LoRA success without `artifacts/hero/mllm_eval.json`
- Shoulder centimetre GO
- RLVR improved decisions
- FIT-100K image training
- Calling synthetic mannequin results real-human generalization
