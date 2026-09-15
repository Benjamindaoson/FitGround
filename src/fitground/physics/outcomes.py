"""Post-simulation fit outcomes from cloth + body meshes. Units: centimetres."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np


def load_obj_vertices(path: str | Path) -> np.ndarray:
    verts: list[list[float]] = []
    with Path(path).open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            if line.startswith("v "):
                parts = line.split()
                verts.append([float(parts[1]), float(parts[2]), float(parts[3])])
    if not verts:
        raise ValueError(f"no vertices in {path}")
    return np.asarray(verts, dtype=float)


def _nearest_distances(cloth: np.ndarray, body: np.ndarray) -> np.ndarray:
    try:
        from scipy.spatial import cKDTree

        return cKDTree(body).query(cloth, k=1)[0]
    except Exception:
        dmin = np.full(len(cloth), np.inf, dtype=float)
        step = 256
        for i in range(0, len(cloth), step):
            chunk = cloth[i : i + step]
            diff = chunk[:, None, :] - body[None, :, :]
            dmin[i : i + step] = np.sqrt((diff ** 2).sum(-1)).min(axis=1)
        return dmin


def regional_masks(verts: np.ndarray) -> dict[str, np.ndarray]:
    y = verts[:, 1]
    ymin, ymax = float(y.min()), float(y.max())
    span = max(ymax - ymin, 1e-6)
    rel = (y - ymin) / span
    x = verts[:, 0]
    xspan = max(float(np.abs(x).max()), 1e-6)
    return {
        "length": rel >= 0,
        "chest": (rel >= 0.55) & (rel <= 0.85),
        "waist": (rel >= 0.30) & (rel <= 0.55),
        "shoulder": rel >= 0.80,
        "sleeve": np.abs(x) >= 0.55 * xspan,
    }


def wrinkle_proxy(verts: np.ndarray, k: int = 8) -> float:
    """Mean local height residual vs kNN plane — a drape/wrinkle stand-in, not strain."""
    if len(verts) < k + 1:
        return 0.0
    try:
        from scipy.spatial import cKDTree

        _, idx = cKDTree(verts).query(verts, k=k + 1)
    except Exception:
        return float(np.std(verts[:, 2]))
    residuals = []
    for i, neighbors in enumerate(idx):
        pts = verts[neighbors[1:]]
        centered = pts - pts.mean(axis=0)
        try:
            _, _, vh = np.linalg.svd(centered, full_matrices=False)
            normal = vh[-1]
            residuals.append(abs(float(np.dot(verts[i] - pts.mean(axis=0), normal))))
        except Exception:
            continue
    return float(np.mean(residuals)) if residuals else 0.0


def cloth_body_outcomes(
    cloth_obj: str | Path,
    body_obj: str | Path,
    contact_cm: float = 0.4,
) -> dict[str, Any]:
    cloth = load_obj_vertices(cloth_obj)
    body = load_obj_vertices(body_obj)
    cloth_span = float((cloth.max(0) - cloth.min(0)).max())
    body_span = float((body.max(0) - body.min(0)).max())
    scale_note = "1"
    # GarmentCode mannequin OBJs are metres; draped cloth OBJs are centimetres.
    if body_span < 10 and cloth_span > 20:
        body = body * 100.0
        scale_note = "body_m_to_cm_x100"
    elif cloth_span < 10 and body_span > 20:
        cloth = cloth * 100.0
        scale_note = "cloth_m_to_cm_x100"
    dist = _nearest_distances(cloth, body)
    masks = regional_masks(cloth)
    regional = {}
    for name, mask in masks.items():
        if not np.any(mask):
            regional[name] = None
            continue
        d = dist[mask]
        regional[name] = {
            "n_verts": int(mask.sum()),
            "clearance_mean_cm": float(d.mean()),
            "clearance_p10_cm": float(np.percentile(d, 10)),
            "contact_ratio": float((d < contact_cm).mean()),
        }
    chest = regional.get("chest") or {}
    return {
        "n_cloth_verts": int(len(cloth)),
        "n_body_verts": int(len(body)),
        "clearance_mean_cm": float(dist.mean()),
        "clearance_p10_cm": float(np.percentile(dist, 10)),
        "clearance_min_cm": float(dist.min()),
        "contact_ratio": float((dist < contact_cm).mean()),
        "tight_vertex_ratio": float((dist < 0.2).mean()),
        "wrinkle_proxy_cm": wrinkle_proxy(cloth),
        "bbox_xyz_cm": [float(x) for x in (cloth.max(0) - cloth.min(0))],
        "regional": regional,
        "chest_clearance_p10_cm": chest.get("clearance_p10_cm"),
        "body_kind": "SYNTHETIC_BODY_PHYSICS",
        "note": "Nearest-vertex clearance to a static mannequin OBJ. Not SMPL-X parametric, not real-world GT.",
        "contact_threshold_cm": contact_cm,
        "unit_alignment": scale_note,
    }
