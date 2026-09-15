# FitGround

**FitGround predicts how a garment modification will change fit, then recommends the smallest effective correction for the next sample.**

This is a technical-designer workspace, not a consumer virtual try-on.

![Current sample drape](reports/figures/baseline_render_front.png)
![Bust +3 cm drape](reports/figures/bust_plus_3cm_render_front.png)

| | |
| --- | --- |
| Problem | Sample is wrong. What changes in the next one? |
| Intervention | Named pattern parameters with **measured** `realized_delta_cm` |
| Physics | Warp XPBD on a **static mannequin OBJ** (`SYNTHETIC_BODY_PHYSICS`). SMPL-X weights are absent; pipeline does not stop. |
| Decision | Enumerated candidates → utility → recommendation, confidence, alternatives |
| Demo | `studio/` Next.js workspace at port 43187 |

| Status | Fact |
| --- | --- |
| Bust calibration | Pattern identity map to ~1e-14 cm; waist coupled (`flare=1`) |
| Sleeve | Re-measured on panel **X** (GarmentCode construction axis). Prior Y-span was a measurement bug. |
| Shoulder | No independent `shoulder_w` on Shirt; connecting_width probed (GO only with evidence) |
| Physics metrics | Body scaled m→cm; chest clearance p10 0.47→0.50 cm at +3 cm; contact 0.027→0.022 |
| Observational B0/B1/XGB | MAE 8.11 / 8.08 / 7.88 cm on FIT-Clean (not intervention GT) |
| Pattern Ridge vs CNN | Ridge 3.45 cm beats CNN 6.23 cm on 192 drawings |
| Transition SFT | MAE 0.47 cm; analytic inverse is 0.00 on this grid |
| Decision SFT / RLVR | Holdout acc 1.0 (n=3); RLVR no residual gain |
| Vision necessity | Material-split benchmark running on GPU; not claimed until pairs exist |

## Demo / Results

Interactive workspace:

```bash
cd studio && npm install && npm run dev
# http://127.0.0.1:43187
```

GPU completion pipeline:

```bash
source scripts/gpu/flux_env.sh
python scripts/gpu/hero_pipeline.py
python scripts/train/train_hero_ladder.py
```


## Demo / Results / 当前 GPU 结果

This GPU pass implemented a real correction slice, not a tutorial:

1. Warp CUDA kernel smoke PASS (`artifacts/gpu/warp_smoke.json`).
2. Bust atomic calibration PARTIAL (`artifacts/bust_atomic_calibration.json`): intended vs realized +1/+2/+3 cm match to numerical noise; +3 cm repeat matches exactly.
3. Physics + render PASS for baseline / +1 / +2 / +3 cm (`artifacts/gpu/physics_lattice/`).
4. CHEST_CASE utility ranking oracle = bust +3 cm (`artifacts/correction_lattice_chest_case.json`).
5. Observational B0 MAE 8.11 / B1 OLS 8.08 / B1 XGBoost 7.88 cm on FIT-Clean garment bust (not intervention GT).
6. Generated-pattern B2 Ridge MAE 3.45 cm; B2 CNN 6.23 cm (CNN does not beat Ridge on 192 drawings).
7. Transition SFT MLP realized-delta test MAE 0.47 cm on 16 held-out rows (identity map is 0.00 on this calibrated bust/length grid).
8. Decision SFT MLP action accuracy 1.0 on 3 held-out CHEST_CASE-style states; RLVR REINFORCE ran 300 CUDA steps and did not improve a zero-regret SFT policy.

![Transition SFT MLP val loss](reports/figures/transition_sft_mlp_loss.png)

![Decision SFT MLP CE](reports/figures/decision_sft_mlp_loss.png)

![RLVR measured utility](reports/figures/rlvr_reward.png)

![Intended vs realized bust delta](reports/figures/bust_intended_vs_realized.png)

![Before (baseline) drape](reports/figures/baseline_render_front.png)

![After Bust +3 cm drape](reports/figures/bust_plus_3cm_render_front.png)

![Candidate utility ranking](reports/figures/candidate_utility_ranking.png)

Do not read these renders as virtual try-on product shots. They are physics-draped Shirt patterns on a static mean body, used as correction evidence.

Demo CLIs:

```bash
python scripts/select_correction.py
python scripts/predict_transition.py --intended-delta-cm 3
python scripts/run_fit_correction_smoke.py --case CHEST_CASE --backend garmentcode --output-dir artifacts/gpu/smoke_out
```

The default smoke runner still preserves `SIMULATION_BACKEND_NOT_CONFIGURED` unless `--backend garmentcode` is set.


## Contents / 目录

- [The problem / 要解决什么问题](#the-problem--要解决什么问题)
- [Who it is for / 服务对象](#who-it-is-for--服务对象)
- [What FitGround does / 系统做什么](#what-fitground-does--系统做什么)
- [Decision loop / 决策闭环](#decision-loop--决策闭环)
- [V0.1 action space / V01 动作空间](#v01-action-space--v01-动作空间)
- [Research design / 研究设计](#research-design--研究设计)
- [Architecture and code map / 架构与代码地图](#architecture-and-code-map--架构与代码地图)
- [Data foundation / 数据基础](#data-foundation--数据基础)
- [What works today / 当前可运行内容](#what-works-today--当前可运行内容)
- [Quick start / 快速开始](#quick-start--快速开始)
- [Validation and roadmap / 验证与路线图](#validation-and-roadmap--验证与路线图)
- [Scope, contribution, and licensing / 范围、贡献与许可证](#scope-contribution-and-licensing--范围贡献与许可证)

---

## The problem / 要解决什么问题

### The expensive question is not “tight or loose”

A technical designer can often see that a sample has a problem: chest tension, a diagonal drag line near the armhole, shoulder restriction, an overly long sleeve, or unwanted looseness. The expensive part is deciding what to change next.

在传统 fit session 中，发现“不合身”通常不难；真正昂贵的是依赖专家经验反复试错：这到底是胸围余量、肩部限制、上胸几何、面料刚度，还是其他结构因素？下一版应改 `+1 cm`、`+2 cm` 还是 `+3 cm`？这样做会不会让别的区域变差？

```text
Current sample has a fit problem
        ↓
What likely caused it?
        ↓
Which correction should be attempted next?
        ↓
How much should change?
        ↓
Will it solve the target region without harming another one?
```

FitGround is built around that decision—not around a binary tight/loose classifier.

FitGround 的目标是提高 **下一版样衣一次改对的概率**，而不只是判断它“紧”还是“松”。

### Why this is hard / 为什么困难

The same visible symptom can have different physical explanations. The same ease measurement can behave differently under another material, body, construction, pose, or fit intent. A measurement-only rule such as `body_bust + garment_bust → delta_bust` therefore cannot be the product.

同一组人体与服装尺寸，可能因为视觉症状不同而需要不同修正；相似的视觉症状，也可能对不同干预动作有不同响应。FitGround 必须保留 visual evidence、material 和 fit intent，避免退化成一个简单的尺寸差公式。

## Who it is for / 服务对象

**Primary user: technical designers** reviewing a physical or simulated sample with a known fit concern.

**主要用户：** 正在审看问题样衣的服装技术设计师。Pattern maker、fit reviewer、开发团队是下游协作者；V0.1 不把他们拆成独立产品 persona。

| Workflow moment / 工作节点 | FitGround's intended contribution / 预期贡献 | It does not claim to do / 不宣称做到 |
| --- | --- | --- |
| Pre-fit-session review | Organize body, garment, visual, material, and intent evidence | Replace expert judgment with an opaque score |
| Fit-comment preparation | Compare a small set of explicit candidate corrections | Automatically issue a production-ready pattern |
| Sample iteration planning | Predict and rank next-fit outcomes when a verifier exists | Promise a real-world fit result without verification |
| Pattern-maker handoff | Preserve intended action, measured realization, provenance, and side effects | Copy intended delta into realized delta |
| Research and QA | Measure regret, side effects, and first-pass correction | Use ordinary classification accuracy as the north star |

## What FitGround does / 系统做什么

FitGround combines five kinds of information about an already-observed sample:

```text
Current fit image / 3D evidence       I
Body measurements                     B
Garment measurements or geometry      G
Material and garment metadata         M
Fit intent                            F
```

Together they form a current state `s = (I, B, G, M, F)`. Given a candidate garment correction `a = ΔG`, FitGround’s central learning target is:

```text
(s, a) → ŝ'
```

In plain language: **given the current sample and one candidate modification, predict the next fit state.** Selection happens downstream:

```text
a* = argmax_a U(ŝ', a)
```

其中 utility `U` 至少考虑目标区域 fit error、修改幅度与未预期副作用。这个建模选择将项目从“直接预测一个动作”转为“比较多个动作分别会带来什么后果”。

### Intended output / 预期输出

For a future verified run, FitGround is designed to return:

1. A **CauseHypothesis** — a likely explanation with supporting evidence and verification status.
2. Ranked **CandidateCorrections** — precise, bounded garment changes.
3. A **PredictedFitOutcome** per candidate — regional before/after state, direction, magnitude, side effects, confidence, and provenance.
4. A **CorrectionLattice** — competing actions, outcomes, utilities, and an oracle only when simulation exists.
5. A recommendation only when an available outcome and utility genuinely support one.

模型可以提出 likely cause，但不把 cause label 伪装为绝对物理真值。一个诊断是否可信，主要取决于它能否正确预测干预后果。

## Decision loop / 决策闭环

```mermaid
flowchart TD
    A[Current sample has a fit problem<br/>当前样衣出现 fit 问题] --> B[Body + Garment + Visual<br/>Material + Fit Intent]
    B --> C[Multimodal understanding<br/>多模态理解]
    C --> D[Likely cause hypothesis<br/>可能原因假设]
    D --> E[Candidate corrections<br/>候选修正动作]
    E --> F[Fit transition prediction<br/>(state, action) to next state]
    F --> G[Physics-based simulated verifier<br/>物理仿真验证]
    G --> H[Utility, regret, side effects<br/>效用、遗憾值与副作用]
    H --> I[Lowest-regret correction<br/>最低遗憾修正建议]
```

The simulator is a **physics-based simulated verifier**, not “real-world ground truth.” Results must preserve backend configuration, artifacts, hashes, and failures rather than presenting a render as fact about a physical production sample.

仿真在 FitGround 中不是“现实世界真值”，而是可追溯的 simulated verifier。任何未运行、未校准或失败的结果必须明确显示为 `NOT_RUN`、`NOT_VERIFIED` 或 `FAILED`。

## V0.1 action space / V0.1 动作空间

FitGround starts small on purpose. V0.1 supports only three explicit action families:

| Action family | Meaning / 含义 | Current status / 当前状态 |
| --- | --- | --- |
| `bust_circumference_delta_cm` | Change garment bust circumference by a named centimetre delta | Contract-ready; mapping not calibrated |
| `shoulder_width_delta_cm` | Change garment shoulder width by a named centimetre delta | Contract-ready; mapping not calibrated |
| `sleeve_length_delta_cm` | Change garment sleeve length by a named centimetre delta | Contract-ready; mapping not calibrated |

Every candidate records both values below; they are never automatically copied:

```text
intended_delta_cm  = requested correction, e.g. +3.00 cm
realized_delta_cm  = physically measured result after a verified operation
```

`realized_delta_cm` remains `null` until a pattern/backend operation has actually happened and been measured. Ambiguous actions such as “armhole +1 cm” are deliberately excluded until their physical mapping is explicit and calibrated.

## Research design / 研究设计

### Diagnosis is validated by intervention prediction

Suppose a chest symptom leads to the hypothesis **insufficient bust ease**. That hypothesis is useful only if it predicts an ordered response:

```text
Bust +1 cm  → slight improvement
Bust +2 cm  → stronger improvement
Bust +3 cm  → target fit

Shoulder +1 cm control → no comparable improvement, or a different side effect
```

```text
Diagnosis credibility ≈ intervention predictive validity
```

FitGround 因此不依赖一个“看起来物理正确”的固定 cause ontology；它要求 cause hypothesis 在候选干预的相对效果上经得起验证。

### The correction lattice / 反事实修正格

The core data structure is a **Counterfactual Fit Correction Lattice**, not a final TIGHT / REGULAR / LOOSE dataset.

```text
Current state
├── Bust +1 cm       → simulated next state
├── Bust +2 cm       → simulated next state
├── Bust +3 cm       → simulated next state
├── Shoulder +1 cm   → control outcome
└── Sleeve -1 cm     → control outcome
```

Each lattice preserves current state, visual assets, material, garment type, fit intent, intended action, independently measured realized delta, next state, side effects, utility, source revisions, hashes, and failure artifacts.

旧版 Controlled Fit Ladder 被完整保留，但重新定位为 `LEGACY / SIMULATION SANITY / INTERVENTION FOUNDATION`，不再被误称为产品的最终 hero dataset。

### Visual disambiguation / 视觉消歧

The future data design must include cases a measurement-only baseline cannot solve:

- Same measurements, different visual symptom
- Similar visual symptom, different intervention response
- Same ease, different material
- Same garment, different fit intent

这组原则构成 **Visual-Disambiguation Set**：多模态模型的价值必须来自真正的视觉、材质与意图消歧，而不是从尺寸字段中走捷径。

### Metrics / 指标

The north-star metric is **Simulation-Verified First-Pass Correction Rate**: the share of first-ranked corrections that reach target fit in simulated verification without unacceptable new problems.

Supporting measures are **Intervention Regret** `U(a*) - U(â)`, **Side-Effect Rate**, and **Correction Magnitude Error**. Ordinary classification accuracy can be diagnostic, but is not the business north star.

## Architecture and code map / 架构与代码地图

```text
┌──────────────────────────────────────────────────────────────────────┐
│ CurrentFitState                                                       │
│ body · garment · visual assets · material · garment type · fit intent │
│ region fit state · provenance                                         │
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Multimodal Fit Transition Model                                       │
│              (CurrentFitState, CandidateCorrection) → PredictedFitOutcome │
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Physics-based simulated verifier                                      │
│ apply action → measure realized delta → simulate → render → extract   │
│ outcome → record provenance, side effects, and failures               │
└──────────────────────────────────────────────────────────────────────┘
```

The source-evidence-based runtime diagram is available in [docs/architecture/FITGROUND_EXISTING_RUNTIME_ARCHITECTURE.html](docs/architecture/FITGROUND_EXISTING_RUNTIME_ARCHITECTURE.html).

| Path | Responsibility / 职责 |
| --- | --- |
| [`src/fitground/correction/`](src/fitground/correction/) | Typed correction contracts, planning API, deterministic lattice builder, validation |
| [`schemas/fit_correction_v0.1.schema.json`](schemas/fit_correction_v0.1.schema.json) | Machine-readable V0.1 schema |
| [`scripts/calibrate_correction_action.py`](scripts/calibrate_correction_action.py) | Dry-run framework for intended vs. realized calibration |
| [`scripts/build_correction_lattice.py`](scripts/build_correction_lattice.py) | Deterministic planned lattice construction |
| [`scripts/validate_correction_lattice.py`](scripts/validate_correction_lattice.py) | Structural and completeness validation |
| [`scripts/run_fit_correction_smoke.py`](scripts/run_fit_correction_smoke.py) | Failure-preserving GPU smoke-runner seam |
| [`tests/`](tests/) | Contract, determinism, failure-preservation, and frozen-history tests |
| [`docs/`](docs/) and [`reports/`](reports/) | Contracts, architecture, audit, migration, readiness, and evidence |
| [`openspec/`](openspec/) | Machine-reviewable product and implementation changes |

## Data foundation / 数据基础

Raw external data is **not** committed to this repository. Source IDs, revisions, hashes, roles, and acquisition status live in [`artifacts/FITGROUND_V0_1_P0_SOURCE_ACQUISITION.json`](artifacts/FITGROUND_V0_1_P0_SOURCE_ACQUISITION.json).

| Asset | Role in FitGround | What it is not |
| --- | --- | --- |
| FIT-Clean v0.1 | Observational visual/measurement/provenance foundation | A correction-outcome dataset |
| Legacy counterfactual matching | Analysis of paired FIT observations | Verified garment intervention data |
| Controlled Fit Ladder / GPU E0 | Simulation sanity and intervention foundation | Calibrated V0.1 action space |
| [GarmentCode](https://github.com/maria-korosteleva/GarmentCode) | Parametric garment and future calibration substrate | A verified FitGround action mapping today |
| [FitVTON](https://github.com/ZenoNing/FitVTON) | Candidate GarmentCodeV2 / Warp pipeline bootstrap | A direct correction-label dataset |
| [GarmentCodeVTONDataset](https://huggingface.co/datasets/ZenoNing/GarmentCodeVTONDataset) | Synthetic visual and pipeline bootstrap | A calibrated intended-to-realized lattice |
| [FittingEffectDataset](https://huggingface.co/datasets/ZenoNing/FittingEffectDataset) | Lightweight real-visual try-on evaluation/probe | A correction side-effect dataset |

### Data principles / 数据原则

- Public research use is evaluated by product relevance and source terms—not automatically rejected because a dataset is non-commercial.
- Raw source data, external code snapshots, caches, and logs stay outside Git to keep the repository reproducible and lightweight.
- A completed download proves byte acquisition, not the semantic existence of V0.1 correction labels.
- Upstream licenses and redistribution rules remain separate from FitGround code. Do not re-upload an upstream dataset simply because it is publicly downloadable.

Read [Data Foundation](docs/FITGROUND_DATA_FOUNDATION_v0.1.md) and [Matching Dataset Scout](reports/FITGROUND_V0_1_MATCHING_DATASET_SCOUT.md) for exact revisions, storage boundaries, and GPU gates.

## What works today / 当前可运行内容

### Verified locally / 已在本地验证

- `CurrentFitState`, `CauseHypothesis`, `CandidateCorrection`, `PredictedFitOutcome`, and `CorrectionLattice` validate multimodal and provenance fields.
- Unsupported action families are rejected; candidate and lattice IDs are deterministic.
- `intended_delta_cm` and `realized_delta_cm` remain separate.
- The lattice validator detects duplicate actions, missing outcomes, incomplete provenance, and invalid rankings.
- Calibration and smoke-runner dry runs preserve `NOT_RUN` / `NOT_VERIFIED` semantics.
- A non-dry-run backend absence becomes a preserved `SIMULATION_BACKEND_NOT_CONFIGURED` artifact rather than a fabricated result.
- Frozen FIT-Clean / experimental / GPU E0 evidence is protected by hash-based tests.

### Not claimed yet / 当前不作此类声明

- Bust circumference is calibrated for GarmentCode `shirt.width.v`; shoulder remains NOT_VERIFIED. Sleeve length `.v` did not change the current panel-dy measurement (realized 0.0), so that family is still NOT_VERIFIED.
- Physics + render exist for the CHEST_CASE bust lattice on static `mean_all.obj`, not SMPL-X.
- Observational B0/B1/B1-XGB are trained. Vision B2/B3 used **generated pattern drawings**, not FIT-100K images.
- Transition SFT and Decision SFT were trained on a measured 88-row lattice. They are small MLP/char-LM models, not a pretrained MLLM.
- RLVR ran, but Decision SFT already had zero utility regret on the holdout, so RLVR is `COMPLETED_NOT_JUSTIFIED` as an extra optimizer.
- No production recommendation model, no real-world first-pass improvement claim.

This evidence boundary is a feature: FitGround is designed to fail visibly before it is allowed to overclaim.

## Quick start / 快速开始

### Install and verify / 安装与验证

```powershell
# From the repository root / 在仓库根目录执行
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
.\.venv\Scripts\python.exe -m pytest -q
```

Expected current result / 当前预期结果:

```text
58 passed, 2 skipped
```

### Plan a smoke run safely / 安全地规划 smoke run

```powershell
.\.venv\Scripts\python.exe scripts\run_fit_correction_smoke.py `
  --dry-run `
  --case CHEST_CASE `
  --output-dir .\local_runs
```

The dry run writes a plan without inventing a simulation result. Without `--dry-run`, the local runner currently preserves a failure artifact because no verified simulation backend is configured. This is expected.

不带 `--dry-run` 的本地 runner 会保留失败 artifact，而不是伪造 after-state、render、utility 或 realized delta；这是正确的安全边界。

## Validation and roadmap / 验证与路线图

### Evidence and reproducibility / 证据与可复现性

| Layer | Current mechanism |
| --- | --- |
| Schema integrity | JSON Schema plus contract tests |
| Determinism | Stable candidate/lattice IDs and uniqueness checks |
| Semantic honesty | Explicit `NOT_RUN`, `NOT_VERIFIED`, `SIMULATED`, and `FAILED` states |
| Failure semantics | Failure artifacts are retained rather than silently omitted |
| Provenance | Source revisions, hashes, environment fields, seeds, and artifact paths |
| Legacy preservation | Hash-based protection for frozen FIT-Clean / contract / GPU E0 files |
| Publication safety | Git ignores raw data, upstream copies, caches, logs, and local tooling state |

Evidence entry points:

- [Product Contract](docs/FITGROUND_PRODUCT_CONTRACT_v0.1.md)
- [Technical Contract](docs/FITGROUND_TECHNICAL_CONTRACT_v0.1.md)
- [File-level Codebase Audit](reports/FITGROUND_V0_1_CODEBASE_AUDIT.md)
- [Old-to-New Migration Matrix](reports/FITGROUND_V0_1_MIGRATION_MATRIX.md)
- [Pre-GPU Readiness Review](reports/FITGROUND_V0_1_PRE_GPU_READINESS.md)
- [Execution Playbook Cross-check](reports/FITGROUND_V0_1_EXECUTION_PLAYBOOK_CROSSCHECK.md)

### Gate-driven roadmap / 按验证门槛推进的路线图

**Phase 0 — correction contracts and evidence boundary ✅**

- Product and technical contracts frozen
- V0.1 schemas, deterministic lattice, dry-run calibration, and failure-preserving runner implemented
- Legacy evidence audited and preserved

**Phase 1 — atomic GPU correction calibration ⏳**

1. Map one named V0.1 action to auditable GarmentCode / pattern parameters.
2. Measure intended versus realized delta and cross-region effects.
3. Run one before → modification → after simulation/render/outcome path with full provenance.
4. Only then extend from chest to shoulder and sleeve actions.

**Phase 2 — correction lattice generation ⏳**

- Generate competing intervention candidates and controls.
- Record visual evidence, affected regions, utility, side effects, and oracle actions only where simulation exists.
- Build visual-disambiguation splits that defeat measurement-only shortcuts.

**Phase 3 — model baselines and transition learning ✅ (measured lattice, not FIT-100K vision)**

1. Rule/ease heuristic (B0) — test MAE 8.11 cm
2. Measurement baseline (B1 OLS / Ridge / XGBoost) — best XGB MAE 7.88 cm
3. Generated-pattern vision (B2 Ridge MAE 3.45 cm beats B2 CNN 6.23 cm)
4. Counterfactual Transition SFT + Decision SFT on 88 measured `(s,a,s')` rows

**Phase 4 — physics-verified optimization ⚠ completed, not justified**

Physics-Verified RLVR was executed (300 REINFORCE steps, cached measured utilities). Decision SFT already matched the oracle on the holdout (accuracy 1.0, regret 0), so RLVR added no residual gain.

## Scope, contribution, and licensing / 范围、贡献与许可证

### Non-goals / 非目标

FitGround is **not** currently building consumer sizing recommendations, generic virtual try-on, return prediction, merchandising, inventory allocation, PIM, agentic commerce, global sizing, a complete fashion platform, or an unverified action-label training benchmark.

聚焦不是功能缺失。FitGround 的 wedge 是把“下一版样衣该怎么改”从经验驱动的 trial-and-error，逐步变成可比较、可验证、可追溯的 correction decision。

### Contributing / 如何贡献

Contributions are welcome when they preserve the evidence boundary:

1. Read the [Product Contract](docs/FITGROUND_PRODUCT_CONTRACT_v0.1.md) and [Technical Contract](docs/FITGROUND_TECHNICAL_CONTRACT_v0.1.md).
2. Do not turn `NOT_RUN` into an implied result or copy intended into realized deltas.
3. Preserve failure artifacts, provenance, and frozen historical evidence.
4. Add tests for new validation, transition, calibration, or state semantics.
5. Keep raw datasets, credentials, caches, and heavyweight generated artifacts outside Git.

### License and attribution / 许可证与归属

This repository currently has **no repository-wide code license file**. Public visibility supports inspection and reproducibility, but it does not grant an unstated license to reuse code or upstream assets. A repository-wide license must be chosen explicitly before representing this project as reusable open-source software.

External projects and datasets—including GarmentCode, FitVTON, GarmentCodeVTONDataset, FittingEffectDataset, SMPL/SMPL-X assets, and NVIDIA Warp components—retain their own licenses, notices, and redistribution conditions. Review those terms before downloading, modifying, redistributing, or publishing derivatives.

FitGround’s future simulation foundation builds on public work from the [GarmentCode](https://github.com/maria-korosteleva/GarmentCode) and [FitVTON](https://github.com/ZenoNing/FitVTON) ecosystems. This repository documents how those assets may be evaluated for FitGround; it does not claim ownership of their code, data, weights, or results.

---

## Read the evidence, not just the headline / 用证据理解项目

For an honest current-state assessment, start with the [Product Contract](docs/FITGROUND_PRODUCT_CONTRACT_v0.1.md), [Technical Contract](docs/FITGROUND_TECHNICAL_CONTRACT_v0.1.md), [Pre-GPU Readiness Review](reports/FITGROUND_V0_1_PRE_GPU_READINESS.md), [Data Foundation](docs/FITGROUND_DATA_FOUNDATION_v0.1.md), and [Codebase Audit](reports/FITGROUND_V0_1_CODEBASE_AUDIT.md).

> **FitGround’s standard:** reuse what is correct, measure what is claimed, preserve what is frozen, and build only what makes the next sample more likely to fit right.
>
> **FitGround 的标准：保留正确的基础，测量每一项主张，冻结每一份证据，只构建真正能提高下一版样衣一次改对概率的能力。**
