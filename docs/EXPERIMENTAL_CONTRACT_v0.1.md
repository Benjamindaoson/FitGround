# Experimental Contract v0.1

**Status:** FROZEN AT PARTIAL  
**Date:** 2026-09-11  
**Depends on:** FIT-Clean v0.1 (unmodified)  
**Machine-readable twin:** `artifacts/experimental_contract_v0.1.yaml`

This contract authorizes a **person-held garment-alternative diagnostic**. It does **not** authorize VLM fine-tuning, LoRA, reward models, DPO, or GRPO.

---

## Research Question

When the person image and body measurements are held fixed, do multimodal fit judgments track **garment/ease measurement change**, or do they track **garment appearance** and other dataset shortcuts?

## Hypothesis

**H1 (diagnostic):** Under person-held TIER C pairs, a measurement-grounded system assigns higher “looser fit / larger ease” to the counterfactual target than to the anchor target at a rate above chance and above an appearance-only baseline.

**H0:** Pair-direction accuracy is explained by garment appearance, ease-bin shortcuts, or split/identity leakage, not by measurements.

TIER A isolation (same cloth image) is **out of scope** — the unit does not exist in FIT-Clean v0.1.

## Experimental Unit

Unordered pair of FIT-Clean rows sharing `person_sha256`, differing in cloth image, garment measurements, and target image. Body vector constant.

- **Anchor:** lower `bust_ease_cm` (ties: lower `garment_bust_cm`, then `sample_id`).
- **Counterfactual:** the other member.

## Independent Variable

Signed garment/ease change, primarily Δ`garment_bust_cm` ≡ Δ`bust_ease_cm` (body held). Secondary recorded IVs: Δ length, Δ sleeve, Δ`bust_ease_ratio`.

This IV is **bundled** with cloth-image change. It is not a ceteris-paribus ease slider.

## Controlled Variables

| Variable | Status |
|----------|--------|
| Person image SHA256 | Held |
| Body (height, bust, waist, hips) | Held |
| Cloth image SHA256 | **Not held** (confound) |
| Garment visual family (pHash) | Held only in TIER B (n=2) |
| Target image | Must differ |
| Official FIT 5K membership | Unchanged as a *sample* split |

## Outcome / Target

The try-on target image, and any score a model assigns to fit / tightness / which of two targets is looser.

## Pair Construction

`scripts/build_counterfactual_candidates.py`  
Table: `data/processed/counterfactual_candidates_v0.1.parquet`  
`pair_id = cf_ + sha256(min(id), max(id))[:24]`  
Strongest eligible tier only. No self-pairs. No unordered duplicates.

## Splits

See `artifacts/experimental_split_policy_v0.1.yaml`.

| Name | Definition |
|------|------------|
| Train | `source_split=train` |
| Official eval | FIT 5K, unmodified |
| Leakage-controlled eval | Official eval minus exact-image overlap flags (4,684 ids) |
| Pair diagnostic | 1,557 train-train pairs; 173 cross-split flagged; 1 eval-eval |

Deterministic: sorted `sample_id`; no RNG in split assignment. Visual-pilot RNG seed = 0.

Semantic identity leakage: **not verified**; do not claim isolation. Near-image duplication: **DEFERRED_TO_GPU**.

## Shortcut Controls

Must not feed `sample_id`, shard id, or split as model inputs. Report appearance confound. Do not treat 1dp ease_ratio as the IV. Exclude leakage-flagged members from leakage-controlled metrics.

## Metrics

Pair-level (diagnostic):

- Direction accuracy: P(score_CF > score_anchor) given construction (CF is looser in ease).
- Correlation of (score_CF − score_anchor) with Δ`bust_ease_cm`.
- Stratified accuracy by ease bin and by intervention type.
- Appearance baseline: same protocol using cloth-image embeddings only (GPU).
- Chance = 0.5 for direction.

Sample-level official eval remains whatever future model card defines; it is **not** the primary CF endpoint.

## Primary Endpoint

**Person-held pair direction accuracy** on train-train TIER C pairs that are not cross-split and not leakage-flagged, versus chance and versus appearance-only baseline.

## Ablations

1. TIER B only (n=2) — qualitative, not statistical.
2. Single-variable pairs (n=7) — qualitative.
3. Drop large-ease tails.
4. Appearance-only baseline (GPU).
5. Leakage-flagged vs clean subset.

## Failure Criteria

The diagnostic **fails to support H1** if:

- Direction accuracy is not above chance after multiple-comparison control, or
- Appearance-only baseline matches or beats the measurement-aware score, or
- Accuracy concentrates in 1–2 ease_ratio 1dp bins, or
- Results use official 5K as if it were a pair eval.

The **research programme** fails (NO-GO upgrade) if visual sanity shows targets do not change with ease (same drape, different filename).

## Statistical Tests

Binomial test vs 0.5 for direction accuracy; Spearman correlation of Δscore vs Δease; report 95% CIs. No peeking at GPU training curves — there is no training.

## Random Seeds

- Split assignment: none.
- Pair ids: none (hash).
- Visual pilot sample: seed 0.
- Future GPU probe: seed 0, then 1 and 2 as sensitivity.

## Reporting Rules

- Separate OBSERVED / DERIVED / INTERPRETED / HYPOTHESIZED / VERIFIED.
- Always state the appearance confound.
- Never cite TIER C n as “controlled measurement counterfactuals” without the confound sentence.
- Do not modify FIT-Clean v0.1.

## What supports H1

Direction accuracy significantly above chance **and** above appearance-only baseline, with effect increasing in |Δease|, on leakage-clean train-train pairs, after visual sanity confirms fit change in targets.

## What rejects H1

Appearance baseline explains the effect; or visual targets do not show fit change; or the effect is a 1dp ease-bin artifact.

## GPU authorization

| Activity | Authorized? |
|----------|-------------|
| Frozen-encoder pair ranking / CLIP-style probe | Yes, as first GPU experiment, after visual sanity |
| LoRA / full VLM train | **No** |
| Reward model / DPO / GRPO | **No** |
| Full FIT download | **No** |
