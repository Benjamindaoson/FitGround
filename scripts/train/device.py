"""Torch device probe used by every training script."""

from __future__ import annotations

from typing import Any


def probe_torch() -> dict[str, Any]:
    info: dict[str, Any] = {
        "torch_imported": False,
        "version": None,
        "cuda_compiled": None,
        "cuda_available": False,
        "device": "cpu",
        "gpu_name": None,
        "error": None,
    }
    try:
        import torch
    except Exception as exc:  # pragma: no cover - environment dependent
        info["error"] = f"{type(exc).__name__}: {exc}"
        return info
    info["torch_imported"] = True
    info["version"] = torch.__version__
    info["cuda_compiled"] = torch.version.cuda
    info["cuda_available"] = bool(torch.cuda.is_available())
    if info["cuda_available"]:
        info["device"] = "cuda"
        info["gpu_name"] = torch.cuda.get_device_name(0)
    return info


def torch_device():
    import torch

    return torch.device("cuda" if torch.cuda.is_available() else "cpu")
