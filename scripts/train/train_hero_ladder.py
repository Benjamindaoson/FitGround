#!/usr/bin/env python3
"""Baseline ladder + OOD + failure-aware selector on the hero lattice."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from fitground.training.geometry import grouped_state_split  # noqa: E402
from fitground.training.metrics import accuracy, mae, rmse  # noqa: E402

HERO = ROOT / "artifacts" / "hero"


def load_jsonl(path: Path):
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def bootstrap_mae(y, yhat, seed=0, n=400):
    y = np.asarray(y, dtype=float)
    yhat = np.asarray(yhat, dtype=float)
    rng = np.random.default_rng(seed)
    stats = []
    for _ in range(n):
        idx = rng.integers(0, len(y), size=len(y))
        stats.append(mae(y[idx], yhat[idx]))
    stats = np.array(stats)
    return {"mae": mae(y, yhat), "mae_lo": float(np.percentile(stats, 2.5)), "mae_hi": float(np.percentile(stats, 97.5)), "n": int(len(y))}


def main() -> int:
    trans = load_jsonl(HERO / "correction_lattice_v0.2.jsonl")
    decisions = json.loads((HERO / "decision_cases.json").read_text()) if (HERO / "decision_cases.json").exists() else []
    if not trans:
        print("missing lattice")
        return 1
    assignment = grouped_state_split([r["state_id"] for r in trans], seed=0)
    def split(rows):
        buckets = {"train": [], "val": [], "test": []}
        for r in rows:
            buckets[assignment.get(r["state_id"], "train")].append(r)
        return buckets

    bust = [r for r in trans if r["action_family"] == "bust_circumference_delta_cm" and r.get("realized_delta_cm") is not None]
    buckets = split(bust)
    # B0 identity: predicted realized = intended
    ident = bootstrap_mae([r["realized_delta_cm"] for r in buckets["test"]], [r["intended_delta_cm"] for r in buckets["test"]])
    ident["model"] = "analytic_inverse_map"
    # B1 OLS: intended + body_bust
    Xtr = np.column_stack([[r["intended_delta_cm"] for r in buckets["train"]], [r["body_bust_cm"] for r in buckets["train"]], np.ones(len(buckets["train"]))])
    ytr = np.array([r["realized_delta_cm"] for r in buckets["train"]], float)
    coef, *_ = np.linalg.lstsq(Xtr, ytr, rcond=None)
    Xte = np.column_stack([[r["intended_delta_cm"] for r in buckets["test"]], [r["body_bust_cm"] for r in buckets["test"]], np.ones(len(buckets["test"]))])
    ols = bootstrap_mae([r["realized_delta_cm"] for r in buckets["test"]], Xte @ coef)
    ols["model"] = "OLS"
    # OOD: train mean_all, test other bodies
    tr = [r for r in bust if r["body_name"] == "mean_all"]
    te = [r for r in bust if r["body_name"] != "mean_all"]
    ood = None
    if tr and te:
        ood = bootstrap_mae([r["realized_delta_cm"] for r in te], [r["intended_delta_cm"] for r in te])
        ood["model"] = "identity_on_unseen_bodies"
        ood["n_train_iid"] = len(tr)
        ood["n_test_ood"] = len(te)

    # Decision: identity intended == target ease
    dec_assign = grouped_state_split([d["state_id"] for d in decisions], seed=0) if decisions else {}
    test_dec = [d for d in decisions if dec_assign.get(d["state_id"]) == "test"] or decisions[-max(1, len(decisions)//5):]
    pred = []
    y = []
    abstain = []
    for d in test_dec:
        target_ease = d["target_garment_bust_cm"] - d["garment_bust_cm"]
        # analytic: pick intended closest to target ease
        cands = d["candidates"]
        pick = min(cands, key=lambda c: abs(c["intended_delta_cm"] - target_ease))
        pred.append(pick["intended_delta_cm"])
        y.append(d["oracle_intended_delta_cm"])
        # failure-aware: abstain if body not mean_all in a mean_all-only policy
        abstain.append(d.get("split_body") not in ("mean_all",))
    acc = accuracy(y, pred)
    payload = {
        "transition_identity": ident,
        "transition_ols": ols,
        "ood_unseen_body_identity": ood,
        "decision_analytic_accuracy": acc,
        "n_decision_test": len(test_dec),
        "failure_aware": {
            "rule": "escalate if body_name unseen vs mean_all support",
            "abstain_rate_on_test": float(np.mean(abstain)) if abstain else None,
        },
        "note": "On calibrated bust, analytic inverse MAE is ~0. Learned models are not expected to win this regime.",
    }
    (HERO / "baseline_ladder.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
