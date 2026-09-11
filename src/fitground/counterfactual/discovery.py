"""Scalable grouping analysis for measurement-counterfactual structure.

Never materializes an N×N dense matrix. Grouping uses pandas groupby;
near-vector search uses unique-vector KDTree / hashing / binning.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from fitground.config import MEANINGFUL_GARMENT_DELTA_CM, MEASUREMENT_EQUAL_ATOL, PHASH_FAMILY_HAMMING_MAX
from fitground.counterfactual.schema import (
    BODY_VECTOR_FIELDS,
    CLOTH_SHA256_FIELD,
    GARMENT_VECTOR_FIELDS,
    RELATIONAL_VECTOR_FIELDS,
    jsonable,
)

BODY = list(BODY_VECTOR_FIELDS)
GARMENT = list(GARMENT_VECTOR_FIELDS)
RELATIONAL = list(RELATIONAL_VECTOR_FIELDS)
ALL_MEAS = BODY + GARMENT + RELATIONAL


def phash_hamming(a: Any, b: Any) -> int:
    if a is None or b is None or (isinstance(a, float) and np.isnan(a)):
        return 64
    sa, sb = str(a), str(b)
    if sa in {"", "nan", "None"} or sb in {"", "nan", "None"}:
        return 64
    try:
        return (int(sa, 16) ^ int(sb, 16)).bit_count()
    except ValueError:
        return 64


def size_distribution(sizes: pd.Series) -> dict[str, Any]:
    if len(sizes) == 0:
        return {
            "n_groups": 0,
            "n_rows": 0,
            "n_groups_gt1": 0,
            "n_rows_in_gt1": 0,
            "min": 0,
            "p50": 0.0,
            "p90": 0.0,
            "p99": 0.0,
            "max": 0,
            "size_histogram_head": {},
        }
    vc = sizes.value_counts().sort_index()
    hist = {str(int(k)): int(v) for k, v in vc.head(20).items()}
    return {
        "n_groups": int(len(sizes)),
        "n_rows": int(sizes.sum()),
        "n_groups_gt1": int((sizes > 1).sum()),
        "n_rows_in_gt1": int(sizes[sizes > 1].sum()),
        "min": int(sizes.min()),
        "p50": float(sizes.quantile(0.50)),
        "p90": float(sizes.quantile(0.90)),
        "p99": float(sizes.quantile(0.99)),
        "max": int(sizes.max()),
        "size_histogram_head": hist,
    }


def _nunique_gt1_any(grouped: pd.DataFrame, cols: list[str]) -> pd.Index:
    nu = grouped[cols].nunique()
    mask = (nu > 1).any(axis=1)
    return nu.index[mask]


def _constant_mask(grouped_nunique: pd.DataFrame) -> pd.Series:
    return (grouped_nunique <= 1).all(axis=1)


def grid_fraction(series: pd.Series, step: float) -> float:
    s = pd.to_numeric(series, errors="coerce").dropna().to_numpy(dtype=np.float64)
    if s.size == 0:
        return 0.0
    on = np.isclose(s / step - np.round(s / step), 0.0, atol=1e-8)
    return float(on.mean())


def unique_after_round(df: pd.DataFrame, cols: list[str], decimals: int) -> int:
    rounded = np.round(df[cols].to_numpy(dtype=np.float64), decimals)
    return int(np.unique(rounded, axis=0).shape[0])


def exact_vector_stats(df: pd.DataFrame, cols: list[str], decimals: int = 6) -> dict[str, Any]:
    arr = np.round(df[cols].to_numpy(dtype=np.float64), decimals)
    uniq, counts = np.unique(arr, axis=0, return_counts=True)
    repeated = counts > 1
    return {
        "n_rows": int(arr.shape[0]),
        "n_unique_vectors": int(uniq.shape[0]),
        "n_repeated_vectors": int(repeated.sum()),
        "n_rows_on_repeated_vectors": int(counts[repeated].sum()),
        "max_vector_frequency": int(counts.max()) if counts.size else 0,
        "mean_vector_frequency": float(counts.mean()) if counts.size else 0.0,
    }


def near_vector_stats(
    df: pd.DataFrame,
    cols: list[str],
    radius: float,
    decimals: int = 6,
) -> dict[str, Any]:
    """KDTree on unique vectors only — not a dense N×N matrix."""
    arr = np.round(df[cols].dropna().to_numpy(dtype=np.float64), decimals)
    if arr.shape[0] == 0:
        return {"radius": radius, "n_unique": 0, "n_near_pairs": 0, "n_unique_with_neighbor": 0}
    uniq = np.unique(arr, axis=0)
    n_unique = int(uniq.shape[0])
    if n_unique < 2:
        return {"radius": radius, "n_unique": n_unique, "n_near_pairs": 0, "n_unique_with_neighbor": 0}
    tree = cKDTree(uniq)
    pairs = tree.query_pairs(r=radius, output_type="set")
    touched: set[int] = set()
    for i, j in pairs:
        touched.add(i)
        touched.add(j)
    return {
        "radius": radius,
        "n_unique": n_unique,
        "n_near_pairs": int(len(pairs)),
        "n_unique_with_neighbor": int(len(touched)),
        "method": "cKDTree.query_pairs_on_unique_vectors",
    }


def _varying_fields(nunique_row: pd.Series, cols: list[str]) -> list[str]:
    return [c for c in cols if int(nunique_row[c]) > 1]


def analyze_person_cloth_groups(df: pd.DataFrame) -> dict[str, Any]:
    """A. same person image + same cloth image."""
    key = ["person_sha256", CLOTH_SHA256_FIELD]
    work = df.dropna(subset=key).copy()
    sizes = work.groupby(key, sort=False).size()
    out: dict[str, Any] = {
        "group_key": ["person_sha256", "cloth_sha256=garment_sha256"],
        "size": size_distribution(sizes),
    }
    multi_idx = sizes[sizes > 1].index
    out["groups_with_gt1_row"] = int(len(multi_idx))
    if len(multi_idx) == 0:
        out["groups_with_different_target"] = 0
        out["groups_with_different_garment_measurements"] = 0
        out["groups_with_different_body_measurements"] = 0
        out["tier_a_groups"] = 0
        out["body_constant_in_multi"] = None
        out["garment_variation_types"] = {}
        out["note"] = (
            "No (person_sha256, garment_sha256) group has more than one row. "
            "TIER A exact same-person-image + same-cloth-image counterfactuals do not exist."
        )
        return out

    multi = work.set_index(key).loc[multi_idx].reset_index()
    grouped = multi.groupby(key, sort=False)
    target_nu = grouped["target_sha256"].nunique()
    body_nu = grouped[BODY].nunique()
    garm_nu = grouped[GARMENT].nunique()
    different_target = target_nu > 1
    different_body = (body_nu > 1).any(axis=1)
    different_garm = (garm_nu > 1).any(axis=1)
    body_constant = _constant_mask(body_nu)
    tier_a = different_target & different_garm & body_constant

    var_types: Counter[str] = Counter()
    single_var = 0
    preset_like = 0
    for idx in garm_nu.index[different_garm.to_numpy()]:
        fields = _varying_fields(garm_nu.loc[idx], GARMENT)
        label = "+".join(fields) if fields else "none"
        var_types[label] += 1
        if len(fields) == 1:
            single_var += 1
            sub = grouped.get_group(idx)
            nlev = int(sub[fields[0]].nunique())
            if 2 <= nlev <= 8:
                preset_like += 1

    out.update(
        {
            "groups_with_different_target": int(different_target.sum()),
            "groups_with_different_garment_measurements": int(different_garm.sum()),
            "groups_with_different_body_measurements": int(different_body.sum()),
            "groups_body_constant": int(body_constant.sum()),
            "tier_a_groups": int(tier_a.sum()),
            "tier_a_rows": int(sizes.loc[tier_a.index[tier_a]].sum()) if int(tier_a.sum()) else 0,
            "single_variable_garment_change_groups": int(single_var),
            "preset_like_level_groups": int(preset_like),
            "garment_variation_types": dict(var_types),
        }
    )
    return out


def analyze_person_groups(df: pd.DataFrame) -> dict[str, Any]:
    """B. same person image reused across garments."""
    work = df.dropna(subset=["person_sha256"]).copy()
    sizes = work.groupby("person_sha256", sort=False).size()
    out: dict[str, Any] = {
        "group_key": ["person_sha256"],
        "size": size_distribution(sizes),
        "unique_person_images": int(work["person_sha256"].nunique()),
    }
    multi_ids = sizes[sizes > 1].index
    if len(multi_ids) == 0:
        out["body_consistency_issues"] = 0
        out["tier_c_groups"] = 0
        return out

    multi = work[work["person_sha256"].isin(multi_ids)]
    grouped = multi.groupby("person_sha256", sort=False)
    body_nu = grouped[BODY].nunique()
    garm_nu = grouped[GARMENT].nunique()
    ease_nu = grouped[["bust_ease_cm", "bust_ease_ratio"]].nunique()
    cloth_nu = grouped[CLOTH_SHA256_FIELD].nunique()
    target_nu = grouped["target_sha256"].nunique()
    phash_nu = grouped["garment_phash"].nunique()
    inconsistent_body = (body_nu > 1).any(axis=1)
    body_constant = _constant_mask(body_nu)
    garment_varies = (garm_nu > 1).any(axis=1)
    ease_varies = (ease_nu > 1).any(axis=1)
    different_cloth = cloth_nu > 1
    different_target = target_nu > 1

    # TIER C: same person, different cloth, body constant, garment meas varies, target varies
    tier_c = body_constant & different_cloth & garment_varies & different_target
    # TIER B candidate groups: same person, multiple cloths, some shared/near phash
    family = _person_garment_family_stats(multi)

    out.update(
        {
            "body_consistency_issues": int(inconsistent_body.sum()),
            "body_consistency_issue_rows": int(sizes.loc[inconsistent_body.index[inconsistent_body]].sum())
            if int(inconsistent_body.sum())
            else 0,
            "groups_body_constant_and_multi": int(body_constant.sum()),
            "groups_with_different_cloth": int(different_cloth.sum()),
            "groups_with_different_target": int(different_target.sum()),
            "groups_with_garment_measurement_variation": int(garment_varies.sum()),
            "groups_with_ease_variation": int(ease_varies.sum()),
            "groups_with_multiple_garment_phash": int((phash_nu > 1).sum()),
            "tier_c_groups": int(tier_c.sum()),
            "tier_c_rows": int(sizes.loc[tier_c.index[tier_c]].sum()) if int(tier_c.sum()) else 0,
            "max_garments_per_person": int(cloth_nu.max()) if len(cloth_nu) else 0,
            "garment_family": family,
        }
    )
    if int(inconsistent_body.sum()) > 0:
        sample_ids = inconsistent_body.index[inconsistent_body][:20].tolist()
        out["body_consistency_issue_person_sha256_sample"] = sample_ids
    return out


def _person_garment_family_stats(multi: pd.DataFrame) -> dict[str, Any]:
    """Within-person pairwise cloth-image family (k is small; not global N²)."""
    n_exact_phash_groups = 0
    n_near_phash_groups = 0
    n_exact_phash_pairs = 0
    n_near_phash_pairs = 0
    n_exact_phash_meas_diff = 0
    n_near_phash_meas_diff = 0
    n_exact_phash_target_diff = 0
    ham_hist: Counter[int] = Counter()

    cols = ["garment_sha256", "garment_phash", "target_sha256", *GARMENT]
    for _, g in multi.groupby("person_sha256", sort=False):
        if len(g) < 2:
            continue
        recs = g[cols].to_dict("records")
        exact_hit = False
        near_hit = False
        for i in range(len(recs)):
            for j in range(i + 1, len(recs)):
                a, b = recs[i], recs[j]
                if a["garment_sha256"] == b["garment_sha256"]:
                    continue  # TIER A, counted elsewhere
                ham = phash_hamming(a["garment_phash"], b["garment_phash"])
                ham_hist[ham] += 1
                meas_diff = any(
                    abs(float(a[f]) - float(b[f])) > MEANINGFUL_GARMENT_DELTA_CM for f in GARMENT
                )
                tgt_diff = a["target_sha256"] != b["target_sha256"]
                if ham == 0:
                    exact_hit = True
                    n_exact_phash_pairs += 1
                    if meas_diff:
                        n_exact_phash_meas_diff += 1
                    if tgt_diff:
                        n_exact_phash_target_diff += 1
                elif ham <= PHASH_FAMILY_HAMMING_MAX:
                    near_hit = True
                    n_near_phash_pairs += 1
                    if meas_diff:
                        n_near_phash_meas_diff += 1
        if exact_hit:
            n_exact_phash_groups += 1
        if near_hit:
            n_near_phash_groups += 1

    ham_head = {str(k): int(ham_hist[k]) for k in sorted(ham_hist)[:16]}
    return {
        "phash_hamming_max_for_family": PHASH_FAMILY_HAMMING_MAX,
        "groups_with_exact_garment_phash_family": n_exact_phash_groups,
        "groups_with_near_garment_phash_family": n_near_phash_groups,
        "pairs_exact_garment_phash_different_sha256": n_exact_phash_pairs,
        "pairs_near_garment_phash": n_near_phash_pairs,
        "pairs_exact_phash_and_measurement_diff": n_exact_phash_meas_diff,
        "pairs_exact_phash_and_target_diff": n_exact_phash_target_diff,
        "pairs_near_phash_and_measurement_diff": n_near_phash_meas_diff,
        "within_person_cloth_phash_hamming_hist_head": ham_head,
        "tier_b_groups": n_exact_phash_groups,
        "tier_b_near_groups": n_near_phash_groups,
    }


def analyze_cloth_groups(df: pd.DataFrame) -> dict[str, Any]:
    """C. same cloth image reused across bodies / measurement conditions."""
    work = df.dropna(subset=[CLOTH_SHA256_FIELD]).copy()
    sizes = work.groupby(CLOTH_SHA256_FIELD, sort=False).size()
    out: dict[str, Any] = {
        "group_key": ["cloth_sha256=garment_sha256"],
        "size": size_distribution(sizes),
        "unique_cloth_images": int(work[CLOTH_SHA256_FIELD].nunique()),
    }
    multi_ids = sizes[sizes > 1].index
    if len(multi_ids) == 0:
        out["garment_measurement_inconsistency_groups"] = 0
        return out

    multi = work[work[CLOTH_SHA256_FIELD].isin(multi_ids)]
    grouped = multi.groupby(CLOTH_SHA256_FIELD, sort=False)
    garm_nu = grouped[GARMENT].nunique()
    body_nu = grouped[BODY].nunique()
    person_nu = grouped["person_sha256"].nunique()
    target_nu = grouped["target_sha256"].nunique()
    inconsistent_garm = (garm_nu > 1).any(axis=1)
    body_varies = (body_nu > 1).any(axis=1)
    different_person = person_nu > 1
    different_target = target_nu > 1
    garment_constant = _constant_mask(garm_nu)

    # Same visual garment, different measurement, different body
    intervention_or_bug = inconsistent_garm & different_person
    # Same visual garment, constant measurement, different body — body CF
    body_cf = garment_constant & different_person & different_target & body_varies

    var_types: Counter[str] = Counter()
    for idx in garm_nu.index[inconsistent_garm.to_numpy()]:
        fields = _varying_fields(garm_nu.loc[idx], GARMENT)
        var_types["+".join(fields) if fields else "none"] += 1

    out.update(
        {
            "garment_measurement_inconsistency_groups": int(inconsistent_garm.sum()),
            "garment_measurement_inconsistency_rows": int(
                sizes.loc[inconsistent_garm.index[inconsistent_garm]].sum()
            )
            if int(inconsistent_garm.sum())
            else 0,
            "groups_with_different_person": int(different_person.sum()),
            "groups_with_different_target": int(different_target.sum()),
            "groups_with_body_variation": int(body_varies.sum()),
            "groups_garment_measurements_constant": int(garment_constant.sum()),
            "same_cloth_diff_measurement_diff_body_groups": int(intervention_or_bug.sum()),
            "same_cloth_constant_measurement_diff_body_groups": int(body_cf.sum()),
            "inconsistent_garment_variation_types": dict(var_types),
            "interpretation_note": (
                "If the same cloth SHA256 has different garment_*_cm values, either the "
                "measurement is an instance-level intervention (not a property of the "
                "cloth image) or the metadata is inconsistent. Distinguishing these "
                "requires checking whether garment values track body size or discrete presets."
            ),
        }
    )
    return out


def analyze_target_groups(df: pd.DataFrame) -> dict[str, Any]:
    """D. repeated target images → shortcut / leakage risk."""
    work = df.dropna(subset=["target_sha256"]).copy()
    sizes = work.groupby("target_sha256", sort=False).size()
    out: dict[str, Any] = {
        "group_key": ["target_sha256"],
        "size": size_distribution(sizes),
        "unique_target_images": int(work["target_sha256"].nunique()),
    }
    multi_ids = sizes[sizes > 1].index
    if len(multi_ids) == 0:
        out["cross_split_duplicate_targets"] = 0
        return out

    multi = work[work["target_sha256"].isin(multi_ids)]
    split_nu = multi.groupby("target_sha256")["source_split"].nunique()
    person_nu = multi.groupby("target_sha256")["person_sha256"].nunique()
    cloth_nu = multi.groupby("target_sha256")[CLOTH_SHA256_FIELD].nunique()
    out.update(
        {
            "duplicate_target_groups": int(len(multi_ids)),
            "duplicate_target_rows": int(sizes.loc[multi_ids].sum()),
            "cross_split_duplicate_targets": int((split_nu > 1).sum()),
            "duplicate_targets_with_different_person": int((person_nu > 1).sum()),
            "duplicate_targets_with_different_cloth": int((cloth_nu > 1).sum()),
            "leakage_risk": (
                "Repeated target SHA256 can create identity shortcuts if a model memorizes "
                "the try-on image. Cross-split duplicates are leakage. Pairs that share a "
                "target are invalid counterfactuals."
            ),
        }
    )
    return out


def analyze_measurement_vectors(df: pd.DataFrame) -> dict[str, Any]:
    """E. exact / near / quantized measurement vectors (hash + KDTree)."""
    work = df.dropna(subset=ALL_MEAS).copy()
    field_uniques = {c: int(work[c].nunique()) for c in ALL_MEAS}
    field_uniques_1dp = {c: int(work[c].round(1).nunique()) for c in ALL_MEAS}
    field_uniques_2dp = {c: int(work[c].round(2).nunique()) for c in ALL_MEAS}
    grids = {}
    for c in ALL_MEAS:
        grids[c] = {
            "frac_on_0.01": grid_fraction(work[c], 0.01),
            "frac_on_0.05": grid_fraction(work[c], 0.05),
            "frac_on_0.1": grid_fraction(work[c], 0.1),
            "frac_on_0.5": grid_fraction(work[c], 0.5),
            "frac_on_1.0": grid_fraction(work[c], 1.0),
        }

    ease = work["bust_ease_ratio"]
    ease_1dp = ease.round(1)
    ease_2dp = ease.round(2)
    top_ease = ease_1dp.value_counts().head(15)
    top_ease_2 = ease_2dp.value_counts().head(20)

    body_exact = exact_vector_stats(work, BODY)
    garm_exact = exact_vector_stats(work, GARMENT)
    rel_exact = exact_vector_stats(work, RELATIONAL)
    full_exact = exact_vector_stats(work, BODY + GARMENT)

    return {
        "n_complete_measurement_rows": int(len(work)),
        "unique_values_raw": field_uniques,
        "unique_values_1dp": field_uniques_1dp,
        "unique_values_2dp": field_uniques_2dp,
        "grid_occupancy": grids,
        "bust_ease_ratio_top_1dp": {str(k): int(v) for k, v in top_ease.items()},
        "bust_ease_ratio_top_2dp": {str(k): int(v) for k, v in top_ease_2.items()},
        "bust_ease_ratio_unique_1dp": int(ease_1dp.nunique()),
        "bust_ease_ratio_unique_2dp": int(ease_2dp.nunique()),
        "body_exact": body_exact,
        "garment_exact": garm_exact,
        "relational_exact": rel_exact,
        "body_plus_garment_exact": full_exact,
        "quantized_unique_body_1dp": unique_after_round(work, BODY, 1),
        "quantized_unique_garment_1dp": unique_after_round(work, GARMENT, 1),
        "quantized_unique_relational_2dp": unique_after_round(work, RELATIONAL, 2),
        "near_body_radius_1cm": near_vector_stats(work, BODY, radius=1.0),
        "near_body_radius_2cm": near_vector_stats(work, BODY, radius=2.0),
        "near_garment_radius_1cm": near_vector_stats(work, GARMENT, radius=1.0),
        "near_garment_radius_2cm": near_vector_stats(work, GARMENT, radius=2.0),
        "near_relational_radius_0.02": near_vector_stats(work, RELATIONAL, radius=0.02),
        "preset_like_hypothesis": (
            "Discrete unique-value counts and grid occupancy are OBSERVED. "
            "Official FIT documentation does not confirm garment scaling presets; "
            "that remains HYPOTHESIZED until visual/docs verification."
        ),
    }


def summarize_tiers(a: dict[str, Any], b: dict[str, Any], c: dict[str, Any]) -> dict[str, Any]:
    family = b.get("garment_family") or {}
    return {
        "tier_a_groups": int(a.get("tier_a_groups") or 0),
        "tier_b_groups_exact_phash_family": int(family.get("tier_b_groups") or 0),
        "tier_b_groups_near_phash_family": int(family.get("tier_b_near_groups") or 0),
        "tier_c_groups_same_person_diff_garment": int(b.get("tier_c_groups") or 0),
        "same_cloth_diff_measurement_diff_body_groups": int(
            c.get("same_cloth_diff_measurement_diff_body_groups") or 0
        ),
        "same_cloth_constant_measurement_diff_body_groups": int(
            c.get("same_cloth_constant_measurement_diff_body_groups") or 0
        ),
        "priority": [
            "TIER A: same person image + same cloth image + different measurement + different target",
            "TIER B: same person + garment phash family + controlled measurement variation",
            "TIER C: same person + measurement-varying garment alternatives (cloth image also changes)",
            "TIER D: nearest-neighbor matching (deferred unless A/B insufficient)",
        ],
    }


def run_structure_discovery(df: pd.DataFrame) -> dict[str, Any]:
    usable = df[df["usable_for_fitground"]].copy() if "usable_for_fitground" in df.columns else df
    a = analyze_person_cloth_groups(usable)
    b = analyze_person_groups(usable)
    c = analyze_cloth_groups(usable)
    d = analyze_target_groups(usable)
    e = analyze_measurement_vectors(usable)
    tiers = summarize_tiers(a, b, c)
    strongest = "NONE"
    if tiers["tier_a_groups"] >= 50:
        strongest = "A"
    elif tiers["tier_b_groups_exact_phash_family"] >= 50:
        strongest = "B"
    elif tiers["tier_c_groups_same_person_diff_garment"] > 0:
        strongest = "C"
        if tiers["tier_a_groups"] > 0:
            strongest = "A_SPARSE_THEN_C"
        elif tiers["tier_b_groups_exact_phash_family"] > 0:
            strongest = "B_SPARSE_THEN_C"
    elif tiers["tier_b_groups_exact_phash_family"] > 0:
        strongest = "B"
    elif tiers["tier_a_groups"] > 0:
        strongest = "A"
    elif tiers["same_cloth_constant_measurement_diff_body_groups"] > 0:
        strongest = "CLOTH_HELD_BODY_VARIED"
    report = {
        "n_rows": int(len(df)),
        "n_usable": int(len(usable)),
        "n_train": int((df["source_split"] == "train").sum()),
        "n_eval": int((df["source_split"] == "eval").sum()),
        "A_same_person_same_cloth": a,
        "B_same_person": b,
        "C_same_cloth": c,
        "D_same_target": d,
        "E_measurement_vectors": e,
        "tier_summary": tiers,
        "strongest_available_unit": strongest,
        "tier_d_policy": "Do not construct TIER D unless TIER A and TIER B are both empty/insufficient.",
    }
    return jsonable(report)
