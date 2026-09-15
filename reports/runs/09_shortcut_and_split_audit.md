# Run 009 — Shortcut and Split Audit

**Run ID:** `run_009`  
**Stage:** Phase 4–5  
**Recorded:** 2026-09-11

## Question

Can these 1,731 pairs be distinguished by a shortcut that is *not* measurement-grounded fit? How should train / official eval / leakage-controlled eval be defined without editing FIT-Clean v0.1?

## Input

- `data/processed/counterfactual_candidates_v0.1.parquet`
- FIT-Clean leakage flags (exact SHA256 only)

## Execution

`fitground.counterfactual.validation.shortcut_audit` plus split-policy builder. Attack surface: person/cloth identity, ease quantization, shard, split, duplicate flags, quality, missingness, target duplicates, filename/`sample_id` structure.

## Results — shortcuts

| Attack | Finding | Level | Verdict |
|--------|---------|-------|---------|
| Person identity within pair | Held (frac=1.0) | OBSERVED | Not a within-pair shortcut |
| Cloth identity within pair | Never held (frac=0.0) | OBSERVED | **Primary confound** |
| Garment category proxy | No category label; 1,574/1,731 change bust+length+sleeve together | OBSERVED | Appearance + silhouette change with IV |
| `bust_ease_ratio` 1dp unique (anchor/CF/delta) | 6 / 8 / 5 | OBSERVED | Coarse rounding |
| Δ ease_ratio on 0.05 grid | **3.8%** | OBSERVED | Not a usable pair-label classifier |
| Δ ease_ratio unique at 2dp | 40 | OBSERVED | Not 2–3 presets |
| Source shard recoverable from ease 1dp | purity 0.16 | OBSERVED | No |
| `pair_split` recoverable from ease 1dp | purity 0.91 | OBSERVED | Mild association, not a key |
| Quality flag | All SUSPICIOUS (person-dup rule) | OBSERVED | Constant; cannot separate pairs |
| Row order / filename | `sample_id` contains split+shard; must not be a model input | DERIVED | Pipeline control |
| Missingness | Core measurements complete on usable rows | VERIFIED (DE) | No |
| Target duplicate within pair | Forbidden by construction | VERIFIED | No |
| Extreme-value threshold | Ease bins populated: neg 401, near0 226, mod 941, large 163 | OBSERVED | Variation exists |
| Exact-image train/eval overlap on pair members | 10.2% leakage-any; 9.99% cross-split | OBSERVED | Flag and isolate |

**Quantization shortcut conclusion:** collapsing ease_ratio to 1 decimal **looks** preset-like (11 values in the full 105K). On *pairs*, only 3.8% of deltas sit on a 0.05 grid, and 2dp still has 40 unique deltas. A model that sees only a handful of preset ease codes **cannot** generally guess the pair. The experiment is **not** disqualified on quantization alone.

The experiment **is** disqualified as a *clean measurement isolation* because cloth image always changes with the IV.

Audit machine verdict: `PARTIAL_CONFOUND`.

## Results — split policy

Defined in `artifacts/experimental_split_policy_v0.1.yaml`. FIT-Clean v0.1 is not modified.

| Split | Rule | N |
|-------|------|---|
| `official_eval` | FIT `source_split=eval`, sorted `sample_id` | 5,000 |
| `leakage_controlled_eval` | official eval minus any exact-image train/eval overlap flag | **4,684** (316 excluded) |
| Train | `source_split=train` | 100,000 |
| CF eval-eval pairs | both members eval | **1** |
| CF train-train pairs | diagnostic only | 1,557 |
| CF cross-split pairs | flagged; not official eval items | 173 |

Determinism: no RNG in split assignment; pair_id and anchor rule are pure functions. Seed `0` is reserved for visual-pilot sampling only.

**Semantic identity leakage:** NOT VERIFIED. Near-duplicate pHash at dataset scale: DEFERRED_TO_GPU.

## Interpretation

Official 5K eval remains the public protocol for any future *sample-level* model score. It is **not** a counterfactual-pair eval set. Pair-level measurement tests live almost entirely in train-train TIER C, which must be reported as a diagnostic, not as FIT official eval performance.

## Decision

Freeze the split policy. Do not rewrite FIT-Clean. Do not claim pair-eval numbers on the official 5K.

## Artifacts

- `reports/counterfactual_shortcut_audit.md`
- `artifacts/counterfactual_shortcut_audit_v0.1.json`
- `artifacts/experimental_split_policy_v0.1.yaml`

## Verification

`leakage_controlled_eval_ids` is a sort of a boolean filter — rerunning it on the frozen manifest must yield 4,684 ids.

## What We Learned

The dangerous shortcut is garment appearance, not ease quantization. Eval-pair starvation (n=1) is a split-design fact, not a bug in pair_id.

## Next

Visual sanity check on a shard-packed subset; feasibility verdict; contract freeze at PARTIAL.
