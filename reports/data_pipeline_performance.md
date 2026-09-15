# Data Pipeline Performance Evidence

## Hardware

| Resource | Value |
|----------|-------|
| vCPU | 3 |
| RAM | 3.8 GiB |
| Swap | ~12 GiB |
| Disk | 99 GB total |

## Full Run (complete — Run 004 + finalize)

| Metric | Value |
|--------|-------|
| Train shards | 406 / 406 |
| Eval shards | 20 / 20 |
| Total rows | 105,000 |
| Manifest size | ~50 MB |
| Peak shard RSS | 1,110,065,152 B (~1.06 GB) |
| Memory guard | 1.5 GiB |
| Memory trend verdict | POSSIBLE_ALLOCATOR_RETENTION |
| OOM after redesign | 0 |
| Disk free (post-finalize) | ~59 GB |

## Engineering Conclusion

On ~4 GB RAM / 100 GB disk, complete multimodal audit of ~213 GB FIT is feasible via ephemeral train shard download, `iter_batches(8)`, incremental checkpoints, and immediate image release. Raw train data is NOT persisted.

See `reports/memory_trend_analysis.md` for RSS trend analysis and future recycling recommendations.
