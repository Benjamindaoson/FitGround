#!/usr/bin/env python3
"""Observational B0/B1 baselines on fit_clean_v0.1. Not intervention ground truth."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PARQUET = ROOT / "data" / "processed" / "fit_clean_v0.1.parquet"
OUT = ROOT / "artifacts" / "observational_baselines"


def grouped_split(df: pd.DataFrame, seed: int = 0):
    rng = np.random.default_rng(seed)
    people = df["person_sha256"].dropna().unique()
    rng.shuffle(people)
    n = len(people)
    n_train = int(0.7 * n)
    n_val = int(0.15 * n)
    train_p = set(people[:n_train])
    val_p = set(people[n_train:n_train + n_val])
    test_p = set(people[n_train + n_val:])
    return (
        df[df["person_sha256"].isin(train_p)].copy(),
        df[df["person_sha256"].isin(val_p)].copy(),
        df[df["person_sha256"].isin(test_p)].copy(),
        {"n_people": int(n), "n_train_people": len(train_p), "n_val_people": len(val_p), "n_test_people": len(test_p)},
    )


def rmse(y, yhat):
    y = np.asarray(y, dtype=float)
    yhat = np.asarray(yhat, dtype=float)
    return float(np.sqrt(np.mean((y - yhat) ** 2)))


def mae(y, yhat):
    y = np.asarray(y, dtype=float)
    yhat = np.asarray(yhat, dtype=float)
    return float(np.mean(np.abs(y - yhat)))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(PARQUET)
    df = df[df["usable_for_fitground"] == True].copy()
    df = df.dropna(subset=["body_bust_cm", "garment_bust_cm", "bust_ease_cm", "person_sha256"])
    train, val, test, split_info = grouped_split(df)
    # B0 heuristic: predicted garment bust = body bust + median train ease
    median_ease = float(train["bust_ease_cm"].median())
    b0_test = test["body_bust_cm"] + median_ease
    # B1: least squares garment_bust ~ body_bust + body_waist + body_hips + body_height
    feats = ["body_bust_cm", "body_waist_cm", "body_hips_cm", "body_height_cm"]
    Xtr = np.column_stack([train[feats].to_numpy(dtype=float), np.ones(len(train))])
    ytr = train["garment_bust_cm"].to_numpy(dtype=float)
    coef, *_ = np.linalg.lstsq(Xtr, ytr, rcond=None)
    Xte = np.column_stack([test[feats].to_numpy(dtype=float), np.ones(len(test))])
    b1_test = Xte @ coef
    yte = test["garment_bust_cm"].to_numpy(dtype=float)
    payload = {
        "task": "observational_forward_prediction_of_garment_bust_cm",
        "warning": "This is NOT a controlled intervention. Images are not local. Do not treat as correction ground truth.",
        "n_rows_usable": int(len(df)),
        "split": split_info,
        "split_unit": "person_sha256",
        "B0": {
            "rule": "garment_bust = body_bust + median_train_ease",
            "median_train_ease_cm": median_ease,
            "test_rmse_cm": rmse(yte, b0_test),
            "test_mae_cm": mae(yte, b0_test),
        },
        "B1": {
            "rule": "OLS garment_bust ~ body_bust + body_waist + body_hips + body_height",
            "coef": {name: float(c) for name, c in zip(feats + ["intercept"], coef)},
            "test_rmse_cm": rmse(yte, b1_test),
            "test_mae_cm": mae(yte, b1_test),
        },
        "B2_vision": {"status": "NOT_RUN", "reason": "fit_clean image binaries are not on disk; only path refs to FIT-100K"},
        "B3_multimodal": {"status": "NOT_RUN", "reason": "no local images; not justified to download FIT-100K"},
        "intervention_regret": "NOT_RUN",
        "simulation_verified_first_pass_correction_rate": "NOT_RUN",
        "n_train": int(len(train)),
        "n_val": int(len(val)),
        "n_test": int(len(test)),
    }
    (OUT / "observational_baselines.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
