# GPU execution state audit

Host: `daka5svhri0c73etu4ug-fitground`  
GPU: NVIDIA GeForce RTX 4090 24564 MiB, driver 580.95.05  
Disk: overlay 40G; `/root/workspace` 50G (yrfs), ~38G free after this work  
FitGround: `/root/workspace/projects/FitGround` (GitHub archive commit `c1dcca9`, no `.git`)  
fitground-core: Python 3.11.16, pytest 58 passed / 2 skipped, pip check PASS  
flux: Python 3.10.21, CUDA toolkit 12.6 nvcc, numpy 2.2.6  

Warp: `warp.so` present; aarch64 LLVM packman hung and was killed. CUDA kernel smoke PASS.  
Torch 2.11+cu126: wheel installed but required `pypi.nvidia.com` CUDA/cudnn meta packages (timeout). Fallback 2.5.1+cu124 wheel downloaded; nvidia-* extra packages may still be blocked by NVIDIA CDN. See `artifacts/gpu/torch_cu124.log`. Physics does **not** depend on PyTorch.  
SMPL pkl: missing (licensed). Static OBJ physics used instead.  
No prior training checkpoints on disk.
