"""Physics outcome unit tests — no GPU required."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from fitground.physics.outcomes import cloth_body_outcomes, load_obj_vertices


def _write_obj(path: Path, verts: np.ndarray) -> None:
    lines = [f"v {x} {y} {z}" for x, y, z in verts]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_body_metres_are_scaled_to_cloth_centimetres(tmp_path: Path) -> None:
    cloth = np.array([[0.0, 100.0, 0.0], [1.0, 101.0, 0.0], [0.0, 100.0, 1.0]], dtype=float)
    body_m = cloth / 100.0  # same shape in metres
    cpath = tmp_path / "c.obj"
    bpath = tmp_path / "b.obj"
    _write_obj(cpath, cloth)
    _write_obj(bpath, body_m)
    out = cloth_body_outcomes(cpath, bpath)
    assert out["unit_alignment"] == "body_m_to_cm_x100"
    assert out["clearance_min_cm"] < 1e-6


def test_load_obj_vertices(tmp_path: Path) -> None:
    p = tmp_path / "t.obj"
    p.write_text("v 1 2 3\nv 4 5 6\n", encoding="utf-8")
    arr = load_obj_vertices(p)
    assert arr.shape == (2, 3)
