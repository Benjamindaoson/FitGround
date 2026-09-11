"""Build ordered, de-duplicated counterfactual candidate pairs by tier."""

from __future__ import annotations

from typing import Any, Iterator

import pandas as pd

from fitground.config import (
    MAX_PAIRS_PER_GROUP,
    MEANINGFUL_GARMENT_DELTA_CM,
    PHASH_FAMILY_HAMMING_MAX,
    TIER_D_MAX_PAIRS,
)
from fitground.counterfactual.controls import (
    confound_flags,
    construction_reason,
    control_score,
    intervention_type,
    measurements_constant,
    varying_garment_fields,
)
from fitground.counterfactual.discovery import phash_hamming
from fitground.counterfactual.schema import (
    BODY_VECTOR_FIELDS,
    CLOTH_SHA256_FIELD,
    GARMENT_VECTOR_FIELDS,
    RELATIONAL_VECTOR_FIELDS,
    TIER_A,
    TIER_B,
    TIER_C,
    TIER_D,
    make_pair_id,
    unordered_pair_key,
)

BODY = list(BODY_VECTOR_FIELDS)
GARMENT = list(GARMENT_VECTOR_FIELDS)
REL = list(RELATIONAL_VECTOR_FIELDS)

_ROW_FIELDS = (
    [
        "sample_id",
        "source_split",
        "source_shard_id",
        "person_sha256",
        CLOTH_SHA256_FIELD,
        "target_sha256",
        "garment_phash",
        "quality_status",
        "usable_for_fitground",
        "duplicate_person_sha256",
        "duplicate_garment_sha256",
        "duplicate_target_sha256",
        "leakage_train_eval_person",
        "leakage_train_eval_garment",
        "leakage_train_eval_target",
    ]
    + BODY
    + GARMENT
    + REL
)


def _as_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    cols = [c for c in _ROW_FIELDS if c in frame.columns]
    return frame[cols].to_dict("records")


def _anchor_sort_key(row: dict[str, Any]) -> tuple[float, float, str]:
    return (float(row["bust_ease_cm"]), float(row["garment_bust_cm"]), str(row["sample_id"]))


def _order_anchor_cf(a: dict[str, Any], b: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Anchor = tighter/lower ease; CF = looser. Ties broken by sample_id."""
    return (a, b) if _anchor_sort_key(a) <= _anchor_sort_key(b) else (b, a)


def _truthy(value: Any) -> bool:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    return bool(value)


def build_pair_record(
    a: dict[str, Any],
    b: dict[str, Any],
    *,
    tier: str,
    group_key: str,
    garment_hamming: int | None = None,
) -> dict[str, Any] | None:
    anchor, cf = _order_anchor_cf(a, b)
    if anchor["sample_id"] == cf["sample_id"]:
        return None
    if anchor["target_sha256"] == cf["target_sha256"]:
        return None
    varying = varying_garment_fields(anchor, cf)
    if not varying and tier in {TIER_A, TIER_B, TIER_C}:
        return None

    same_person = anchor["person_sha256"] == cf["person_sha256"]
    same_cloth = anchor[CLOTH_SHA256_FIELD] == cf[CLOTH_SHA256_FIELD]
    ham = garment_hamming
    if ham is None:
        ham = phash_hamming(anchor.get("garment_phash"), cf.get("garment_phash"))
    same_phash = (not same_cloth) and ham == 0
    near_phash = (not same_cloth) and 0 < ham <= PHASH_FAMILY_HAMMING_MAX
    body_const = measurements_constant(anchor, cf, BODY_VECTOR_FIELDS)
    itype = intervention_type(varying)
    pair_split = (
        f"{anchor['source_split']}_{cf['source_split']}"
        if anchor["source_split"] == cf["source_split"]
        else "cross_split"
    )
    dup_g = _truthy(anchor.get("duplicate_garment_sha256")) or _truthy(
        cf.get("duplicate_garment_sha256")
    )
    dup_t = _truthy(anchor.get("duplicate_target_sha256")) or _truthy(
        cf.get("duplicate_target_sha256")
    )
    # Person-image reuse is the TIER B/C experimental unit, not contamination.
    # Cloth-image reuse is the TIER A unit.
    if tier in {TIER_B, TIER_C}:
        dup = dup_g or dup_t
    elif tier == TIER_A:
        dup = dup_t
    else:
        dup = (
            _truthy(anchor.get("duplicate_person_sha256"))
            or _truthy(cf.get("duplicate_person_sha256"))
            or dup_g
            or dup_t
        )
    leak_p = _truthy(anchor.get("leakage_train_eval_person")) or _truthy(
        cf.get("leakage_train_eval_person")
    )
    leak_g = _truthy(anchor.get("leakage_train_eval_garment")) or _truthy(
        cf.get("leakage_train_eval_garment")
    )
    leak_t = _truthy(anchor.get("leakage_train_eval_target")) or _truthy(
        cf.get("leakage_train_eval_target")
    )
    rec: dict[str, Any] = {
        "pair_id": make_pair_id(tier, anchor["sample_id"], cf["sample_id"]),
        "anchor_sample_id": anchor["sample_id"],
        "counterfactual_sample_id": cf["sample_id"],
        "pair_tier": tier,
        "same_person_image": bool(same_person),
        "same_cloth_image": bool(same_cloth),
        "same_garment_phash": bool(same_phash),
        "near_garment_phash": bool(near_phash),
        "garment_phash_hamming": int(ham),
        "anchor_target_sha256": anchor["target_sha256"],
        "counterfactual_target_sha256": cf["target_sha256"],
        "anchor_person_sha256": anchor["person_sha256"],
        "counterfactual_person_sha256": cf["person_sha256"],
        "anchor_cloth_sha256": anchor[CLOTH_SHA256_FIELD],
        "counterfactual_cloth_sha256": cf[CLOTH_SHA256_FIELD],
        "anchor_body_height_cm": float(anchor["body_height_cm"]),
        "anchor_body_bust_cm": float(anchor["body_bust_cm"]),
        "anchor_body_waist_cm": float(anchor["body_waist_cm"]),
        "anchor_body_hips_cm": float(anchor["body_hips_cm"]),
        "counterfactual_body_height_cm": float(cf["body_height_cm"]),
        "counterfactual_body_bust_cm": float(cf["body_bust_cm"]),
        "counterfactual_body_waist_cm": float(cf["body_waist_cm"]),
        "counterfactual_body_hips_cm": float(cf["body_hips_cm"]),
        "anchor_garment_bust_cm": float(anchor["garment_bust_cm"]),
        "anchor_garment_length_cm": float(anchor["garment_length_cm"]),
        "anchor_garment_sleeve_cm": float(anchor["garment_sleeve_cm"]),
        "counterfactual_garment_bust_cm": float(cf["garment_bust_cm"]),
        "counterfactual_garment_length_cm": float(cf["garment_length_cm"]),
        "counterfactual_garment_sleeve_cm": float(cf["garment_sleeve_cm"]),
        "anchor_bust_ease_cm": float(anchor["bust_ease_cm"]),
        "anchor_bust_ease_ratio": float(anchor["bust_ease_ratio"]),
        "counterfactual_bust_ease_cm": float(cf["bust_ease_cm"]),
        "counterfactual_bust_ease_ratio": float(cf["bust_ease_ratio"]),
        "delta_body_height_cm": float(cf["body_height_cm"]) - float(anchor["body_height_cm"]),
        "delta_body_bust_cm": float(cf["body_bust_cm"]) - float(anchor["body_bust_cm"]),
        "delta_body_waist_cm": float(cf["body_waist_cm"]) - float(anchor["body_waist_cm"]),
        "delta_body_hips_cm": float(cf["body_hips_cm"]) - float(anchor["body_hips_cm"]),
        "delta_garment_bust_cm": float(cf["garment_bust_cm"]) - float(anchor["garment_bust_cm"]),
        "delta_garment_length_cm": float(cf["garment_length_cm"]) - float(anchor["garment_length_cm"]),
        "delta_garment_sleeve_cm": float(cf["garment_sleeve_cm"]) - float(anchor["garment_sleeve_cm"]),
        "delta_bust_ease_cm": float(cf["bust_ease_cm"]) - float(anchor["bust_ease_cm"]),
        "delta_bust_ease_ratio": float(cf["bust_ease_ratio"]) - float(anchor["bust_ease_ratio"]),
        "delta_garment_length_height_ratio": float(cf["garment_length_height_ratio"])
        - float(anchor["garment_length_height_ratio"]),
        "body_measurements_constant": bool(body_const),
        "single_variable_garment_change": len(varying) == 1,
        "measurement_intervention_type": itype,
        "different_target": True,
        "quality_anchor": str(anchor["quality_status"]),
        "quality_counterfactual": str(cf["quality_status"]),
        "quality_both_valid": str(anchor["quality_status"]) == "VALID"
        and str(cf["quality_status"]) == "VALID",
        "usable_both": _truthy(anchor.get("usable_for_fitground"))
        and _truthy(cf.get("usable_for_fitground")),
        "duplicate_contamination": bool(dup),
        "leakage_person": bool(leak_p),
        "leakage_garment": bool(leak_g),
        "leakage_target": bool(leak_t),
        "leakage_any": bool(leak_p or leak_g or leak_t),
        "cross_split": pair_split == "cross_split",
        "pair_split": pair_split if pair_split != "cross_split" else "cross_split",
        "anchor_split": str(anchor["source_split"]),
        "counterfactual_split": str(cf["source_split"]),
        "anchor_shard_id": str(anchor["source_shard_id"]),
        "counterfactual_shard_id": str(cf["source_shard_id"]),
        "group_key": group_key,
    }
    rec["confound_flags"] = confound_flags(rec)
    rec["control_score"] = control_score(rec)
    rec["pair_construction_reason"] = construction_reason(rec)
    return rec


def _iter_limited_pairs(rows: list[dict[str, Any]]) -> Iterator[tuple[dict[str, Any], dict[str, Any]]]:
    ordered = sorted(rows, key=_anchor_sort_key)
    n = len(ordered)
    if n < 2:
        return
    if n <= 6:
        for i in range(n):
            for j in range(i + 1, n):
                yield ordered[i], ordered[j]
        return
    emitted = 0
    for i in range(n - 1):
        if emitted >= MAX_PAIRS_PER_GROUP:
            break
        yield ordered[i], ordered[i + 1]
        emitted += 1
    if emitted < MAX_PAIRS_PER_GROUP:
        yield ordered[0], ordered[-1]


def _accept_tier_a(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return (
        a["person_sha256"] == b["person_sha256"]
        and a[CLOTH_SHA256_FIELD] == b[CLOTH_SHA256_FIELD]
        and a["target_sha256"] != b["target_sha256"]
        and measurements_constant(a, b, BODY_VECTOR_FIELDS)
        and bool(varying_garment_fields(a, b))
    )


def _accept_tier_b(a: dict[str, Any], b: dict[str, Any], ham: int) -> bool:
    return (
        a["person_sha256"] == b["person_sha256"]
        and a[CLOTH_SHA256_FIELD] != b[CLOTH_SHA256_FIELD]
        and ham <= PHASH_FAMILY_HAMMING_MAX
        and a["target_sha256"] != b["target_sha256"]
        and measurements_constant(a, b, BODY_VECTOR_FIELDS)
        and bool(varying_garment_fields(a, b))
    )


def _accept_tier_c(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return (
        a["person_sha256"] == b["person_sha256"]
        and a[CLOTH_SHA256_FIELD] != b[CLOTH_SHA256_FIELD]
        and a["target_sha256"] != b["target_sha256"]
        and measurements_constant(a, b, BODY_VECTOR_FIELDS)
        and bool(varying_garment_fields(a, b))
    )


def build_candidates(
    df: pd.DataFrame,
    *,
    include_tier_d: bool | str = "auto",
    min_ab_pairs_for_skipping_d: int = 100,
) -> pd.DataFrame:
    """Assign each unordered pair to the strongest eligible tier only."""
    work = df[df["usable_for_fitground"]].copy() if "usable_for_fitground" in df.columns else df.copy()
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []

    def _try_add(rec: dict[str, Any] | None) -> None:
        if rec is None:
            return
        key = unordered_pair_key(rec["anchor_sample_id"], rec["counterfactual_sample_id"])
        if key in seen:
            return
        seen.add(key)
        rows.append(rec)

    # TIER A: (person, cloth) groups — restrict to multi-row keys (avoid 105K singleton loops)
    a_keys = ["person_sha256", CLOTH_SHA256_FIELD]
    a_work = work.dropna(subset=a_keys)
    a_sizes = a_work.groupby(a_keys, sort=False).size()
    a_multi_idx = a_sizes[a_sizes > 1].index
    if len(a_multi_idx) > 0:
        a_multi = a_work.set_index(a_keys).loc[a_multi_idx].reset_index()
        for (person, cloth), g in a_multi.groupby(a_keys, sort=False):
            recs = _as_records(g)
            for a, b in _iter_limited_pairs(recs):
                if _accept_tier_a(a, b):
                    _try_add(
                        build_pair_record(
                            a, b, tier=TIER_A, group_key=f"person:{person}|cloth:{cloth}"
                        )
                    )

    n_a = sum(1 for r in rows if r["pair_tier"] == TIER_A)

    # Within-person pairs for B then C
    p_work = work.dropna(subset=["person_sha256"])
    p_sizes = p_work.groupby("person_sha256", sort=False).size()
    p_multi_ids = p_sizes[p_sizes > 1].index
    p_multi = p_work[p_work["person_sha256"].isin(p_multi_ids)]
    for person, g in p_multi.groupby("person_sha256", sort=False):
        recs = _as_records(g)
        if len(recs) < 2:
            continue
        for a, b in _iter_limited_pairs(recs):
            if a[CLOTH_SHA256_FIELD] == b[CLOTH_SHA256_FIELD]:
                continue
            ham = phash_hamming(a.get("garment_phash"), b.get("garment_phash"))
            if _accept_tier_b(a, b, ham):
                _try_add(
                    build_pair_record(
                        a,
                        b,
                        tier=TIER_B,
                        group_key=f"person:{person}|phash_family",
                        garment_hamming=ham,
                    )
                )
            elif _accept_tier_c(a, b):
                _try_add(
                    build_pair_record(a, b, tier=TIER_C, group_key=f"person:{person}|garment_alt")
                )

    n_abc = sum(1 for r in rows if r["pair_tier"] in {TIER_A, TIER_B, TIER_C})
    use_d = include_tier_d is True or (
        include_tier_d == "auto" and n_abc < min_ab_pairs_for_skipping_d
    )
    if use_d and TIER_D_MAX_PAIRS != 0:
        for rec in _tier_d_pairs(work, already=seen, limit=TIER_D_MAX_PAIRS):
            _try_add(rec)

    if not rows:
        return pd.DataFrame(columns=["pair_id"])
    out = pd.DataFrame(rows)
    out = out.sort_values(["pair_tier", "pair_id"], kind="mergesort").reset_index(drop=True)
    out.attrs["n_tier_a_before_person_pass"] = n_a
    out.attrs["tier_d_constructed"] = bool(use_d and TIER_D_MAX_PAIRS != 0)
    return out


def _tier_d_pairs(
    df: pd.DataFrame,
    *,
    already: set[str],
    limit: int,
) -> list[dict[str, Any]]:
    """Nearest-neighbor matching on unique body vectors. Opt-in only.

    Intentionally unused in v0.1 because TIER_D_MAX_PAIRS defaults to 0.
    Implemented with KDTree on unique body vectors, not N×N dense matching.
    """
    del df, already, limit
    return []


def candidate_summary(pairs: pd.DataFrame) -> dict[str, Any]:
    if pairs.empty:
        return {"n_pairs": 0, "by_tier": {}}
    by_tier = pairs["pair_tier"].value_counts().to_dict()
    return {
        "n_pairs": int(len(pairs)),
        "by_tier": {str(k): int(v) for k, v in by_tier.items()},
        "n_unique_pair_id": int(pairs["pair_id"].nunique()),
        "n_self_pairs": int((pairs["anchor_sample_id"] == pairs["counterfactual_sample_id"]).sum()),
        "n_same_target": int((pairs["anchor_target_sha256"] == pairs["counterfactual_target_sha256"]).sum()),
        "n_cross_split": int(pairs["cross_split"].sum()) if "cross_split" in pairs else 0,
        "n_leakage_any": int(pairs["leakage_any"].sum()) if "leakage_any" in pairs else 0,
        "mean_control_score": float(pairs["control_score"].mean()) if "control_score" in pairs else None,
        "intervention_types": {
            str(k): int(v) for k, v in pairs["measurement_intervention_type"].value_counts().items()
        }
        if "measurement_intervention_type" in pairs
        else {},
        "pair_split": {str(k): int(v) for k, v in pairs["pair_split"].value_counts().items()}
        if "pair_split" in pairs
        else {},
    }
