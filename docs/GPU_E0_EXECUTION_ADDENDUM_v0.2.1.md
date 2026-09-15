# GPU E0 Execution Addendum v0.2.1

**Status:** FROZEN  
**Frozen:** 2026-09-11  
**Type:** Execution addendum only. Not a new experimental contract.

**Does not modify:**

- FIT-Clean v0.1
- Experimental Contract v0.1
- Experimental Contract v0.2
- `artifacts/gpu_e0_pilot_v0.2.yaml`
- `artifacts/experimental_contract_v0.2.yaml`
- `artifacts/control_variable_matrix_v0.2.yaml`
- `artifacts/controlled_fit_ladder_schema_v0.2.yaml`

Machine-readable twin: `artifacts/gpu_e0_execution_v0.2.1.yaml`

This file freezes GPU E0 Stage 1 execution rules that v0.2 left underspecified. It does **not** authorize training, Sim2Real Stage 2, or any change to frozen GO cutoffs after seeing renders.

---

## Purpose

v0.2 already authorizes **GPU E0 Stage 1 only**. Before that pilot runs, four execution holes must be closed **without looking at GPU images**:

1. Causal wording of the generation mechanism
2. Track A size-leakage audit
3. Human visibility protocol
4. Contract errata for two easy-to-misread v0.2 sentences

After this freeze, the only allowed next task is:

**GPU E0 Stage 1 — Controlled Counterfactual Generation Pilot**  
3 bodies × 5 designs × 3 levels ≈ 45 conditions / 15 ladders

---

## Scope lock

| Allowed now | Forbidden now |
|-------------|----------------|
| Implement documented GarmentCode cross-drape | VLM training |
| Generate 15 ladders / 45 conditions | LoRA / RM / DPO / GRPO |
| Track A canonical cloth + Track B size-specific cloth | Full FIT-100K regeneration |
| Frozen leakage audit + blinded human contact sheets | Sim2Real Stage 2 |
| Record realized measurement vectors | Rewriting v0.1 / v0.2 / FIT-Clean |
| | Choosing leakage metrics after unblinding |
| | Treating S/M/L as the intervention |
| | Claiming `do(garment_bust=...)` unless code sets that cm directly |

---

## 1. Causal wording

### 1.1 What E0 actually does

GPU E0 Stage 1 does **not**, in general, apply a primitive `do(garment_bust = x)` operator.

The executable physical intervention is a **garment-sizing / source-body sizing condition**:

| Ladder label | Physical intervention \(Z\) |
|--------------|-----------------------------|
| TIGHT | Draft the frozen design on a **smaller source body** than the target |
| REGULAR | Draft on a **source body matched** to the target |
| LOOSE | Draft on a **larger source body** than the target |

Then drape that pattern on the **fixed target body** (FIT-documented cross-drape, with box-mesh realignment re-implemented if needed).

TIGHT / REGULAR / LOOSE name **sizing conditions**, not independently set bust-centimeter values.

### 1.2 Causal graph (required language)

```
Z  physical intervention
   garment-sizing / source-body sizing condition
        ↓
G  pattern geometry
   size-specific 2D sewing pattern / panel dimensions
        ↓
M  mediator / realized treatment
   garment measurement vector extracted from the pattern
   (garment_bust_cm, garment_length_cm, garment_sleeve_cm)
   and induced ease vs the fixed target body
        ↓
Y  outcome
   draped target geometry / human-visible fit
```

Held fixed within a ladder: target body identity, body measurements, design YAML, pose, fabric, camera, render seed.

**Independent variable in the generator:** \(Z\) (sizing condition).  
**Realized treatment / mediator:** \(M\) (and pattern geometry \(G\)).  
**Outcome for E0:** \(Y\) (draped target geometry and visible fit).

### 1.3 Why measurements still matter

The **scientific object remains measurement grounding**.

That means: a later model test (not authorized here) must track body–garment measurement relations, not cloth appearance alone.

It does **not** mean the generator’s primitive operator is `do(M)` or `do(garment_bust=...)`.

Permitted summary:

> Intervene on source-body sizing \(Z\) so that the **realized** measurement vector \(M\) is ordered TIGHT < REGULAR < LOOSE on `garment_bust_cm` and `bust_ease_cm`, and test whether target geometry / visible fit \(Y\) follows that order.

Forbidden summary:

> Apply `do(garment_bust=...)`.
> Directly set bust/length/sleeve sliders.
> Official photoreal \(I_g\) is independent of size.

If — and only if — Stage 1 code later **directly** sets a named pattern measurement (e.g. an explicit bust parameter) while holding other pattern dimensions fixed, that one axis may then be described as a direct `do()`. That is an empirical finding, not the default claim. v0.2 already forbids a univariate-bust claim unless E0 shows other dimensions fixed.

### 1.4 Mapping from v0.2 shorthand

| v0.2 phrase | v0.2.1 execution reading |
|-------------|--------------------------|
| “measurement-vector intervention” | Intervene on \(Z\); record realized \(M\); do not pretend \(M\) was set atomically |
| “independent variable = measurement vector \(M\)” | **Targeted / recorded treatment.** Primitive intervention is \(Z\). Identification target is still \(M\) |
| “`do(measurement change)`” | Shorthand for controlled sizing + realized \(M\), **not** a bust-cm Pearl intervention unless code sets that cm |
| Track A “measurement-isolated” | Isolation is a **claim to be tested** by §2, not a property assumed from bbox-normalization |

### 1.5 Cloth images are not the intervention

- Track A canonical / bbox-normalized cloth is a **design-identity token** plus a leakage probe.
- Track B size-specific cloth is a **naturalistic covariate** of \(G\).
- Neither cloth image is \(Z\). Official photoreal \(I_g\) is downstream of sized try-on try-off (§4.1).

---

## 2. Track A size-leakage test

Frozen **before** any GPU E0 image is inspected for leakage, fit, or “which metric works.”

If Track A cloth appearance alone can stably recover TIGHT / REGULAR / LOOSE, Track A **must not** be called measurement-isolated.

### 2.1 What is tested

**Input (appearance-only):** the three Track A canonical / bbox-normalized cloth images in a ladder.

**Forbidden at test time:** size labels, measurement tables, Track B cloths, target / person renders, generation logs.

**Unit:** ladder (\(n = 15\)).

### 2.2 Frozen foreground extraction

Apply identically to every Track A cloth. Do not retune after unblinding.

1. Convert to grayscale.
2. If an alpha channel exists, foreground = alpha > 0. Else Otsu threshold, taking the polarity whose mean row-index is closer to the image center.
3. Keep the largest connected component. Drop components < 0.5% of canvas pixels.
4. Silhouette mask = that component.

If a mask cannot be extracted, the condition is `LEAKAGE_UNSCORABLE` and the ladder is excluded from leakage denominators (and cannot support a Track A isolation claim).

### 2.3 Frozen descriptor family

Compute **all** of the following on the silhouette. Do not drop, add, or replace descriptors after seeing which ones leak.

| ID | Descriptor | Definition |
|----|------------|------------|
| D1 | `bbox_width_px` | Width of silhouette axis-aligned bbox |
| D2 | `bbox_height_px` | Height of silhouette axis-aligned bbox |
| D3 | `bbox_aspect_ratio` | D1 / D2 |
| D4 | `bbox_width_rel` | D1 / canvas width |
| D5 | `bbox_height_rel` | D2 / canvas height |
| D6 | `fg_area_ratio` | foreground pixels / canvas pixels |
| D7 | `fg_fill_of_bbox` | foreground pixels / (D1 × D2) |
| D8 | `perimeter_px` | perimeter of the largest-component contour |
| D9 | `compactness` | \(4\pi \cdot \text{area} / \text{perimeter}^2\) |
| D10 | `perimeter_over_sqrt_area` | perimeter / sqrt(area) |
| D11 | `centroid_y_rel` | centroid y inside bbox / bbox height (0 = top) |
| D12 | `upper_half_area_ratio` | foreground pixels in upper 50% of bbox / foreground pixels |
| D13 | `width_at_q25_rel` | silhouette width at 25% of bbox height / bbox width |
| D14 | `width_at_q50_rel` | same at 50% |
| D15 | `width_at_q75_rel` | same at 75% |
| D16 | `y_of_max_width_rel` | y of maximum silhouette width / bbox height |

**Absolute-scale block (v0.2 inherited):** D1 and D2 must vary ≤ 5% across the three conditions in a ladder (max/min ≤ 1.05). This is the bbox-normalization check, not the isolation claim.

**Proportional / length-sleeve block:** D3, D6, D7, D11–D16. These are the pre-registered length / sleeve / fill cues that can survive bbox normalization.

**Silhouette / perimeter block:** D8–D10, D7.

Sleeveless or otherwise degenerate designs: if a descriptor is undefined, store `NA` and impute the **training-fold median** inside the classifier only. Do not delete the descriptor from the frozen family.

### 2.4 Automated condition-ordering recoverability

Encode size as TIGHT=0, REGULAR=1, LOOSE=2.

**Primary automated test (locked):**

- Feature vector = `{D3, D4, D5, D6, D7, D9, D10, D11, D12, D13, D14, D15, D16}` (scale-free / proportional; D1/D2 used only for the 5% rule).
- Classifier: multinomial logistic regression, L2, `C = 1.0`, `lbfgs`, max_iter=200.
- Standardize features using **training ladders only**.
- Cross-validation: leave-one-**ladder**-out (never leave-one-image-out).
- Metric: 3-way accuracy. Chance = \(1/3\).

**Secondary automated tests (all reported; Holm over the descriptor family):**

- For each descriptor, within each ladder, rank the 3 cloths and compute Kendall \(\tau\) vs the true order (two-sided: \(\tau\) or \(-\tau\) is **not** chosen post-hoc as a global direction per descriptor; direction is estimated only inside each LOO train set and applied to the held-out ladder).
- Exact-order match: \(\tau = 1\) after applying the train-set direction.
- Null for exact-order count: \(\mathrm{Binomial}(n_{\text{complete ladders}}, 1/6)\).
- Pairwise TIGHT vs LOOSE using the same train-set direction. Chance = \(1/2\).

Do not replace this family with a CNN, PCA, or “best leaking feature” after unblinding. Those would be a new addendum.

### 2.5 Human cloth-only recoverability

Separate from the fit-visibility protocol in §3.

- Show only the three Track A cloths, independently permuted per rater.
- Hide labels and measurements.
- Task: order the three images from **smallest-looking garment** to **largest-looking garment**.
- Forced pairwise: “Which cloth looks larger?” for each pair, with `Indistinguishable`.

Chance: exact order \(1/6\); TIGHT vs LOOSE pairwise \(1/2\).

### 2.6 GO / PARTIAL / NO-GO

These operationalize v0.2 `visual_leakage_severity.track_a`. They do not rewrite that file.

Let \(n\) = number of complete, scorable ladders (target 15).

| Verdict | Rule |
|---------|------|
| **NO-GO** | Any of: (H1) human majority recovers the **exact** TIGHT < REGULAR < LOOSE cloth order on ≥ 80% of ladders; (H2) human majority recovers TIGHT vs LOOSE cloth pairwise on ≥ 90% of ladders **and** exact-order rate ≥ 50%; (A1) LOO 3-way accuracy ≥ 0.80; (A2) any frozen descriptor, after Holm, has exact-order rate ≥ 80%. |
| **PARTIAL** | Not NO-GO, but leakage exists: LOO accuracy Wilson 95% CI excludes \(1/3\); or any Holm-significant descriptor exact-order test; or human TIGHT vs LOOSE pairwise Wilson CI excludes \(1/2\); or the 5% bbox-scale rule fails on more than 0 but fewer than all ladders while recoverability is below NO-GO. This includes “scale-normalized but length/sleeve proportions still leak.” |
| **GO** | 5% bbox-scale rule holds on all complete ladders; human exact-order Wilson CI includes \(1/6\) **and** TIGHT–LOOSE pairwise CI includes \(1/2\); LOO 3-way Wilson CI includes \(1/3\); no Holm-significant descriptor exact-order test. |

Track B leakage is **expected**. Track B success cannot rescue Track A.

### 2.7 Naming rule

Track A may be called **measurement-isolated** only if this audit is **GO**.

If the audit is PARTIAL, say **partially scale-normalized, residual proportional leakage**.

If the audit is NO-GO, say **appearance-leaking / not measurement-isolated**. Do not keep the PRIMARY track name as a scientific claim.

v0.2 overall E0 GO already requires Track A leakage not NO-GO. This addendum supplies the missing pre-registered test.

---

## 3. Human visibility protocol

Frozen **before** raters see E0 images. This protocol scores v0.2 `target_fit_change_visibility`. It is not VLM self-labeling.

### 3.1 Unit

The experimental unit is the **ladder**, not 45 iid images.

Raters see the three target images of one ladder as a set. They do not score a mixed deck of conditions from different ladders as if independent.

### 3.2 Two artifacts (do not confuse them)

| Artifact | Contents | Use |
|----------|----------|-----|
| **DIAGNOSTIC_SHEET** | v0.2 labeled contact sheet, including TIGHT/REGULAR/LOOSE panel names and the measurement table | Engineering QA only. **Not** used for visibility GO |
| **BLIND_FIT_SHEET** | Three target images, random order, anonymous codes, **no** size labels, **no** measurements, **no** Track A/B size cues | **Only** source for visibility GO |
| **BLIND_CLOTH_A_SHEET** | Three Track A cloths, random order, no labels | Leakage test §2.5 only |

v0.2 listed a labeled contact sheet with measurements. That sheet remains the diagnostic artifact. Scoring visibility from it would unblind the core question. This addendum therefore **executes** the v0.2 human criterion on `BLIND_FIT_SHEET`.

### 3.3 Blinding and randomization

- Condition order randomized **independently per ladder and per rater**.
- Permutation keys sealed until that rater submits the ladder.
- Hide `TIGHT` / `REGULAR` / `LOOSE`.
- Hide all garment and body measurements, ease, and deltas.
- Raters do not see each other’s scores, generation logs, or leakage metrics.
- One optional practice ladder is allowed and **excluded** from the 15 official ladders.

### 3.4 Frozen rubric

Relative to the three unlabeled targets on the sheet. Do not switch items after seeing images.

**Core questions (required):**

1. **Which is more loose?** Forced pairwise for every pair \(\{A,B,C\}\):  
   `Left more loose` / `Right more loose` / `Indistinguishable`.
2. **Is the more-loose member of each pair obviously looser, or only subtle?**  
   `Clear` / `Subtle` / `No difference`.

After unblinding, the pair that maps to actual LOOSE vs REGULAR is the **visibility-critical pair**. The pair that maps to TIGHT vs LOOSE is the **distinguishability pair**.

**Checklist (within-ladder ranks; ties allowed as `TIE`):**

| Item | Rank meaning |
|------|----------------|
| chest/waist looseness | 1 = tightest, 3 = loosest |
| drape | 1 = closest hang, 3 = most pooling / hanging away |
| wrinkle/tension | 1 = dominant tension/drag, 3 = dominant excess fold |
| silhouette | 1 = closest to body, 3 = stands farthest away / boxy |
| length | 1 = shortest appearance, 3 = longest appearance |
| sleeve | 1 = tightest/shortest appearance, 3 = loosest/longest appearance |

Anchors (frozen):

- **More loose:** more unfilled volume at chest/waist, more break/pooling, fewer stretch/tension lines, silhouette stands farther from the body.
- **More tight:** closer to skin, more tension/drag, less spare fold at chest/waist.
- Author-known limitation: TIGHT vs REGULAR may look similar. That does **not** relax LOOSE vs REGULAR.

Do not score “which has the larger bust measurement.” Score visible fit only.

### 3.5 Raters

Prefer **3 independent raters**.

| \(N\) | Grade | Consequence |
|-------|-------|-------------|
| 3 | `PUBLICATION_ELIGIBLE` if agreement rules pass | May support publication-grade human validation |
| 1 | `PILOT_ONLY` | Record as pilot signal only. **Must not** be cited as publication-grade human validation |
| 2 | `PILOT_ONLY` | Insufficient; treat as pilot |

`PILOT_ONLY` may still inform engineering PARTIAL/NO-GO discussion. It does **not** convert v0.2 visibility GO into a publication-grade result.

### 3.6 Disagreement and aggregation

Map every rater’s `{A,B,C}` answers back to `{TIGHT, REGULAR, LOOSE}` using that rater’s sealed permutation.

**Pairwise item (N=3):**

- Majority (≥2) wins.
- 1–1–1 or majority `Indistinguishable` → `Indistinguishable` (not distinguishable).
- Opposite majority (e.g. two raters say REGULAR looser than LOOSE) → `REVERSED`.

**Ranks (N=3):** median rank. If all three ranks differ, `UNRESOLVED` on that checklist item.

**N=1:** take the single score; tag every human result `PILOT_ONLY`.

**N=2:** require exact agreement; else `UNRESOLVED`. Still `PILOT_ONLY`.

**Ladder-level visibility vote (used for v0.2 rates):**

A ladder **passes** only if all of the following hold after aggregation:

1. Critical pair: LOOSE vs REGULAR = LOOSE more loose (not `Indistinguishable`, not `REVERSED`).
2. Distinguishability pair: TIGHT vs LOOSE is not `Indistinguishable` and not `REVERSED` (LOOSE more loose than TIGHT).
3. Chest/waist looseness does not contradict (1): median rank(LOOSE) ≥ median rank(REGULAR). `UNRESOLVED` on this item counts as a fail.

Obviousness (`Clear` / `Subtle` / `No difference`) is recorded on every pair. `Clear` or `Subtle` both count as visible for the v0.2 pass/fail rate. Report a secondary **obvious-only** rate that counts only `Clear` on LOOSE vs REGULAR. Do not choose which of these rates is “the” rate after seeing scores: the primary rate is `Clear` or `Subtle`; the obvious-only rate is secondary and pre-registered.

**Agreement reporting (required, not optional):**

- Pairwise percent agreement on LOOSE vs REGULAR and TIGHT vs LOOSE.
- Fleiss’ \(\kappa\) (N=3) or Cohen’s \(\kappa\) (N=2) on the LOOSE-vs-REGULAR pairwise item.
- If N=3 and Fleiss’ \(\kappa < 0.20\) on the visibility-critical pair, publication-grade human validation is **denied** even if the pass rate is high. Record visibility as `LOW_AGREEMENT` and cap the human criterion at PARTIAL for publication purposes.

**Missing / unresolved ladders:** count against the GO numerator (fail), remain in the denominator of complete generated ladders. Do not drop hard ladders post-hoc.

### 3.7 Mapping onto v0.2 visibility cutoffs

Unchanged numeric cutoffs, now with a defined numerator:

- **GO:** ≥ 80% of complete ladders pass §3.6.
- **PARTIAL:** ≥ 50% and < 80%, **or** LOOSE>REGULAR holds but TIGHT≈REGULAR on a majority of ladders (author tightness limitation), still with LOOSE vs REGULAR visible.
- **NO-GO:** < 50%, or LOOSE is not looser than REGULAR on the aggregated critical pair for a majority of ladders.

If `PILOT_ONLY`, publish those percentages only as `PILOT_SIGNAL`. Do not call them publication-grade human validation.

---

## 4. Contract errata

Recorded here. **Do not rewrite** frozen v0.2 files.

### 4.1 Official photoreal \(I_g\) is not size-independent

v0.2 already states that official layflat \(I_g\) is VLM try-off from the **sized** try-on, and that official photoreal \(I_g\) **cannot** be held fixed independent of size.

**Erratum / reading rule:** any later sentence that treats official \(I_g\) as a size-invariant garment photo is a misreading. Official \(I_g\) is derived from sized try-on try-off. Do not assume \(I_g \perp\) size.

Track A exists because official \(I_g\) is **not** size-isolated. Track A is a FitGround overlay, not an official FIT output.

### 4.2 “10,000-ladder bootstrap” is not 10,000 ladders

v0.2 markdown Statistical Plan says: “E0 rates: Wilson 95% CI; 10,000-ladder bootstrap.”

v0.2 YAML already says: `bootstrap: 10_000 resamples of ladders for CIs on rates`.

**Erratum / reading rule:** this means

> **10,000 bootstrap resamples at the ladder level**

It does **not** mean E0 has 10,000 ladders.

GPU E0 Stage 1 has **15 ladders**. The bootstrap resamples those 15 ladder-level outcomes 10,000 times. Unit of analysis remains the ladder.

### 4.3 What stays frozen

Acceptance cutoffs, scale 3×5×3, Track A/B split, training denial, and Stage 2 block remain as in v0.2. This addendum only disambiguates mechanism language, leakage measurement, human scoring, and the two errata above.

---

## GPU E0 execution readiness

| Gate | Verdict |
|------|---------|
| FIT-Clean v0.1 | FROZEN — not modified |
| Experimental Contract v0.1 | FROZEN — not modified |
| Experimental Contract v0.2 | FROZEN — not modified |
| Causal wording | FROZEN in this addendum |
| Track A leakage audit | FROZEN in this addendum |
| Human visibility protocol | FROZEN in this addendum |
| Contract errata | RECORDED in this addendum |
| Training / Stage 2 | DENIED |

**GPU_E0_EXECUTION_READY = YES**

Meaning: permission to run **GPU E0 Stage 1 only**. Not permission to train. Not permission to start Sim2Real Stage 2. Not a claim that Stage 1 has already succeeded.

### Next allowed task (only)

GPU E0 Stage 1 — Controlled Counterfactual Generation Pilot  

3 bodies × 5 designs × 3 levels  
≈ 45 conditions / 15 ladders

Stop after this addendum. Do not train a VLM. Do not run LoRA / RM / DPO / GRPO. Do not start Sim2Real Stage 2.
