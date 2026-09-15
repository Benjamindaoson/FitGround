"""Main FIT data engineering pipeline."""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from tqdm import tqdm

from fitground.config import (
    EVAL_SHARD_COUNT,
    INTERIM_DIR,
    MANIFEST_PATH,
    PROCESSED_DIR,
    RAW_FIT_DIR,
    REPORTS_DIR,
    TRAIN_SHARD_COUNT,
)
from fitground.data.download import (
    cleanup_ephemeral_shard,
    download_eval_split,
    download_shard,
    storage_audit,
    write_storage_report,
)
from fitground.data.duplicates import (
    annotate_duplicates_and_leakage,
    leakage_summary,
    near_duplicate_phash_groups,
)
from fitground.data.schema import manifest_arrow_schema, parquet_schema_description
from fitground.data.shard_processor import process_shard_rows


def _disk_available_bytes() -> int:
    usage = shutil.disk_usage("/workspace")
    return usage.free


def _shard_name(split: str, index: int) -> str:
    if split == "train":
        return f"train-{index:05d}-of-{TRAIN_SHARD_COUNT:05d}.parquet"
    return f"eval-{index:05d}-of-{EVAL_SHARD_COUNT:05d}.parquet"


def _existing_shard_path(split: str, index: int) -> Path | None:
    name = _shard_name(split, index)
    raw_path = RAW_FIT_DIR / "data" / name
    if raw_path.exists():
        return raw_path
    interim_path = INTERIM_DIR / "shards" / "data" / name
    if interim_path.exists():
        return interim_path
    return None


def _process_shard(split: str, shard_path: Path, shard_name: str) -> list[dict]:
    return list(process_shard_rows(str(shard_path), split, shard_name))


def _write_shard_manifest(rows: list[dict], shard_manifest_dir: Path, shard_id: str, schema: pa.Schema) -> None:
    if not rows:
        return
    shard_manifest_dir.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(rows, schema=schema)
    pq.write_table(table, shard_manifest_dir / f"{shard_id}.parquet")


def _concat_shard_manifests(shard_manifest_dir: Path, output_path: Path) -> None:
    files = sorted(shard_manifest_dir.glob("*.parquet"))
    if not files:
        return
    tables = [pq.read_table(f) for f in files]
    pq.write_table(pa.concat_tables(tables), output_path)


def run_pipeline(
    skip_train: bool = False,
    skip_eval_download: bool = False,
    max_train_shards: int | None = None,
) -> dict:
    """Execute full data engineering pipeline."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    RAW_FIT_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    available = _disk_available_bytes()
    storage = write_storage_report(REPORTS_DIR / "storage_audit.json", available)

    # Schema audit report
    schema_report = parquet_schema_description()
    schema_report["storage_audit"] = storage
    schema_report["generated_at"] = datetime.now(UTC).isoformat()
    _write_schema_audit(schema_report)

    interim_manifest = INTERIM_DIR / "fit_manifest_partial.parquet"
    shard_manifest_dir = INTERIM_DIR / "shard_manifests"
    schema = manifest_arrow_schema()

    stats = {"train_shards_processed": 0, "eval_shards_processed": 0, "rows": 0}

    # Phase 1: Eval — download and keep permanently if space allows
    if not skip_eval_download and storage["can_download_eval"]:
        print("Downloading eval split...")
        download_eval_split()

    for i in range(EVAL_SHARD_COUNT):
        shard_name = _shard_name("eval", i)
        shard_path = _existing_shard_path("eval", i)
        if shard_path is None:
            if storage["can_download_eval"]:
                shard_path = download_shard("eval", i, ephemeral=False)
            else:
                print(f"Skipping eval shard {i}: not available and cannot download")
                continue
        rows = _process_shard("eval", shard_path, shard_name)
        _write_shard_manifest(rows, shard_manifest_dir, f"eval_{i:03d}", schema)
        stats["eval_shards_processed"] += 1
        stats["rows"] += len(rows)

    # Phase 2: Train — ephemeral shard processing
    if not skip_train:
        train_limit = max_train_shards if max_train_shards is not None else TRAIN_SHARD_COUNT
        for i in tqdm(range(train_limit), desc="Train shards"):
            shard_name = _shard_name("train", i)
            shard_path = _existing_shard_path("train", i)
            ephemeral = False
            if shard_path is None:
                # Use ephemeral download unless full download fits
                ephemeral = not storage["can_download_full"]
                shard_path = download_shard("train", i, ephemeral=ephemeral)
            rows = _process_shard("train", shard_path, shard_name)
            _write_shard_manifest(rows, shard_manifest_dir, f"train_{i:05d}", schema)
            stats["train_shards_processed"] += 1
            stats["rows"] += len(rows)
            if ephemeral and shard_path.parent.as_posix().endswith("interim/shards/data"):
                cleanup_ephemeral_shard(shard_path)

    _concat_shard_manifests(shard_manifest_dir, interim_manifest)

    if not interim_manifest.exists():
        return {"error": "no_rows_processed", "stats": stats, "storage": storage}

    print("Running duplicate/leakage audit...")
    df = pd.read_parquet(interim_manifest)
    df = annotate_duplicates_and_leakage(df)
    near_dup = near_duplicate_phash_groups(df)

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(MANIFEST_PATH, index=False)

    leakage = leakage_summary(df)
    _write_duplicate_report(df, leakage, near_dup)

    result = {
        "manifest_path": str(MANIFEST_PATH),
        "total_rows": len(df),
        "train_rows": int((df["source_split"] == "train").sum()),
        "eval_rows": int((df["source_split"] == "eval").sum()),
        "valid": int((df["quality_status"] == "VALID").sum()),
        "suspicious": int((df["quality_status"] == "SUSPICIOUS").sum()),
        "invalid": int((df["quality_status"] == "INVALID").sum()),
        "usable": int(df["usable_for_fitground"].sum()),
        "leakage": leakage,
        "near_duplicate_groups": {k: len(v) for k, v in near_dup.items()},
        "stats": stats,
        "storage": storage,
    }
    (REPORTS_DIR / "pipeline_result.json").write_text(json.dumps(result, indent=2, default=str))
    return result


def _write_schema_audit(schema_report: dict) -> None:
    lines = [
        "# FIT Schema Audit",
        "",
        f"Generated: {schema_report.get('generated_at', 'unknown')}",
        "",
        "## Repository Layout",
        "",
        "- **Source**: `Yuanhao-Harry-Wang/fitvto-100k` on Hugging Face",
        "- **Format**: Parquet shards with embedded PNG images",
        f"- **Train shards**: {TRAIN_SHARD_COUNT} (expected 100,000 rows)",
        f"- **Eval shards**: {EVAL_SHARD_COUNT} (expected 5,000 rows)",
        "",
        "## Storage Audit",
        "",
        f"- Required (full dataset): {schema_report['storage_audit']['required_bytes_full'] / 1e9:.2f} GB",
        f"- Required (eval only): {schema_report['storage_audit']['required_bytes_eval'] / 1e9:.2f} GB",
        f"- Available: {schema_report['storage_audit']['available_bytes'] / 1e9:.2f} GB",
        f"- Shortfall (full): {schema_report['storage_audit']['shortfall_bytes_full'] / 1e9:.2f} GB",
        f"- Strategy: `{schema_report['storage_audit']['strategy']}`",
        "",
        "## Schema",
        "",
        f"- Image representation: {schema_report['image_representation']}",
        f"- Image resolution: {schema_report['image_resolution']}",
        f"- Measurement unit: {schema_report['measurement_unit']}",
        "",
        "### Raw Fields",
        "",
        "| Field | Description |",
        "|-------|-------------|",
    ]
    desc = schema_report["raw_fields"]
    for k, v in desc.items():
        lines.append(f"| `{k}` | {v} |")

    lines.extend(
        [
            "",
            "### Canonical Mapping",
            "",
            "| Raw | Canonical |",
            "|-----|-----------|",
        ]
    )
    for raw, canon in schema_report["canonical_mapping"].items():
        lines.append(f"| `{raw}` | `{canon}` |")

    lines.extend(
        [
            "",
            "## Uncertainties",
            "",
            "- README mentions `metadata.jsonl` and folder layout; actual HF distribution uses embedded-image Parquet only.",
            "- `garment_sleeve_length` can be 0.0 for sleeveless garments (not missing).",
            "- Perceptual near-duplicate detection is approximate (phash Hamming distance ≤ 5).",
        ]
    )
    (REPORTS_DIR / "fit_schema_audit.md").write_text("\n".join(lines))


def _write_duplicate_report(df: pd.DataFrame, leakage: dict, near_dup: dict) -> None:
    lines = [
        "# FIT Duplicate & Leakage Audit",
        "",
        f"Total samples audited: {len(df)}",
        "",
        "## Exact Duplicates (MD5)",
        "",
        f"- Exact record duplicates (same person+garment+target MD5): {leakage['exact_record_duplicates']}",
        f"- Duplicate person images: {leakage['duplicate_person_md5']}",
        f"- Duplicate garment images: {leakage['duplicate_garment_md5']}",
        f"- Duplicate target images: {leakage['duplicate_target_md5']}",
        f"- Duplicate person-garment pairs: {leakage['duplicate_person_garment_pair']}",
        "",
        "## Train/Eval Leakage",
        "",
        f"- Person image overlap (train ∩ eval): {leakage['train_eval_person_overlap']}",
        f"- Garment image overlap (train ∩ eval): {leakage['train_eval_garment_overlap']}",
        f"- Target image overlap (train ∩ eval): {leakage['train_eval_target_overlap']}",
        f"- Person-garment pair overlap: {leakage['train_eval_pair_overlap']}",
        "",
        "## Near Duplicates (Perceptual Hash)",
        "",
    ]
    for role, groups in near_dup.items():
        lines.append(f"- {role}: {len(groups)} near-duplicate clusters (Hamming ≤ 5)")

    lines.extend(
        [
            "",
            "## Policy",
            "",
            "- Duplicates are FLAGged (SUSPICIOUS), not deleted.",
            "- Leakage overlaps are FLAGged; eval samples with leakage should be EXCLUDE_FROM_EVAL in modeling.",
            "- Extreme fit measurements are NOT marked INVALID.",
        ]
    )
    (REPORTS_DIR / "fit_duplicate_leakage_audit.md").write_text("\n".join(lines))
