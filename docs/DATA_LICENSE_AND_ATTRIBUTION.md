# Data License & Attribution

## Dataset

| Field | Value |
|-------|-------|
| Name | FIT (fitvto-100k) |
| Identifier | `Yuanhao-Harry-Wang/fitvto-100k` |
| URL | https://huggingface.co/datasets/Yuanhao-Harry-Wang/fitvto-100k |
| Revision (pinned) | `5563646729edf148ed2b32c4b9c794d51a1bc828` |
| License (per HF card) | **CC BY-NC-ND 4.0** |

## Citation

Use the citation from the official FIT dataset card / paper when publishing.

## Redistribution

| Asset | Status |
|-------|--------|
| Raw FIT images | **May NOT be redistributed** (NC-ND license) |
| Derived manifest (metadata, hashes, measurements) | Likely publishable as derived metadata — **CHECK REQUIRED** for public release |
| Thumbnails / contact sheets | **CHECK REQUIRED** — NC-ND may prohibit |
| SHA256 / pHash / measurements in manifest | Generally publishable as non-substantial metadata — **VERIFY** |
| Demo sample manifest (no image bytes) | Preferred for GitHub |

## FitGround Repository Policy

- **Do NOT commit** raw FIT parquet, embedded images, or HF cache to GitHub.
- **Do commit:** code, schema, audit reports, small demo manifests, hashes/metadata tables.
- Image evidence samples under `reports/evidence_samples/` — metadata only in git; any extracted images stay local and gitignored.

## UNKNOWN / CHECK REQUIRED

- Whether derived `fit_clean_v0.1.parquet` (contains no image bytes) may be uploaded to public GitHub Release without author permission.
- Whether pHash values constitute derivative work under NC-ND.

**Action before public upload:** Confirm with dataset authors or legal review.
