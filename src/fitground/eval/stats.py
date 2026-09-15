"""Bootstrap CIs and paired comparisons. No GPU required."""

from __future__ import annotations

from typing import Callable, Sequence

import numpy as np


def bootstrap_ci(
    values: Sequence[float],
    fn: Callable[[np.ndarray], float] | None = None,
    n: int = 800,
    seed: int = 0,
    alpha: float = 0.05,
) -> dict:
    arr = np.asarray(list(values), dtype=float)
    fn = fn or (lambda x: float(np.mean(x)))
    if len(arr) == 0:
        return {"n": 0, "mean": None, "std": None, "lo": None, "hi": None}
    rng = np.random.default_rng(seed)
    stats = np.empty(n, dtype=float)
    for i in range(n):
        stats[i] = fn(arr[rng.integers(0, len(arr), size=len(arr))])
    point = fn(arr)
    lo = float(np.percentile(stats, 100 * alpha / 2))
    hi = float(np.percentile(stats, 100 * (1 - alpha / 2)))
    return {
        "n": int(len(arr)),
        "mean": float(point),
        "std": float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0,
        "lo": lo,
        "hi": hi,
    }


def paired_sign_rate(a: Sequence[float], b: Sequence[float]) -> dict:
    """Fraction of pairs where a beats b (lower is better if values are errors)."""
    aa = np.asarray(list(a), dtype=float)
    bb = np.asarray(list(b), dtype=float)
    if len(aa) != len(bb) or len(aa) == 0:
        return {"n": 0, "a_better": None, "mean_diff": None}
    diff = aa - bb
    return {
        "n": int(len(aa)),
        "mean_diff": float(np.mean(diff)),
        "a_better": float(np.mean(diff < 0)),
        "b_better": float(np.mean(diff > 0)),
        "tie": float(np.mean(diff == 0)),
    }
