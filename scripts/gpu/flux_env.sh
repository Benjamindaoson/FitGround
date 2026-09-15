#!/bin/bash
export CONDA_PREFIX=/root/workspace/conda/envs/flux
export CUDA_HOME="$CONDA_PREFIX"
export CUDA_PATH="$CONDA_PREFIX"
export PATH="$CONDA_PREFIX/bin:/usr/bin:/bin:$PATH"
export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$CONDA_PREFIX/lib64:${LD_LIBRARY_PATH:-}"
export PYTHONNOUSERSITE=1
export PYOPENGL_PLATFORM=egl
export PYTHONPATH=/root/workspace/external/FitVTON-source-tree/GarmentCodeV2:${PYTHONPATH:-}
# Torch 2.5+cu124 looks for libcudnn.so.9 from the nvidia-cudnn-cu12 wheel.
if [ -d "$CONDA_PREFIX/lib/python3.10/site-packages/nvidia/cudnn/lib" ]; then
  export LD_LIBRARY_PATH="$CONDA_PREFIX/lib/python3.10/site-packages/nvidia/cudnn/lib:$LD_LIBRARY_PATH"
fi
