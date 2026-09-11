#!/usr/bin/env python3
"""Materialize a shard-packed visual sanity sample of counterfactual pairs.

Images go to D:\\FitGroundData\\... (outside git). Metadata table is also copied
into reports/ for the evidence pack.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fitground.config import (
    COUNTERFACTUAL_CANDIDATES_PATH,
    COUNTERFACTUAL_PILOT_DIR,
    EXTERNAL_HF_CACHE_DIR,
    MANIFEST_PATH,
    REPORTS_DIR,
)
from fitground.counterfactual.pilot import select_pilot_pairs

# Import materialize helpers from the CLI module.
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
from materialize_samples import materialize_many  # noqa: E402


def _font(size: int = 18) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _load_rgb(path: Path, size: tuple[int, int]) -> Image.Image:
    img = Image.open(path).convert("RGB")
    return img.resize(size, Image.Resampling.BILINEAR)


def render_pair_sheet(pair: pd.Series, image_root: Path, out_path: Path) -> None:
    thumb = (256, 342)
    labels = ("person", "cloth", "target")
    canvas = Image.new("RGB", (thumb[0] * 3 + 40, thumb[1] * 2 + 90), "white")
    draw = ImageDraw.Draw(canvas)
    font = _font(16)
    title = (
        f"{pair['pair_id']}  tier={pair['pair_tier']}  "
        f"d_bust={float(pair['delta_garment_bust_cm']):.2f}cm  "
        f"d_ease={float(pair['delta_bust_ease_cm']):.2f}cm"
    )
    draw.text((10, 8), title, fill="black", font=font)
    for r, role, sid in (
        (0, "ANCHOR", pair["anchor_sample_id"]),
        (1, "CF", pair["counterfactual_sample_id"]),
    ):
        folder = image_root / str(sid).replace("/", "_")
        draw.text((10, 32 + r * (thumb[1] + 28)), role, fill="black", font=font)
        for c, name in enumerate(labels):
            img = _load_rgb(folder / f"{name}.png", thumb)
            canvas.paste(img, (20 + c * thumb[0], 50 + r * (thumb[1] + 28)))
            draw.text((20 + c * thumb[0], 50 + r * (thumb[1] + 28) - 16), name, fill="black", font=font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize counterfactual visual-check pairs")
    parser.add_argument("--n-pairs", type=int, default=120)
    parser.add_argument("--max-shards", type=int, default=64)
    parser.add_argument("--skip-download", action="store_true")
    args = parser.parse_args()
    n_pairs = args.n_pairs
    max_shards = args.max_shards
    if not COUNTERFACTUAL_CANDIDATES_PATH.exists():
        raise SystemExit("run scripts/build_counterfactual_candidates.py first")
    pairs = pd.read_parquet(COUNTERFACTUAL_CANDIDATES_PATH)
    pilot = select_pilot_pairs(pairs, n_pairs=n_pairs, max_shards=max_shards)
    out_dir = COUNTERFACTUAL_PILOT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    sheets_dir = out_dir / "contact_sheets"
    images_dir = out_dir / "images"
    meta_path = out_dir / "pilot_pairs.parquet"
    csv_path = out_dir / "pilot_pairs.csv"
    report_csv = REPORTS_DIR / "counterfactual_pilot_metadata.csv"
    id_file = out_dir / "sample_ids.txt"

    sample_ids = sorted(
        set(pilot["anchor_sample_id"].astype(str)) | set(pilot["counterfactual_sample_id"].astype(str))
    )
    id_file.write_text("\n".join(sample_ids) + "\n", encoding="utf-8")
    pilot.to_parquet(meta_path, index=False)
    keep_cols = [
        c
        for c in [
            "pair_id",
            "pair_tier",
            "anchor_sample_id",
            "counterfactual_sample_id",
            "same_person_image",
            "same_cloth_image",
            "measurement_intervention_type",
            "delta_garment_bust_cm",
            "delta_bust_ease_cm",
            "delta_bust_ease_ratio",
            "anchor_split",
            "counterfactual_split",
            "control_score",
            "confound_flags",
            "pair_construction_reason",
        ]
        if c in pilot.columns
    ]
    csv_df = pilot[keep_cols].copy()
    csv_df.to_csv(csv_path, index=False)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    csv_df.to_csv(report_csv, index=False)

    print(
        json.dumps(
            {
                "n_pairs": int(len(pilot)),
                "n_sample_ids": len(sample_ids),
                "n_shards": int(pilot.attrs.get("n_shards", 0)),
                "shards": pilot.attrs.get("pilot_shards", []),
                "output_dir": str(out_dir),
                "skip_download": args.skip_download,
            },
            indent=2,
        )
    )
    if args.skip_download:
        return

    results = materialize_many(
        MANIFEST_PATH,
        sample_ids,
        images_dir,
        verify_hash=True,
        keep_shard=False,
        cache_dir=EXTERNAL_HF_CACHE_DIR,
        ephemeral_dir=EXTERNAL_HF_CACHE_DIR / "ephemeral_shards",
    )
    (out_dir / "materialize_log.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    sheets_dir.mkdir(parents=True, exist_ok=True)
    for _, pair in pilot.iterrows():
        render_pair_sheet(pair, images_dir, sheets_dir / f"{pair['pair_id']}.jpg")

    print(json.dumps({"materialized": len(results), "sheets": int(len(list(sheets_dir.glob('*.jpg'))))}, indent=2))


if __name__ == "__main__":
    main()
