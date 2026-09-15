#!/usr/bin/env python3
"""Train a small visual autoencoder on GarmentCodeVTON renders.

This is a GPU-start proxy task: it pretrains a reusable visual encoder from the
downloaded simulated renders, but it does not claim fit-correction supervision.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import time
from pathlib import Path

from PIL import Image

import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset


class RenderDataset(Dataset):
    def __init__(self, root: Path, image_size: int, limit: int | None = None) -> None:
        self.root = root
        paths = sorted(p for p in root.rglob("render_front.png") if ".cache" not in p.parts)
        if limit:
            paths = paths[:limit]
        if not paths:
            raise SystemExit(f"no render_front.png files under {root}")
        self.paths = paths
        self.image_size = image_size

    def __len__(self) -> int:
        return len(self.paths)

    def __getitem__(self, idx: int) -> torch.Tensor:
        img = Image.open(self.paths[idx]).convert("RGB").resize((self.image_size, self.image_size))
        data = torch.ByteTensor(torch.ByteStorage.from_buffer(img.tobytes()))
        return data.view(self.image_size, self.image_size, 3).permute(2, 0, 1).float().div_(255.0)


class AutoEncoder(nn.Module):
    def __init__(self, latent: int = 256) -> None:
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(3, 32, 4, 2, 1),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 64, 4, 2, 1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 128, 4, 2, 1),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, latent, 4, 2, 1),
            nn.ReLU(inplace=True),
        )
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(latent, 128, 4, 2, 1),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(128, 64, 4, 2, 1),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(64, 32, 4, 2, 1),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(32, 3, 4, 2, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.decoder(self.encoder(x))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=Path("data/external/GarmentCodeVTONDataset"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/training/visual_encoder_proxy"))
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--image-size", type=int, default=128)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    dataset = RenderDataset(args.data_root, args.image_size, args.limit)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, num_workers=2, pin_memory=device.type == "cuda")
    model = AutoEncoder().to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3)
    loss_fn = nn.L1Loss()

    metrics_path = args.output_dir / "metrics.csv"
    with metrics_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["epoch", "step", "loss", "device", "elapsed_sec"])
        writer.writeheader()
        start = time.time()
        step = 0
        for epoch in range(1, args.epochs + 1):
            model.train()
            for batch in loader:
                step += 1
                batch = batch.to(device, non_blocking=True)
                pred = model(batch)
                loss = loss_fn(pred, batch)
                opt.zero_grad(set_to_none=True)
                loss.backward()
                opt.step()
                if step == 1 or step % 25 == 0:
                    row = {
                        "epoch": epoch,
                        "step": step,
                        "loss": float(loss.detach().cpu()),
                        "device": str(device),
                        "elapsed_sec": round(time.time() - start, 2),
                    }
                    writer.writerow(row)
                    f.flush()
                    print(json.dumps(row), flush=True)
            torch.save(
                {
                    "model": model.state_dict(),
                    "epoch": epoch,
                    "step": step,
                    "data_root": str(args.data_root),
                    "n_images": len(dataset),
                    "task": "visual_encoder_proxy_autoencoder_not_fit_correction",
                },
                args.output_dir / f"checkpoint_epoch_{epoch}.pt",
            )
    (args.output_dir / "status.json").write_text(
        json.dumps(
            {
                "status": "DONE",
                "task": "visual_encoder_proxy_autoencoder_not_fit_correction",
                "device": str(device),
                "n_images": len(dataset),
                "epochs": args.epochs,
                "metrics": str(metrics_path),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
