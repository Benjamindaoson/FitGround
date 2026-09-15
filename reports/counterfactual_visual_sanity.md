# Counterfactual Visual Sanity Check

**Status:** Protocol ready; **pixel review NOT VERIFIED**  
**Date:** 2026-09-11  
**Output root (outside git):** `D:\FitGroundData\materialized\counterfactual_pilot\`

## Question

Do person-held TIER C (and the two TIER B) pairs actually show the same person, different cloth, and a target drape change when measurements change?

## Sampling (metadata, completed)

Shard packing is mandatory: only 4/1,731 pairs share a shard. Random 200 pairs would touch hundreds of ~500MB shards.

| Packed set | Value |
|------------|-------|
| Pairs | **91** (includes both TIER B and the single eval-eval pair) |
| Sample ids | 179 |
| Shards | 64 |
| Ease bins | negative / near-zero / moderate / large represented |
| Table | `reports/counterfactual_pilot_metadata.csv` |
| Id list | `D:\FitGroundData\materialized\counterfactual_pilot\sample_ids.txt` |

This is slightly under the 100–300 suggestion because 64 shards is already a large download at WAN speed; 80 shards would be needed for ~155 pairs.

## Image download (attempted)

`scripts/materialize_samples.py --use-external-data-root` and a 2-id eval-eval probe.

**OBSERVED:**

- Hugging Face Hub warned: unauthenticated requests.
- `hf_xet` transfer reported ~38 KB/s, “connection struggling”; incomplete parquet stayed 0 bytes on disk while CAS buffers grew.
- HTTP retry (`HF_HUB_DISABLE_XET=1`) still showed a 0-byte `.incomplete` lock after >90s.
- Completing 64 shards at this rate would be hours–days and is forbidden by the CPU/time rule.

Download was stopped. Ephemeral shards / xet staging were deleted. No PNGs were written. No VLM labels were produced.

## Human review checklist (when images exist)

For each contact sheet: same person image? different cloth? does the looser-ease target actually look looser / larger / longer? suspicious quantization artifacts?

## Decision

Pixel-level fit change remains **NOT VERIFIED**. The experimental contract’s visual failure criterion is therefore **open**. Metadata feasibility (PARTIAL) does not depend on this download succeeding.

Re-run when an HF token / faster path is available:

```powershell
$env:HF_HUB_DISABLE_XET='1'
$env:HF_TOKEN='<token>'
python scripts/materialize_counterfactual_pilot.py --n-pairs 91 --max-shards 64
```

Images must stay under `D:\FitGroundData\` (60GB cap). Do not copy them into the git repo.
