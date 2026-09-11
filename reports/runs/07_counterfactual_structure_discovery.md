# Run 007 — Counterfactual Structure Discovery

**Run ID:** `run_007`  
**Stage:** Phase 1–2 — grouping A–E and experimental-unit ranking  
**Recorded:** 2026-09-11  
**Input:** `data/processed/fit_clean_v0.1.parquet` (105,000 rows; analysis on 104,999 usable)

## Question

Does FIT-Clean v0.1 natively support a **controlled measurement counterfactual** — same person image, same cloth image, different garment measurement, different target?

## Execution

Metadata-only `groupby` / hashing / `cKDTree.query_pairs` on unique vectors. No N×N dense matrix. No images. CLI: `python scripts/discover_counterfactual_structure.py`.

Artifact: `artifacts/counterfactual_structure_v0.1.json`

## Results

### A. Same person + same cloth (`person_sha256` + `garment_sha256`)

| Statistic | Value | Level |
|-----------|-------|-------|
| Groups | 104,999 | OBSERVED |
| Groups with >1 row | **0** | OBSERVED |
| TIER A groups | **0** | DERIVED |

Every (person image, cloth image) pair is unique. FIT did not generate multiple measurement conditions for the same visual pair.

### B. Same person (`person_sha256`)

| Statistic | Value | Level |
|-----------|-------|-------|
| Unique person images | 103,289 | OBSERVED |
| Groups with >1 row | **1,689** (1,668 size 2; 21 size 3; max 3) | OBSERVED |
| Rows in those groups | 3,399 | OBSERVED |
| Body-measurement consistency issues | **0** | OBSERVED |
| Different cloth / different target / garment meas. varies | 1,689 / 1,689 / 1,689 | OBSERVED |
| Ease varies | 1,628 / 1,689 | OBSERVED |
| Exact garment pHash family (TIER B) | **1 group / 1 pair** | OBSERVED |
| Near pHash (hamming ≤ 4) | **1 additional pair** | OBSERVED |
| Typical within-person cloth pHash hamming | 16–32 (unrelated garments) | OBSERVED |
| Train-only / cross-split / eval-only person groups | 1,519 / **169** / 1 | OBSERVED |

Same person image **is** reused. Body measurements are constant (as they must be for an identical image). The second garment is almost never a visual sibling of the first.

### C. Same cloth (`garment_sha256`)

| Statistic | Value | Level |
|-----------|-------|-------|
| Unique cloth images | 103,372 | OBSERVED |
| Groups with >1 row | 1,598 (max 3) | OBSERVED |
| Garment-measurement inconsistency | **0** | OBSERVED |
| Different person | 1,598 | OBSERVED |
| Different target | **0** | OBSERVED |
| Body-vector variation | **0** | OBSERVED |

Same cloth image ⇒ same garment measurements **and** same target. Person SHA256/pHash differ. **INTERPRETED:** cloth reuse is an alternate person-render of the same try-on instance, not a measurement intervention and not a body-held counterfactual.

### D. Same target (`target_sha256`)

| Statistic | Value | Level |
|-----------|-------|-------|
| Unique targets | 103,345 | OBSERVED |
| Duplicate target groups / rows | 1,624 / 3,278 | OBSERVED |
| Cross-split duplicate targets | 146 | OBSERVED |
| Duplicate targets with different person | 1,624 | OBSERVED |
| Duplicate targets with different cloth | 26 | OBSERVED |

Repeated targets are a memorization / leakage risk. Pairs that share a target are rejected.

### E. Measurement vectors

| Vector | Unique exact | Repeated vectors | Notes | Level |
|--------|--------------|------------------|-------|-------|
| BODY (h,bust,waist,hips) | **105** | 105 (all of them) | max frequency 2,801; mean ~1,000 | OBSERVED |
| GARMENT | 64,468 | 27,769 | high cardinality | OBSERVED |
| RELATIONAL | 61,983 | 26,658 | | OBSERVED |
| `bust_ease_ratio` raw / 2dp / 1dp | 29,387 / 87 / **11** | — | 1dp collapse | OBSERVED |
| Body KDTree radius 1 cm near-pairs | 0 | bodies well separated | OBSERVED |
| Body KDTree radius 2 cm near-pairs | 6 | | OBSERVED |

`bust_ease_ratio` rounded to 2dp has a mode at `0.05` (21,998 rows). Strict 0.05-grid occupancy of the raw ratio is only ~0.3%. **HYPOTHESIZED** (not verified from FIT docs): generation uses a small set of body avatars (105) plus relatively continuous garment parameters.

### Tier ranking

| Tier | Groups | Pairs (possible) | Quality | Decision |
|------|--------|------------------|---------|----------|
| A | 0 | 0 | N/A | Unavailable |
| B | 1 exact + 1 near | 2 | strongest visual-garment control | Sparse — keep but insufficient |
| C | **1,689** | **1,731 unordered** | person held; cloth appearance **not** held; typically 3 garment fields change | **Strongest available unit** |
| D | not constructed | 0 | would confound person image | Deferred; C is sufficient in count, insufficient in isolation |

## Interpretation

FIT supports **person-held garment-alternative pairs** with perfect body-measurement control. It does **not** support same-cloth measurement interventions. The independent variable in TIER C is a **full garment swap**, not a single-parameter ease edit.

## Decision

Proceed to candidate generation on TIER B+C. Do not construct TIER D. Feasibility cannot be GO for measurement isolation; it can be PARTIAL for a person-held diagnostic.

## Artifacts

- `artifacts/counterfactual_structure_v0.1.json`
- `src/fitground/counterfactual/discovery.py`

## Verification

Re-run `python scripts/discover_counterfactual_structure.py`. TIER A `groups_with_gt1_row` must remain 0. Person multi groups must remain 1,689 on this frozen manifest.

## What We Learned

The theoretically strongest counterfactual (TIER A) is empty by construction of FIT. The dataset's real reuse structure is (a) ~105 discrete bodies, (b) rare person-image reuse with different garments, (c) cloth/target reuse with alternate person bytes.

## Next

Build the candidate parquet and attack it with a shortcut audit.
