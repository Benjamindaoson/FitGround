# Asset inventory after GPU shutdown

The GPU host (`cn-north-b.ssh.damodel.com:35236`) now refuses connections.
Everything that still existed on **this** workspace was pushed to `origin/main`.

## Already in git (this repo)

- All FitGround source, tests, Makefile, Next.js `studio/`
- `data/processed/fit_clean_v0.1.parquet` (~50 MB)
- Training lattice, 289 pattern PNGs, SFT/RLVR checkpoints under `artifacts/training/`
- GPU physics lattice renders/meshes under `artifacts/gpu/physics_lattice/` (baseline / +1 / +2 / +3)
- Hero JSON/JSONL: 636-row lattice, physics outcomes, visual disambiguation, OOD, failure-aware, Qwen2-VL eval metrics
- Figures `reports/figures/01_…14_*.png` and designer evidence PNGs
- Resume / interview reports

## On the GPU disk only — not recoverable from here

These were never copied off the GPU before the host went down:

| Path | What it was |
| --- | --- |
| `artifacts/hero/_pat/` | 677 GarmentCode serialize folders |
| `artifacts/hero/pattern_pngs/` | 677 v0.2 lattice pattern drawings |
| `artifacts/hero/sim/` and `sim_vd/` | Warp `.obj` meshes + extra drape renders (112-case material grid) |
| `/root/workspace/hf-cache/` | Qwen2-VL-2B-Instruct weights (~4.2 GB) |
| flux conda env, Warp, GarmentCodeV2 trees | Runtime, reinstallable from scripts |

Numeric results from those runs **are** in git (`physics_vd.json`, `visual_disambiguation.json`, `mllm_eval.json`). Only the bulky regenerable binaries are missing.
