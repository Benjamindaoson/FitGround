# Materialize Samples

Rehydrate person/cloth/target images for specific `sample_id`s without storing the full 213GB FIT dataset.

## Prerequisites

- `data/processed/fit_clean_v0.1.parquet` (or eval manifest)
- Network access to Hugging Face
- HF cache: `data/cache/huggingface/` (auto-created)

## Usage

```bash
.venv/bin/python scripts/materialize_samples.py \
  --sample-id "eval/eval-00000-of-00020/0000" \
  --output-dir data/materialized/ \
  --verify-hash
```

### Options

| Flag | Description |
|------|-------------|
| `--sample-id` | Repeatable; manifest sample_id |
| `--input-manifest` | Default: `data/processed/fit_clean_v0.1.parquet` |
| `--output-dir` | Required output directory |
| `--keep-shard` | Do not delete ephemeral downloaded shard |
| `--verify-hash` | Verify SHA256 against manifest (default: on) |

## Behavior

1. Lookup row in manifest by `sample_id`
2. Download required HF parquet shard to ephemeral staging
3. Extract row `person`, `cloth`, `target` bytes
4. Verify SHA256 if requested
5. Write PNG files + `metadata.json`
6. Delete ephemeral shard unless `--keep-shard`

## Windows / Local

Same commands after `git clone` and venv setup. Paths are relative to project root.
