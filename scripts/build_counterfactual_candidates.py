#!/usr/bin/env python3
"""Build FIT-Clean v0.1 measurement-counterfactual candidate pairs (metadata only)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fitground.config import (
    ARTIFACTS_DIR,
    COUNTERFACTUAL_CANDIDATES_PATH,
    COUNTERFACTUAL_RANDOM_SEED,
    COUNTERFACTUAL_STRUCTURE_PATH,
    EXPERIMENTAL_SPLIT_POLICY_PATH,
    HF_SOURCE_REVISION,
    MANIFEST_PATH,
)
from fitground.counterfactual.discovery import run_structure_discovery
from fitground.counterfactual.matching import build_candidates, candidate_summary
from fitground.counterfactual.schema import PAIR_REQUIRED_COLUMNS, jsonable
from fitground.counterfactual.validation import (
    leakage_controlled_eval_ids,
    official_eval_ids,
    shortcut_audit,
    validate_candidates,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(jsonable(payload), indent=2, ensure_ascii=False), encoding="utf-8")


def build_split_policy(manifest: pd.DataFrame, pairs: pd.DataFrame) -> dict:
    official = official_eval_ids(manifest)
    controlled = leakage_controlled_eval_ids(manifest)
    excluded = sorted(set(official) - set(controlled))
    pair_eval_touch = []
    if not pairs.empty:
        pair_eval_touch = sorted(
            set(pairs.loc[pairs["anchor_split"] == "eval", "anchor_sample_id"].astype(str))
            | set(pairs.loc[pairs["counterfactual_split"] == "eval", "counterfactual_sample_id"].astype(str))
        )
    return {
        "version": "v0.1",
        "frozen_manifest": "data/processed/fit_clean_v0.1.parquet",
        "manifest_not_modified": True,
        "source_revision": HF_SOURCE_REVISION,
        "determinism": {
            "official_eval_order": "sorted sample_id ascending",
            "leakage_controlled_eval_order": "sorted sample_id ascending",
            "pair_id": "sha256(sorted(anchor, counterfactual))[:24] with cf_ prefix",
            "anchor_rule": "lower bust_ease_cm, then lower garment_bust_cm, then sample_id",
            "random_seed": COUNTERFACTUAL_RANDOM_SEED,
            "rng_used_in_split_assignment": False,
        },
        "official_eval": {
            "definition": "FIT official eval split, unmodified 5K (minus the single INVALID row if present in usable filters downstream)",
            "source_split": "eval",
            "n_sample_ids": len(official),
            "why": "Preserve the public FIT eval protocol for comparability.",
        },
        "leakage_controlled_eval": {
            "definition": "official eval sample_ids that do not carry exact-image train/eval overlap flags",
            "exclusion_rule": (
                "Drop eval rows where any of leakage_train_eval_person, "
                "leakage_train_eval_garment, leakage_train_eval_target, "
                "leakage_train_eval_pair is True"
            ),
            "n_sample_ids": len(controlled),
            "n_excluded_exact_image_overlap": len(excluded),
            "why": "Isolate eval from known exact-image contamination without rewriting FIT-Clean v0.1.",
        },
        "image_overlap_policy": {
            "exact_sha256": "annotated in FIT-Clean v0.1; excluded from leakage_controlled_eval",
            "near_duplicate_phash": "NOT VERIFIED at dataset scale; DEFERRED_TO_GPU",
            "semantic_person_identity": (
                "NOT VERIFIED. FIT has no person_id. Same-sha256 is image identity only. "
                "Do not claim semantic identity isolation."
            ),
        },
        "counterfactual_pairs": {
            "eligible_for_official_eval_protocol": "pairs whose members are both source_split=eval",
            "eligible_for_leakage_controlled_protocol": (
                "eval-eval pairs where neither member is in the exact-image overlap exclusion set"
            ),
            "cross_split_pairs": "flagged; not used as official eval items",
            "n_pairs_touching_official_eval_ids": len(pair_eval_touch),
        },
        "train": {
            "definition": "source_split=train",
            "n_rows": int((manifest["source_split"] == "train").sum()),
            "pair_use": "train-train pairs may be used for diagnostic analysis; not for claiming eval performance",
        },
    }


def main() -> None:
    if not MANIFEST_PATH.exists():
        raise SystemExit(f"manifest not found: {MANIFEST_PATH}")
    df = pd.read_parquet(MANIFEST_PATH)
    structure = run_structure_discovery(df)
    _write_json(COUNTERFACTUAL_STRUCTURE_PATH, structure)

    pairs = build_candidates(df, include_tier_d="auto")
    COUNTERFACTUAL_CANDIDATES_PATH.parent.mkdir(parents=True, exist_ok=True)
    if pairs.empty:
        # Still write an empty parquet with schema for downstream tools.
        empty = pd.DataFrame({c: [] for c in PAIR_REQUIRED_COLUMNS})
        empty.to_parquet(COUNTERFACTUAL_CANDIDATES_PATH, index=False)
        pairs = empty
    else:
        pairs.to_parquet(COUNTERFACTUAL_CANDIDATES_PATH, index=False)

    validation = validate_candidates(pairs, require_rows=False)
    summary = candidate_summary(pairs)
    audit = shortcut_audit(pairs) if not pairs.empty else {"verdict": "NO_PAIRS"}
    policy = build_split_policy(df, pairs)
    EXPERIMENTAL_SPLIT_POLICY_PATH.write_text(
        yaml.safe_dump(policy, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    _write_json(ARTIFACTS_DIR / "counterfactual_candidate_summary_v0.1.json", summary)
    _write_json(ARTIFACTS_DIR / "counterfactual_shortcut_audit_v0.1.json", audit)
    _write_json(ARTIFACTS_DIR / "counterfactual_validation_v0.1.json", validation)

    print(
        json.dumps(
            {
                "n_pairs": summary.get("n_pairs", 0),
                "by_tier": summary.get("by_tier", {}),
                "validation_ok": validation.get("ok"),
                "shortcut_verdict": audit.get("verdict"),
                "strongest_available_unit": structure.get("strongest_available_unit"),
                "candidates": str(COUNTERFACTUAL_CANDIDATES_PATH),
                "split_policy": str(EXPERIMENTAL_SPLIT_POLICY_PATH),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
