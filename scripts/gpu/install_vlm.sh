#!/usr/bin/env bash
# Install a real pretrained VLM without NVIDIA CUDA extra wheels.
set -euo pipefail
source /root/workspace/projects/FitGround/scripts/gpu/flux_env.sh
export PYTHONUNBUFFERED=1
export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"
export HF_HOME="${HF_HOME:-/root/workspace/hf-cache}"
mkdir -p "$HF_HOME" /root/workspace/projects/FitGround/artifacts/hero
LOG=/root/workspace/projects/FitGround/artifacts/hero/vlm_fetch.log
exec >>"$LOG" 2>&1
echo "VLM_FETCH2_START $(date -u)"
# flux already has tokenizers 0.23; use a transformers that accepts it
python -m pip install -q --no-deps "transformers==4.49.0"
python -m pip install -q huggingface_hub pillow requests regex tqdm safetensors filelock packaging pyyaml
python - << 'PY'
import json, os, traceback
from pathlib import Path
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HOME", "/root/workspace/hf-cache")
status_path = Path("/root/workspace/projects/FitGround/artifacts/hero/mllm_status.json")
candidates = [
    "Qwen/Qwen2-VL-2B-Instruct",
    "HuggingFaceTB/SmolVLM-256M-Instruct",
]
last_err = None
for name in candidates:
    try:
        print("TRY", name, flush=True)
        import transformers
        print("transformers", transformers.__version__, flush=True)
        from transformers import AutoProcessor, AutoModelForVision2Seq
        proc = AutoProcessor.from_pretrained(name, trust_remote_code=True)
        model = AutoModelForVision2Seq.from_pretrained(
            name, trust_remote_code=True, torch_dtype="auto", low_cpu_mem_usage=False
        )
        n = sum(p.numel() for p in model.parameters())
        payload = {"status": "DOWNLOADED", "model": name, "n_params": int(n), "transformers": transformers.__version__}
        status_path.write_text(json.dumps(payload, indent=2))
        print("LOADED", payload, flush=True)
        break
    except Exception as exc:
        last_err = f"{type(exc).__name__}: {exc}"
        print("FAIL", name, last_err, flush=True)
        traceback.print_exc()
        try:
            from transformers import AutoModelForImageTextToText
            print("RETRY ImageTextToText", name, flush=True)
            proc = AutoProcessor.from_pretrained(name, trust_remote_code=True)
            model = AutoModelForImageTextToText.from_pretrained(
                name, trust_remote_code=True, torch_dtype="auto", low_cpu_mem_usage=False
            )
            n = sum(p.numel() for p in model.parameters())
            payload = {"status": "DOWNLOADED", "model": name, "n_params": int(n), "loader": "AutoModelForImageTextToText"}
            status_path.write_text(json.dumps(payload, indent=2))
            print("LOADED", payload, flush=True)
            break
        except Exception as exc2:
            last_err = f"{type(exc2).__name__}: {exc2}"
            traceback.print_exc()
            status_path.write_text(json.dumps({"status": "FAILED", "model": name, "error": last_err}))
else:
    print("ALL_FAILED", last_err, flush=True)
print("VLM_FETCH2_END", flush=True)
PY
echo "VLM_FETCH2_END $(date -u)"
