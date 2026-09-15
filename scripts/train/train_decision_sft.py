#!/usr/bin/env python3
"""Decision SFT: s -> best correction on measured CHEST_CASE-style cases."""
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
from fitground.training.textfmt import format_decision_example, parse_generated_fields  # noqa: E402
from io_utils import write_json  # noqa: E402
from device import probe_torch, torch_device  # noqa: E402


def load_cases(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def action_vocab(cases: list[dict]) -> list[float]:
    intended = sorted({float(c["oracle_intended_delta_cm"]) for c in cases})
    extra = set()
    for case in cases:
        for cand in case.get("candidates") or []:
            extra.add(float(cand["intended_delta_cm"]))
    return sorted(extra or intended)


def split_cases(cases: list[dict], seed: int = 0):
    assignment = grouped_state_split([c["state_id"] for c in cases], seed=seed)
    buckets = {"train": [], "val": [], "test": []}
    for case in cases:
        buckets[assignment[case["state_id"]]].append(case)
    return buckets


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


def train_mlp(buckets, vocab, epochs, seed) -> dict:
    info = probe_torch()
    if not info["torch_imported"]:
        return {"status": "FAILED", "reason": info["error"], "torch": info}
    import torch
    import torch.nn as nn

    device = torch_device()
    torch.manual_seed(seed)
    index = {v: i for i, v in enumerate(vocab)}

    def pack(items):
        x = torch.tensor(np.stack([case_x(c) for c in items]), dtype=torch.float32)
        y = torch.tensor([index[float(c["oracle_intended_delta_cm"])] for c in items], dtype=torch.long)
        return x, y

    xtr, ytr = pack(buckets["train"])
    xte, yte = pack(buckets["test"])
    mu, sd = xtr.mean(0), xtr.std(0).clamp_min(1e-6)
    model = nn.Sequential(nn.Linear(6, 64), nn.ReLU(), nn.Linear(64, 64), nn.ReLU(), nn.Linear(64, len(vocab))).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=2e-3, weight_decay=1e-4)
    history = []
    t0 = time.time()
    peak = 0
    xtr_n = ((xtr - mu) / sd).to(device)
    ytr_d = ytr.to(device)
    for epoch in range(epochs):
        model.train()
        opt.zero_grad()
        loss = nn.functional.cross_entropy(model(xtr_n), ytr_d)
        loss.backward()
        opt.step()
        history.append({"epoch": epoch, "train_ce": float(loss.item())})
        if device.type == "cuda":
            peak = max(peak, int(torch.cuda.max_memory_allocated()))
    model.eval()
    with torch.no_grad():
        pred = model(((xte - mu) / sd).to(device)).argmax(-1).cpu().numpy()
    acc = accuracy(yte.numpy(), pred)
    # regret vs oracle utility
    regrets = []
    for case, p in zip(buckets["test"], pred):
        intended = vocab[int(p)]
        cand = {float(c["intended_delta_cm"]): c["utility"] for c in case["candidates"]}
        regrets.append(case["oracle_utility"] - cand.get(float(intended), case["oracle_utility"] - 10))
    ckpt = ROOT / "artifacts" / "training" / "checkpoints" / "decision_mlp.pt"
    ckpt.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "mu": mu, "sd": sd, "vocab": vocab, "seed": seed}, ckpt)
    return {
        "status": "PASS",
        "model": "MLP_classifier_over_intended_bust_delta",
        "epochs": epochs,
        "seed": seed,
        "device": str(device),
        "torch": info,
        "n_train": len(buckets["train"]),
        "n_val": len(buckets["val"]),
        "n_test": len(buckets["test"]),
        "n_classes": len(vocab),
        "test_action_accuracy": acc,
        "test_mean_utility_regret": float(np.mean(regrets)) if regrets else None,
        "peak_cuda_bytes": peak,
        "checkpoint": str(ckpt),
        "history": history,
        "runtime_s": time.time() - t0,
    }


def train_tiny_lm(buckets, epochs, seed) -> dict:
    info = probe_torch()
    if not info["torch_imported"]:
        return {"status": "FAILED", "reason": info["error"], "torch": info}
    import torch
    import torch.nn as nn

    device = torch_device()
    torch.manual_seed(seed)
    texts = [format_decision_example(c, include_target=True) for c in buckets["train"] + buckets["test"]]
    chars = sorted(set("".join(texts)))
    stoi = {c: i + 1 for i, c in enumerate(chars)}
    stoi["<pad>"] = 0
    itos = {i: c for c, i in stoi.items()}
    max_len = min(192, max(len(t) for t in texts) + 2)

    class CharLM(nn.Module):
        def __init__(self):
            super().__init__()
            d = 96
            self.emb = nn.Embedding(len(stoi), d, padding_idx=0)
            self.pos = nn.Embedding(max_len, d)
            layer = nn.TransformerEncoderLayer(d_model=d, nhead=4, dim_feedforward=192, batch_first=True, dropout=0.1)
            self.enc = nn.TransformerEncoder(layer, num_layers=3)
            self.head = nn.Linear(d, len(stoi))

        def forward(self, idx):
            t = idx.size(1)
            x = self.emb(idx) + self.pos(torch.arange(t, device=idx.device))[None, :, :]
            mask = torch.triu(torch.ones(t, t, device=idx.device) * float("-inf"), diagonal=1)
            h = self.enc(x, mask=mask, src_key_padding_mask=idx.eq(0))
            return self.head(h)

    def encode(text):
        return [stoi.get(c, 0) for c in text]

    def pack(items):
        arr = np.zeros((len(items), max_len), dtype=np.int64)
        for i, case in enumerate(items):
            ids = encode(format_decision_example(case, include_target=True))[: max_len - 1]
            arr[i, : len(ids)] = ids
        return torch.tensor(arr)

    model = CharLM().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=3e-4)
    xtr = pack(buckets["train"]).to(device)
    history = []
    t0 = time.time()
    nparams = sum(p.numel() for p in model.parameters())
    for epoch in range(epochs):
        model.train()
        opt.zero_grad()
        logits = model(xtr[:, :-1])
        loss = nn.functional.cross_entropy(logits.reshape(-1, logits.size(-1)), xtr[:, 1:].reshape(-1), ignore_index=0)
        loss.backward()
        opt.step()
        history.append({"epoch": epoch, "train_ce": float(loss.item())})

    def generate(prompt, max_new=40):
        ids = encode(prompt)[: max_len - 1]
        cur = torch.tensor([ids], device=device)
        with torch.no_grad():
            for _ in range(max_new):
                if cur.size(1) >= max_len:
                    break
                nxt = int(torch.argmax(model(cur)[:, -1, :], dim=-1).item())
                if nxt == 0:
                    break
                cur = torch.cat([cur, torch.tensor([[nxt]], device=device)], dim=1)
                text = "".join(itos.get(i, "") for i in cur[0].tolist() if i)
                if "FAMILY=" in text:
                    break
        return "".join(itos.get(i, "") for i in cur[0].tolist() if i)

    parsed = 0
    acc_n = 0
    examples = []
    for case in buckets["test"]:
        prompt = format_decision_example(case, include_target=False)
        text = generate(prompt)
        fields = parse_generated_fields(text)
        if "INTENDED" in fields:
            parsed += 1
            try:
                if abs(float(fields["INTENDED"]) - float(case["oracle_intended_delta_cm"])) < 1e-6:
                    acc_n += 1
            except ValueError:
                pass
        examples.append({"prompt": prompt, "generated": text[len(prompt) :], "parsed": fields})
    ckpt = ROOT / "artifacts" / "training" / "checkpoints" / "decision_tiny_lm.pt"
    torch.save({"state_dict": model.state_dict(), "stoi": stoi, "max_len": max_len, "seed": seed}, ckpt)
    n_test = max(1, len(buckets["test"]))
    return {
        "status": "PASS",
        "model": "tiny_causal_transformer_charlm",
        "n_params": nparams,
        "epochs": epochs,
        "device": str(device),
        "torch": info,
        "test_parse_rate": parsed / n_test,
        "test_intended_accuracy_when_parsed": acc_n / n_test,
        "checkpoint": str(ckpt),
        "history": history,
        "examples_head": examples[:5],
        "runtime_s": time.time() - t0,
    }


def maybe_plot(history, path, ykey, title):
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        plt.figure(figsize=(6, 4))
        plt.plot([h["epoch"] for h in history], [h[ykey] for h in history])
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
    parser.add_argument("--cases", type=Path, default=ROOT / "artifacts" / "training" / "decision_cases.json")
    parser.add_argument("--mlp-epochs", type=int, default=400)
    parser.add_argument("--lm-epochs", type=int, default=80)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    cases = load_cases(args.cases)
    buckets = split_cases(cases, seed=args.seed)
    vocab = action_vocab(cases)
    mlp = train_mlp(buckets, vocab, args.mlp_epochs, args.seed)
    lm = train_tiny_lm(buckets, args.lm_epochs, args.seed)
    if mlp.get("history"):
        maybe_plot(mlp["history"], ROOT / "reports" / "figures" / "decision_sft_mlp_loss.png", "train_ce", "Decision SFT MLP CE")
    payload = {
        "task": "decision_sft_s_to_best_correction",
        "n_cases": len(cases),
        "action_vocab_intended_cm": vocab,
        "mlp": mlp,
        "tiny_lm": lm,
        "huggingface_foundation_model": "NOT_RUN",
    }
    write_json(ROOT / "artifacts" / "training" / "decision_sft.json", payload)
    slim = json.loads(json.dumps(payload, default=str))
    if "history" in slim.get("mlp", {}):
        slim["mlp"]["history"] = slim["mlp"]["history"][-5:]
    if "history" in slim.get("tiny_lm", {}):
        slim["tiny_lm"]["history"] = slim["tiny_lm"]["history"][-5:]
    print(json.dumps(slim, indent=2)[:8000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
