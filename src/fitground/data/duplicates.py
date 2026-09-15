"""Duplicate and train/eval leakage detection."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import pandas as pd


def _pair_key(a: str | None, b: str | None) -> str | None:
    if a is None or b is None:
        return None
    return f"{a}|{b}"


def annotate_duplicates_and_leakage(df: pd.DataFrame) -> pd.DataFrame:
    """Add duplicate and leakage flags in-place, return df."""
    out = df.copy()

    # Record-level exact duplicate: same triple of image md5s.
    record_key = (
        out["person_md5"].astype(str)
        + "|"
        + out["garment_md5"].astype(str)
        + "|"
        + out["target_md5"].astype(str)
    )
    record_counts = record_key.value_counts()
    dup_records = set(record_counts[record_counts > 1].index)
    out["duplicate_record_exact"] = record_key.isin(dup_records)

    for col, flag_col in (
        ("person_md5", "duplicate_person_md5"),
        ("garment_md5", "duplicate_garment_md5"),
        ("target_md5", "duplicate_target_md5"),
    ):
        counts = out[col].value_counts()
        dup_vals = set(counts[counts > 1].index) - {None, "None", "nan"}
        out[flag_col] = out[col].isin(dup_vals)

    pair_keys = out.apply(
        lambda r: _pair_key(r.get("person_md5"), r.get("garment_md5")), axis=1
    )
    pair_counts = pair_keys.value_counts()
    dup_pairs = set(pair_counts[pair_counts > 1].index) - {None}
    out["duplicate_person_garment_pair"] = pair_keys.isin(dup_pairs)

    # Train/eval leakage: same md5 appears in both splits.
    train = out[out["source_split"] == "train"]
    eval_ = out[out["source_split"] == "eval"]

    train_person = set(train["person_md5"].dropna())
    train_garment = set(train["garment_md5"].dropna())
    train_target = set(train["target_md5"].dropna())
    train_pairs = set(
        _pair_key(r.person_md5, r.garment_md5)
        for r in train.itertuples()
        if r.person_md5 and r.garment_md5
    )

    eval_person = set(eval_["person_md5"].dropna())
    eval_garment = set(eval_["garment_md5"].dropna())
    eval_target = set(eval_["target_md5"].dropna())

    overlap_person = train_person & eval_person
    overlap_garment = train_garment & eval_garment
    overlap_target = train_target & eval_target

    out["leakage_train_eval_person"] = out["person_md5"].isin(overlap_person)
    out["leakage_train_eval_garment"] = out["garment_md5"].isin(overlap_garment)
    out["leakage_train_eval_target"] = out["target_md5"].isin(overlap_target)

    eval_pairs = {
        _pair_key(r.person_md5, r.garment_md5)
        for r in eval_.itertuples()
        if r.person_md5 and r.garment_md5
    }
    overlap_pairs = train_pairs & eval_pairs
    out["leakage_train_eval_pair"] = pair_keys.isin(overlap_pairs)

    # Flag suspicious samples with leakage.
    leakage_mask = (
        out["leakage_train_eval_person"]
        | out["leakage_train_eval_garment"]
        | out["leakage_train_eval_target"]
        | out["leakage_train_eval_pair"]
    )
    for idx in out.index[leakage_mask]:
        flags = list(out.at[idx, "quality_flags"]) if out.at[idx, "quality_flags"] else []
        if "possible_train_eval_leakage" not in flags:
            flags.append("possible_train_eval_leakage")
        out.at[idx, "quality_flags"] = flags
        if out.at[idx, "quality_status"] == "VALID":
            out.at[idx, "quality_status"] = "SUSPICIOUS"

    dup_mask = (
        out["duplicate_record_exact"]
        | out["duplicate_person_md5"]
        | out["duplicate_garment_md5"]
        | out["duplicate_target_md5"]
        | out["duplicate_person_garment_pair"]
    )
    for idx in out.index[dup_mask]:
        flags = list(out.at[idx, "quality_flags"]) if out.at[idx, "quality_flags"] else []
        if "possible_duplicate" not in flags:
            flags.append("possible_duplicate")
        out.at[idx, "quality_flags"] = flags
        if out.at[idx, "quality_status"] == "VALID":
            out.at[idx, "quality_status"] = "SUSPICIOUS"

    return out


def near_duplicate_phash_groups(
    df: pd.DataFrame, threshold: int = 5
) -> dict[str, list[str]]:
    """
    Find near-duplicate groups via perceptual hash Hamming distance.

    Uses simple bucket grouping — O(n) per role. Returns role -> list of group ids.
    """
    import imagehash

    groups: dict[str, list[str]] = {}
    for role in ("person", "garment", "target"):
        col = f"{role}_phash"
        hashes = df[col].dropna().unique()
        visited: set[str] = set()
        group_ids: list[str] = []
        hash_list = list(hashes)
        for i, h1 in enumerate(hash_list):
            if h1 in visited:
                continue
            cluster = [h1]
            visited.add(h1)
            try:
                ih1 = imagehash.hex_to_hash(h1)
            except Exception:
                continue
            for h2 in hash_list[i + 1 :]:
                if h2 in visited:
                    continue
                try:
                    ih2 = imagehash.hex_to_hash(h2)
                    if ih1 - ih2 <= threshold:
                        cluster.append(h2)
                        visited.add(h2)
                except Exception:
                    continue
            if len(cluster) > 1:
                group_ids.append(f"{role}_near_dup_{len(group_ids)}")
        groups[role] = group_ids
    return groups


def leakage_summary(df: pd.DataFrame) -> dict[str, Any]:
    return {
        "train_eval_person_overlap": int(df["leakage_train_eval_person"].sum()),
        "train_eval_garment_overlap": int(df["leakage_train_eval_garment"].sum()),
        "train_eval_target_overlap": int(df["leakage_train_eval_target"].sum()),
        "train_eval_pair_overlap": int(df["leakage_train_eval_pair"].sum()),
        "exact_record_duplicates": int(df["duplicate_record_exact"].sum()),
        "duplicate_person_md5": int(df["duplicate_person_md5"].sum()),
        "duplicate_garment_md5": int(df["duplicate_garment_md5"].sum()),
        "duplicate_target_md5": int(df["duplicate_target_md5"].sum()),
        "duplicate_person_garment_pair": int(df["duplicate_person_garment_pair"].sum()),
    }
