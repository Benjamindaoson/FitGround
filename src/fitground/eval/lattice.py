"""Strict validation of measured transition lattices."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from fitground.training.geometry import assert_realized_not_copied


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def validate_transition_row(row: Mapping[str, Any]) -> list[str]:
    errors = []
    try:
        assert_realized_not_copied(row)
    except ValueError as exc:
        errors.append(str(exc))
    if row.get("realized_delta_cm") is None:
        errors.append("realized_delta_cm is None")
    if row.get("realized_source") == "intended":
        errors.append("intended copied into realized_source")
    before = row.get("garment_measurement_before") or {}
    after = row.get("garment_measurement_after") or {}
    if not before or not after:
        errors.append("missing before/after measurements")
    return errors


def validate_lattice(rows: Iterable[Mapping[str, Any]]) -> dict:
    rows = list(rows)
    keys = []
    dup = 0
    seen = set()
    failed = []
    for row in rows:
        key = (
            row.get("state_id"),
            row.get("action_family"),
            round(float(row.get("intended_delta_cm") or 0), 3),
            row.get("action_id"),
        )
        if key in seen:
            dup += 1
        seen.add(key)
        keys.append(key)
        errs = validate_transition_row(row)
        if errs:
            failed.append({"action_id": row.get("action_id"), "errors": errs})
    bodies = Counter(r.get("body_name") for r in rows)
    garments = Counter(r.get("action_family") for r in rows)
    mags = Counter(round(float(r.get("intended_delta_cm") or 0), 2) for r in rows)
    return {
        "n_transitions": len(rows),
        "n_unique_state_action": len(seen),
        "n_duplicate_state_action": dup,
        "n_failed_validation": len(failed),
        "n_valid": len(rows) - len(failed),
        "n_bodies": len(bodies),
        "bodies": dict(bodies),
        "n_action_families": len(garments),
        "action_families": dict(garments),
        "action_magnitudes": {str(k): v for k, v in sorted(mags.items())},
        "failures": failed[:50],
        "ok": dup == 0 and not failed,
    }
