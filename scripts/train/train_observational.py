#!/usr/bin/env python3
"""B0–B3 baselines.

B0/B1 run on FIT-Clean measurements (observational, not intervention GT).
B2/B3 cannot use FIT-100K images (not on disk). They train on generated
GarmentCode pattern PNGs with measured centimetre labels.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "train"))

from fitground.training.geometry import grouped_state_split  # noqa: E402
from fitground.training.metrics import mae, rmse  # noqa: E402
from io_utils import read_jsonl, write_json  # noqa: E402
from device import probe_torch, torch_device  # noqa: E402


def grouped_split_df(df, seed: int = 0):
    rng = np.random.default_rng(seed)
    people = df["person_sha256"].dropna().unique()
    rng.shuffle(people)
    n = len(people)
    n_train = int(0.7 * n)
    n_val = int(0.15 * n)
    train_p = set(people[:n_train])
    val_p = set(people[n_train : n_train + n_val])
    test_p = set(people[n_train + n_val :])
    return (
        df[df["person_sha256"].isin(train_p)].copy(),
        df[df["person_sha256"].isin(val_p)].copy(),
        df[df["person_sha256"].isin(test_p)].copy(),
        {
            "n_people": int(n),
            "n_train_people": len(train_p),
            "n_val_people": len(val_p),
            "n_test_people": len(test_p),
        },
    )


def load_png_array(path: str, size: int = 128) -> np.ndarray:
    img = Image.open(path).convert("L").resize((size, size))
    return np.asarray(img, dtype=np.float32) / 255.0


def train_b0_b1(parquet: Path, seed: int = 0) -> dict:
    import pandas as pd

    df = pd.read_parquet(parquet)
    df = df[df["usable_for_fitground"] == True].copy()  # noqa: E712
    df = df.dropna(subset=["body_bust_cm", "garment_bust_cm", "bust_ease_cm", "person_sha256"])
    train, val, test, split_info = grouped_split_df(df, seed=seed)
    median_ease = float(train["bust_ease_cm"].median())
    yte = test["garment_bust_cm"].to_numpy(dtype=float)
    b0_test = test["body_bust_cm"].to_numpy(dtype=float) + median_ease
    feats = ["body_bust_cm", "body_waist_cm", "body_hips_cm", "body_height_cm"]
    Xtr = np.column_stack([train[feats].to_numpy(dtype=float), np.ones(len(train))])
    ytr = train["garment_bust_cm"].to_numpy(dtype=float)
    coef, *_ = np.linalg.lstsq(Xtr, ytr, rcond=None)
    Xte = np.column_stack([test[feats].to_numpy(dtype=float), np.ones(len(test))])
    b1_ols = Xte @ coef
    payload: dict = {
        "task": "observational_forward_prediction_of_garment_bust_cm",
        "warning": "FIT-Clean B0/B1 are NOT a controlled intervention and are not correction ground truth.",
        "n_rows_usable": int(len(df)),
        "split": split_info,
        "split_unit": "person_sha256",
        "n_train": int(len(train)),
        "n_val": int(len(val)),
        "n_test": int(len(test)),
        "B0": {
            "rule": "garment_bust = body_bust + median_train_ease",
            "median_train_ease_cm": median_ease,
            "test_rmse_cm": rmse(yte, b0_test),
            "test_mae_cm": mae(yte, b0_test),
        },
        "B1": {
            "rule": "OLS garment_bust ~ body_bust + body_waist + body_hips + body_height",
            "coef": {name: float(c) for name, c in zip(feats + ["intercept"], coef)},
            "test_rmse_cm": rmse(yte, b1_ols),
            "test_mae_cm": mae(yte, b1_ols),
        },
    }
    try:
        from sklearn.linear_model import Ridge
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler

        ridge = make_pipeline(StandardScaler(), Ridge(alpha=1.0, random_state=seed))
        ridge.fit(train[feats], ytr)
        pred = ridge.predict(test[feats])
        payload["B1_ridge"] = {
            "rule": "Ridge(alpha=1) on standardized body measurements",
            "test_rmse_cm": rmse(yte, pred),
            "test_mae_cm": mae(yte, pred),
        }
    except Exception as exc:
        payload["B1_ridge"] = {"status": "FAILED", "error": f"{type(exc).__name__}: {exc}"}
    try:
        from xgboost import XGBRegressor

        model = XGBRegressor(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.08,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=seed,
            n_jobs=4,
            tree_method="hist",
        )
        model.fit(train[feats], ytr, eval_set=[(val[feats], val["garment_bust_cm"])], verbose=False)
        pred = model.predict(test[feats])
        payload["B1_xgboost"] = {
            "rule": "XGBRegressor on body bust/waist/hips/height",
            "n_estimators": 200,
            "test_rmse_cm": rmse(yte, pred),
            "test_mae_cm": mae(yte, pred),
        }
    except Exception as exc:
        payload["B1_xgboost"] = {"status": "FAILED", "error": f"{type(exc).__name__}: {exc}"}
    payload["B2_fit100k"] = {
        "status": "NOT_RUN",
        "reason": "fit_clean image binaries are not on disk; FIT-100K was not downloaded",
    }
    payload["B3_fit100k"] = {
        "status": "NOT_RUN",
        "reason": "no local FIT-100K images",
    }
    return payload


def _split_vision(rows: list[dict], seed: int = 0):
    assignment = grouped_state_split([r["state_id"] for r in rows], seed=seed)
    buckets = {"train": [], "val": [], "test": []}
    for row in rows:
        buckets[assignment[row["state_id"]]].append(row)
    return buckets, assignment


def train_b2_pixel_ridge(rows: list[dict], seed: int = 0) -> dict:
    buckets, _ = _split_vision(rows, seed=seed)
    def pack(split_rows):
        x = np.stack([load_png_array(r["png"]).reshape(-1) for r in split_rows])
        y = np.array([r["garment_bust_cm"] for r in split_rows], dtype=float)
        return x, y

    xtr, ytr = pack(buckets["train"])
    xte, yte = pack(buckets["test"])
    from sklearn.linear_model import Ridge
    from sklearn.decomposition import PCA
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    model = make_pipeline(
        StandardScaler(with_mean=True),
        PCA(n_components=min(64, len(xtr) - 1, xtr.shape[1])),
        Ridge(alpha=10.0),
    )
    model.fit(xtr, ytr)
    pred = model.predict(xte)
    return {
        "status": "PASS",
        "dataset": "generated_garmentcode_pattern_png",
        "not_fit100k": True,
        "model": "StandardScaler+PCA+Ridge",
        "n_train": len(buckets["train"]),
        "n_val": len(buckets["val"]),
        "n_test": len(buckets["test"]),
        "test_rmse_cm": rmse(yte, pred),
        "test_mae_cm": mae(yte, pred),
        "target": "garment_bust_cm",
    }


def train_b2_cnn(rows: list[dict], epochs: int = 40, seed: int = 0) -> dict:
    torch_info = probe_torch()
    if not torch_info["torch_imported"]:
        return {"status": "FAILED", "reason": torch_info["error"], "torch": torch_info}
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, Dataset

    class PngSet(Dataset):
        def __init__(self, items, with_body=False):
            self.items = items
            self.with_body = with_body

        def __len__(self):
            return len(self.items)

        def __getitem__(self, idx):
            row = self.items[idx]
            x = torch.from_numpy(load_png_array(row["png"])[None, ...])
            y = torch.tensor(row["garment_bust_cm"], dtype=torch.float32)
            body = torch.tensor(
                [
                    row["body_bust_cm"] or 0.0,
                    row.get("body_waist_cm") or 0.0,
                    row.get("body_shoulder_w_cm") or 0.0,
                ],
                dtype=torch.float32,
            )
            return x, body, y

    class CNN(nn.Module):
        def __init__(self, multimodal: bool):
            super().__init__()
            self.features = nn.Sequential(
                nn.Conv2d(1, 16, 3, padding=1),
                nn.ReLU(),
                nn.MaxPool2d(2),
                nn.Conv2d(16, 32, 3, padding=1),
                nn.ReLU(),
                nn.MaxPool2d(2),
                nn.Conv2d(32, 64, 3, padding=1),
                nn.ReLU(),
                nn.AdaptiveAvgPool2d(4),
            )
            self.multimodal = multimodal
            in_dim = 64 * 16 + (3 if multimodal else 0)
            self.head = nn.Sequential(nn.Linear(in_dim, 64), nn.ReLU(), nn.Linear(64, 1))

        def forward(self, x, body):
            h = self.features(x).reshape(x.size(0), -1)
            if self.multimodal:
                h = torch.cat([h, body], dim=1)
            return self.head(h).squeeze(-1)

    def run(multimodal: bool) -> dict:
        buckets, _ = _split_vision(rows, seed=seed)
        device = torch_device()
        torch.manual_seed(seed)
        model = CNN(multimodal=multimodal).to(device)
        opt = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
        loss_fn = nn.MSELoss()
        train_loader = DataLoader(PngSet(buckets["train"]), batch_size=16, shuffle=True)
        history = []
        t0 = time.time()
        peak_mem = 0
        for epoch in range(epochs):
            model.train()
            losses = []
            for x, body, y in train_loader:
                x, body, y = x.to(device), body.to(device), y.to(device)
                opt.zero_grad()
                pred = model(x, body)
                loss = loss_fn(pred, y)
                loss.backward()
                opt.step()
                losses.append(float(loss.item()))
            history.append({"epoch": epoch, "train_mse": float(np.mean(losses))})
            if device.type == "cuda":
                peak_mem = max(peak_mem, int(torch.cuda.max_memory_allocated()))
        model.eval()
        with torch.no_grad():
            xt = torch.stack([torch.from_numpy(load_png_array(r["png"])[None, ...]) for r in buckets["test"]]).to(device)
            bt = torch.stack(
                [
                    torch.tensor(
                        [r["body_bust_cm"] or 0.0, r.get("body_waist_cm") or 0.0, r.get("body_shoulder_w_cm") or 0.0],
                        dtype=torch.float32,
                    )
                    for r in buckets["test"]
                ]
            ).to(device)
            pred = model(xt, bt).cpu().numpy()
        yte = np.array([r["garment_bust_cm"] for r in buckets["test"]], dtype=float)
        ckpt = ROOT / "artifacts" / "training" / "checkpoints" / ("b3_cnn.pt" if multimodal else "b2_cnn.pt")
        ckpt.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"state_dict": model.state_dict(), "multimodal": multimodal, "seed": seed}, ckpt)
        return {
            "status": "PASS",
            "dataset": "generated_garmentcode_pattern_png",
            "not_fit100k": True,
            "model": "SmallCNN+body" if multimodal else "SmallCNN",
            "epochs": epochs,
            "batch_size": 16,
            "seed": seed,
            "device": str(device),
            "torch": torch_info,
            "n_train": len(buckets["train"]),
            "n_val": len(buckets["val"]),
            "n_test": len(buckets["test"]),
            "test_rmse_cm": rmse(yte, pred),
            "test_mae_cm": mae(yte, pred),
            "final_train_mse": history[-1]["train_mse"] if history else None,
            "peak_cuda_bytes": peak_mem,
            "checkpoint": str(ckpt),
            "history_tail": history[-5:],
            "runtime_s": time.time() - t0,
        }

    return run(False), run(True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parquet", type=Path, default=ROOT / "data" / "processed" / "fit_clean_v0.1.parquet")
    parser.add_argument("--vision-jsonl", type=Path, default=ROOT / "artifacts" / "training" / "vision_pattern_samples.jsonl")
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    out_dir = ROOT / "artifacts" / "training"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = train_b0_b1(args.parquet, seed=args.seed)
    if args.vision_jsonl.exists():
        rows = read_jsonl(args.vision_jsonl)
        try:
            payload["B2_generated_pattern_ridge"] = train_b2_pixel_ridge(rows, seed=args.seed)
        except Exception as exc:
            payload["B2_generated_pattern_ridge"] = {"status": "FAILED", "error": f"{type(exc).__name__}: {exc}"}
        try:
            b2, b3 = train_b2_cnn(rows, epochs=args.epochs, seed=args.seed)
            payload["B2_generated_pattern_cnn"] = b2
            payload["B3_generated_pattern_multimodal"] = b3
        except Exception as exc:
            payload["B2_generated_pattern_cnn"] = {"status": "FAILED", "error": f"{type(exc).__name__}: {exc}"}
            payload["B3_generated_pattern_multimodal"] = {"status": "FAILED", "error": f"{type(exc).__name__}: {exc}"}
    else:
        payload["B2_generated_pattern_ridge"] = {"status": "NOT_RUN", "reason": f"missing {args.vision_jsonl}"}
        payload["B2_generated_pattern_cnn"] = {"status": "NOT_RUN", "reason": f"missing {args.vision_jsonl}"}
        payload["B3_generated_pattern_multimodal"] = {"status": "NOT_RUN", "reason": f"missing {args.vision_jsonl}"}
    write_json(out_dir / "observational_and_vision_baselines.json", payload)
    # keep the original artifact path in sync for B0/B1
    legacy = {
        k: payload[k]
        for k in (
            "task",
            "warning",
            "n_rows_usable",
            "split",
            "split_unit",
            "B0",
            "B1",
            "n_train",
            "n_val",
            "n_test",
        )
        if k in payload
    }
    legacy["B2_vision"] = payload.get("B2_fit100k")
    legacy["B3_multimodal"] = payload.get("B3_fit100k")
    legacy["B1_ridge"] = payload.get("B1_ridge")
    legacy["B1_xgboost"] = payload.get("B1_xgboost")
    legacy["B2_generated_pattern_cnn"] = payload.get("B2_generated_pattern_cnn")
    legacy["B3_generated_pattern_multimodal"] = payload.get("B3_generated_pattern_multimodal")
    write_json(ROOT / "artifacts" / "observational_baselines" / "observational_baselines.json", legacy)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
