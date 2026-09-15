"""Eval-only pipeline with strict bounded-memory image processing."""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import seaborn as sns

from fitground.config import (
    EVAL_MANIFEST_PATH,
    EVAL_SHARD_COUNT,
    FIGURES_DIR,
    RAW_FIT_DIR,
    REPORTS_DIR,
    SOURCE_DATASET,
)
from fitground.data.eval_checkpoint import EvalCheckpointManager
from fitground.data.features import compute_relational_features
from fitground.data.identity import make_image_identity, make_sample_id, shard_id_from_filename
from fitground.data.images import audit_image_bytes, image_ref
from fitground.data.measurements import normalize_measurements
from fitground.data.memory import MemoryLimitError, MemoryTracker, release_memory
from fitground.data.quality import classify_quality
from fitground.data.schema import (
    RAW_TO_CANONICAL,
    eval_manifest_arrow_schema,
    parquet_schema_description,
)

MEASUREMENT_COLUMNS = tuple(RAW_TO_CANONICAL.keys())
IMAGE_COLUMNS = ("person", "cloth", "target")
DEFAULT_BATCH_SIZE = 8
MAX_BATCH_SIZE = 16
WORKERS = 1  # single-process only


def _eval_shard_paths() -> list[Path]:
    data_dir = RAW_FIT_DIR / "data"
    paths = sorted(data_dir.glob("eval-*-of-*.parquet"))
    if len(paths) != EVAL_SHARD_COUNT:
        raise FileNotFoundError(
            f"Expected {EVAL_SHARD_COUNT} eval shards in {data_dir}, found {len(paths)}"
        )
    return paths


def load_eval_measurements() -> dict[tuple[str, int], dict[str, float | None]]:
    """
    Load all 5000 measurement rows (no images) into memory.

    Key: (shard_id, row_id) -> canonical measurements + relational features.
    """
    store: dict[tuple[str, int], dict[str, float | None]] = {}
    for shard_path in _eval_shard_paths():
        shard_id = shard_id_from_filename(shard_path.name)
        pf = pq.ParquetFile(shard_path)
        table = pf.read(columns=list(MEASUREMENT_COLUMNS), use_threads=False)
        for row_id in range(table.num_rows):
            row = {col: table[col][row_id].as_py() for col in MEASUREMENT_COLUMNS}
            measurements = normalize_measurements(row)
            relational = compute_relational_features(measurements)
            store[(shard_id, row_id)] = {**measurements, **relational}
        del table
        release_memory()
    return store


def _struct_field(struct_val: Any, field: str) -> Any:
    if struct_val is None:
        return None
    if isinstance(struct_val, dict):
        return struct_val.get(field)
    return None


def _build_manifest_row(
    split: str,
    shard_id: str,
    row_id: int,
    person_audit: Any,
    garment_audit: Any,
    target_audit: Any,
    person_path: str | None,
    garment_path: str | None,
    target_path: str | None,
    feat: dict[str, float | None],
) -> dict[str, Any]:
    from fitground.data.schema import CANONICAL_BODY_FIELDS, CANONICAL_GARMENT_FIELDS, CANONICAL_RELATIONAL_FIELDS

    measurements = {k: feat[k] for k in CANONICAL_BODY_FIELDS + CANONICAL_GARMENT_FIELDS}
    relational = {k: feat[k] for k in CANONICAL_RELATIONAL_FIELDS}
    quality_status, quality_flags = classify_quality(
        measurements, person_audit, garment_audit, target_audit, relational
    )
    return {
        "sample_id": make_sample_id(split, shard_id, row_id),
        "source_dataset": SOURCE_DATASET,
        "source_split": split,
        "source_shard_id": shard_id,
        "source_row_id": row_id,
        "person_image_ref": image_ref(split, shard_id, row_id, "person", person_path),
        "garment_image_ref": image_ref(split, shard_id, row_id, "cloth", garment_path),
        "target_image_ref": image_ref(split, shard_id, row_id, "target", target_path),
        "person_image_identity": make_image_identity("person", person_audit.sha256 or ""),
        "garment_image_identity": make_image_identity("cloth", garment_audit.sha256 or ""),
        "target_image_identity": make_image_identity("target", target_audit.sha256 or ""),
        "person_sha256": person_audit.sha256,
        "garment_sha256": garment_audit.sha256,
        "target_sha256": target_audit.sha256,
        "person_phash": person_audit.phash,
        "garment_phash": garment_audit.phash,
        "target_phash": target_audit.phash,
        "person_format": person_audit.format,
        "garment_format": garment_audit.format,
        "target_format": target_audit.format,
        "person_width": person_audit.width,
        "person_height": person_audit.height,
        "garment_width": garment_audit.width,
        "garment_height": garment_audit.height,
        "target_width": target_audit.width,
        "target_height": target_audit.height,
        **measurements,
        **relational,
        "quality_status": quality_status,
        "quality_flags": quality_flags,
        "duplicate_person_sha256": False,
        "duplicate_garment_sha256": False,
        "duplicate_target_sha256": False,
        "duplicate_person_garment_pair": False,
        "duplicate_record_exact": False,
        "usable_for_fitground": quality_status != "INVALID",
    }


def process_shard_streaming(
    shard_path: Path,
    measurements: dict[tuple[str, int], dict[str, float | None]],
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_rows: int | None = None,
    tracker: MemoryTracker | None = None,
) -> list[dict[str, Any]]:
    """
    Process one shard row-group/batch at a time — never load full shard table.
    """
    batch_size = min(max(1, batch_size), MAX_BATCH_SIZE)
    shard_id = shard_id_from_filename(shard_path.name)
    pf = pq.ParquetFile(shard_path)
    columns = list(IMAGE_COLUMNS)
    rows: list[dict[str, Any]] = []
    row_offset = 0

    for batch in pf.iter_batches(batch_size=batch_size, columns=columns, use_threads=False):
        if tracker:
            tracker.check_limit(shard_id)

        n = batch.num_rows
        limit = n
        if max_rows is not None:
            remaining = max_rows - row_offset
            if remaining <= 0:
                break
            limit = min(n, remaining)

        for i in range(limit):
            global_row_id = row_offset + i
            feat = measurements[(shard_id, global_row_id)]

            person_struct = batch.column("person")[i].as_py()
            cloth_struct = batch.column("cloth")[i].as_py()
            target_struct = batch.column("target")[i].as_py()

            person_bytes = _struct_field(person_struct, "bytes")
            garment_bytes = _struct_field(cloth_struct, "bytes")
            target_bytes = _struct_field(target_struct, "bytes")

            person_audit = audit_image_bytes(
                bytes(person_bytes) if person_bytes else None,
                _struct_field(person_struct, "path"),
            )
            del person_bytes, person_struct

            garment_audit = audit_image_bytes(
                bytes(garment_bytes) if garment_bytes else None,
                _struct_field(cloth_struct, "path"),
            )
            del garment_bytes, cloth_struct

            target_audit = audit_image_bytes(
                bytes(target_bytes) if target_bytes else None,
                _struct_field(target_struct, "path"),
            )
            del target_bytes, target_struct

            rows.append(
                _build_manifest_row(
                    "eval",
                    shard_id,
                    global_row_id,
                    person_audit,
                    garment_audit,
                    target_audit,
                    person_audit.path,
                    garment_audit.path,
                    target_audit.path,
                    feat,
                )
            )
            del person_audit, garment_audit, target_audit

        row_offset += limit
        del batch
        release_memory()

        if tracker:
            tracker.sample(shard_id)
        if max_rows is not None and row_offset >= max_rows:
            break

    return rows


def process_eval_shards_streaming(
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    shard_limit: int | None = None,
    max_rows_per_shard: int | None = None,
    resume: bool = True,
    checkpoint: EvalCheckpointManager | None = None,
    tracker: MemoryTracker | None = None,
) -> EvalCheckpointManager:
    """Shard-by-shard with per-shard checkpoint and resume."""
    ckpt = checkpoint or EvalCheckpointManager()
    mem = tracker or MemoryTracker()
    measurements = load_eval_measurements()

    shard_paths = _eval_shard_paths()
    if shard_limit is not None:
        shard_paths = shard_paths[:shard_limit]

    for shard_path in shard_paths:
        shard_id = shard_id_from_filename(shard_path.name)
        if resume and ckpt.is_shard_done(shard_id):
            continue

        mem.shard_peak_bytes = 0
        mem.sample(shard_id)

        rows = process_shard_streaming(
            shard_path,
            measurements,
            batch_size=batch_size,
            max_rows=max_rows_per_shard,
            tracker=mem,
        )
        ckpt.write_shard_checkpoint(shard_id, rows)
        mem.finish_shard(shard_id)
        ckpt.record_shard_rss_peak(shard_id, mem.shard_peaks.get(shard_id, 0))
        del rows
        release_memory()

    return ckpt


def assemble_manifest_from_checkpoints(ckpt: EvalCheckpointManager) -> pd.DataFrame:
    tables: list[pa.Table] = []
    for path in ckpt.list_checkpoint_tables():
        tables.append(pq.read_table(path))
    if not tables:
        return pd.DataFrame()
    combined = pa.concat_tables(tables)
    return combined.to_pandas()


def annotate_eval_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col, flag in (
        ("person_sha256", "duplicate_person_sha256"),
        ("garment_sha256", "duplicate_garment_sha256"),
        ("target_sha256", "duplicate_target_sha256"),
    ):
        counts = out[col].value_counts()
        dup = set(counts[counts > 1].index) - {None}
        out[flag] = out[col].isin(dup)

    pair_key = out["person_sha256"] + "|" + out["garment_sha256"]
    pair_counts = pair_key.value_counts()
    dup_pairs = set(pair_counts[pair_counts > 1].index)
    out["duplicate_person_garment_pair"] = pair_key.isin(dup_pairs)

    record_key = pair_key + "|" + out["target_sha256"]
    record_counts = record_key.value_counts()
    dup_records = set(record_counts[record_counts > 1].index)
    out["duplicate_record_exact"] = record_key.isin(dup_records)

    dup_mask = (
        out["duplicate_person_sha256"]
        | out["duplicate_garment_sha256"]
        | out["duplicate_target_sha256"]
        | out["duplicate_person_garment_pair"]
        | out["duplicate_record_exact"]
    )
    for idx in out.index[dup_mask]:
        raw_flags = out.at[idx, "quality_flags"]
        flags = list(raw_flags) if raw_flags is not None and len(raw_flags) > 0 else []
        if "possible_duplicate" not in flags:
            flags.append("possible_duplicate")
        out.at[idx, "quality_flags"] = flags
        if out.at[idx, "quality_status"] == "VALID":
            out.at[idx, "quality_status"] = "SUSPICIOUS"
    return out


def analyze_bust_ease_ratio_quantization(df: pd.DataFrame) -> dict[str, Any]:
    series = df["bust_ease_ratio"].dropna()
    rounded_2 = series.round(2)
    rounded_1 = series.round(1)
    top_r2 = Counter(rounded_2.tolist()).most_common(20)
    top_r1 = Counter(rounded_1.tolist()).most_common(20)
    top10_r2_count = sum(c for _, c in top_r2[:10])
    concentration_r2 = top10_r2_count / len(series) if len(series) else 0
    on_005_grid = series.apply(lambda x: abs(round(x / 0.05) * 0.05 - x) < 1e-6)
    pct_on_005 = float(on_005_grid.mean())
    on_010_grid = series.apply(lambda x: abs(round(x / 0.10) * 0.10 - x) < 1e-6)
    pct_on_010 = float(on_010_grid.mean())
    top1_r2_share = top_r2[0][1] / len(series) if top_r2 and len(series) else 0
    top1_r1_share = top_r1[0][1] / len(series) if top_r1 and len(series) else 0

    verdict = "likely_continuous"
    if (
        rounded_1.nunique() <= 12
        or top1_r2_share >= 0.15
        or concentration_r2 >= 0.45
        or top1_r1_share >= 0.30
    ):
        verdict = "likely_quantized_preset_levels"
    elif pct_on_010 > 0.25:
        verdict = "moderate_quantization_0.10_steps"

    return {
        "n_samples": int(len(series)),
        "n_unique_raw": int(series.nunique()),
        "n_unique_rounded_2dp": int(rounded_2.nunique()),
        "n_unique_rounded_1dp": int(rounded_1.nunique()),
        "top20_rounded_2dp": [{"value": float(v), "count": int(c)} for v, c in top_r2],
        "top20_rounded_1dp": [{"value": float(v), "count": int(c)} for v, c in top_r1],
        "top10_rounded_2dp_concentration": float(concentration_r2),
        "pct_on_0.05_grid": pct_on_005,
        "pct_on_0.10_grid": pct_on_010,
        "verdict": verdict,
        "stats": {
            "min": float(series.min()),
            "p5": float(series.quantile(0.05)),
            "median": float(series.median()),
            "p75": float(series.quantile(0.75)),
            "p95": float(series.quantile(0.95)),
            "max": float(series.max()),
        },
        "bust_ease_sign": {
            "negative": int((df["bust_ease_cm"] < 0).sum()),
            "zero": int((df["bust_ease_cm"] == 0).sum()),
            "positive": int((df["bust_ease_cm"] > 0).sum()),
        },
        "sleeveless_count": int((df["garment_sleeve_cm"] == 0).sum()),
    }


def _distribution_stats(series: pd.Series) -> dict[str, float | int]:
    s = series.dropna()
    if len(s) == 0:
        return {"count": 0, "missing": int(series.isna().sum())}
    return {
        "count": int(len(s)),
        "missing": int(series.isna().sum()),
        "mean": float(s.mean()),
        "std": float(s.std()),
        "min": float(s.min()),
        "p5": float(s.quantile(0.05)),
        "p25": float(s.quantile(0.25)),
        "median": float(s.median()),
        "p75": float(s.quantile(0.75)),
        "p95": float(s.quantile(0.95)),
        "p99": float(s.quantile(0.99)),
        "max": float(s.max()),
    }


def write_figures(df: pd.DataFrame, quant: dict[str, Any]) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    for col in [
        "body_height_cm", "body_bust_cm", "body_waist_cm", "body_hips_cm",
        "garment_bust_cm", "garment_length_cm", "garment_sleeve_cm",
        "bust_ease_cm", "bust_ease_ratio", "garment_length_height_ratio",
    ]:
        fig, ax = plt.subplots(figsize=(8, 5))
        data = df[col].dropna()
        if len(data):
            ax.hist(data, bins=50, edgecolor="black", alpha=0.7)
            ax.set_title(f"eval: {col}")
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / f"eval_hist_{col}.png", dpi=120)
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    r2 = df["bust_ease_ratio"].dropna().round(2)
    vc = r2.value_counts().sort_index()
    ax.bar(vc.index.astype(str), vc.values, width=0.8)
    ax.set_title("bust_ease_ratio rounded to 2dp frequency")
    plt.xticks(rotation=90, fontsize=6)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "eval_bust_ease_ratio_quantization.png", dpi=120)
    plt.close(fig)


def write_audit_report(df: pd.DataFrame, quant: dict[str, Any], mem: MemoryTracker | None = None) -> dict[str, Any]:
    def _flags_list(f: Any) -> list:
        if f is None:
            return []
        return list(f) if len(f) > 0 else []

    missing_images = int(df["quality_flags"].apply(lambda f: any("missing" in x for x in _flags_list(f))).sum())
    corrupt_images = int(df["quality_flags"].apply(lambda f: any("corrupt" in x for x in _flags_list(f))).sum())
    suspicious_meas = int(
        df["quality_flags"].apply(
            lambda f: any(x.startswith("extreme_") or x.startswith("impossible_") for x in _flags_list(f))
        ).sum()
    )
    summary: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "n_samples": len(df),
        "n_shards": EVAL_SHARD_COUNT,
        "valid": int((df["quality_status"] == "VALID").sum()),
        "suspicious": int((df["quality_status"] == "SUSPICIOUS").sum()),
        "invalid": int((df["quality_status"] == "INVALID").sum()),
        "usable_for_fitground": int(df["usable_for_fitground"].sum()),
        "missing_images": missing_images,
        "corrupt_images": corrupt_images,
        "measurement_suspicious": suspicious_meas,
        "duplicate_person": int(df["duplicate_person_sha256"].sum()),
        "duplicate_garment": int(df["duplicate_garment_sha256"].sum()),
        "duplicate_target": int(df["duplicate_target_sha256"].sum()),
        "duplicate_pair": int(df["duplicate_person_garment_pair"].sum()),
        "duplicate_record_exact": int(df["duplicate_record_exact"].sum()),
        "memory": {
            "global_rss_peak_bytes": mem.global_peak_bytes if mem else None,
            "shard_rss_peaks_bytes": mem.shard_peaks if mem else {},
            "rss_limit_bytes": mem.limit_bytes if mem else None,
        },
        "quantization": quant,
    }
    (REPORTS_DIR / "fit_eval_audit.json").write_text(json.dumps(summary, indent=2, default=str))
    (REPORTS_DIR / "fit_eval_audit.md").write_text(
        f"# FIT Eval Audit\n\nSamples: {len(df)}\n\n"
        f"VALID={summary['valid']} SUSPICIOUS={summary['suspicious']} INVALID={summary['invalid']}\n"
    )
    return summary


def write_distribution_report(df: pd.DataFrame, quant: dict[str, Any]) -> None:
    cols = [
        "body_height_cm", "body_bust_cm", "body_waist_cm", "body_hips_cm",
        "garment_bust_cm", "garment_length_cm", "garment_sleeve_cm",
        "bust_ease_cm", "bust_ease_ratio", "garment_length_height_ratio",
    ]
    stats = {col: _distribution_stats(df[col]) for col in cols}
    (REPORTS_DIR / "fit_eval_distribution.json").write_text(
        json.dumps({"distributions": stats, "quantization": quant}, indent=2)
    )
    (REPORTS_DIR / "fit_eval_distribution.md").write_text(
        f"# FIT Eval Distribution\n\nSamples: {len(df)}\n\nVerdict: {quant['verdict']}\n"
    )


def finalize_manifest(ckpt: EvalCheckpointManager, tracker: MemoryTracker | None = None) -> dict[str, Any]:
    """Assemble checkpoints, duplicate audit, reports — metadata only."""
    df = assemble_manifest_from_checkpoints(ckpt)
    if df.empty:
        return {"error": "no_checkpoint_data"}
    df = annotate_eval_duplicates(df)
    quant = analyze_bust_ease_ratio_quantization(df)
    table = pa.Table.from_pandas(df, schema=eval_manifest_arrow_schema(), preserve_index=False)
    pq.write_table(table, EVAL_MANIFEST_PATH)
    mem = tracker or MemoryTracker()
    if ckpt.state.get("shard_rss_peaks_bytes"):
        mem.shard_peaks = dict(ckpt.state["shard_rss_peaks_bytes"])
        mem.global_peak_bytes = max(mem.shard_peaks.values()) if mem.shard_peaks else 0
    summary = write_audit_report(df, quant, mem)
    write_distribution_report(df, quant)
    if len(df) >= 1000:
        write_figures(df, quant)
    summary["manifest_path"] = str(EVAL_MANIFEST_PATH)
    return summary


def run_eval_pipeline(
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    shard_limit: int | None = None,
    max_rows_per_shard: int | None = None,
    resume: bool = True,
    finalize: bool = True,
    process_only: bool = False,
) -> dict[str, Any]:
    """
    Bounded-memory eval pipeline.

    process_only=True: only stream shards to checkpoints (no finalize).
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    schema_desc = parquet_schema_description()
    (REPORTS_DIR / "fit_schema_audit.md").write_text(
        "# FIT Schema Audit\n\n```json\n" + json.dumps(schema_desc, indent=2) + "\n```\n"
    )

    tracker = MemoryTracker()
    ckpt = EvalCheckpointManager()

    try:
        ckpt = process_eval_shards_streaming(
            batch_size=batch_size,
            shard_limit=shard_limit,
            max_rows_per_shard=max_rows_per_shard,
            resume=resume,
            checkpoint=ckpt,
            tracker=tracker,
        )
    except MemoryLimitError as exc:
        ckpt.save_state(stopped_reason=str(exc))
        return {
            "status": "stopped_memory_limit",
            "error": str(exc),
            "completed_shards": ckpt.state.get("completed_shards", []),
            "rss_peak_bytes": tracker.global_peak_bytes,
        }

    if process_only or (shard_limit is not None and shard_limit < EVAL_SHARD_COUNT):
        return {
            "status": "checkpoint_only",
            "completed_shards": ckpt.state.get("completed_shards", []),
            "rss_peak_bytes": tracker.global_peak_bytes,
            "shard_rss_peaks": tracker.shard_peaks,
        }

    if not finalize:
        return {"status": "processed", "completed_shards": ckpt.state.get("completed_shards", [])}

    return finalize_manifest(ckpt, tracker)
