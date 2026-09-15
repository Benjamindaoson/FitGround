# COUNTERFACTUAL FEASIBILITY

**Verdict: PARTIAL**  
**Date:** 2026-09-11  
**Manifest:** FIT-Clean v0.1 (`6b998bc4…0177`) — **not modified**

This is the Phase 7 decision record. Every numbered answer is tagged OBSERVED / DERIVED / INTERPRETED / HYPOTHESIZED / VERIFIED.

---

## Verdict

**PARTIAL.**

FIT supports a paper-usable **person-held garment-alternative diagnostic** (TIER C, 1,689 groups, 1,731 pairs) with perfect body-measurement control and real ease/target variation. FIT does **not** support the theoretically strongest unit: same person image + same cloth image + measurement intervention + different target (TIER A = 0).

A claim of “measurement-grounded counterfactuals that isolate ease from garment appearance” is **not identified**. A claim of “person-held pairs in which garment measurements and targets co-vary, with appearance as a known confound” **is** identified.

GPU VLM/LoRA/RM/DPO/GRPO training is **not** authorized by this verdict. A later GPU *diagnostic probe* may be authorized by the frozen PARTIAL contract.

---

## Answers

### 1. Strongest counterfactual unit

**TIER C:** same `person_sha256` + different `garment_sha256` + different `target_sha256` + constant body vector + varying garment measurements.  
TIER B (same person + garment pHash family) exists but n=2.  
TIER A does not exist.

Level: **OBSERVED** (structure), **DERIVED** (ranking).

### 2. How many groups

| Unit | Groups |
|------|--------|
| TIER A (person+cloth) | 0 |
| TIER B exact pHash family | 1 |
| TIER C person-held | **1,689** (1,668×2 + 21×3) |

Level: **OBSERVED**.

### 3. How many candidate pairs

**1,731** unordered pairs (2 TIER B + 1,729 TIER C). No self-pairs, no duplicate unordered keys, no same-target pairs.  
Level: **VERIFIED** (`validate_candidates`).

### 4. What is the measurement intervention

Almost always a **multi-variable garment swap**: bust+length+sleeve change together in 1,574/1,731 pairs. Single-variable pairs: 7. Because body is held, Δ`bust_ease_cm` ≡ Δ`garment_bust_cm` (median 9.1 cm).  
Level: **OBSERVED**.

This is **not** a ceteris-paribus ease slider on one garment. **INTERPRETED.**

### 5. Does the target change

SHA256 of the target image differs in every candidate pair (**VERIFIED**). Whether the *pixels* show a fit change is **NOT VERIFIED**: visual materialization was attempted; unauthenticated Hugging Face downloads stalled at ~0–40 KB/s and were stopped before any PNG was written (see `reports/counterfactual_visual_sanity.md`). 91 pairs are packed for human review when a token/faster link exists.

### 6. Is there enough variation

Yes for a diagnostic: Δ ease from 0 to 46.9 cm; bins negative / near-zero / moderate / large are all populated; 1,731 pairs. No for a large supervised training set and no for official-eval pair protocol (only **1** eval-eval pair).  
Level: **OBSERVED**.

### 7. Does quantization constitute a shortcut

**No as a pair-label oracle; yes as a reporting caveat.**

- 105K `bust_ease_ratio` has 11 unique values at 1dp (**OBSERVED**).
- Pair Δease_ratio is on a 0.05 grid for only 3.8% of pairs; 40 unique values at 2dp (**OBSERVED**).
- Body space has **105** exact unique vectors — discrete avatars, not a continuous population (**OBSERVED**).

Preset garment scaling is **HYPOTHESIZED**, not verified from FIT documentation.

### 8. Duplicate / leakage control

- Exact-image flags already in FIT-Clean v0.1 (**VERIFIED**).
- `leakage_controlled_eval`: 4,684 / 5,000 eval ids after dropping exact-image overlap (**DERIVED**).
- 173 cross-split pairs flagged; not used as official eval items (**OBSERVED**).
- Person-reuse SUSPICIOUS flags are the experimental unit, not contamination (**DERIVED**).
- Semantic identity and dataset-scale near-dup pHash: **NOT VERIFIED** / **DEFERRED_TO_GPU**.

FIT-Clean v0.1 is unchanged.

### 9. Is approximate matching needed

**Not for constructing the available unit.** TIER D was not built. Approximate matching would only be required if the research question demanded same-cloth isolation, which the data cannot provide.  
Level: **DERIVED**.

### 10. Uncontrollable confound

**Garment appearance (cloth image) always changes with the IV in TIER C.** Silhouette (length/sleeve) usually changes with bust. That cannot be controlled in metadata.  
Level: **OBSERVED** (always-different cloth), **INTERPRETED** (identification failure for measurement isolation).

Secondary: only 105 body avatars, so “person image held” is not the same as “body identity in a natural population.” **INTERPRETED.**

### 11. Can FIT support a paper-level measurement-grounding experiment

**PARTIAL.**

| Claim | Support |
|-------|---------|
| FIT has measurement-complete try-on triples | VERIFIED (DE) |
| FIT has same-(person,cloth) measurement ladders | **No** (TIER A=0) |
| FIT has person-held garment swaps with ease/target change | **Yes** (TIER C) |
| Those swaps isolate measurement from appearance | **No** |
| Official 5K can host the pair experiment | **No** (1 eval-eval pair) |
| A paper can report a *diagnostic* of whether a model’s fit judgment tracks ease under person-held garment change, with appearance as confound | **Yes, if framed honestly** |

---

## What this stage must not claim

- That FIT implements a controlled ease intervention on a fixed garment image.
- That TIER C pairs are unconfounded causal units.
- That official FIT eval is a counterfactual-pair benchmark.
- That semantic person identity is isolated.

## GPU gate

**Not ready for VLM training.** Ready to freeze a PARTIAL experimental contract. First GPU item is a frozen-encoder ranking probe (see contract), not LoRA/DPO/GRPO.

## Artifacts

- `artifacts/counterfactual_structure_v0.1.json`
- `data/processed/counterfactual_candidates_v0.1.parquet`
- `artifacts/experimental_split_policy_v0.1.yaml`
- `reports/counterfactual_shortcut_audit.md`
- `docs/EXPERIMENTAL_CONTRACT_v0.1.md`
- `artifacts/experimental_contract_v0.1.yaml`
