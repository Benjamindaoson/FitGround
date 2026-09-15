"""Post-finalize closure audits for FIT-Clean v0.1."""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy import stats

from fitground.config import (
    EXPECTED_IMAGE_HEIGHT,
    EXPECTED_IMAGE_WIDTH,
    FIGURES_DIR,
    MANIFEST_PATH,
    REPORTS_DIR,
)

MEAS_COLS = [
    "body_height_cm", "body_bust_cm", "body_waist_cm", "body_hips_cm",
    "garment_bust_cm", "garment_length_cm", "garment_sleeve_cm",
    "bust_ease_cm", "bust_ease_ratio", "garment_length_height_ratio",
]


def load_manifest(path: Path = MANIFEST_PATH) -> pd.DataFrame:
    return pd.read_parquet(path)


def validate_manifest(df: pd.DataFrame) -> dict[str, Any]:
    n = len(df)
    train_n = int((df["source_split"] == "train").sum())
    eval_n = int((df["source_split"] == "eval").sum())
    dup_ids = int(df["sample_id"].duplicated().sum())
    return {
        "total_rows": n,
        "train_rows": train_n,
        "eval_rows": eval_n,
        "unique_sample_id": int(df["sample_id"].nunique()),
        "duplicate_sample_id": dup_ids,
        "null_sample_id": int(df["sample_id"].isna().sum()),
        "schema_columns": list(df.columns),
        "person_hash_coverage": float(df["person_sha256"].notna().mean()),
        "garment_hash_coverage": float(df["garment_sha256"].notna().mean()),
        "target_hash_coverage": float(df["target_sha256"].notna().mean()),
        "quality_sum_check": int(
            (df["quality_status"].isin(["VALID", "SUSPICIOUS", "INVALID"])).sum()
        ),
        "usable_invalid_consistency": int(
            ((df["quality_status"] == "INVALID") == (~df["usable_for_fitground"])).sum()
        ),
    }


def distribution_stats(series: pd.Series) -> dict[str, float | int]:
    s = series.dropna()
    if len(s) == 0:
        return {"count": 0, "missing": int(series.isna().sum())}
    return {
        "count": int(len(s)),
        "missing": int(series.isna().sum()),
        "mean": float(s.mean()),
        "std": float(s.std()),
        "min": float(s.min()),
        "p1": float(s.quantile(0.01)),
        "p5": float(s.quantile(0.05)),
        "p25": float(s.quantile(0.25)),
        "median": float(s.median()),
        "p75": float(s.quantile(0.75)),
        "p95": float(s.quantile(0.95)),
        "p99": float(s.quantile(0.99)),
        "max": float(s.max()),
    }


def split_distribution_audit(df: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {"ALL": {}, "train": {}, "eval": {}}
    for split_key, sub in [("ALL", df), ("train", df[df["source_split"] == "train"]),
                           ("eval", df[df["source_split"] == "eval"])]:
        out[split_key] = {col: distribution_stats(sub[col]) for col in MEAS_COLS}
    shift: dict[str, Any] = {}
    train = df[df["source_split"] == "train"]
    eval_ = df[df["source_split"] == "eval"]
    for col in MEAS_COLS:
        t = train[col].dropna()
        e = eval_[col].dropna()
        if len(t) > 0 and len(e) > 0:
            ks = float(stats.ks_2samp(t, e).statistic)
            wd = float(stats.wasserstein_distance(t, e))
            shift[col] = {"ks_statistic": ks, "wasserstein_distance": wd}
    out["train_vs_eval_shift"] = shift
    return out


def quantization_audit(df: pd.DataFrame) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for split_key, sub in [("ALL", df), ("train", df[df["source_split"] == "train"]),
                           ("eval", df[df["source_split"] == "eval"])]:
        s = sub["bust_ease_ratio"].dropna()
        r3 = s.round(3)
        r2 = s.round(2)
        r1 = s.round(1)
        top2 = Counter(r2.tolist()).most_common(15)
        result[split_key] = {
            "n": int(len(s)),
            "unique_raw": int(s.nunique()),
            "unique_rounded_3dp": int(r3.nunique()),
            "unique_rounded_2dp": int(r2.nunique()),
            "unique_rounded_1dp": int(r1.nunique()),
            "top_levels_2dp": [{"value": float(v), "count": int(c)} for v, c in top2],
            "top_level_mass_2dp": float(top2[0][1] / len(s)) if top2 and len(s) else 0.0,
        }
    return result


def image_integrity_audit(df: pd.DataFrame) -> dict[str, Any]:
    modalities = {
        "person": ("person_sha256", "person_format", "person_width", "person_height"),
        "cloth": ("garment_sha256", "garment_format", "garment_width", "garment_height"),
        "target": ("target_sha256", "target_format", "target_width", "target_height"),
    }
    n = len(df)
    report: dict[str, Any] = {"total_samples": n, "modalities": {}}
    for name, (hcol, fcol, wcol, hcol2) in modalities.items():
        missing = int(df[hcol].isna().sum())
        wrong_dim = int(
            ((df[wcol] != EXPECTED_IMAGE_WIDTH) | (df[hcol2] != EXPECTED_IMAGE_HEIGHT))
            .fillna(False)
            .sum()
        )
        non_png = int(df[fcol].dropna().ne("PNG").sum()) if fcol in df else 0
        report["modalities"][name] = {
            "checked": n,
            "missing_hash": missing,
            "unexpected_dimensions": wrong_dim,
            "non_png_format": non_png,
            "expected_768x1024_rgb_png_compliant": int(n - missing - wrong_dim - non_png),
        }
    return report


def quality_audit(df: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for split_key, sub in [("ALL", df), ("train", df[df["source_split"] == "train"]),
                           ("eval", df[df["source_split"] == "eval"])]:
        vc = sub["quality_status"].value_counts().to_dict()
        out[split_key] = {
            "total": len(sub),
            "VALID": int(vc.get("VALID", 0)),
            "SUSPICIOUS": int(vc.get("SUSPICIOUS", 0)),
            "INVALID": int(vc.get("INVALID", 0)),
            "usable_for_fitground": int(sub["usable_for_fitground"].sum()),
        }
    flag_counts: Counter[str] = Counter()
    for flags in df["quality_flags"]:
        if flags is not None and len(flags) > 0:
            for f in flags:
                flag_counts[str(f)] += 1
    out["flag_counts"] = dict(flag_counts.most_common())
    out["usable_definition"] = (
        "usable_for_fitground=True iff quality_status != INVALID. "
        "SUSPICIOUS samples remain usable unless explicitly excluded downstream."
    )
    return out


def duplicate_leakage_audit(df: pd.DataFrame) -> dict[str, Any]:
    return {
        "exact_record_duplicate": int(df["duplicate_record_exact"].sum()),
        "exact_person_image_sha256": int(df["duplicate_person_sha256"].sum()),
        "exact_cloth_image_sha256": int(df["duplicate_garment_sha256"].sum()),
        "exact_target_image_sha256": int(df["duplicate_target_sha256"].sum()),
        "exact_person_cloth_pair": int(df["duplicate_person_garment_pair"].sum()),
        "cross_split_leakage_person_image": int(df["leakage_train_eval_person"].sum()),
        "cross_split_leakage_cloth_image": int(df["leakage_train_eval_garment"].sum()),
        "cross_split_leakage_target_image": int(df["leakage_train_eval_target"].sum()),
        "cross_split_leakage_pair": int(df["leakage_train_eval_pair"].sum()),
        "semantic_person_identity_verified": False,
        "semantic_identity_note": (
            "Semantic person-identity leakage is NOT VERIFIED by SHA256/pHash alone. "
            "FIT manifest has no reliable person_id metadata."
        ),
        "near_duplicate_status": "DEFERRED_TO_LOCAL_GPU_SPLIT_DESIGN_STAGE",
        "phash_available": True,
    }


def export_eval_leakage_candidates(df: pd.DataFrame, out_path: Path) -> None:
    """Export eval rows with train↔eval exact-image leakage flags.

    Policy: preserve official eval split; annotate only. Downstream may define
    official_eval vs clean_eval — Data Engineering does not modify splits.
    """
    eval_mask = df["source_split"] == "eval"
    leak_mask = (
        df["leakage_train_eval_person"]
        | df["leakage_train_eval_garment"]
        | df["leakage_train_eval_target"]
        | df["leakage_train_eval_pair"]
    )
    cols = [
        "sample_id", "source_split", "source_shard_id", "source_row_id",
        "person_sha256", "garment_sha256", "target_sha256",
        "leakage_train_eval_person", "leakage_train_eval_garment",
        "leakage_train_eval_target", "leakage_train_eval_pair",
        "quality_status", "quality_flags", "usable_for_fitground",
    ]
    sub = df.loc[eval_mask & leak_mask, cols]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sub.to_parquet(out_path, index=False)


def export_duplicate_candidates(df: pd.DataFrame, out_path: Path) -> None:
    mask = (
        df["duplicate_record_exact"]
        | df["duplicate_person_sha256"]
        | df["duplicate_garment_sha256"]
        | df["duplicate_target_sha256"]
        | df["leakage_train_eval_person"]
        | df["leakage_train_eval_garment"]
        | df["leakage_train_eval_target"]
    )
    cols = [
        "sample_id", "source_split", "source_shard_id", "source_row_id",
        "person_sha256", "garment_sha256", "target_sha256",
        "duplicate_record_exact", "duplicate_person_sha256",
        "duplicate_garment_sha256", "duplicate_target_sha256",
        "leakage_train_eval_person", "leakage_train_eval_garment",
        "leakage_train_eval_target", "quality_flags",
    ]
    sub = df.loc[mask, cols]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sub.to_parquet(out_path, index=False)


def _flags_list(f: Any) -> list:
    if f is None:
        return []
    return list(f) if len(f) > 0 else []


def export_evidence_samples(df: pd.DataFrame, out_dir: Path, max_per_flag: int = 5) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    categories = {
        "missing_image": lambda f: any("missing" in x for x in _flags_list(f)),
        "corrupt_image": lambda f: any("corrupt" in x for x in _flags_list(f)),
        "sleeveless": lambda f: "sleeveless_garment" in _flags_list(f),
        "extreme_bust_ease": lambda f: any(x.startswith("extreme_bust_ease") for x in _flags_list(f)),
        "duplicate_candidate": lambda f: "possible_duplicate" in _flags_list(f),
        "leakage_candidate": lambda f: "possible_train_eval_leakage" in _flags_list(f),
    }
    cols = [
        "sample_id", "source_split", "source_shard_id", "source_row_id",
        "body_height_cm", "body_bust_cm", "garment_bust_cm", "bust_ease_cm",
        "bust_ease_ratio", "garment_sleeve_cm", "quality_status", "quality_flags",
        "person_sha256", "garment_sha256", "target_sha256",
    ]
    for cat, pred in categories.items():
        mask = df["quality_flags"].apply(pred)
        sub = df.loc[mask, cols].head(max_per_flag)
        if len(sub):
            sub.to_csv(out_dir / f"{cat}_samples.csv", index=False)


def write_distribution_figures(df: pd.DataFrame) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    for col in MEAS_COLS:
        fig, ax = plt.subplots(figsize=(8, 5))
        for split, label in [("train", "train"), ("eval", "eval")]:
            data = df[df["source_split"] == split][col].dropna()
            if len(data):
                ax.hist(data, bins=50, alpha=0.5, label=label)
        ax.set_title(f"full_fit: {col}")
        ax.legend()
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / f"full_fit_hist_{col}.png", dpi=120)
        plt.close(fig)


def run_full_closure(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    df = load_manifest(manifest_path)
    validation = validate_manifest(df)
    dist = split_distribution_audit(df)
    quant = quantization_audit(df)
    img = image_integrity_audit(df)
    qual = quality_audit(df)
    dup = duplicate_leakage_audit(df)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "tables").mkdir(exist_ok=True)

    # CSV table
    rows = []
    for split in ("ALL", "train", "eval"):
        for col, st in dist[split].items():
            if isinstance(st, dict) and "count" in st:
                rows.append({"split": split, "field": col, **st})
    pd.DataFrame(rows).to_csv(REPORTS_DIR / "tables" / "full_fit_distribution.csv", index=False)

    export_duplicate_candidates(df, REPORTS_DIR / "tables" / "duplicate_candidates.parquet")
    from fitground.config import ARTIFACTS_DIR

    export_eval_leakage_candidates(df, ARTIFACTS_DIR / "eval_leakage_candidates.parquet")
    export_evidence_samples(df, REPORTS_DIR / "evidence_samples")
    write_distribution_figures(df)

    quant_verdict = {
        "OBSERVED": quant,
        "INTERPRETED": "Discrete concentration in bust_ease_ratio at rounded 1dp/2dp levels",
        "HYPOTHESIS": "May reflect preset garment scaling in data generation",
        "VERIFICATION_STATUS": "NOT VERIFIED from official generation documentation",
    }

    summary = {
        "generated_at": datetime.now(UTC).isoformat(),
        "validation": validation,
        "distribution": dist,
        "quantization": quant_verdict,
        "image_integrity": img,
        "quality": qual,
        "duplicate_leakage": dup,
    }

    _write_md_reports(summary, quant)
    (REPORTS_DIR / "closure_audit.json").write_text(json.dumps(summary, indent=2, default=str))
    return summary


def _write_md_reports(summary: dict, quant: dict) -> None:
    v = summary["validation"]
    lines = [
        "# Full FIT Distribution Audit",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        f"Total rows: {v['total_rows']} (train {v['train_rows']}, eval {v['eval_rows']})",
        "",
        "## Train vs Eval Shift (KS / Wasserstein)",
        "",
        "| field | KS | Wasserstein |",
        "|-------|-----|-------------|",
    ]
    for col, sh in summary["distribution"].get("train_vs_eval_shift", {}).items():
        lines.append(f"| {col} | {sh['ks_statistic']:.4f} | {sh['wasserstein_distance']:.4f} |")
    (REPORTS_DIR / "full_fit_distribution_audit.md").write_text("\n".join(lines))

    dup = summary["duplicate_leakage"]
    dup_lines = [
        "# Full FIT Duplicate & Leakage Audit",
        "",
        "## IMAGE-LEVEL EXACT DUPLICATES",
        f"- Record exact: {dup['exact_record_duplicate']}",
        f"- Person image SHA256: {dup['exact_person_image_sha256']}",
        f"- Cloth image SHA256: {dup['exact_cloth_image_sha256']}",
        f"- Target image SHA256: {dup['exact_target_image_sha256']}",
        f"- Person-cloth pair: {dup['exact_person_cloth_pair']}",
        "",
        "## CROSS-SPLIT IMAGE LEAKAGE (train ∩ eval)",
        f"- Person: {dup['cross_split_leakage_person_image']}",
        f"- Cloth: {dup['cross_split_leakage_cloth_image']}",
        f"- Target: {dup['cross_split_leakage_target_image']}",
        f"- Pair: {dup['cross_split_leakage_pair']}",
        "",
        f"**{dup['semantic_identity_note']}**",
        "",
        f"Near-duplicate: {dup['near_duplicate_status']}",
    ]
    (REPORTS_DIR / "full_fit_duplicate_leakage_audit.md").write_text("\n".join(dup_lines))

    img = summary["image_integrity"]
    img_lines = ["# Full FIT Image Integrity", "", f"Samples: {img['total_samples']}", ""]
    for mod, st in img["modalities"].items():
        img_lines.append(f"## {mod}")
        for k, val in st.items():
            img_lines.append(f"- {k}: {val}")
    (REPORTS_DIR / "full_fit_image_integrity.md").write_text("\n".join(img_lines))
