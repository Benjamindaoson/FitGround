#!/usr/bin/env python3
"""Transition SFT: (s, a) -> s' on measured lattice rows.

Trains a tabular MLP (primary) and a tiny causal LM (secondary). Neither is a
foundation MLLM. Realized targets come from panel geometry, not intended_delta.
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

from fitground.training.geometry import grouped_state_split, assert_realized_not_copied  # noqa: E402
from fitground.training.metrics import mae, rmse  # noqa: E402
from fitground.training.textfmt import format_transition_example, parse_generated_fields  # noqa: E402
from io_utils import read_jsonl, write_json  # noqa: E402
from device import probe_torch, torch_device  # noqa: E402

FAMILIES = (
    "bust_circumference_delta_cm",
    "sleeve_length_delta_cm",
    "shirt_length_delta_cm",
)


def features(row: dict) -> np.ndarray:
    before = row["garment_measurement_before"]
    fam = [1.0 if row["action_family"] == f else 0.0 for f in FAMILIES]
    return np.array(
        [
            row["body_bust_cm"] or 0.0,
            before.get("bust_circumference_cm") or 0.0,
            before.get("waist_cm") or 0.0,
            before.get("length_cm") or 0.0,
            before.get("sleeve_length_cm") or 0.0,
            row["intended_delta_cm"],
            *fam,
        ],
        dtype=np.float32,
    )


def targets(row: dict) -> np.ndarray:
    after = row["garment_measurement_after"]
    return np.array(
        [
            row["realized_delta_cm"],
            after.get("bust_circumference_cm") or 0.0,
            after.get("waist_cm") or 0.0,
            after.get("length_cm") or 0.0,
            after.get("sleeve_length_cm") or 0.0,
        ],
        dtype=np.float32,
    )


def split_rows(rows: list[dict], seed: int = 0):
    assignment = grouped_state_split([r["state_id"] for r in rows], seed=seed)
    buckets = {"train": [], "val": [], "test": []}
    for row in rows:
        buckets[assignment[row["state_id"]]].append(row)
    return buckets


def train_mlp(buckets: dict, epochs: int, seed: int) -> dict:
    info = probe_torch()
    if not info["torch_imported"]:
        return {"status": "FAILED", "reason": info["error"], "torch": info}
    import torch
    import torch.nn as nn

    device = torch_device()
    torch.manual_seed(seed)
    xtr = torch.tensor(np.stack([features(r) for r in buckets["train"]]), dtype=torch.float32)
    ytr = torch.tensor(np.stack([targets(r) for r in buckets["train"]]), dtype=torch.float32)
    xva = torch.tensor(np.stack([features(r) for r in buckets["val"]]), dtype=torch.float32) if buckets["val"] else xtr[:1]
    yva = torch.tensor(np.stack([targets(r) for r in buckets["val"]]), dtype=torch.float32) if buckets["val"] else ytr[:1]
    xte = torch.tensor(np.stack([features(r) for r in buckets["test"]]), dtype=torch.float32)
    yte = torch.tensor(np.stack([targets(r) for r in buckets["test"]]), dtype=torch.float32)
    mu = xtr.mean(0)
    sd = xtr.std(0).clamp_min(1e-6)
    model = nn.Sequential(
        nn.Linear(xtr.shape[1], 64),
        nn.ReLU(),
        nn.Linear(64, 64),
        nn.ReLU(),
        nn.Linear(64, ytr.shape[1]),
    ).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=2e-3, weight_decay=1e-4)
    loss_fn = nn.MSELoss()
    history = []
    t0 = time.time()
    peak = 0
    xtr_n = ((xtr - mu) / sd).to(device)
    ytr_d = ytr.to(device)
    xva_n = ((xva - mu) / sd).to(device)
    yva_d = yva.to(device)
    for epoch in range(epochs):
        model.train()
        opt.zero_grad()
        pred = model(xtr_n)
        loss = loss_fn(pred, ytr_d)
        loss.backward()
        opt.step()
        model.eval()
        with torch.no_grad():
            vloss = float(loss_fn(model(xva_n), yva_d).item())
        history.append({"epoch": epoch, "train_mse": float(loss.item()), "val_mse": vloss})
        if device.type == "cuda":
            peak = max(peak, int(torch.cuda.max_memory_allocated()))
    model.eval()
    with torch.no_grad():
        pred = model(((xte - mu) / sd).to(device)).cpu().numpy()
    ynp = yte.numpy()
    ckpt = ROOT / "artifacts" / "training" / "checkpoints" / "transition_mlp.pt"
    ckpt.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "mu": mu, "sd": sd, "seed": seed}, ckpt)
    names = ["realized_delta_cm", "after_bust_cm", "after_waist_cm", "after_length_cm", "after_sleeve_cm"]
    per = {name: {"test_mae": mae(ynp[:, i], pred[:, i]), "test_rmse": rmse(ynp[:, i], pred[:, i])} for i, name in enumerate(names)}
    return {
        "status": "PASS",
        "model": "MLP_64x64",
        "epochs": epochs,
        "seed": seed,
        "device": str(device),
        "torch": info,
        "n_train": len(buckets["train"]),
        "n_val": len(buckets["val"]),
        "n_test": len(buckets["test"]),
        "metrics": per,
        "test_realized_mae_cm": per["realized_delta_cm"]["test_mae"],
        "test_realized_rmse_cm": per["realized_delta_cm"]["test_rmse"],
        "identity_cheat_mae_cm": mae(ynp[:, 0], np.array([r["intended_delta_cm"] for r in buckets["test"]], dtype=float)),
        "peak_cuda_bytes": peak,
        "checkpoint": str(ckpt),
        "history": history,
        "runtime_s": time.time() - t0,
        "note": "identity_cheat_mae_cm is intended_delta vs realized on the test split; not a trained model.",
    }


class Vocab:
    def __init__(self, texts: list[str]):
        chars = sorted(set("".join(texts)))
        self.stoi = {c: i + 1 for i, c in enumerate(chars)}
        self.stoi["<pad>"] = 0
        self.itos = {i: c for c, i in self.stoi.items()}

    def encode(self, text: str) -> list[int]:
        return [self.stoi.get(c, 0) for c in text]

    def decode(self, ids: list[int]) -> str:
        return "".join(self.itos.get(i, "") for i in ids if i != 0)

    def __len__(self):
        return len(self.stoi)


def train_tiny_lm(buckets: dict, epochs: int, seed: int) -> dict:
    info = probe_torch()
    if not info["torch_imported"]:
        return {"status": "FAILED", "reason": info["error"], "torch": info}
    import torch
    import torch.nn as nn

    device = torch_device()
    torch.manual_seed(seed)
    texts = [format_transition_example(r, include_target=True) for r in buckets["train"] + buckets["val"] + buckets["test"]]
    vocab = Vocab(texts)
    max_len = min(256, max(len(t) for t in texts) + 2)

    class CharLM(nn.Module):
        def __init__(self):
            super().__init__()
            d = 128
            self.emb = nn.Embedding(len(vocab), d, padding_idx=0)
            self.pos = nn.Embedding(max_len, d)
            layer = nn.TransformerEncoderLayer(d_model=d, nhead=4, dim_feedforward=256, batch_first=True, dropout=0.1)
            self.enc = nn.TransformerEncoder(layer, num_layers=4)
            self.head = nn.Linear(d, len(vocab))

        def forward(self, idx):
            b, t = idx.shape
            pos = torch.arange(t, device=idx.device)
            x = self.emb(idx) + self.pos(pos)[None, :, :]
            mask = torch.triu(torch.ones(t, t, device=idx.device) * float("-inf"), diagonal=1)
            pad = idx.eq(0)
            h = self.enc(x, mask=mask, src_key_padding_mask=pad)
            return self.head(h)

    def pack(rows):
        seqs = []
        for row in rows:
            ids = vocab.encode(format_transition_example(row, include_target=True))[: max_len - 1]
            seqs.append(ids)
        arr = np.zeros((len(seqs), max_len), dtype=np.int64)
        for i, ids in enumerate(seqs):
            arr[i, : len(ids)] = ids
        return torch.tensor(arr)

    model = CharLM().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=3e-4)
    xtr = pack(buckets["train"]).to(device)
    history = []
    t0 = time.time()
    peak = 0
    nparams = sum(p.numel() for p in model.parameters())
    for epoch in range(epochs):
        model.train()
        opt.zero_grad()
        logits = model(xtr[:, :-1])
        loss = nn.functional.cross_entropy(
            logits.reshape(-1, logits.size(-1)),
            xtr[:, 1:].reshape(-1),
            ignore_index=0,
        )
        loss.backward()
        opt.step()
        history.append({"epoch": epoch, "train_ce": float(loss.item())})
        if device.type == "cuda":
            peak = max(peak, int(torch.cuda.max_memory_allocated()))

    def generate(prompt: str, max_new: int = 80) -> str:
        model.eval()
        ids = vocab.encode(prompt)[: max_len - 1]
        cur = torch.tensor([ids], device=device)
        with torch.no_grad():
            for _ in range(max_new):
                if cur.size(1) >= max_len:
                    break
                logits = model(cur)[:, -1, :]
                nxt = int(torch.argmax(logits, dim=-1).item())
                if nxt == 0:
                    break
                cur = torch.cat([cur, torch.tensor([[nxt]], device=device)], dim=1)
                if vocab.itos.get(nxt) == " " and cur.size(1) > len(ids) + 8:
                    # keep going; stop if we have REALIZED and AFTER_SLEEVE
                    text = vocab.decode(cur[0].tolist())
                    if "AFTER_SLEEVE=" in text:
                        break
        return vocab.decode(cur[0].tolist())

    parsed = 0
    abs_err = []
    examples = []
    for row in buckets["test"]:
        prompt = format_transition_example(row, include_target=False)
        text = generate(prompt)
        fields = parse_generated_fields(text)
        ok = "REALIZED" in fields
        parsed += int(ok)
        rec = {"prompt": prompt, "generated": text[len(prompt) :], "parsed": fields}
        if ok:
            try:
                pred_r = float(fields["REALIZED"])
                abs_err.append(abs(pred_r - float(row["realized_delta_cm"])))
                rec["realized_abs_err"] = abs_err[-1]
            except ValueError:
                pass
        examples.append(rec)
    ckpt = ROOT / "artifacts" / "training" / "checkpoints" / "transition_tiny_lm.pt"
    torch.save({"state_dict": model.state_dict(), "stoi": vocab.stoi, "max_len": max_len, "seed": seed}, ckpt)
    return {
        "status": "PASS",
        "model": "tiny_causal_transformer_charlm",
        "n_params": nparams,
        "epochs": epochs,
        "seed": seed,
        "device": str(device),
        "torch": info,
        "n_train": len(buckets["train"]),
        "n_test": len(buckets["test"]),
        "test_parse_rate": parsed / max(1, len(buckets["test"])),
        "test_realized_mae_when_parsed": float(np.mean(abs_err)) if abs_err else None,
        "peak_cuda_bytes": peak,
        "checkpoint": str(ckpt),
        "history_tail": history[-5:],
        "history": history,
        "examples_head": examples[:5],
        "runtime_s": time.time() - t0,
        "note": "From-scratch ~0.5-2M param LM. Not a pretrained MLLM. HuggingFace models were not downloaded.",
    }


def maybe_plot(history: list[dict], path: Path, ykey: str, title: str) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        xs = [h["epoch"] for h in history]
        ys = [h[ykey] for h in history]
        plt.figure(figsize=(6, 4))
        plt.plot(xs, ys)
        plt.xlabel("epoch")
        plt.ylabel(ykey)
        plt.title(title)
        plt.tight_layout()
        path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(path, dpi=140)
        plt.close()
    except Exception:
        return


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lattice", type=Path, default=ROOT / "artifacts" / "training" / "transition_lattice.jsonl")
    parser.add_argument("--mlp-epochs", type=int, default=400)
    parser.add_argument("--lm-epochs", type=int, default=80)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    rows = read_jsonl(args.lattice)
    usable = [r for r in rows if r.get("realized_delta_cm") is not None]
    for row in usable:
        assert_realized_not_copied(row)
    buckets = split_rows(usable, seed=args.seed)
    mlp = train_mlp(buckets, epochs=args.mlp_epochs, seed=args.seed)
    lm = train_tiny_lm(buckets, epochs=args.lm_epochs, seed=args.seed)
    if mlp.get("history"):
        maybe_plot(mlp["history"], ROOT / "reports" / "figures" / "transition_sft_mlp_loss.png", "val_mse", "Transition SFT MLP val MSE")
    if lm.get("history"):
        maybe_plot(lm["history"], ROOT / "reports" / "figures" / "transition_sft_lm_loss.png", "train_ce", "Transition SFT tiny LM CE")
    payload = {
        "task": "transition_sft_s_a_to_s_prime",
        "n_rows": len(usable),
        "split_unit": "state_id",
        "mlp": mlp,
        "tiny_lm": lm,
        "huggingface_foundation_model": "NOT_RUN",
        "huggingface_reason": "No pretrained MLLM downloaded; trained a from-scratch tiny LM plus tabular MLP on measured lattice.",
    }
    write_json(ROOT / "artifacts" / "training" / "transition_sft.json", payload)
    print(json.dumps({k: payload[k] if k != "mlp" else {kk: vv for kk, vv in mlp.items() if kk != "history"} for k in payload}, indent=2, default=str)[:8000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
