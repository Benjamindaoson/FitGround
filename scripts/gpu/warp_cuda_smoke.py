#!/usr/bin/env python3
import hashlib
import json
import os
import subprocess
import time
import traceback
from pathlib import Path

import numpy as np
import warp as wp

WARP_SO = Path("/root/workspace/external/FitVTON-source-tree/NvidiaWarp-GarmentCode/warp/bin/warp.so")
OUT = Path("/root/workspace/projects/FitGround/artifacts/gpu/warp_smoke.json")


@wp.kernel
def inc(a: wp.array(dtype=float)):
    tid = wp.tid()
    a[tid] = a[tid] + 1.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    t0 = time.time()
    payload = {
        "status": "FAIL",
        "wp_is_cuda_available": None,
        "device": None,
        "kernel_ok": False,
        "kernel_output": None,
        "expected": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        "error": None,
        "warp_file": getattr(wp, "__file__", None),
        "warp_version": getattr(wp, "__version__", None),
        "library_path": str(WARP_SO),
        "library_exists": WARP_SO.exists(),
        "cwd": os.getcwd(),
    }
    try:
        wp.init()
        payload["wp_is_cuda_available"] = bool(wp.is_cuda_available())
        device = wp.get_device("cuda:0")
        payload["device"] = str(device)
        a = wp.zeros(8, dtype=float, device="cuda:0")
        wp.launch(inc, dim=8, inputs=[a], device="cuda:0")
        wp.synchronize()
        y_np = [float(v) for v in a.numpy()]
        payload["kernel_output"] = y_np
        expected = [1.0] * 8
        payload["expected"] = expected
        payload["kernel_ok"] = all(abs(v - 1.0) < 1e-5 for v in y_np)
        payload["status"] = "PASS" if payload["wp_is_cuda_available"] and payload["kernel_ok"] else "FAIL"
        payload["cuda_devices"] = [str(d) for d in wp.get_cuda_devices()]
    except Exception as exc:
        payload["error"] = f"{type(exc).__name__}: {exc}"
        payload["traceback"] = traceback.format_exc()
    payload["runtime_s"] = time.time() - t0
    if WARP_SO.exists():
        payload["library_sha256"] = sha256(WARP_SO)
        payload["library_size_bytes"] = WARP_SO.stat().st_size
    payload["nvcc"] = subprocess.check_output(["nvcc", "--version"], text=True)
    payload["nvidia_smi"] = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
        text=True,
    ).strip()
    payload["CUDA_HOME"] = os.environ.get("CUDA_HOME")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
