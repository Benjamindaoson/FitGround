"""Counterfactual decision engine: candidates → utility → rank → abstain."""

from __future__ import annotations

from typing import Any, Mapping, Sequence


def physics_utility(
    outcomes: Mapping[str, Any] | None,
    edit_cm: float,
    *,
    contact_weight: float = 25.0,
    tightness_weight: float = 20.0,
    edit_weight: float = 0.15,
    comfortable_chest_p10_cm: float = 0.50,
    uncertainty: float = 0.0,
    uncertainty_weight: float = 0.4,
    side_effect_cm: float = 0.0,
    side_weight: float = 0.25,
) -> float | None:
    if not outcomes:
        return None
    contact = float(outcomes.get("contact_ratio") or 0.0)
    chest = float(outcomes.get("chest_clearance_p10_cm") or outcomes.get("clearance_p10_cm") or 0.0)
    tightness = max(0.0, comfortable_chest_p10_cm - chest)
    return float(
        -contact_weight * contact
        - tightness_weight * tightness
        - edit_weight * abs(float(edit_cm))
        - uncertainty_weight * abs(float(uncertainty))
        - side_weight * abs(float(side_effect_cm))
    )


def rank_candidates(candidates: Sequence[Mapping[str, Any]], utility_key: str = "utility") -> list[dict]:
    scored = [dict(c) for c in candidates if c.get(utility_key) is not None]
    scored.sort(key=lambda c: c[utility_key], reverse=True)
    for i, row in enumerate(scored):
        row["rank"] = i + 1
        row["recommended"] = i == 0
    return scored


def should_abstain(
    *,
    body_in_support: bool,
    material_in_support: bool,
    action_in_support: bool,
    simulation_stable: bool,
    candidate_gap: float | None,
    min_gap: float = 0.02,
    ood_score: float = 0.0,
    ood_threshold: float = 0.55,
) -> dict:
    reasons = []
    if not body_in_support:
        reasons.append("OOD_BODY")
    if not material_in_support:
        reasons.append("OOD_MATERIAL")
    if not action_in_support:
        reasons.append("OOD_ACTION_MAGNITUDE")
    if not simulation_stable:
        reasons.append("SIMULATION_UNSTABLE")
    if candidate_gap is not None and candidate_gap < min_gap:
        reasons.append("AMBIGUOUS_CANDIDATES")
    if ood_score >= ood_threshold:
        reasons.append("OOD_DETECTOR")
    return {
        "abstain": bool(reasons),
        "escalate_to_human": bool(reasons),
        "reasons": reasons,
        "ood_score": float(ood_score),
    }


def ood_heuristic(
    *,
    body_name: str,
    support_bodies: Sequence[str],
    material: str,
    support_materials: Sequence[str],
    intended_delta_cm: float,
    action_lo: float = -3.0,
    action_hi: float = 3.0,
    sim_failed: bool = False,
) -> float:
    score = 0.0
    if body_name not in support_bodies:
        score += 0.45
    if material not in support_materials:
        score += 0.35
    if not (action_lo <= float(intended_delta_cm) <= action_hi):
        score += 0.40
    if sim_failed:
        score += 0.50
    return min(1.0, score)
