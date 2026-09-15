#!/usr/bin/env python3
"""Physics/measurement-verified RLVR on the cached decision lattice.

The environment is a lookup table of measured (s, a) -> utility. Rewards are
not invented: they are the CHEST_CASE utility of measured outcomes.

RLVR runs only as a residual-gap optimizer. If Decision SFT already matches the
oracle on the train states, the report records NOT_JUSTIFIED for extra gain,
but a short REINFORCE run is still executed so the task is complete.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "train"))

from fitground.training.geometry import grouped_state_split  # noqa: E402
from fitground.training.metrics import accuracy  # noqa: E402
from io_utils import write_json  # noqa: E402
from device import probe_torch, torch_device  # noqa: E402


def case_x(case: dict) -> np.ndarray:
    return np.array(
        [
            case["body_bust_cm"],
            case["garment_bust_cm"],
            case["target_garment_bust_cm"],
            case.get("garment_length_cm") or 0.0,
            case.get("garment_sleeve_cm") or 0.0,
            case["target_garment_bust_cm"] - case["garment_bust_cm"],
        ],
        dtype=np.float32,
    )


def evaluate_policy(model, mu, sd, cases, vocab, device):
    import torch

    index = {float(v): i for i, v in enumerate(vocab)}
    xs = torch.tensor(np.stack([case_x(c) for c in cases]), dtype=torch.float32)
    with torch.no_grad():
        logits = model(((xs - mu) / sd).to(device))
        pred = logits.argmax(-1).cpu().numpy()
    y = np.array([index[float(c["oracle_intended_delta_cm"])] for c in cases])
    regrets = []
    for case, p in zip(cases, pred):
        intended = vocab[int(p)]
        cand = {float(c["intended_delta_cm"]): c["utility"] for c in case["candidates"]}
        regrets.append(case["oracle_utility"] - cand[float(intended)])
    return {
        "accuracy": accuracy(y, pred),
        "mean_utility_regret": float(np.mean(regrets)) if regrets else 0.0,
        "n": len(cases),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=ROOT / "artifacts" / "training" / "decision_cases.json")
    parser.add_argument("--sft", type=Path, default=ROOT / "artifacts" / "training" / "decision_sft.json")
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    sft = json.loads(args.sft.read_text(encoding="utf-8")) if args.sft.exists() else {}
    assignment = grouped_state_split([c["state_id"] for c in cases], seed=args.seed)
    train = [c for c in cases if assignment[c["state_id"]] == "train"]
    test = [c for c in cases if assignment[c["state_id"]] == "test"]
    vocab = sorted({float(c["intended_delta_cm"]) for case in cases for c in case["candidates"]})
    sft_acc = (sft.get("mlp") or {}).get("test_action_accuracy")
    sft_regret = (sft.get("mlp") or {}).get("test_mean_utility_regret")
    residual = None
    if sft_regret is not None:
        residual = float(sft_regret)
    justified = residual is not None and residual > 1e-6
    info = probe_torch()
    payload = {
        "task": "physics_verified_rlvr",
        "reward_source": "cached_measured_lattice_utility",
        "sft_test_action_accuracy": sft_acc,
        "sft_test_mean_utility_regret": sft_regret,
        "residual_gap_present": justified,
        "justification": (
            "Decision SFT still has positive utility regret on held-out states; REINFORCE uses measured utilities."
            if justified
            else "Decision SFT already matches oracle utility on the reported split; RLVR is run for completeness, not because a large residual gap remains."
        ),
        "torch": info,
    }
    if not info["torch_imported"]:
        payload["status"] = "FAILED"
        payload["error"] = info["error"]
        write_json(ROOT / "artifacts" / "training" / "rlvr.json", payload)
        print(json.dumps(payload, indent=2))
        return 1

    import torch
    import torch.nn as nn

    device = torch_device()
    torch.manual_seed(args.seed)
    xtr = torch.tensor(np.stack([case_x(c) for c in train]), dtype=torch.float32)
    mu, sd = xtr.mean(0), xtr.std(0).clamp_min(1e-6)
    model = nn.Sequential(nn.Linear(6, 64), nn.ReLU(), nn.Linear(64, 64), nn.ReLU(), nn.Linear(64, len(vocab))).to(device)
    # warm start from SFT checkpoint when shapes match
    ckpt_path = ROOT / "artifacts" / "training" / "checkpoints" / "decision_mlp.pt"
    if ckpt_path.exists():
        try:
            blob = torch.load(ckpt_path, map_location=device, weights_only=False)
            model.load_state_dict(blob["state_dict"])
            mu = blob["mu"]
            sd = blob["sd"]
            payload["warm_start"] = str(ckpt_path)
        except Exception as exc:
            payload["warm_start_error"] = f"{type(exc).__name__}: {exc}"
    opt = torch.optim.Adam(model.parameters(), lr=5e-4)
    history = []
    t0 = time.time()
    before = evaluate_policy(model, mu, sd, test, vocab, device)
    rng = np.random.default_rng(args.seed)
    for step in range(args.steps):
        case = train[int(rng.integers(0, len(train)))]
        x = torch.tensor(case_x(case), dtype=torch.float32)
        logits = model(((x - mu) / sd).to(device))
        dist = torch.distributions.Categorical(logits=logits)
        action = dist.sample()
        intended = vocab[int(action.item())]
        cand = {float(c["intended_delta_cm"]): c["utility"] for c in case["candidates"]}
        reward = float(cand[float(intended)])
        # baseline = mean candidate utility so reward is a regret-like advantage
        baseline = float(np.mean(list(cand.values())))
        advantage = reward - baseline
        loss = -(dist.log_prob(action) * advantage)
        opt.zero_grad()
        loss.backward()
        opt.step()
        history.append({"step": step, "reward": reward, "advantage": advantage, "loss": float(loss.item())})
    after = evaluate_policy(model, mu, sd, test, vocab, device)
    ckpt = ROOT / "artifacts" / "training" / "checkpoints" / "rlvr_policy.pt"
    torch.save({"state_dict": model.state_dict(), "mu": mu, "sd": sd, "vocab": vocab, "seed": args.seed}, ckpt)
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        rewards = [h["reward"] for h in history]
        if rewards:
            kernel = 20
            smooth = np.convolve(rewards, np.ones(kernel) / kernel, mode="valid")
            plt.figure(figsize=(6, 4))
            plt.plot(smooth)
            plt.xlabel("step")
            plt.ylabel(f"reward (moving avg {kernel})")
            plt.title("RLVR REINFORCE measured utility")
            plt.tight_layout()
            fig = ROOT / "reports" / "figures" / "rlvr_reward.png"
            fig.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(fig, dpi=140)
            plt.close()
            payload["reward_curve"] = str(fig)
    except Exception:
        pass
    payload.update(
        {
            "status": "PASS",
            "algorithm": "REINFORCE_on_cached_measured_utilities",
            "steps": args.steps,
            "seed": args.seed,
            "device": str(device),
            "n_train_cases": len(train),
            "n_test_cases": len(test),
            "before_test": before,
            "after_test": after,
            "regret_delta": after["mean_utility_regret"] - before["mean_utility_regret"],
            "checkpoint": str(ckpt),
            "history_tail": history[-10:],
            "runtime_s": time.time() - t0,
            "note": "Verifier is the measured lattice, not live Warp during the RL loop. No fabricated rewards.",
        }
    )
    if justified:
        payload["matrix_status"] = "PASS" if after["mean_utility_regret"] <= before["mean_utility_regret"] + 1e-9 else "PARTIAL"
    else:
        payload["matrix_status"] = "COMPLETED_NOT_JUSTIFIED"
    write_json(ROOT / "artifacts" / "training" / "rlvr.json", payload)
    slim = {k: v for k, v in payload.items() if k != "history_tail"}
    print(json.dumps(slim, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
