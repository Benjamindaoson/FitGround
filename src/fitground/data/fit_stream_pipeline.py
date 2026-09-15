"""Full FIT streaming pipeline: ephemeral train + local eval."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from huggingface_hub import hf_hub_download

from fitground.config import (
    EVAL_SHARD_COUNT,
    FIGURES_DIR,
    HF_CACHE_DIR,
    HF_REPO_ID,
    INTERIM_DIR,
    MANIFEST_PATH,
    RAW_FIT_DIR,
    REPORTS_DIR,
    TRAIN_SHARD_COUNT,
)
from fitground.data.disk_guard import DiskSpaceError, disk_status, require_disk_headroom
from fitground.data.eval_pipeline import (
    analyze_bust_ease_ratio_quantization,
    write_audit_report,
    write_distribution_report,
    write_figures,
)
from fitground.data.fit_checkpoint import FitCheckpointManager
from fitground.data.hf_env import configure_hf_cache, prune_cache_except
from fitground.data.identity import shard_id_from_filename
from fitground.data.memory import MemoryLimitError, MemoryTracker, release_memory
from fitground.data.schema import eval_manifest_arrow_schema, parquet_schema_description
from fitground.data.stream_core import (
    DEFAULT_BATCH_SIZE,
    load_shard_measurements,
    process_shard_streaming,
)

EPHEMERAL_DIR = INTERIM_DIR / "ephemeral_shards"
MAX_HF_CACHE_BYTES = 2 * 1024**3  # 2 GiB hub cache cap


def _train_shard_name(index: int) -> str:
    return f"train-{index:05d}-of-{TRAIN_SHARD_COUNT:05d}"


def _eval_shard_name(index: int) -> str:
    return f"eval-{index:05d}-of-{EVAL_SHARD_COUNT:05d}"


def _local_eval_path(index: int) -> Path:
    return RAW_FIT_DIR / "data" / f"{_eval_shard_name(index)}.parquet"


def _local_train_path(index: int) -> Path:
    return RAW_FIT_DIR / "data" / f"{_train_shard_name(index)}.parquet"


def _ephemeral_train_path(index: int) -> Path:
    return EPHEMERAL_DIR / "data" / f"{_train_shard_name(index)}.parquet"


def acquire_train_shard(index: int) -> tuple[Path, bool]:
    """
    Return (path, ephemeral).

    Prefer persistent raw copy; otherwise download to ephemeral staging.
    """
    configure_hf_cache()
    require_disk_headroom()
    local = _local_train_path(index)
    if local.exists():
        return local, False
    EPHEMERAL_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"data/{_train_shard_name(index)}.parquet"
    hf_hub_download(
        HF_REPO_ID,
        filename,
        repo_type="dataset",
        local_dir=str(EPHEMERAL_DIR),
    )
    path = _ephemeral_train_path(index)
    if not path.exists():
        raise FileNotFoundError(f"Download failed: {path}")
    return path, True


def release_train_shard(path: Path, ephemeral: bool) -> None:
    if not ephemeral:
        return
    if path.exists():
        path.unlink()
    # Prune hub cache to cap size.
    prune_cache_except(keep_paths=set(), max_bytes=MAX_HF_CACHE_BYTES)
    release_memory()


def process_train_shards(
    ckpt: FitCheckpointManager,
    tracker: MemoryTracker,
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    resume: bool = True,
    shard_limit: int | None = None,
) -> None:
    limit = shard_limit if shard_limit is not None else TRAIN_SHARD_COUNT
    for index in range(limit):
        shard_id = _train_shard_name(index)
        if resume and ckpt.is_shard_done(shard_id):
            continue
        require_disk_headroom()
        path, ephemeral = acquire_train_shard(index)
        tracker.shard_peak_bytes = 0
        tracker.sample(shard_id)
        measurements = load_shard_measurements(path, shard_id)
        rows = process_shard_streaming(
            path, "train", measurements, batch_size=batch_size, tracker=tracker
        )
        ckpt.write_shard_checkpoint(shard_id, rows)
        tracker.finish_shard(shard_id)
        ckpt.record_shard_rss_peak(shard_id, tracker.shard_peaks.get(shard_id, 0))
        del rows, measurements
        release_train_shard(path, ephemeral)
        release_memory()


def process_eval_shards(
    ckpt: FitCheckpointManager,
    tracker: MemoryTracker,
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    resume: bool = True,
) -> None:
    for index in range(EVAL_SHARD_COUNT):
        shard_id = _eval_shard_name(index)
        if resume and ckpt.is_shard_done(shard_id):
            continue
        path = _local_eval_path(index)
        if not path.exists():
            raise FileNotFoundError(f"Eval shard missing locally: {path}")
        require_disk_headroom()
        tracker.shard_peak_bytes = 0
        measurements = load_shard_measurements(path, shard_id)
        rows = process_shard_streaming(
            path, "eval", measurements, batch_size=batch_size, tracker=tracker
        )
        ckpt.write_shard_checkpoint(shard_id, rows)
        tracker.finish_shard(shard_id)
        ckpt.record_shard_rss_peak(shard_id, tracker.shard_peaks.get(shard_id, 0))
        del rows, measurements
        release_memory()


def annotate_duplicates_and_leakage(df: pd.DataFrame) -> pd.DataFrame:
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
    dup_pairs = set(pair_key.value_counts()[pair_key.value_counts() > 1].index)
    out["duplicate_person_garment_pair"] = pair_key.isin(dup_pairs)

    record_key = pair_key + "|" + out["target_sha256"]
    dup_records = set(record_key.value_counts()[record_key.value_counts() > 1].index)
    out["duplicate_record_exact"] = record_key.isin(dup_records)

    train = out[out["source_split"] == "train"]
    eval_ = out[out["source_split"] == "eval"]
    overlap_person = set(train["person_sha256"].dropna()) & set(eval_["person_sha256"].dropna())
    overlap_garment = set(train["garment_sha256"].dropna()) & set(eval_["garment_sha256"].dropna())
    overlap_target = set(train["target_sha256"].dropna()) & set(eval_["target_sha256"].dropna())
    train_pairs = {
        f"{r.person_sha256}|{r.garment_sha256}"
        for r in train.itertuples()
        if r.person_sha256 and r.garment_sha256
    }
    eval_pairs = {
        f"{r.person_sha256}|{r.garment_sha256}"
        for r in eval_.itertuples()
        if r.person_sha256 and r.garment_sha256
    }
    overlap_pairs = train_pairs & eval_pairs

    out["leakage_train_eval_person"] = out["person_sha256"].isin(overlap_person)
    out["leakage_train_eval_garment"] = out["garment_sha256"].isin(overlap_garment)
    out["leakage_train_eval_target"] = out["target_sha256"].isin(overlap_target)
    out["leakage_train_eval_pair"] = pair_key.isin(overlap_pairs)

    leakage_mask = (
        out["leakage_train_eval_person"]
        | out["leakage_train_eval_garment"]
        | out["leakage_train_eval_target"]
        | out["leakage_train_eval_pair"]
    )
    dup_mask = (
        out["duplicate_person_sha256"]
        | out["duplicate_garment_sha256"]
        | out["duplicate_target_sha256"]
        | out["duplicate_person_garment_pair"]
        | out["duplicate_record_exact"]
    )
    for idx in out.index[leakage_mask | dup_mask]:
        raw_flags = out.at[idx, "quality_flags"]
        flags = list(raw_flags) if raw_flags is not None and len(raw_flags) > 0 else []
        if leakage_mask[idx] and "possible_train_eval_leakage" not in flags:
            flags.append("possible_train_eval_leakage")
        if dup_mask[idx] and "possible_duplicate" not in flags:
            flags.append("possible_duplicate")
        out.at[idx, "quality_flags"] = flags
        if out.at[idx, "quality_status"] == "VALID":
            out.at[idx, "quality_status"] = "SUSPICIOUS"
    return out


def assemble_manifest(ckpt: FitCheckpointManager) -> pd.DataFrame:
    paths = ckpt.list_checkpoint_paths()
    if not paths:
        return pd.DataFrame()
    # Eval and train checkpoints may differ (e.g. leakage cols added mid-run).
    # Unify to full manifest schema before concat.
    target_schema = eval_manifest_arrow_schema()
    tables = []
    for p in paths:
        t = pq.read_table(p)
        for name, field in zip(target_schema.names, target_schema):
            if name not in t.column_names:
                fill = pa.nulls(t.num_rows, type=field.type)
                if pa.types.is_boolean(field.type):
                    fill = pa.array([False] * t.num_rows, type=pa.bool_())
                t = t.append_column(name, fill)
        tables.append(t.select(target_schema.names))
    return pa.concat_tables(tables).to_pandas()


def finalize_fit_clean(ckpt: FitCheckpointManager, tracker: MemoryTracker | None = None) -> dict[str, Any]:
    df = assemble_manifest(ckpt)
    if df.empty:
        return {"error": "no_data"}
    df = annotate_duplicates_and_leakage(df)
    quant = analyze_bust_ease_ratio_quantization(df)
    table = pa.Table.from_pandas(df, schema=eval_manifest_arrow_schema(), preserve_index=False)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, MANIFEST_PATH)
    mem = tracker or MemoryTracker()
    if ckpt.state.get("shard_rss_peaks_bytes"):
        mem.shard_peaks = dict(ckpt.state["shard_rss_peaks_bytes"])
        mem.global_peak_bytes = max(mem.shard_peaks.values()) if mem.shard_peaks else 0
    summary = write_audit_report(df, quant, mem)
    write_distribution_report(df, quant)
    write_figures(df, quant)
    summary["manifest_path"] = str(MANIFEST_PATH)
    summary["disk"] = disk_status()
    (REPORTS_DIR / "fit_stream_result.json").write_text(json.dumps(summary, indent=2, default=str))
    return summary


def run_fit_stream(
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    resume: bool = True,
    process_train: bool = True,
    process_eval: bool = True,
    train_shard_limit: int | None = None,
    finalize: bool = False,
) -> dict[str, Any]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    configure_hf_cache()
    (REPORTS_DIR / "fit_schema_audit.md").write_text(
        "# FIT Schema Audit\n\n```json\n"
        + json.dumps(parquet_schema_description(), indent=2)
        + "\n```\n"
    )
    ckpt = FitCheckpointManager()
    tracker = MemoryTracker()
    status: dict[str, Any] = {
        "disk_before": disk_status(),
        "completed_train": ckpt.completed_count("train"),
        "completed_eval": ckpt.completed_count("eval"),
    }
    try:
        if process_eval:
            process_eval_shards(ckpt, tracker, batch_size=batch_size, resume=resume)
        if process_train:
            process_train_shards(
                ckpt, tracker, batch_size=batch_size, resume=resume, shard_limit=train_shard_limit
            )
    except (MemoryLimitError, DiskSpaceError) as exc:
        ckpt.save_state(stopped_reason=str(exc))
        status["status"] = "stopped"
        status["error"] = str(exc)
        status["completed_train"] = ckpt.completed_count("train")
        status["completed_eval"] = ckpt.completed_count("eval")
        status["rss_peak_bytes"] = tracker.global_peak_bytes
        return status

    status["completed_train"] = ckpt.completed_count("train")
    status["completed_eval"] = ckpt.completed_count("eval")
    status["rss_peak_bytes"] = tracker.global_peak_bytes
    status["disk_after"] = disk_status()

    if finalize and status["completed_train"] == TRAIN_SHARD_COUNT and status["completed_eval"] == EVAL_SHARD_COUNT:
        status["finalize"] = finalize_fit_clean(ckpt, tracker)
        status["status"] = "complete"
    else:
        status["status"] = "checkpointed"
    return status
