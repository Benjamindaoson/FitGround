# FitGround Evidence Ledger

Project-wide provenance index. **Append-only — do not overwrite history.**

| Date | Run ID | Stage | Question | Input | Main Result | Decision | Artifacts | Status | Next |
|------|--------|-------|----------|-------|-------------|----------|-----------|--------|------|
| 2026-09-10 | run_001 | Environment & FIT Schema | Can we access FIT and is full local download feasible? | HF `fitvto-100k`, VPS 99GB disk | Schema confirmed (Parquet+embedded PNG, cm); full download shortfall ~128GB | Eval persistent, train ephemeral | `reports/runs/01_environment_and_fit_schema.md`, `reports/storage_audit.json` | DONE | Eval audit |
| 2026-09-10 | run_002 | Eval Measurement Audit | Is eval 5K measurement-complete and fit-varied? | 20 eval shards, 5000 samples | 0% meas missing; bust_ease -14.9→+61.7cm; VALID 4987/5000 | sleeve=0 is sleeveless not invalid; modality:sha256 identity | `reports/runs/02_eval_measurement_audit.md`, `data/processed/fit_eval_clean_v0.1.parquet` | DONE | Fix OOM, stream train |
| 2026-09-10 | run_003 | OOM Failure & Streaming Redesign | Why OOM and how to fix? | dmesg: python anon-rss 1.05GB killed | `iter_batches(8)` + checkpoint; peak RSS ~805MB | Shard streaming mandatory; RSS limit 1.5GB | `reports/runs/03_oom_failure_and_streaming_redesign.md`, `stream_core.py` | DONE | Full train stream |
| 2026-09-10 | run_004 | Full FIT Train Streaming | Audit 100K train without raw persistence? | Ephemeral train shards, batch=8, PID 309342 | **57/406 train** (live); eval 20/20; RSS ~510MB; no new OOM | Do not stop/restart running pipeline | `reports/runs/04_full_fit_stream_progress.md`, `data/interim/fit_checkpoint/` | PARTIAL | Finalize at 406/406 |
| 2026-09-10 | run_005 | Data Engineering Closure (partial) | Close DE with evidence pack? | 89/406 train, eval done | Contracts, materialize tool, 30 tests pass | Do not stop pipeline | `reports/runs/05_data_engineering_closure_partial.md` | PARTIAL | Finalize at 406/406 |
| — | run_006 | Global FIT-Clean + EDA | Full 105K quality, leakage, distributions? | All checkpoints | NOT STARTED | — | `data/processed/fit_clean_v0.1.parquet` | BLOCKED | Counterfactual feasibility |
| — | run_006 | Counterfactual Feasibility | Sufficient controlled measurement variation? | FIT-Clean manifest | NOT STARTED in this checkout's original ledger | — | TBD | BLOCKED | ML/VLM baselines |
| 2026-09-11 | inherited_phase_2 | Measurement counterfactual on released FIT-100K | Can released FIT-100K isolate measurement interventions? | FIT-Clean v0.1 | TIER A=0; TIER B sparse; TIER C=1689 groups / 1729 pairs; appearance co-varies with measurements; COUNTERFACTUAL_FEASIBILITY=PARTIAL | Do not train; do not treat TIER C as do(measurement) | Phase 2 freeze facts in `docs/context/PHASE_2_5_CONTEXT.md` | FROZEN | Controlled generation contract |
| 2026-09-11 | run_011 | Controlled Counterfactual Generation Contract | Can we design a controlled intervention set for GPU E0? | FIT paper, GarmentCode, Phase 2 freeze | Official code unpublished; Track A overlay feasible at 3D stage; vector intervention; E0=3×5×3 | CONTROLLED_COUNTERFACTUAL_GENERATION=PARTIAL; READY_FOR_GPU_E0=YES Stage 1 only; training denied | `docs/EXPERIMENTAL_CONTRACT_v0.2.md`, `artifacts/experimental_contract_v0.2.yaml`, `reports/FIT_GENERATION_MECHANISM_AUDIT.md` | DONE | GPU E0 Stage 1 only |

---

## Evidence Chain (current)

```
Research Question: Do VLMs learn measurement-grounded fit?
    ↓
Run 001–005: FIT-Clean v0.1 frozen (105K, SHA256 6b998bc4…0177)
    ↓
Phase 2 (inherited freeze): released FIT-100K COUNTERFACTUAL_FEASIBILITY=PARTIAL
    (TIER A=0; TIER C appearance co-varies with measurements)
    ↓
Run 011: Experimental Contract v0.2 — controlled generation design
    CONTROLLED_COUNTERFACTUAL_GENERATION=PARTIAL
    READY_FOR_GPU_E0=YES (Stage 1 only)
    ↓
Next: GPU E0 Stage 1 Controlled Counterfactual Generation Pilot
    (NOT VLM/LoRA/RM/DPO/GRPO training)
```

---

## Rules (Evidence-First Development)

1. Every meaningful run → independent Markdown report in `reports/runs/`.
2. Naming: `YYYYMMDD_HHMM_<stage>_<run_id>.md` for future runs; historical runs use numbered `01_`–`04_` prefix.
3. No overwriting prior reports.
4. Failures are evidence — document, don't hide.
5. Code ≠ completion; require execution evidence.
