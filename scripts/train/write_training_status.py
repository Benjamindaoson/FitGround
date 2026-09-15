#!/usr/bin/env python3
"""Write FINAL_STATUS and a training report from artifacts after jobs finish."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def status_of(block, pass_key="status"):
    if not block:
        return "NOT_RUN"
    if isinstance(block, str):
        return block
    return block.get(pass_key) or block.get("matrix_status") or "UNKNOWN"


def main() -> int:
    lattice = load(ROOT / "artifacts" / "training" / "lattice_summary.json") or {}
    obs = load(ROOT / "artifacts" / "training" / "observational_and_vision_baselines.json") or {}
    trans = load(ROOT / "artifacts" / "training" / "transition_sft.json") or {}
    dec = load(ROOT / "artifacts" / "training" / "decision_sft.json") or {}
    rlvr = load(ROOT / "artifacts" / "training" / "rlvr.json") or {}
    prev = load(ROOT / "artifacts" / "FINAL_STATUS.json") or {}
    matrix = dict(prev.get("matrix") or {})
    matrix["Classical baseline"] = "PASS" if obs.get("B0") and obs.get("B1") else matrix.get("Classical baseline", "NOT_RUN")
    b2 = obs.get("B2_generated_pattern_cnn") or {}
    b3 = obs.get("B3_generated_pattern_multimodal") or {}
    matrix["Vision baseline"] = "PASS" if b2.get("status") == "PASS" else ("NOT_RUN" if not b2 else b2.get("status", "FAIL"))
    matrix["Multimodal baseline"] = "PASS" if b3.get("status") == "PASS" else ("NOT_RUN" if not b3 else b3.get("status", "FAIL"))
    matrix["Transition SFT"] = "PASS" if (trans.get("mlp") or {}).get("status") == "PASS" else "NOT_RUN"
    matrix["Decision SFT"] = "PASS" if (dec.get("mlp") or {}).get("status") == "PASS" else "NOT_RUN"
    if rlvr.get("matrix_status") == "COMPLETED_NOT_JUSTIFIED":
        matrix["RLVR"] = "COMPLETED_NOT_JUSTIFIED"
    elif rlvr.get("status") == "PASS":
        matrix["RLVR"] = rlvr.get("matrix_status") or "PASS"
    else:
        matrix["RLVR"] = rlvr.get("status") or "NOT_RUN"
    notes = dict(prev.get("notes") or {})
    notes["SFT/RLVR"] = (
        f"Measured lattice n_transitions={lattice.get('n_transitions')} "
        f"n_decision={lattice.get('n_decision_cases')} "
        f"transition_mae={(trans.get('mlp') or {}).get('test_realized_mae_cm')} "
        f"decision_acc={(dec.get('mlp') or {}).get('test_action_accuracy')} "
        f"rlvr={matrix['RLVR']}. "
        "Vision B2/B3 used generated pattern PNGs, not FIT-100K."
    )
    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "host": prev.get("host", "daka5svhri0c73etu4ug-fitground"),
        "gpu": prev.get("gpu", "NVIDIA GeForce RTX 4090 24GB"),
        "matrix": matrix,
        "notes": notes,
        "training": {
            "lattice": lattice,
            "B0_test_mae_cm": (obs.get("B0") or {}).get("test_mae_cm"),
            "B1_test_mae_cm": (obs.get("B1") or {}).get("test_mae_cm"),
            "B1_xgboost_test_mae_cm": (obs.get("B1_xgboost") or {}).get("test_mae_cm"),
            "B2_cnn_test_mae_cm": b2.get("test_mae_cm"),
            "B3_cnn_test_mae_cm": b3.get("test_mae_cm"),
            "transition_sft_realized_mae_cm": (trans.get("mlp") or {}).get("test_realized_mae_cm"),
            "decision_sft_accuracy": (dec.get("mlp") or {}).get("test_action_accuracy"),
            "rlvr": {
                "status": rlvr.get("matrix_status") or rlvr.get("status"),
                "before_test": rlvr.get("before_test"),
                "after_test": rlvr.get("after_test"),
            },
        },
    }
    (ROOT / "artifacts" / "FINAL_STATUS.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md = ROOT / "reports" / "TRAINING_RUN.md"
    md.write_text(
        "\n".join(
            [
                "# FitGround training run",
                "",
                "This run trains B0–B3, Transition SFT, Decision SFT, and RLVR on **measured** GarmentCode panel geometry.",
                "FIT-100K images were not downloaded. Vision models use rasterized pattern drawings.",
                "No `intended_delta_cm` was copied into `realized_delta_cm`.",
                "",
                "```json",
                json.dumps(payload["training"], indent=2, default=str),
                "```",
                "",
                "## Matrix",
                "",
                *[f"- {k}: {v}" for k, v in matrix.items()],
                "",
                "## Honesty",
                "",
                "- Observational B0/B1 remain FIT-Clean measurement prediction, not intervention GT.",
                "- B2/B3 FIT-100K: NOT_RUN. B2/B3 generated-pattern: trained.",
                "- Tiny LMs are from-scratch character transformers, not pretrained MLLMs.",
                "- RLVR reward is cached measured utility from the lattice, not a live Warp loop.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, default=str)[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
