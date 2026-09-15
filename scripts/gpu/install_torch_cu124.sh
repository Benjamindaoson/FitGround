#!/bin/bash
source /root/workspace/projects/FitGround/scripts/gpu/flux_env.sh
python -m pip uninstall -y torch torchvision torchaudio >/dev/null 2>&1 || true
python -m pip install --retries 8 --timeout 120 torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu124
python - << 'PY'
import torch
print("torch", torch.__version__, "cuda", torch.version.cuda, "avail", torch.cuda.is_available())
if torch.cuda.is_available():
    print("device", torch.cuda.get_device_name(0))
    x = torch.zeros(8, device="cuda")
    print("tensor_ok", float(x.sum()))
PY
