<p align="right">
  <a href="./README.md">中文</a> · <b>English</b>
</p>

# FitGround

**The sample is wrong. What should change in the next one, by how many centimetres, and what else will move?**

FitGround is not a dressing-room virtual try-on and not a chatbot. It is a **next-sample correction engine for technical designers**: edit a named pattern parameter, **measure** the geometry change, run cloth–body physics, then rank the next edit with an explicit utility. When evidence is thin, the system **abstains** instead of inventing a centimetre.

[![GitHub](https://img.shields.io/badge/GitHub-Benjamindaoson%2FFitGround-111)](https://github.com/Benjamindaoson/FitGround)
[![Hugging Face](https://img.shields.io/badge/HuggingFace-jlai300%2FFitGround-ffcc00)](https://huggingface.co/datasets/jlai300/FitGround)

| Current sample | After bust +3 cm |
| --- | --- |
| ![baseline](reports/figures/baseline_render_front.png) | ![bust+3](reports/figures/bust_plus_3cm_render_front.png) |

These are Warp drapes on a static mannequin. They are **not** product try-on shots.

---

## Contents

1. [What problem are we solving?](#what-problem-are-we-solving)
2. [How did we solve it?](#how-did-we-solve-it)
3. [Six conclusions that are hard to forget](#six-conclusions-that-are-hard-to-forget)
4. [The experiment: from observational data to an intervention lattice](#the-experiment-from-observational-data-to-an-intervention-lattice)
5. [Training conclusions: what was worth learning](#training-conclusions-what-was-worth-learning)
6. [Is there a better approach?](#is-there-a-better-approach)
7. [Full figure gallery](#full-figure-gallery)
8. [Status matrix and data index](#status-matrix-and-data-index)
9. [How to run](#how-to-run)
10. [Hard limits](#hard-limits)

---

## What problem are we solving?

Seeing “tight across the chest” is cheap. Deciding **the next cut** is expensive:

```text
Current sample has a fit problem
    → Is it ease, a shoulder lock, sleeve length, or cloth stiffness?
    → Next sample: +1, +2, or +3 cm?
    → Will the waist or sleeve get worse?
    → If evidence is thin, can the system refuse instead of inventing a number?
```

In apparel development, the expensive loop is not “does this look fitted?” It is **sample iteration**: change the pattern → cut another garment → try again. Every centimetre costs fabric, sewing, and calendar time. Most existing tools stop at “how it looks.” They do not stop at “which centimetre to change next.”

Common stacks answer a different question:

| Approach | Question it actually answers | Why it is not enough |
| --- | --- | --- |
| Virtual try-on | “Does this look good on a body?” | No centimetre pattern edit |
| VLM / RAG / Agent copy | “Looks a bit tight” | No intervention, no measured Δ, no physics |
| Observational regression | “Historically, similar garments differed by X cm” | Correlation is not a counterfactual |
| Jump to MLLM + RLVR | “The model is new” | On trivial geometry the analytic map already has 0 error |

FitGround answers one sentence: **what should change in the next sample.**

---

## How did we solve it?

An engineering–research loop, with artifacts at every step:

```text
Pattern-parameter intervention
  → measured 2D geometry (after − before; never copy intended into realized)
  → Warp cloth/body physics (static OBJ mannequin)
  → clearance / contact fit metrics
  → counterfactual candidate ranking
  → decision utility (target error + edit size + side effects + uncertainty)
  → technical-designer workspace
```

![system loop](reports/figures/01_system_architecture.png)

![intervention pipeline](reports/figures/02_intervention_pipeline.png)

Shirt bust is controlled by one named parameter:

```text
shirt.width.v = desired_bust_cm / body_bust_cm
```

So in the **trivial geometry regime**, adding 3 cm of garment bust means adding `3 / body_bust` to `width.v`. That is the pattern definition, not a model that “learned centimetres.” Copying intended into realized would fake a 0 error — tests in this repo reject those rows.

### Four layers that must not be collapsed

Do not write a blanket “GarmentCode physics PASS”:

| Layer | Status | Meaning |
| --- | --- | --- |
| Parametric garment geometry | **PASS** | Shirt panels serialize; centimetres are measured |
| `SYNTHETIC_BODY_PHYSICS` | **PASS** | Warp XPBD vs in-repo static OBJ, metres→cm |
| SMPL / SMPL-X body physics | **HARD_BLOCKED_LICENSE** | Weights absent; not pirated; pipeline continues |
| Real-human validation | **HARD_BLOCKED_LICENSE** | Needs licensed, consented capture |

---

## Six conclusions that are hard to forget

### 1. ±3 cm pattern edits are calibratable to millimetres / sub-centimetres

Bust is controlled by `shirt.width.v = desired_cm / body_bust`. On a −3…+3 cm grid, measured `realized_delta_cm` matches intended to ~`1e-14` cm; three +3 cm repeats are exact.

![bust calibration](reports/figures/03_bust_calibration.png)
![intended vs realized](reports/figures/bust_intended_vs_realized.png)
![calibration curve](reports/figures/bust_calibration_curve.png)

Sleeve: an early probe used panel **Y**. GarmentCode constructs sleeve length along **X**. After fixing the measure, ±2 cm MAE = 0. Do not NO-GO sleeve because of the old bug.

Shoulder: this Shirt has **no independent garment shoulder DoF**. Scanning `sleeve.connecting_width` moves sleeve length, not the torso top-edge shoulder proxy. Official:

`SHOULDER_ACTION = NO_GO_FOR_CURRENT_PATTERN_FAMILY`

Side effects are structural, not noise. With `flare=1`, a ±3 cm bust edit **always** moves the waist. The decision utility must price that, or the system will always prefer the largest cut.

![side effects](reports/figures/bust_side_effects.png)

### 2. The correction changes measurable cloth–body clearance / contact

Same Shirt, static mannequin, units aligned:

| Version | Chest clearance p10 | Contact ratio |
| --- | --- | --- |
| Current | 0.47 cm | 0.027 |
| +1 cm | 0.48 cm | 0.029 |
| +2 cm | 0.48 cm | 0.027 |
| +3 cm | 0.50 cm | 0.022 |

The effect is **millimetres of clearance**, not a fashion render. It is still a real physical consequence of a pattern edit.

![physics](reports/figures/04_physics_before_after.png)
![clearance / contact](reports/figures/05_clearance_contact.png)
![physics_clearance_contact](reports/figures/physics_clearance_contact.png)

| Current | +1 cm | +2 cm | +3 cm |
| --- | --- | --- | --- |
| ![b0](reports/figures/baseline_render_front.png) | ![b1](reports/figures/bust_plus_1cm_render_front.png) | ![b2](reports/figures/bust_plus_2cm_render_front.png) | ![b3](reports/figures/bust_plus_3cm_render_front.png) |

Same measurements, different bending (default vs stiff) — the physical feedstock for the vision-necessity experiment:

| Tight default | Tight stiff | Roomy default | Roomy stiff |
| --- | --- | --- | --- |
| ![td](studio/public/evidence/tight_default_render_front.png) | ![ts](studio/public/evidence/tight_stiff_render_front.png) | ![rd](studio/public/evidence/roomy_default_render_front.png) | ![rs](studio/public/evidence/roomy_stiff_render_front.png) |

### 3. Simple geometry does not need ML; the analytic inverse wins

| Method | Test MAE (cm) | Note |
| --- | --- | --- |
| Analytic inverse | **~0** | `Δwidth = Δcm / body_bust` |
| Transition SFT MLP | 0.47 | 88-row lattice, test n=16 |
| Observational B0 | 8.11 | FIT-Clean 104,999 rows; **not** intervention GT |
| B1 OLS | 8.08 | body circumferences → garment bust |
| B1 XGBoost | 7.88 | still correlation, not a counterfactual |
| Pattern Ridge | 3.45 | 192 generated drawings |
| Pattern CNN | 6.23 | RTX 4090, 40 epochs; does not beat Ridge |
| CNN+body | 6.24 | no multimodal gain |

![baseline ladder](reports/figures/06_baseline_ladder.png)
![trivial vs complex](reports/figures/09_trivial_vs_complex.png)
![observational MAE](reports/figures/observational_baseline_mae.png)

Copying intended into realized would fake a 0 error. Tests reject that. The analytic map wins because this Shirt bust map **is** identity geometry, not because a model is weak.

### 4. In the material/drape-ambiguity regime, vision necessity is not statistically established

We built **33 pairs** with the same 2D spec and different bending stiffness. **7 pairs** (21%, bootstrap 95% CI about 9%–36%) flip the best correction.

On a grouped split: measurement-only accuracy 0.90 [0.70, 1.00] vs drape features 1.00; **CIs overlap** →

**`VISION_NECESSITY_NOT_ESTABLISHED`**

We did not retune the split for an MLLM story. Ridge beating the CNN on drawings is the same honesty rule.

![visual disambiguation](reports/figures/07_visual_disambiguation.png)
![multimodal ablation](reports/figures/08_multimodal_ablation.png)

Qwen2-VL-2B-Instruct zero-shot structured JSON: parse rate 100%, action match 83% (n=12, majority class `no_edit`). n is too small for LoRA without leakage. Matching the majority class is not “the VLM can edit patterns.”

### 5. Under OOD the system abstains instead of inventing a centimetre

| Split | Result |
| --- | --- |
| IID trivial geometry | analytic MAE ~0 (n=88) |
| Synthetic-body OOD | geometry map still ~0 (n=402); **not real-human generalization** |
| Material OOD | measurement-only disagrees with stiff gold 21% [9%, 36%] (n=33) |
| Action outside ±3 cm | policy: abstain |
| ±3 cm bust with flare=1 | waist follows 100% (structural side effect, n=162) |

Failure-aware (n=633): OOD-detection AUROC **0.90**, abstention precision **1.0**. OOD body / OOD material / ambiguous buckets all abstain; in-distribution easy cases are accuracy 1.0 with abstain rate 0. Hero case 4 is an explicit **refusal**.

![OOD](reports/figures/10_ood_results.png)
![risk–coverage](reports/figures/11_risk_coverage.png)
![decision regret](reports/figures/12_decision_regret.png)
![failure buckets](reports/figures/14_failure_gallery.png)

### 6. The experiments become a next-sample recommendation for a technical designer

The workspace asks the same question: **What should change in the next sample?** The header has a one-click 中文 / English toggle.

```bash
cd studio && npm install && npm run dev
# http://127.0.0.1:43187
```

Five hero cases: chest tight → +3 cm; same measurements, different cloth; waist side-effect prefers a smaller edit; OOD body abstains; bust vs shoulder resolved as shoulder NO-GO.

![Hero cases](reports/figures/13_hero_cases.png)
![candidate utility](reports/figures/candidate_utility_ranking.png)

---

## The experiment: from observational data to an intervention lattice

The path was not “train a large model, then find a story.” It was the reverse: **prove the intervention is measurable, then decide whether learning is necessary.**

### Step 1. Observational data gives correlation, not the next cut

FIT-Clean comes from public FIT-100K measurement fields (~105k rows, split by person hash). It can answer “historically, similar bodies had garments that differed by X cm.” It cannot build a counterfactual. B0 median-ease MAE is 8.11 cm; XGBoost only reaches 7.88 cm — that is an observational ceiling, not a failure of the correction system.

Eval-split body and garment sizes:

| Body bust | Body waist | Body hips | Body height |
| --- | --- | --- | --- |
| ![eb](reports/figures/eval_hist_body_bust_cm.png) | ![ew](reports/figures/eval_hist_body_waist_cm.png) | ![eh](reports/figures/eval_hist_body_hips_cm.png) | ![eht](reports/figures/eval_hist_body_height_cm.png) |

| Garment bust | Garment length | Sleeve | Bust ease |
| --- | --- | --- | --- |
| ![gb](reports/figures/eval_hist_garment_bust_cm.png) | ![gl](reports/figures/eval_hist_garment_length_cm.png) | ![gs](reports/figures/eval_hist_garment_sleeve_cm.png) | ![ge](reports/figures/eval_hist_bust_ease_cm.png) |

| Ease ratio | Ease quantization | Length/height | Ease scatter |
| --- | --- | --- | --- |
| ![er](reports/figures/eval_hist_bust_ease_ratio.png) | ![eq](reports/figures/eval_bust_ease_ratio_quantization.png) | ![elr](reports/figures/eval_hist_garment_length_height_ratio.png) | ![esc](reports/figures/eval_bust_ease_scatter.png) |

Full-FIT distribution audit (same fields; eval is not a special case):

| Body bust | Body waist | Body hips | Body height |
| --- | --- | --- | --- |
| ![fb](reports/figures/full_fit_hist_body_bust_cm.png) | ![fw](reports/figures/full_fit_hist_body_waist_cm.png) | ![fh](reports/figures/full_fit_hist_body_hips_cm.png) | ![fht](reports/figures/full_fit_hist_body_height_cm.png) |

| Garment bust | Garment length | Sleeve | Bust ease |
| --- | --- | --- | --- |
| ![fgb](reports/figures/full_fit_hist_garment_bust_cm.png) | ![fgl](reports/figures/full_fit_hist_garment_length_cm.png) | ![fgs](reports/figures/full_fit_hist_garment_sleeve_cm.png) | ![fge](reports/figures/full_fit_hist_bust_ease_cm.png) |

| Ease ratio | Length/height |
| --- | --- |
| ![fer](reports/figures/full_fit_hist_bust_ease_ratio.png) | ![felr](reports/figures/full_fit_hist_garment_length_height_ratio.png) |

Data engineering left its own traces: shard memory, near-duplicates, leakage audits live under `reports/`. Observational image bytes are **not** in this repo (license and size); measurements, schemas, and audit plots are.

![shard memory](reports/figures/memory_by_shard.png)

### Step 2. Turn pattern parameters into repeatable centimetres

On GPU (RTX 4090, Warp 1.0.0-beta.6, Torch 2.5.1+cu124) we atomically calibrated the GarmentCode Shirt: change `shirt.width.v`, serialize panels, **measure** after−before. Only after the identity map is real can we talk about a lattice, physics, and learning.

An early sleeve probe along panel Y produced Δ=0 — a measurement-definition bug, not a broken pattern. The shoulder probe showed this family has no independent shoulder DoF. That is a **NO-GO result**, not an unfinished experiment.

### Step 3. Send those centimetres into cloth physics

Body OBJ is metres; cloth mesh is centimetres. After alignment, Warp XPBD on a static mannequin yields clearance / contact. v0.2 freeze: **636** transitions (0 duplicate state-action pairs, 0 intended→realized copies), **127** successful physics sims. Visual disambiguation adds 33 pairs / 71 physics cases.

No SMPL-X weights. The pipeline did not halt; it labelled the run `SYNTHETIC_BODY_PHYSICS` and forbade calling a dummy a real-human validation.

### Step 4. Train only where learning might beat the analytic map

On trivial geometry the analytic inverse is already 0. We still trained Transition SFT, Decision SFT, and RLVR — not to pad a leaderboard, but to **measure residual**. Result: SFT loses to analytic; decision holdout n=3 already has regret 0; RLVR adds nothing and is officially `NOT_JUSTIFIED`.

In the complex regime (matched measurements, different drape) the best correction can flip, but grouped-split CIs overlap, so vision necessity is **not statistically established**. That is the honest stopping line.

---

## Training conclusions: what was worth learning

GPU training completed: B0, B1, B1-Ridge, B1-XGBoost, generated-pattern B2/B3, Transition SFT, Decision SFT, RLVR. The 197GB FIT-100K images were **not downloaded**; vision baselines use rasterized pattern drawings (192 images).

| Task | Status | Headline |
| --- | --- | --- |
| B0 ease heuristic | PASS | test MAE 8.11 cm (observational, not intervention GT) |
| B1 OLS | PASS | test MAE 8.08 cm |
| B1 Ridge | PASS | test MAE 8.08 cm |
| B1 XGBoost | PASS | test MAE 7.88 cm |
| B2 FIT-100K vision | NOT_RUN | images not on disk |
| B2 generated-pattern Ridge | PASS | test MAE 3.45 cm (192 drawings) |
| B2 generated-pattern CNN | PASS | test MAE 6.23 cm; Ridge wins |
| B3 CNN+body | PASS | test MAE 6.24 cm; no multimodal gain |
| Transition SFT MLP | PASS | MAE 0.47 cm; analytic ~0 |
| Decision SFT MLP | PASS | holdout accuracy 1.0, regret 0.0 (**n=3; do not boast**) |
| RLVR REINFORCE | NOT_JUSTIFIED | 300 CUDA steps; no residual after SFT |
| Qwen2-VL-2B zero-shot | PASS | parse 100%, match 83%, n=12, majority class |

![Transition SFT MLP](reports/figures/transition_sft_mlp_loss.png)
![Transition SFT LM](reports/figures/transition_sft_lm_loss.png)
![Decision SFT](reports/figures/decision_sft_mlp_loss.png)
![RLVR](reports/figures/rlvr_reward.png)

**Training in one paragraph:**

- Stronger observational regression still cannot answer “how many centimetres in the next sample.”
- On pattern drawings a linear model beats a small CNN: the signal is measurable geometry, not texture mysticism.
- On the intervention lattice the analytic inverse is the iron baseline; SFT does not beat it.
- RLVR has no research value when regret is already 0 and holdout is 3 rows.
- Vision / MLLM becomes necessary only when matched measurements change the best correction **and** grouped-split CIs separate. That is not established here.

Longer argument: [`reports/WHEN_IS_LEARNING_NECESSARY.md`](reports/WHEN_IS_LEARNING_NECESSARY.md) and [`reports/TRAINING_RUN.md`](reports/TRAINING_RUN.md).

---

## Is there a better approach?

Yes. We refused several that photograph better.

| Approach that looks stronger | Why not this round / when it becomes justified |
| --- | --- |
| Fine-tune Qwen2-VL / GPT-4V first | Analytic inverse is already 0 error on trivial geometry |
| An agent that edits patterns | No measured Δ, no physics — a talkative dressing room |
| RLVR / RL pattern editing | Decision holdout n=3, regret already 0; RLVR `NOT_JUSTIFIED` |
| Train a CNN on FIT-100K | 197GB not downloaded; Ridge > CNN on 192 drawings |
| Copy intended into realized | Fraud; tests reject it |
| Halt without SMPL-X | Wrong. Continue on synthetic mannequins and label them |
| Force a shoulder PASS on Shirt | No independent DoF; a NO-GO is the research result |
| Tune the split until vision “wins” | 7/33 flips are real; statistical necessity is not |
| Call millimetre clearance a factory fit | Dummy evidence ≠ a real fit session |

**Better next steps (after licensed assets):**

1. Repeat the same lattice on licensed SMPL-X  
2. Keep the analytic inverse as the trivial-regime iron baseline  
3. Claim vision/MLLM necessity only when matched measurements flip the best correction **and** grouped-split CIs separate  
4. Validate on real fit sessions — do not call a dummy a production system  
5. If you train the complex regime, grow the physics gold and the grouped split first, then consider LoRA — do not jump from zero-shot n=12 to “multimodal success”

---

## Full figure gallery

The narrative above already embeds the headline figures. Below is **every** statistical chart and evidence plot still in the repo, archived by experiment stage so no figure sits outside the story.

### A. System and intervention

| Architecture | Pipeline | Hero cases |
| --- | --- | --- |
| ![a1](reports/figures/01_system_architecture.png) | ![a2](reports/figures/02_intervention_pipeline.png) | ![a3](reports/figures/13_hero_cases.png) |

### B. Geometry calibration

| Bust calibration | Intended vs realized | Calibration curve | Side effects |
| --- | --- | --- | --- |
| ![b1](reports/figures/03_bust_calibration.png) | ![b2](reports/figures/bust_intended_vs_realized.png) | ![b3](reports/figures/bust_calibration_curve.png) | ![b4](reports/figures/bust_side_effects.png) |

### C. Synthetic-body physics

| Physics before/after | Clearance/contact | Physics metrics | Candidate utility |
| --- | --- | --- | --- |
| ![c1](reports/figures/04_physics_before_after.png) | ![c2](reports/figures/05_clearance_contact.png) | ![c3](reports/figures/physics_clearance_contact.png) | ![c4](reports/figures/candidate_utility_ranking.png) |

### D. Baselines, vision, OOD

| Baseline ladder | Visual disambiguation | Multimodal ablation | Trivial vs complex |
| --- | --- | --- | --- |
| ![d1](reports/figures/06_baseline_ladder.png) | ![d2](reports/figures/07_visual_disambiguation.png) | ![d3](reports/figures/08_multimodal_ablation.png) | ![d4](reports/figures/09_trivial_vs_complex.png) |

| OOD | Risk–coverage | Decision regret | Failure buckets |
| --- | --- | --- | --- |
| ![d5](reports/figures/10_ood_results.png) | ![d6](reports/figures/11_risk_coverage.png) | ![d7](reports/figures/12_decision_regret.png) | ![d8](reports/figures/14_failure_gallery.png) |

### E. Training curves (negative results kept)

| Transition MLP | Transition LM | Decision SFT | RLVR |
| --- | --- | --- | --- |
| ![e1](reports/figures/transition_sft_mlp_loss.png) | ![e2](reports/figures/transition_sft_lm_loss.png) | ![e3](reports/figures/decision_sft_mlp_loss.png) | ![e4](reports/figures/rlvr_reward.png) |

| Observational MAE | Shard memory |
| --- | --- |
| ![e5](reports/figures/observational_baseline_mae.png) | ![e6](reports/figures/memory_by_shard.png) |

Numbers: [`artifacts/FINAL_METRICS.json`](artifacts/FINAL_METRICS.json) · [`artifacts/FINAL_STATUS.json`](artifacts/FINAL_STATUS.json) · [`artifacts/hero/ood_results.json`](artifacts/hero/ood_results.json) · [`artifacts/hero/failure_aware.json`](artifacts/hero/failure_aware.json) · [`artifacts/hero/visual_disambiguation.json`](artifacts/hero/visual_disambiguation.json) · [`artifacts/training/observational_and_vision_baselines.json`](artifacts/training/observational_and_vision_baselines.json) · [`artifacts/hero/mllm_eval.json`](artifacts/hero/mllm_eval.json) · [`artifacts/hero/correction_lattice_v0.2.jsonl`](artifacts/hero/correction_lattice_v0.2.jsonl)

What died with the GPU host is listed in [`artifacts/GPU_SHUTDOWN_ASSET_INVENTORY.md`](artifacts/GPU_SHUTDOWN_ASSET_INVENTORY.md): ~677 pattern PNGs, most Warp `.obj` files, and ~4.2GB of Qwen weights. **The conclusions live in JSON, not in the lost PNGs.**

---

## Status matrix and data index

Allowed words only: `PASS` · `NO_GO_WITH_EVIDENCE` · `NOT_JUSTIFIED` · `HARD_BLOCKED_LICENSE`

| Track | Status |
| --- | --- |
| Core / Warp / PyTorch | PASS |
| Geometry / synthetic physics | PASS |
| Bust / sleeve / large lattice | PASS |
| Shoulder | NO_GO_WITH_EVIDENCE |
| Visual disambiguation | PASS (verdict: necessity not established) |
| Classical / vision / multimodal baselines | PASS |
| Pretrained MLLM experiment | PASS (zero-shot, n=12) |
| Transition | PASS (analytic is better) |
| Decision SFT | PASS (n=3; do not boast) |
| RLVR | NOT_JUSTIFIED |
| OOD / failure-aware / demo | PASS |
| SMPL-X / real human | HARD_BLOCKED_LICENSE |

Lattice: 636 transitions, 0 duplicate state-action pairs, 0 intended→realized copies. Physics: 127 SIMULATED rows.

Reports: [`reports/EXPERIMENT_TABLE.md`](reports/EXPERIMENT_TABLE.md) · [`reports/WHEN_IS_LEARNING_NECESSARY.md`](reports/WHEN_IS_LEARNING_NECESSARY.md) · [`reports/TRAINING_RUN.md`](reports/TRAINING_RUN.md) · [`reports/OOD_REPORT.md`](reports/OOD_REPORT.md) · [`reports/FAILURE_ANALYSIS.md`](reports/FAILURE_ANALYSIS.md) · [`reports/RESUME_CLAIMS.md`](reports/RESUME_CLAIMS.md) · [`reports/TECHNICAL_ARCHITECTURE.md`](reports/TECHNICAL_ARCHITECTURE.md)

Mirrors: [GitHub](https://github.com/Benjamindaoson/FitGround) · [Hugging Face datasets](https://huggingface.co/datasets/jlai300/FitGround)

---

## How to run

```bash
make smoke
make benchmark-fast
cd studio && npm install && npm run dev   # :43187 , in-page 中文 / English toggle
```

GPU (GarmentCodeV2 + Warp + RTX; this cloud box does not have the billed-and-powered-off 4090):

```bash
source scripts/gpu/flux_env.sh
python scripts/gpu/hero_pipeline.py
python scripts/gpu/expand_visual_physics.py
python scripts/gpu/finalize_closure.py
```

---

## Hard limits

No SMPL-X weights. No real-human validation. Shirt/tee family only. The v0.2 677 pattern PNGs and most Warp `.obj` files died with the GPU host; **the numbers live in JSON**. Qwen2-VL eval n=12. Decision/RLVR holdout is tiny. Clearance shifts are millimetre-class dummy results, not a factory fit session.

<p align="right">
  <a href="./README.md">中文</a> · <b>English</b>
</p>
