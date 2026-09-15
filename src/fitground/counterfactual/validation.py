"""Candidate schema checks and shortcut / split audits."""

from __future__ import annotations

from collections import Counter
from typing import Any

import numpy as np
import pandas as pd

from fitground.counterfactual.schema import PAIR_REQUIRED_COLUMNS, make_pair_id, unordered_pair_key


class CandidateValidationError(ValueError):
    pass


def validate_candidates(pairs: pd.DataFrame, *, require_rows: bool = False) -> dict[str, Any]:
    if require_rows and pairs.empty:
        raise CandidateValidationError("candidate table is empty")
    missing = [c for c in PAIR_REQUIRED_COLUMNS if c not in pairs.columns]
    if missing and not pairs.empty:
        raise CandidateValidationError(f"missing columns: {missing}")
    if pairs.empty:
        return {
            "ok": True,
            "n_pairs": 0,
            "n_unique_pair_id": 0,
            "n_self_pairs": 0,
            "n_duplicate_unordered": 0,
            "n_pair_id_mismatch": 0,
            "n_delta_mismatch": 0,
            "n_same_target": 0,
        }

    n_self = int((pairs["anchor_sample_id"] == pairs["counterfactual_sample_id"]).sum())
    keys = [
        unordered_pair_key(a, b)
        for a, b in zip(pairs["anchor_sample_id"], pairs["counterfactual_sample_id"], strict=True)
    ]
    n_dup = int(len(keys) - len(set(keys)))
    expected_ids = [
        make_pair_id(t, a, b)
        for t, a, b in zip(
            pairs["pair_tier"],
            pairs["anchor_sample_id"],
            pairs["counterfactual_sample_id"],
            strict=True,
        )
    ]
    n_id_mismatch = int(sum(e != p for e, p in zip(expected_ids, pairs["pair_id"], strict=True)))

    bust_delta = (
        pairs["counterfactual_garment_bust_cm"] - pairs["anchor_garment_bust_cm"]
    )
    ease_delta = pairs["counterfactual_bust_ease_cm"] - pairs["anchor_bust_ease_cm"]
    n_delta = int(
        (~np.isclose(bust_delta, pairs["delta_garment_bust_cm"], atol=1e-9, rtol=0)).sum()
        + (~np.isclose(ease_delta, pairs["delta_bust_ease_cm"], atol=1e-9, rtol=0)).sum()
    )
    n_same_target = int(
        (pairs["anchor_target_sha256"] == pairs["counterfactual_target_sha256"]).sum()
    )
    ok = n_self == 0 and n_dup == 0 and n_id_mismatch == 0 and n_delta == 0 and n_same_target == 0
    result = {
        "ok": ok,
        "n_pairs": int(len(pairs)),
        "n_unique_pair_id": int(pairs["pair_id"].nunique()),
        "n_self_pairs": n_self,
        "n_duplicate_unordered": n_dup,
        "n_pair_id_mismatch": n_id_mismatch,
        "n_delta_mismatch": n_delta,
        "n_same_target": n_same_target,
    }
    if not ok:
        raise CandidateValidationError(f"candidate validation failed: {result}")
    return result


def ease_bin(value: float) -> str:
    if value < -2:
        return "negative"
    if value < 2:
        return "near_zero"
    if value < 15:
        return "moderate_positive"
    return "large_positive"


def shortcut_audit(pairs: pd.DataFrame) -> dict[str, Any]:
    """Attack the candidate design for measurement / identity / split shortcuts."""
    if pairs.empty:
        return {"n_pairs": 0, "verdict": "NO_PAIRS", "issues": ["empty candidate table"]}

    issues: list[str] = []
    notes: list[str] = []
    n = len(pairs)

    unique_anchor_ease_1dp = int(pairs["anchor_bust_ease_ratio"].round(1).nunique())
    unique_cf_ease_1dp = int(pairs["counterfactual_bust_ease_ratio"].round(1).nunique())
    unique_delta_ease_2dp = int(pairs["delta_bust_ease_ratio"].round(2).nunique())
    unique_delta_ease_1dp = int(pairs["delta_bust_ease_ratio"].round(1).nunique())

    delta = pairs["delta_bust_ease_ratio"].to_numpy(dtype=np.float64)
    on_005 = float(np.isclose(delta / 0.05 - np.round(delta / 0.05), 0.0, atol=1e-8).mean())
    on_01 = float(np.isclose(delta / 0.1 - np.round(delta / 0.1), 0.0, atol=1e-8).mean())

    # Direction is defined by construction (anchor = lower ease). That is not a
    # label shortcut; it is the IV encoding. The risk is discrete preset values.
    if unique_delta_ease_1dp <= 6:
        issues.append(
            "delta_bust_ease_ratio has very few 1dp values; a model could latch onto "
            "a handful of preset-like ease steps instead of continuous measurement."
        )
    if on_005 >= 0.8:
        issues.append(
            ">=80% of pair ease-ratio deltas fall on a 0.05 grid (quantization shortcut risk)."
        )

    frac_same_person = float(pairs["same_person_image"].mean())
    frac_same_cloth = float(pairs["same_cloth_image"].mean())
    if frac_same_cloth < 0.01 and (pairs["pair_tier"] == "A").sum() == 0:
        issues.append(
            "Almost no pairs share a cloth image; garment appearance is an uncontrolled confound "
            "for TIER C-dominant designs."
        )

    # Can split be recovered from measurements alone?
    split_from_ease = _purity_by_key(pairs, "pair_split", pairs["anchor_bust_ease_ratio"].round(1))
    shard_from_ease = _purity_by_key(
        pairs, "anchor_shard_id", pairs["anchor_bust_ease_ratio"].round(1)
    )
    quality_from_ease = _purity_by_key(
        pairs, "quality_anchor", pairs["anchor_bust_ease_ratio"].round(1)
    )

    if split_from_ease >= 0.95 and pairs["pair_split"].nunique() > 1:
        issues.append("ease-ratio 1dp bins almost perfectly recover pair_split.")
    if shard_from_ease >= 0.95:
        issues.append("ease-ratio 1dp bins almost perfectly recover anchor shard (ordering/shard shortcut).")

    frac_leak = float(pairs["leakage_any"].mean()) if "leakage_any" in pairs else 0.0
    frac_cross = float(pairs["cross_split"].mean()) if "cross_split" in pairs else 0.0
    frac_dup = float(pairs["duplicate_contamination"].mean()) if "duplicate_contamination" in pairs else 0.0

    # Identity shortcut: if every pair has a unique person, identity still changes
    # across pairs (between-pair) even if within-pair person is held.
    n_person = int(pd.concat([pairs["anchor_person_sha256"], pairs["counterfactual_person_sha256"]]).nunique())
    n_cloth = int(pd.concat([pairs["anchor_cloth_sha256"], pairs["counterfactual_cloth_sha256"]]).nunique())

    if frac_same_person < 1.0:
        issues.append("Some pairs do not hold person image constant.")

    intervention = pairs["measurement_intervention_type"].value_counts().to_dict()
    tiers = pairs["pair_tier"].value_counts().to_dict()

    verdict = "FAIL" if any("0.05 grid" in x or "very few 1dp" in x for x in issues) else "PASS_WITH_CONTROLS"
    if frac_same_cloth < 0.01 and "A" not in {str(t) for t in pairs["pair_tier"].unique()}:
        verdict = "PARTIAL_CONFOUND"
    if not issues:
        verdict = "PASS"

    notes.append(
        "Pair direction (anchor=tighter, CF=looser) is defined by construction and is not "
        "a hidden label. Shortcut risk is whether discrete ease presets, identity, shard, "
        "or quality flags can replace measurement-grounded reasoning."
    )

    return {
        "n_pairs": n,
        "verdict": verdict,
        "issues": issues,
        "notes": notes,
        "unique_anchor_ease_ratio_1dp": unique_anchor_ease_1dp,
        "unique_cf_ease_ratio_1dp": unique_cf_ease_1dp,
        "unique_delta_ease_ratio_1dp": unique_delta_ease_1dp,
        "unique_delta_ease_ratio_2dp": unique_delta_ease_2dp,
        "frac_delta_ease_on_0.05_grid": on_005,
        "frac_delta_ease_on_0.1_grid": on_01,
        "frac_same_person_image": frac_same_person,
        "frac_same_cloth_image": frac_same_cloth,
        "frac_leakage_any": frac_leak,
        "frac_cross_split": frac_cross,
        "frac_duplicate_contamination": frac_dup,
        "n_unique_person_images_in_pairs": n_person,
        "n_unique_cloth_images_in_pairs": n_cloth,
        "split_purity_from_ease_1dp": split_from_ease,
        "shard_purity_from_ease_1dp": shard_from_ease,
        "quality_purity_from_ease_1dp": quality_from_ease,
        "intervention_types": {str(k): int(v) for k, v in intervention.items()},
        "tiers": {str(k): int(v) for k, v in tiers.items()},
        "delta_bust_ease_cm": _series_stats(pairs["delta_bust_ease_cm"]),
        "delta_garment_bust_cm": _series_stats(pairs["delta_garment_bust_cm"]),
        "control_score": _series_stats(pairs["control_score"]),
        "ease_bin_pairs": dict(Counter(ease_bin(float(x)) for x in pairs["anchor_bust_ease_cm"])),
    }


def _series_stats(s: pd.Series) -> dict[str, float]:
    x = pd.to_numeric(s, errors="coerce").dropna()
    if x.empty:
        return {}
    return {
        "min": float(x.min()),
        "p25": float(x.quantile(0.25)),
        "median": float(x.median()),
        "p75": float(x.quantile(0.75)),
        "max": float(x.max()),
        "mean": float(x.mean()),
    }


def _purity_by_key(pairs: pd.DataFrame, label_col: str, key: pd.Series) -> float:
    """Mean majority-class fraction within each key bin."""
    tmp = pd.DataFrame({"k": key.astype(str), "y": pairs[label_col].astype(str)})
    def _purity(g: pd.Series) -> float:
        return float(g.value_counts().iloc[0] / len(g))
    purities = tmp.groupby("k")["y"].apply(_purity)
    return float(purities.mean()) if len(purities) else 0.0


def leakage_controlled_eval_ids(manifest: pd.DataFrame) -> list[str]:
    """Official eval sample_ids that do not carry exact-image train/eval overlap flags."""
    eval_df = manifest[manifest["source_split"] == "eval"]
    leak_cols = [
        c
        for c in (
            "leakage_train_eval_person",
            "leakage_train_eval_garment",
            "leakage_train_eval_target",
            "leakage_train_eval_pair",
        )
        if c in eval_df.columns
    ]
    if not leak_cols:
        return sorted(eval_df["sample_id"].astype(str).tolist())
    leak = eval_df[leak_cols].fillna(False).any(axis=1)
    kept = eval_df.loc[~leak, "sample_id"].astype(str)
    return sorted(kept.tolist())


def official_eval_ids(manifest: pd.DataFrame) -> list[str]:
    eval_df = manifest[manifest["source_split"] == "eval"]
    return sorted(eval_df["sample_id"].astype(str).tolist())
