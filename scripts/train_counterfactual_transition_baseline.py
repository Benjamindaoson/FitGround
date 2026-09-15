#!/usr/bin/env python3
"""Train a weak-supervision FitGround transition baseline from FIT-Clean pairs.

This is not physics-verified correction training. It converts observed
person-held garment-swap counterfactual pairs into a measurement transition
baseline shaped like (state, candidate_delta) -> next measurement state.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset


STATE_FIELDS = [
    "body_height_cm",
    "body_bust_cm",
    "body_waist_cm",
    "body_hips_cm",
    "garment_bust_cm",
    "garment_length_cm",
    "garment_sleeve_cm",
    "bust_ease_cm",
    "bust_ease_ratio",
]

ACTION_FIELDS = [
    "delta_garment_bust_cm",
    "delta_garment_length_cm",
    "delta_garment_sleeve_cm",
]

TARGET_FIELDS = [
    "next_garment_bust_cm",
    "next_garment_length_cm",
    "next_garment_sleeve_cm",
    "next_bust_ease_cm",
    "next_bust_ease_ratio",
]


def _examples(pairs: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, float]] = []
    for r in pairs.itertuples(index=False):
        base = {
            "body_height_cm": r.anchor_body_height_cm,
            "body_bust_cm": r.anchor_body_bust_cm,
            "body_waist_cm": r.anchor_body_waist_cm,
            "body_hips_cm": r.anchor_body_hips_cm,
            "garment_bust_cm": r.anchor_garment_bust_cm,
            "garment_length_cm": r.anchor_garment_length_cm,
            "garment_sleeve_cm": r.anchor_garment_sleeve_cm,
            "bust_ease_cm": r.anchor_bust_ease_cm,
            "bust_ease_ratio": r.anchor_bust_ease_ratio,
            "delta_garment_bust_cm": r.delta_garment_bust_cm,
            "delta_garment_length_cm": r.delta_garment_length_cm,
            "delta_garment_sleeve_cm": r.delta_garment_sleeve_cm,
            "next_garment_bust_cm": r.counterfactual_garment_bust_cm,
            "next_garment_length_cm": r.counterfactual_garment_length_cm,
            "next_garment_sleeve_cm": r.counterfactual_garment_sleeve_cm,
            "next_bust_ease_cm": r.counterfactual_bust_ease_cm,
            "next_bust_ease_ratio": r.counterfactual_bust_ease_ratio,
        }
        rev = {
            "body_height_cm": r.counterfactual_body_height_cm,
            "body_bust_cm": r.counterfactual_body_bust_cm,
            "body_waist_cm": r.counterfactual_body_waist_cm,
            "body_hips_cm": r.counterfactual_body_hips_cm,
            "garment_bust_cm": r.counterfactual_garment_bust_cm,
            "garment_length_cm": r.counterfactual_garment_length_cm,
            "garment_sleeve_cm": r.counterfactual_garment_sleeve_cm,
            "bust_ease_cm": r.counterfactual_bust_ease_cm,
            "bust_ease_ratio": r.counterfactual_bust_ease_ratio,
            "delta_garment_bust_cm": -r.delta_garment_bust_cm,
            "delta_garment_length_cm": -r.delta_garment_length_cm,
            "delta_garment_sleeve_cm": -r.delta_garment_sleeve_cm,
            "next_garment_bust_cm": r.anchor_garment_bust_cm,
            "next_garment_length_cm": r.anchor_garment_length_cm,
            "next_garment_sleeve_cm": r.anchor_garment_sleeve_cm,
            "next_bust_ease_cm": r.anchor_bust_ease_cm,
            "next_bust_ease_ratio": r.anchor_bust_ease_ratio,
        }
        rows.extend([base, rev])
    out = pd.DataFrame(rows)
    return out.replace([np.inf, -np.inf], np.nan).dropna()


class MLP(nn.Module):
    def __init__(self, in_dim: int, out_dim: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, out_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def _standardize(train: np.ndarray, all_: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean = train.mean(axis=0)
    std = train.std(axis=0)
    std[std < 1e-6] = 1.0
    return (all_ - mean) / std, mean, std


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", type=Path, default=Path("data/processed/counterfactual_candidates_v0.1.parquet"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/training/counterfactual_transition_baseline"))
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    pairs = pd.read_parquet(args.pairs)
    pairs = pairs[(pairs["usable_both"]) & (~pairs["leakage_any"])].copy()
    data = _examples(pairs)

    x_raw = data[STATE_FIELDS + ACTION_FIELDS].to_numpy("float32")
    y_raw = data[TARGET_FIELDS].to_numpy("float32")
    n = len(data)
    if n < 100:
        raise SystemExit(f"not enough examples: {n}")
    rng = np.random.default_rng(args.seed)
    order = rng.permutation(n)
    split = int(n * 0.8)
    train_idx, val_idx = order[:split], order[split:]
    x, x_mean, x_std = _standardize(x_raw[train_idx], x_raw)
    y, y_mean, y_std = _standardize(y_raw[train_idx], y_raw)

    train_ds = TensorDataset(torch.from_numpy(x[train_idx]).float(), torch.from_numpy(y[train_idx]).float())
    val_x = torch.from_numpy(x[val_idx]).float()
    val_y = torch.from_numpy(y[val_idx]).float()
    loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = MLP(x.shape[1], y.shape[1]).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-4)
    loss_fn = nn.MSELoss()
    val_x, val_y = val_x.to(device), val_y.to(device)

    metrics_path = args.output_dir / "metrics.csv"
    with metrics_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["epoch", "train_mse", "val_mse", "val_mae_cm", "device", "elapsed_sec"])
        writer.writeheader()
        start = time.time()
        best = float("inf")
        for epoch in range(1, args.epochs + 1):
            model.train()
            losses = []
            for xb, yb in loader:
                xb, yb = xb.to(device), yb.to(device)
                pred = model(xb)
                loss = loss_fn(pred, yb)
                opt.zero_grad(set_to_none=True)
                loss.backward()
                opt.step()
                losses.append(float(loss.detach().cpu()))
            model.eval()
            with torch.no_grad():
                pred = model(val_x)
                val_mse = float(loss_fn(pred, val_y).cpu())
                pred_raw = pred.cpu().numpy() * y_std + y_mean
                true_raw = val_y.cpu().numpy() * y_std + y_mean
                val_mae_cm = float(np.mean(np.abs(pred_raw[:, :4] - true_raw[:, :4])))
            row = {
                "epoch": epoch,
                "train_mse": float(np.mean(losses)),
                "val_mse": val_mse,
                "val_mae_cm": val_mae_cm,
                "device": str(device),
                "elapsed_sec": round(time.time() - start, 2),
            }
            writer.writerow(row)
            f.flush()
            if epoch == 1 or epoch % 10 == 0:
                print(json.dumps(row), flush=True)
            if val_mse < best:
                best = val_mse
                torch.save(
                    {
                        "model": model.state_dict(),
                        "feature_fields": STATE_FIELDS + ACTION_FIELDS,
                        "target_fields": TARGET_FIELDS,
                        "x_mean": x_mean,
                        "x_std": x_std,
                        "y_mean": y_mean,
                        "y_std": y_std,
                        "epoch": epoch,
                        "val_mse": val_mse,
                        "n_pairs": int(len(pairs)),
                        "n_examples": int(n),
                        "training_label_status": "WEAK_OBSERVATIONAL_NOT_PHYSICS_VERIFIED",
                    },
                    args.output_dir / "best.pt",
                )
    (args.output_dir / "status.json").write_text(
        json.dumps(
            {
                "status": "DONE",
                "task": "counterfactual_transition_baseline",
                "training_label_status": "WEAK_OBSERVATIONAL_NOT_PHYSICS_VERIFIED",
                "device": str(device),
                "n_pairs": int(len(pairs)),
                "n_examples": int(n),
                "best_checkpoint": str(args.output_dir / "best.pt"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
