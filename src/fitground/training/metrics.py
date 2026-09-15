"""Shared numeric metrics for training reports."""

from __future__ import annotations

import numpy as np


def rmse(y, yhat) -> float:
    y = np.asarray(y, dtype=float)
    yhat = np.asarray(yhat, dtype=float)
    return float(np.sqrt(np.mean((y - yhat) ** 2)))


def mae(y, yhat) -> float:
    y = np.asarray(y, dtype=float)
    yhat = np.asarray(yhat, dtype=float)
    return float(np.mean(np.abs(y - yhat)))


def accuracy(y, yhat) -> float:
    y = np.asarray(y)
    yhat = np.asarray(yhat)
    if len(y) == 0:
        return float("nan")
    return float(np.mean(y == yhat))
