# Run 008 — Counterfactual Candidate Construction

**Run ID:** `run_008`  
**Stage:** Phase 3  
**Recorded:** 2026-09-11  
**CLI:** `python scripts/build_counterfactual_candidates.py`

## Question

Can we emit a deterministic, de-duplicated pair table in which every row explains why it is a legal measurement-counterfactual *candidate*?

## Input

- FIT-Clean v0.1 manifest (unmodified)
- Structure discovery from run 007
- Pair identity: `pair_id = cf_ + sha256(sorted(sample_a, sample_b))[:24]`
- Anchor rule: lower `bust_ease_cm`, then lower `garment_bust_cm`, then `sample_id`

## Execution

`fitground.counterfactual.matching.build_candidates`:

1. TIER A on multi-row (person, cloth) keys — none.
2. TIER B then C on the 1,689 multi-row person keys only (no 105K singleton loop).
3. Strongest-tier wins; unordered keys de-duplicated.
4. TIER D auto-gated: only if A+B+C < 100 pairs. C is large, so D is not built (`TIER_D_MAX_PAIRS=0`).

## Results

| Quantity | Value | Level |
|----------|-------|-------|
| Candidate pairs | **1,731** | OBSERVED |
| TIER B | 2 | OBSERVED |
| TIER C | 1,729 | OBSERVED |
| Unique `pair_id` | 1,731 | VERIFIED |
| Self-pairs | 0 | VERIFIED |
| Same-target pairs | 0 | VERIFIED |
| Schema validation | PASS | VERIFIED |
| `train_train` / `cross_split` / `eval_eval` | 1,557 / 173 / **1** | OBSERVED |
| `same_person_image` | 1.0 | OBSERVED |
| `same_cloth_image` | 0.0 | OBSERVED |
| `body_measurements_constant` | 1.0 | OBSERVED |
| Single-variable garment change | **7** | OBSERVED |
| `garment_bust_and_length_and_sleeve` | 1,574 | OBSERVED |
| Mean / median Δ`garment_bust_cm` (= Δ ease, body held) | 10.79 / 9.10 cm (max 46.9) | OBSERVED |
| Leakage-any pairs | 177 | OBSERVED |
| Person-duplicate flag as contamination | redefined: **not** contamination for TIER B/C | DERIVED |

Every pair stores anchor/CF measurements, deltas, quality, leakage, `control_score`, `confound_flags`, and `pair_construction_reason`.

TIER B examples:

- hamming 0, Δ bust 5.98 cm — only exact garment-pHash family pair
- hamming 4, Δ bust 0.80 cm — near family

## Interpretation

The candidate table is a **person-held garment-swap set**, not a same-cloth ease ladder. Official-eval pair coverage is one pair. Most experimental work on these pairs is a train-set diagnostic.

`quality_status=SUSPICIOUS` on all members is **by construction** of the DE duplicate-person rule. Usable flag remains true.

## Decision

Accept 1,731 pairs as the v0.1 candidate set. Do not enlarge with TIER D. Do not modify FIT-Clean v0.1.

## Artifacts

- `data/processed/counterfactual_candidates_v0.1.parquet` (gitignored large-ish table; regenerated from frozen manifest)
- `artifacts/counterfactual_candidate_summary_v0.1.json`
- `artifacts/counterfactual_validation_v0.1.json`
- `src/fitground/counterfactual/{matching,controls,schema}.py`

## Verification

`validate_candidates` must remain ok. `pytest tests/test_counterfactual.py` covers pair_id, deltas, no self-pairs, no unordered duplicates, leakage, control score, schema, materializer lookup, shard-capped pilot.

## What We Learned

Person reuse almost never lands two rows in the same parquet shard (4 / 1,731 same-shard pairs). Visual materialization therefore requires many shards even for a small pilot.

## Next

Shortcut audit and split policy.
