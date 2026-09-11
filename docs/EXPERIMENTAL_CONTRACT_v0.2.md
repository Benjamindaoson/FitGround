# Experimental Contract v0.2

**Status:** FROZEN  
**Frozen:** 2026-09-11  
**Does not modify:** Experimental Contract v0.1 (PARTIAL / FROZEN; diagnostic only)

v0.1 remains the observational-stage freeze. v0.2 is the **controlled generation** contract. It authorizes a later **GPU E0 Stage 1** generation pilot. It does **not** authorize VLM training, LoRA, RM, DPO, GRPO, or full benchmark training.

Machine-readable twin: `artifacts/experimental_contract_v0.2.yaml`

---

## Research Question

Does a multimodal model respond correctly to controlled interventions in body–garment measurement relations when major visual and identity confounders are held fixed or explicitly controlled?

This is **not** “how high is VLM accuracy on FIT-100K.”

---

## Motivation

FitGround’s object is measurement-grounded fit understanding. Released FIT-100K supplies photoreal triplets and centimeter measurements, but Phase 2 showed that the only plentiful comparison unit (TIER C) changes the garment image together with the measurements. That is observational confounding, not a controlled `do(measurement)` experiment.

---

## Phase 2 Negative Finding

Inherited freeze (do not re-guess):

| Finding | Value |
|---------|-------|
| TIER A (same person + same cloth, multi-row) | 0 |
| TIER B | 1 exact + 1 near |
| TIER C groups / pairs | 1,689 / 1,729 |
| bust+length+sleeve all change | 1,574 / 1,731 |
| Univariate pairs | rare |
| Same-cloth measurement inconsistency | 0 |
| Body measurements in same-person groups | constant |
| Pixel-level fit change | NOT VERIFIED |
| Semantic identity leakage | NOT VERIFIED |
| Near-image duplicate | DEFERRED |
| COUNTERFACTUAL_FEASIBILITY | PARTIAL |

v0.1 allowed diagnosis, not training.

---

## Observational Limitation

Released FIT-100K identifies approximately:

\[
P(Y \mid \text{different garment}, \text{different measurement})
\]

It does not identify:

\[
P(Y \mid do(\text{measurement change}), \text{controlled context})
\]

Largest confound: **garment visual appearance co-varies completely with the measurement intervention.** Same cloth SHA256 never carries two measurement vectors. Searching the release for more pairs will not remove that confound.

---

## Controlled Generation Rationale

The FIT paper (Karras et al., SIGGRAPH 2026) documents a generator that *can* hold a body and a garment **design** while changing size via GarmentCode **cross-draping** (pattern drafted on source body A, draped on target body B, with box-mesh realignment).

Audit (`reports/FIT_GENERATION_MECHANISM_AUDIT.md`):

- Procedure: **VERIFIED_FROM_DOCS**
- Official FIT generation code: **not released**
- Public executable substrate: GarmentCode `d449629979028123a5c4dc9e732a2ec19b7fce31` — **VERIFIED_FROM_CODE**
- Official layflat `I_g`: VLM try-off from the **sized** try-on — **not** size-isolated

GPU E0 therefore implements the **documented 3D procedure**, not a claim to have rerun unpublished Flux LoRA / Nano Banana Pro.

---

## Primary Hypothesis / Null / Variables

**Primary hypothesis.** On a Controlled Fit Ladder (fixed body, body measurements, pose, garment design, fabric, texture, camera, render condition), moving the garment measurement vector TIGHT → REGULAR → LOOSE produces ordered target-geometry and human-visible fit change. In any later model test (not authorized here), model outputs should track the measurement relation rather than cloth appearance alone.

**Null.** After controls, remaining appearance differences fully explain target or model-output change; measurements add no independent contribution; or the ladder is not a valid intervention (no visible fit change, controls broken, or Track A still a size oracle).

| Role | Quantity |
|------|----------|
| Independent variable | Measurement vector \(M\) = (garment bust, length, sleeve) and induced ease / length ratio, ordered TIGHT < REGULAR < LOOSE |
| Controlled variables | body identity, body measurements, pose, garment design identity, fabric, texture, camera, render seed, background |
| Outcome (E0) | Draped target geometry + human-visible fit |
| Outcome (future models) | Response under pre-registered shortcut attacks |

S/M/L labels are **not** the independent variable. Authors use them only for visualization.

---

## Experimental Unit

**Controlled Fit Ladder** — schema: `artifacts/controlled_fit_ladder_schema_v0.2.yaml`

Each ladder has:

`ladder_id`, `body_id`, `garment_design_id`, `pose_id`, `fabric_id`, `texture_id`, `camera_id`, `render_seed`

Each condition has:

`condition_id`, `size_level` ∈ {TIGHT, REGULAR, LOOSE}, garment measurements, body measurements, relational measurements and deltas vs REGULAR, `source_body_id`, target artifact IDs, and confound metadata.

Within a ladder, every CONTROLLED field must actually be identical. Every changed field must be logged. If resizing moves bust, length, and sleeve together, the intervention is named **measurement vector intervention**, not univariate bust.

---

## Intervention

Ordered:

TIGHT → REGULAR → LOOSE

Mechanism: FIT-documented cross-drape.

| Level | Pattern source | Intended ease |
|-------|----------------|---------------|
| TIGHT | Smaller source body than target | Lower `bust_ease_cm` than REGULAR |
| REGULAR | Source body matched to target | Near made-to-measure |
| LOOSE | Larger source body than target | Higher `bust_ease_cm` than REGULAR |

Record \(\Delta\) garment bust, \(\Delta\) bust ease, \(\Delta\) length, \(\Delta\) sleeve. Do not pretend a single slider if the vector moves.

Author limitation (VERIFIED_FROM_DOCS): tightness is poorly differentiated; TIGHT vs REGULAR may look similar. LOOSE vs REGULAR is the visibility-critical pair.

---

## Control Variables

See `artifacts/control_variable_matrix_v0.2.yaml`.

**Truly hold-fixed at 3D stage (YES):** body identity, body measurements, garment design YAML.

**Hold-fixed if we pin them (PARTIAL):** pose (must override FIT’s random 528-pose sample; A-pose is the conservative executable path), physics fabric, GarmentCode camera, sampler seed.

**Cannot hold-fixed:** garment geometry (that is the intervention), official photoreal `I_g` independent of size, univariate bust in general.

**UNKNOWN:** photoreal lighting, Flux/VLM seeds, unpublished Sim2Real identity preservation.

---

## Measurement-Isolated Track (PRIMARY)

**Track A.** Same canonical / bbox-normalized garment representation + different measurement vectors + different physically simulated targets.

Official FIT does **not** emit this (`I_g` is try-off from sized `I_try-on`). Track A is a **FitGround overlay** on GarmentCode, conditionally feasible at the 3D stage.

Physical consistency: the canonical cloth is a **design-identity token**. After scale normalization it is **not** the true size-specific pattern photograph. That split is intentional. Residual leak: length/sleeve **proportions** can survive bbox normalization.

If GPU E0 shows Track A cloth still ranks size almost perfectly, Track A is NO-GO as a measurement-isolation benchmark.

---

## Naturalistic Track (SECONDARY)

**Track B.** Size-specific garment image + matching measurements + matching target.

Physically consistent; closest to official FIT. Appearance **will** leak size. Track B is a naturalistic performance track. It **cannot alone** prove measurement grounding.

v0.2 therefore distinguishes:

- PRIMARY: Measurement-Isolated Counterfactual Track  
- SECONDARY: Naturalistic Counterfactual Track  

Both are generated in E0 so leakage can be compared. If Track A is impossible, the honest outcome is PARTIAL/NO-GO on isolation, not a forced “same design ⇒ appearance fixed” story.

---

## Controlled Fit Ladder

See schema artifact. One ladder = one experimental unit with three ordered conditions. GPU E0 has 15 ladders (3 bodies × 5 designs).

---

## GPU E0 Pilot

Spec: `artifacts/gpu_e0_pilot_v0.2.yaml`

**Stage 1 (the only GPU task this contract allows):** 3 bodies × 5 designs × 3 levels ≈ **45 conditions**. Pin pose and fabric. Implement documented cross-drape (re-implement box-mesh realignment if needed). Produce Track A + Track B artifacts, metadata, and contact sheets.

**Stage 2 (blocked):** unpublished Sim2Real / try-off.

E0 answers only generation/control questions (stability, invariance, monotonicity, visible fit, appearance leakage, reproducibility). It does not answer whether to train a VLM.

---

## Acceptance Criteria

Frozen **before** seeing GPU results. Details and numeric cutoffs: `artifacts/gpu_e0_pilot_v0.2.yaml`.

| Criterion | GO | PARTIAL | NO-GO |
|-----------|----|---------|-------|
| Generation success | ≥90% of 45 | 70–90% | <70% |
| Control consistency | all ladders hold CONTROLLED IDs | ≤2 ladders fail a non-identity control | body or design identity breaks |
| Measurement monotonicity | bust and ease TIGHT < REGULAR < LOOSE | bust ordered; other dims invert | ease/bust not ordered TIGHT < LOOSE |
| Target uniqueness | 3 distinct targets / ladder | TIGHT≠LOOSE; REGULAR collides | all three identical |
| Fit-change visibility (human) | ≥80% ladders | 50–80%, or TIGHT≈REGULAR but LOOSE visible | <50% or LOOSE not looser |
| Track A leakage | cloth not an absolute-size oracle | proportional silhouette leak | appearance-only recovers size |
| Reproducibility | pattern + mesh hashes match on rerun | visual match, hash noise | ordering changes |
| Metadata | 100% required fields | optional confound fields missing | measurements or control IDs missing |

Overall E0 GO requires the core criteria GO and Track A leakage not NO-GO. PARTIAL or NO-GO **still forbids training**.

---

## Shortcut Tests

Designed now; **not executed** until a later contract authorizes models.

Appearance-only; Measurement-only; Vision+Measurement; Vision+shuffled measurements; Vision+wrong measurements; Vision+counterfactual measurements; Garment-image-only; Target-image-only diagnostic; Quantization-only; Design-ID proxy; Body-ID proxy.

If appearance-only already solves the task, the benchmark **does not prove measurement grounding**. The decisive comparisons are (1) independent contribution of measurements and (2) correct physical change when measurements are perturbed.

---

## Evaluation Policy

**Official eval policy.** The released FIT-100K eval split (5,000) stays the official observational split. It is **not** the Controlled Fit Ladder test set.

**Leakage-controlled policy.** Any future use of released FIT-100K must still respect v0.1 leakage annotations if those artifacts are present. E0 ladders are a new generated set; mixing them with official eval must be explicit.

**E0 evaluation.** Human contact sheets + metadata invariants. **No VLM self-labeling.**

---

## Primary Endpoint

**This contract’s primary endpoint is GPU E0 overall GO/PARTIAL/NO-GO** under the frozen table above.

A future model primary endpoint, **if** a later contract authorizes it, is a **paired ladder-level measurement-contribution test**, not headline VLM accuracy.

---

## Secondary Metrics

Per-dimension deltas; drape-failure rate; Track A bbox scale variation; human checklist item rates (looseness, drape, wrinkle/tension, silhouette, length, sleeve).

---

## Ablations

Design-only, not run now: Track A vs B; A-pose vs pinned casual pose; with vs without box-mesh realignment.

---

## Statistical Plan

Chosen **before** GPU results.

- Unit of analysis: **ladder** (repeated measures), not iid images.
- E0 rates: Wilson 95% CI; 10,000-ladder bootstrap.
- Future model tests (unauthorized): paired Wilcoxon or paired bootstrap; Cohen’s \(d_z\) / rank-biserial; Holm on the pre-registered shortcut family.
- Chance: 1/3 for 3-way size; 1/2 for pairwise order.
- Ranking: Kendall \(\tau\) vs TIGHT < REGULAR < LOOSE.
- Calibration (Brier/ECE) only if a model emits probabilities.

Do not switch the analysis after unblinding.

---

## Failure Criteria

The controlled-generation program fails if:

1. We cannot generate multi-measurement conditions on fixed body+design.
2. CONTROLLED variables do not hold.
3. Targets do not uniquely and monotonically reflect the ladder.
4. Humans cannot see LOOSE vs REGULAR fit change.
5. Track A cloth remains a size oracle (appearance-only solution).
6. Results are not reproducible at the 3D artifact level.

High accuracy on an appearance-leaking task is a **failure to identify measurement grounding**, not a scientific success.

---

## Reproducibility

Pin GarmentCode revision, design YAML hashes, body IDs, sim config hash, seeds, mesh SHA256. Photoreal bit-exactness is **not** required for Stage 1. FIT-Clean v0.1 SHA256 remains the observational freeze and must not be rewritten.

---

## Known Limitations

- Official FIT generator unpublished.
- Track A is not an official FIT output.
- Vector intervention, not univariate bust.
- Tight-fit visual collapse (authors).
- Released FIT-100K pixel fit still NOT VERIFIED.
- Sim2Real unquantified.
- Box-mesh realignment must be re-implemented.

---

## Go/No-Go Logic

| Gate | Verdict |
|------|---------|
| CONTROLLED_COUNTERFACTUAL_GENERATION | **PARTIAL** |
| READY_FOR_GPU_E0 | **YES** (Stage 1 only) |
| Training (VLM/LoRA/RM/DPO/GRPO) | **DENIED** |

PARTIAL because the official photoreal stack is not runnable, Track A is a FitGround overlay, and the intervention is a vector. YES because Stage 1 is specified, sourced, and has frozen acceptance criteria.

---

## GPU Handoff

Read first: `docs/context/PHASE_2_5_CONTEXT.md`

Then: generation audit, this contract, control matrix, ladder schema, GPU E0 YAML.

**Only allowed GPU task:** GPU E0 Stage 1 — Controlled Counterfactual Generation Pilot.

Stop. Do not train.
