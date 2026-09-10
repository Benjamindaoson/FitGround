# Memory Trend Analysis

**Generated:** from `/workspace/FitGround/data/interim/fit_checkpoint/state.json`
**Train shards analyzed:** 406
**Eval shards:** 20

## Verdict

**POSSIBLE_ALLOCATOR_RETENTION**

## Metrics

| Metric | Value |
|--------|-------|
| train_shards | 406 |
| first_window_mean_mb | 892.29 |
| last_window_mean_mb | 1031.22 |
| growth_mb | 138.93 |
| global_slope_mb_per_shard | 0.36 |
| r_squared | 0.82 |
| last_window_std_mb | 10.47 |
| last_window_range_mb | 46.42 |
| last_window_monotonic_up_fraction | 0.48 |
| global_peak_mb | 1058.64 |
| global_min_mb | 769.37 |

## Last 30 Train Shards (peak RSS)

| shard_id | peak_rss_mb |
|----------|-------------|
| train-00376-of-00406 | 1025.7 |
| train-00377-of-00406 | 1036.9 |
| train-00378-of-00406 | 1045.7 |
| train-00379-of-00406 | 1032.9 |
| train-00380-of-00406 | 1040.3 |
| train-00381-of-00406 | 1027.4 |
| train-00382-of-00406 | 1025.6 |
| train-00383-of-00406 | 1053.5 |
| train-00384-of-00406 | 1030.1 |
| train-00385-of-00406 | 1032.5 |
| train-00386-of-00406 | 1022.7 |
| train-00387-of-00406 | 1022.7 |
| train-00388-of-00406 | 1014.5 |
| train-00389-of-00406 | 1058.6 |
| train-00390-of-00406 | 1032.5 |
| train-00391-of-00406 | 1050.9 |
| train-00392-of-00406 | 1033.6 |
| train-00393-of-00406 | 1012.2 |
| train-00394-of-00406 | 1031.0 |
| train-00395-of-00406 | 1015.5 |
| train-00396-of-00406 | 1032.5 |
| train-00397-of-00406 | 1033.6 |
| train-00398-of-00406 | 1028.6 |
| train-00399-of-00406 | 1021.1 |
| train-00400-of-00406 | 1030.7 |
| train-00401-of-00406 | 1031.4 |
| train-00402-of-00406 | 1022.3 |
| train-00403-of-00406 | 1032.0 |
| train-00404-of-00406 | 1029.6 |
| train-00405-of-00406 | 1029.9 |

## Interpretation

Early shards show lower peak RSS (~770–850 MB) while the last ~30 shards plateau near ~1.02–1.06 GB without monotonic climb. This pattern is consistent with Python allocator / object retention rather than unbounded leak. No OOM occurred; peak remains below the 1.5 GiB guard.

**Recommendation (if memory guard stops future runs):** consider process recycling every N shards or per-shard child-process isolation so RSS resets on resume. Do NOT hot-modify a running process.

## Artifacts

- `reports/tables/memory_by_shard.csv`
- `reports/figures/memory_by_shard.png`