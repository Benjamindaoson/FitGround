# FIT Streaming Data Engineering

## Mode
- **Eval**: 20 shards read from local `data/raw/fit/data/` (9.9GB, persistent)
- **Train**: 406 shards downloaded **ephemerally** per shard (~500MB), processed, checkpointed, deleted
- **HF cache**: `data/cache/huggingface/` (capped ~2GB, pruned after each train shard)
- **Checkpoints**: `data/interim/fit_checkpoint/{shard_id}.parquet` (metadata only, incremental)
- **Final manifest**: `data/processed/fit_clean_v0.1.parquet`

## Memory
- `iter_batches(batch_size=8)` — never `read_table()` on image columns
- Per-shard measurements only (~250 rows)
- RSS limit: 1.5 GiB (hard stop + resume)
- Observed peak: ~800 MB/shard

## Disk
- Reserve: 20 GiB minimum free
- No full 200GB+ dataset on disk
- Ephemeral train shard deleted after each checkpoint

## Resume
```bash
.venv/bin/python scripts/run_fit_stream.py --no-eval --resume
.venv/bin/python scripts/run_fit_stream.py --finalize-only  # when 406+20 shards done
```
