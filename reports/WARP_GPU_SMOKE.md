# Warp GPU smoke

**Status: PASS**

| Field | Value |
| --- | --- |
| wp.is_cuda_available() | True |
| device | cuda:0 NVIDIA GeForce RTX 4090 |
| kernel | `inc`: zeros + 1 on CUDA, output all 1.0 |
| Warp | 1.0.0-beta.6 from NvidiaWarp-GarmentCode |
| library | `warp/bin/warp.so` SHA256 `9e61637a8868fd7813e75d1601119c8aa91b76f0d2e766a6296fcfee8edb2c8c` (108,606,704 bytes) |
| nvcc | CUDA 12.6.85 |
| driver | 580.95.05 (CUDA 13.0) |
| CUDA_HOME | `/root/workspace/conda/envs/flux` |
| artifact | `artifacts/gpu/warp_smoke.json` |

Notes:
- CUDA `warp.so` was already built (`build cuda took ~125s` earlier). A stuck packman job was downloading **linux-aarch64 LLVM** on this x86_64 machine; it was killed. `warp-clang` / standalone CPU JIT is **not** installed.
- Kernel source must live in a `.py` file (not stdin) and must **not** use `from __future__ import annotations`.
