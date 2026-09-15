"""Geometry, measurement deltas, and utility — never copy intended into realized."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np
from PIL import Image, ImageDraw


def realized_delta(before_cm: float | None, after_cm: float | None) -> float | None:
    """Measured after-minus-before. Returns None if either side is missing."""
    if before_cm is None or after_cm is None:
        return None
    return float(after_cm) - float(before_cm)


def assert_realized_not_copied(row: Mapping[str, Any]) -> None:
    """Refuse rows that claim a realized delta without a measurement provenance."""
    if row.get("realized_delta_cm") is None:
        return
    source = row.get("realized_source")
    if source != "panel_geometry_after_minus_before":
        raise ValueError(f"realized_delta_cm lacks measurement provenance: {source!r}")
    before = row.get("garment_measurement_before") or {}
    after = row.get("garment_measurement_after") or {}
    key = row.get("realized_measurement_key")
    if not key:
        raise ValueError("realized_measurement_key is required")
    expected = realized_delta(before.get(key), after.get(key))
    got = float(row["realized_delta_cm"])
    if expected is None or abs(expected - got) > 1e-9:
        raise ValueError("realized_delta_cm does not match after-minus-before measurements")


def utility_chest_case(
    target_error_cm: float,
    intended_delta_cm: float,
    sleeve_side_effect_cm: float = 0.0,
    length_side_effect_cm: float = 0.0,
    edit_weight: float = 0.15,
    side_weight: float = 0.5,
) -> float:
    """Same utility as the CHEST_CASE lattice: closer target, smaller edit, fewer side effects."""
    return float(
        -abs(target_error_cm)
        - edit_weight * abs(intended_delta_cm)
        - side_weight * (abs(sleeve_side_effect_cm) + abs(length_side_effect_cm))
    )


def rasterize_specification(
    spec: Mapping[str, Any] | str | Path,
    out_png: str | Path | None = None,
    size: int = 128,
) -> Image.Image:
    """Draw 2D panel outlines from a GarmentCode specification JSON."""
    if isinstance(spec, (str, Path)):
        payload = json.loads(Path(spec).read_text(encoding="utf-8"))
    else:
        payload = spec
    panels = payload["pattern"]["panels"]
    chunks: list[np.ndarray] = []
    for panel in panels.values():
        verts = np.asarray(panel["vertices"], dtype=float)
        if verts.ndim != 2 or verts.shape[1] < 2 or len(verts) < 2:
            continue
        chunks.append(verts[:, :2])
    img = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(img)
    if not chunks:
        if out_png is not None:
            img.save(out_png)
        return img
    allv = np.vstack(chunks)
    minxy = allv.min(axis=0)
    span = float((allv.max(axis=0) - minxy).max())
    if span <= 0:
        span = 1.0
    margin = 6.0
    scale = (size - 2 * margin) / span
    for verts in chunks:
        xy = (verts - minxy) * scale + margin
        seq = [(float(x), float(size - 1 - y)) for x, y in xy]
        draw.line(seq + [seq[0]], fill=255, width=2)
        if len(seq) >= 3:
            draw.polygon(seq, outline=255)
    if out_png is not None:
        Path(out_png).parent.mkdir(parents=True, exist_ok=True)
        img.save(out_png)
    return img


def grouped_state_split(
    state_ids: list[str],
    seed: int = 0,
    train_frac: float = 0.7,
    val_frac: float = 0.15,
) -> dict[str, str]:
    """Split unique state ids, then map each id to train/val/test."""
    rng = np.random.default_rng(seed)
    uniq = np.array(sorted(set(state_ids)))
    rng.shuffle(uniq)
    n = len(uniq)
    n_train = max(1, int(round(train_frac * n)))
    n_val = max(1, int(round(val_frac * n))) if n >= 3 else 0
    if n_train + n_val >= n and n > 1:
        n_val = max(0, n - n_train - 1)
    n_train = min(n_train, n - n_val)
    assignment: dict[str, str] = {}
    for i, sid in enumerate(uniq.tolist()):
        if i < n_train:
            assignment[sid] = "train"
        elif i < n_train + n_val:
            assignment[sid] = "val"
        else:
            assignment[sid] = "test"
    return assignment
