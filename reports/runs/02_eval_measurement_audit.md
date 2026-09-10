# Run 002 — Eval Measurement & Integrity Audit

**Run ID:** `run_002`  
**Stage:** Eval Measurement Audit + FIT-Eval-Clean  
**Recorded:** 2026-09-10 (retroactive; audit completed 2026-09-10T16:17 UTC)  
**Status:** DONE

---

## 1. What This Stage Does

**Research question:** Does official FIT eval (5K) have complete measurements, decodable images, meaningful body–garment fit variation, and acceptable duplicate/leakage risk?

**Why:** Before streaming 100K train, we must prove the audit pipeline on a complete local split with known row count.

**Position:** Validates measurement cleaning, relational features, quality tiers, and hash-based identity on real data.

---

## 2. Input / Preconditions

| Item | Value |
|------|-------|
| Dataset | `fitvto-100k` eval split |
| Shards | 20 / 20 local |
| Samples | 5,000 (expected) |
| Raw path | `data/raw/fit/data/eval-*.parquet` |
| Raw size | ~9.9 GB |
| batch_size | 8 |
| workers | 1 |
| Pipeline | `scripts/run_eval_audit.py` → `eval_pipeline.py` (later superseded by streaming core) |
| Git HEAD | NO_COMMIT |

---

## 3. What Was Actually Done

1. Bounded-memory shard iteration (20 eval shards).
2. Per-image: bytes → decode → SHA256 → perceptual hash → release.
3. Measurement normalization to canonical `*_cm` fields.
4. Relational features: `bust_ease_cm`, `bust_ease_ratio`, `garment_length_height_ratio`.
5. Quality classification: VALID / SUSPICIOUS / INVALID.
6. Exact duplicate audit (SHA256).
7. `bust_ease_ratio` quantization analysis.
8. Wrote manifest + reports + figures.

**Failures during this run:** Initial pipeline OOM (see Run 003). Eval audit succeeded after bounded-memory rewrite.

---

## 4. Results — Real Data

### Coverage

| Metric | Value |
|--------|-------|
| Samples processed | 5,000 |
| Eval shards | 20 / 20 |

### Quality

| Status | Count |
|--------|-------|
| VALID | 4,987 |
| SUSPICIOUS | 12 |
| INVALID | 1 |
| usable_for_fitground | 4,999 |

### Images

| Issue | Count |
|-------|-------|
| Missing images | 1 |
| Corrupt images | 0 |
| Measurement suspicious flags | 4 |

### Measurement missing rate

All core fields: **0.0%** missing (5,000 / 5,000 each).

### Sleeveless garments

`garment_sleeve_cm == 0`: **428** samples (flagged `sleeveless_garment`, NOT invalid).

### Bust ease sign (eval)

| Sign | Count |
|------|-------|
| Negative (tight) | 783 |
| Zero | 3 |
| Positive (loose) | 4,214 |

### Key distributions (from `reports/fit_eval_distribution.json`)

| Field | min | p5 | median | p75 | p95 | max |
|-------|-----|-----|--------|-----|-----|-----|
| body_height_cm | 149.77 | 157.68 | 171.33 | 176.96 | 185.59 | 195.72 |
| body_bust_cm | 82.72 | 89.97 | 103.35 | 108.77 | 126.01 | 147.04 |
| garment_bust_cm | 87.43 | 95.80 | 112.52 | 122.44 | 137.28 | 172.61 |
| bust_ease_cm | -14.89 | -7.90 | 6.82 | 15.25 | 28.55 | 61.72 |
| bust_ease_ratio | -0.137 | -0.071 | 0.063 | 0.150 | 0.290 | 0.609 |

### Duplicates (exact SHA256)

| Type | Count |
|------|-------|
| Duplicate person | 2 |
| Duplicate garment | 6 |
| Duplicate target | 6 |
| Duplicate person-garment pair | 0 |
| Exact record duplicate | 0 |

### bust_ease_ratio quantization

| Metric | Value |
|--------|-------|
| Unique raw | 3,191 |
| Unique rounded 2dp | 72 |
| Unique rounded 1dp | 8 |
| Top 2dp value 0.05 count | 1,071 (21.4%) |
| Top 1dp value 0.10 count | 1,906 (38.1%) |
| Verdict | `likely_quantized_preset_levels` |

### Memory (eval streaming run)

| Metric | Value |
|--------|-------|
| Global RSS peak | 844,488,704 bytes (~805 MB) |
| RSS limit | 1,610,612,736 bytes (1.5 GiB) |

---

## 5. Interpretation

**Observation:** bust_ease_cm spans -14.9 to +61.7 cm; 783 samples have negative ease.

**Interpretation:** Eval includes genuinely tight fits — not data errors. Extreme fit ≠ dirty data.

**Implication:** FitGround can study measurement-grounded fit across tight→loose spectrum.

**Observation:** bust_ease_ratio concentrates at discrete levels (8 unique values at 1dp; 21% at 0.05).

**Interpretation:** Garment scaling may use preset levels — important for counterfactual design and shortcut detection.

**Implication:** Models may exploit quantization artifacts; counterfactual pairs should vary within and across levels.

**Observation:** 428 sleeveless (sleeve=0), 0% measurement missing.

**Interpretation:** Zero sleeve length is semantic (sleeveless), not missing data.

---

## 6. Decision

**DECISION:** `garment_sleeve_length == 0` → flag `sleeveless_garment`, never INVALID.

**DECISION:** Image identity = `modality:sha256`, not path alone.

**DECISION:** Duplicates → SUSPICIOUS flag, not deletion.

---

## 7. Failure Evidence

- First eval pipeline attempt: OOM (Python killed, anon RSS ~1.05 GB). Fixed in Run 003.
- Post-fix eval audit: **verified successful** (this run).

---

## 8. Artifacts

| Artifact | Path |
|----------|------|
| Eval manifest | `data/processed/fit_eval_clean_v0.1.parquet` (~2.6 MB) |
| Audit JSON | `reports/fit_eval_audit.json` |
| Audit MD | `reports/fit_eval_audit.md` |
| Distribution JSON | `reports/fit_eval_distribution.json` |
| Distribution MD | `reports/fit_eval_distribution.md` |
| Figures | `reports/figures/eval_hist_*.png`, `eval_bust_ease_scatter.png`, etc. |
| Checkpoints | `data/interim/eval_checkpoint/` (migrated to `fit_checkpoint/`) |

---

## 9. Verification

- pytest (at time of eval completion): 22 passed
- Row count: 5,000
- Measurement missing: 0%
- Hash coverage: 100% of processed images (1 missing-bytes sample flagged INVALID)

---

## 10. What We Learned

1. Eval is measurement-complete (0% missing).
2. Fit variation is wide enough for fit-aware research.
3. bust_ease_ratio shows quantization — likely preset garment scaling.
4. Duplicate rate is low but non-zero; must flag not drop.
5. Bounded-memory eval processing peaks ~805 MB — viable on 3.8 GB RAM + swap.

---

## 11. Project State

| Area | Status |
|------|--------|
| Eval audit | DONE |
| Eval FIT-Clean manifest | DONE |
| Train audit | PARTIAL (streaming in progress, Run 004) |
| Global FIT-Clean | BLOCKED until 406/406 train |

---

## 12. Next Stage

**NEXT:** OOM diagnosis + streaming redesign (Run 003), then full FIT train streaming (Run 004).
