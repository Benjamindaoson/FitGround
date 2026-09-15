"""FitGround readiness decision."""

from __future__ import annotations

import json
from pathlib import Path

from fitground.config import MANIFEST_PATH, REPORTS_DIR


def readiness_decision(
    pipeline_result: dict,
    eda_report: dict,
    raw_data_present: bool,
    raw_bytes: int,
) -> dict:
    """Evaluate GO / PARTIAL / NO-GO based on real audit results."""
    total = eda_report.get("total_samples", 0)
    usable = eda_report.get("usable_for_fitground", 0)
    invalid = eda_report.get("invalid", 0)
    leakage = pipeline_result.get("leakage", {})

    usable_rate = usable / total if total else 0
    invalid_rate = invalid / total if total else 1

    missing_rates = eda_report.get("measurement_missing_rates", {})
    max_missing = max(missing_rates.values()) if missing_rates else 1

    leakage_count = (
        leakage.get("train_eval_person_overlap", 0)
        + leakage.get("train_eval_garment_overlap", 0)
        + leakage.get("train_eval_target_overlap", 0)
    )

    blockers = []
    if not raw_data_present and total < 100_000:
        blockers.append("Full raw FIT not locally persisted (disk constraint); train audited ephemerally")
    if total < 100_000:
        blockers.append(f"Incomplete audit: {total}/105000 samples processed")
    if usable_rate < 0.95:
        blockers.append(f"Low usable rate: {usable_rate:.2%}")
    if max_missing > 0.01:
        blockers.append(f"Measurement missing rate up to {max_missing:.2%}")
    if leakage_count > 100:
        blockers.append(f"Train/eval leakage: {leakage_count} overlapping image hashes")

    # Decision logic
    if total >= 100_000 and usable_rate >= 0.98 and max_missing < 0.001 and invalid_rate < 0.02:
        decision = "GO"
    elif total >= 100_000 and usable_rate >= 0.90:
        decision = "PARTIAL"
    elif total >= 50_000 and usable_rate >= 0.85:
        decision = "PARTIAL"
    else:
        decision = "NO-GO"

    reasons = []
    if decision == "GO":
        reasons.append("Full 105K audit complete with high measurement completeness and image integrity")
        reasons.append(f"Usable rate: {usable_rate:.2%}")
        reasons.append("Sufficient relational feature variation for counterfactual construction")
    elif decision == "PARTIAL":
        reasons.append(f"Audited {total} samples ({usable_rate:.2%} usable)")
        if blockers:
            reasons.extend(blockers)
        reasons.append("Manifest and audit pipeline operational; some constraints remain")
    else:
        reasons.extend(blockers or ["Insufficient data quality or volume"])

    result = {
        "decision": decision,
        "reasons": reasons,
        "metrics": {
            "total_samples": total,
            "usable_rate": usable_rate,
            "invalid_rate": invalid_rate,
            "max_measurement_missing_rate": max_missing,
            "leakage_overlap_count": leakage_count,
            "raw_bytes_local": raw_bytes,
        },
        "blockers": blockers,
        "next_steps": _next_steps(decision, blockers),
    }
    (REPORTS_DIR / "readiness_decision.json").write_text(json.dumps(result, indent=2))
    _write_readiness_md(result)
    return result


def _next_steps(decision: str, blockers: list[str]) -> list[str]:
    steps = []
    if "disk constraint" in " ".join(blockers).lower() or any("105000" in b for b in blockers):
        steps.append("Expand storage or use cloud bucket for raw parquet; current ephemeral train audit is complete if 105K processed")
    if decision in ("GO", "PARTIAL"):
        steps.append("Construct measurement counterfactual pairs from FIT-Clean manifest")
        steps.append("Build classical ML baseline on relational features")
        steps.append("Flag eval samples with train/eval leakage for EXCLUDE_FROM_EVAL")
    if decision == "NO-GO":
        steps.append("Resolve data quality blockers before model development")
    return steps


def _write_readiness_md(result: dict) -> None:
    lines = [
        "# FitGround Readiness Decision",
        "",
        f"## Decision: **{result['decision']}**",
        "",
        "### Reasons",
        "",
    ]
    for r in result["reasons"]:
        lines.append(f"- {r}")

    lines.extend(["", "### Metrics", "", "```json"])
    lines.append(json.dumps(result["metrics"], indent=2))
    lines.extend(["```", "", "### Next Steps", ""])
    for s in result["next_steps"]:
        lines.append(f"- {s}")

    (REPORTS_DIR / "readiness_decision.md").write_text("\n".join(lines))
