"""Counterfactual pair construction and validation tests."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from fitground.counterfactual.controls import control_score
from fitground.counterfactual.discovery import analyze_person_cloth_groups, phash_hamming
from fitground.counterfactual.matching import build_candidates, build_pair_record
from fitground.counterfactual.pilot import select_pilot_pairs
from fitground.counterfactual.schema import PAIR_REQUIRED_COLUMNS, make_pair_id, unordered_pair_key
from fitground.counterfactual.validation import (
    leakage_controlled_eval_ids,
    official_eval_ids,
    shortcut_audit,
    validate_candidates,
)
from fitground.data.sample_lookup import locate_sample


def _row(
    sample_id: str,
    *,
    person: str,
    cloth: str,
    target: str,
    split: str = "train",
    shard: str = "train-00000-of-00406",
    body: tuple[float, float, float, float] = (170.0, 90.0, 70.0, 95.0),
    garment: tuple[float, float, float] = (100.0, 60.0, 10.0),
    phash: str = "aaaaaaaaaaaaaaaa",
    quality: str = "VALID",
    leak_person: bool = False,
    dup_person: bool = False,
) -> dict:
    height, bust, waist, hips = body
    gbust, glen, sleeve = garment
    ease = gbust - bust
    return {
        "sample_id": sample_id,
        "source_split": split,
        "source_shard_id": shard,
        "person_sha256": person,
        "garment_sha256": cloth,
        "target_sha256": target,
        "garment_phash": phash,
        "quality_status": quality,
        "usable_for_fitground": quality != "INVALID",
        "duplicate_person_sha256": dup_person,
        "duplicate_garment_sha256": False,
        "duplicate_target_sha256": False,
        "leakage_train_eval_person": leak_person,
        "leakage_train_eval_garment": False,
        "leakage_train_eval_target": False,
        "body_height_cm": height,
        "body_bust_cm": bust,
        "body_waist_cm": waist,
        "body_hips_cm": hips,
        "garment_bust_cm": gbust,
        "garment_length_cm": glen,
        "garment_sleeve_cm": sleeve,
        "bust_ease_cm": ease,
        "bust_ease_ratio": ease / bust,
        "garment_length_height_ratio": glen / height,
    }


def test_pair_id_deterministic_and_unordered() -> None:
    a = make_pair_id("C", "eval/x/0001", "eval/x/0002")
    b = make_pair_id("A", "eval/x/0002", "eval/x/0001")
    assert a == b
    assert a.startswith("cf_")
    with pytest.raises(ValueError):
        make_pair_id("C", "same", "same")


def test_same_image_grouping_tier_a_and_c() -> None:
    rows = [
        _row("train/s/0000", person="p1", cloth="c1", target="t1", garment=(100.0, 60.0, 10.0)),
        _row("train/s/0001", person="p1", cloth="c1", target="t2", garment=(110.0, 60.0, 10.0)),
        _row("train/s/0002", person="p1", cloth="c2", target="t3", garment=(120.0, 62.0, 10.0), phash="bbbbbbbbbbbbbbbb"),
        _row("train/s/0003", person="p2", cloth="c9", target="t9", garment=(100.0, 60.0, 10.0)),
    ]
    df = pd.DataFrame(rows)
    a = analyze_person_cloth_groups(df)
    assert a["groups_with_gt1_row"] == 1
    assert a["tier_a_groups"] == 1
    pairs = build_candidates(df, include_tier_d=False)
    assert set(pairs["pair_tier"]) <= {"A", "B", "C"}
    assert (pairs["pair_tier"] == "A").any()
    # p1/c2 vs p1/c1 is TIER C (or B if phash close). c1-c2 phash differs.
    assert (pairs["same_person_image"]).all()


def test_measurement_delta_correctness() -> None:
    a = _row("train/s/0000", person="p", cloth="c1", target="t1", garment=(100.0, 60.0, 10.0))
    b = _row("train/s/0001", person="p", cloth="c2", target="t2", garment=(108.0, 60.0, 10.0), phash="bbbbbbbbbbbbbbbb")
    rec = build_pair_record(a, b, tier="C", group_key="g")
    assert rec is not None
    assert rec["anchor_sample_id"] == "train/s/0000"
    assert rec["counterfactual_sample_id"] == "train/s/0001"
    assert rec["delta_garment_bust_cm"] == pytest.approx(8.0)
    assert rec["delta_bust_ease_cm"] == pytest.approx(8.0)
    assert rec["single_variable_garment_change"] is True
    assert rec["measurement_intervention_type"] == "garment_bust_only"


def test_no_self_pairs_or_duplicate_unordered() -> None:
    rows = [
        _row("train/s/0000", person="p", cloth="c1", target="t1", garment=(100.0, 60.0, 10.0)),
        _row("train/s/0001", person="p", cloth="c2", target="t2", garment=(110.0, 60.0, 10.0), phash="bbbbbbbbbbbbbbbb"),
        _row("train/s/0002", person="p", cloth="c3", target="t3", garment=(120.0, 60.0, 10.0), phash="cccccccccccccccc"),
    ]
    pairs = build_candidates(pd.DataFrame(rows), include_tier_d=False)
    assert (pairs["anchor_sample_id"] != pairs["counterfactual_sample_id"]).all()
    keys = [
        unordered_pair_key(a, b)
        for a, b in zip(pairs["anchor_sample_id"], pairs["counterfactual_sample_id"], strict=True)
    ]
    assert len(keys) == len(set(keys))
    validate_candidates(pairs)


def test_candidate_schema_and_control_score() -> None:
    a = _row("train/s/0000", person="p", cloth="c1", target="t1")
    b = _row("train/s/0001", person="p", cloth="c1", target="t2", garment=(110.0, 60.0, 10.0))
    rec = build_pair_record(a, b, tier="A", group_key="g")
    assert rec is not None
    for col in PAIR_REQUIRED_COLUMNS:
        assert col in rec
    score = control_score(rec)
    assert 0.0 <= score <= 1.0
    assert score > 0.7
    assert rec["pair_construction_reason"]
    assert "TIER A" in rec["pair_construction_reason"]


def test_leakage_annotations_and_split_deterministic() -> None:
    rows = [
        _row("train/s/0000", person="p", cloth="c1", target="t1", split="train", leak_person=True),
        _row(
            "eval/s/0001",
            person="p",
            cloth="c2",
            target="t2",
            split="eval",
            shard="eval-00000-of-00020",
            garment=(110.0, 60.0, 10.0),
            phash="bbbbbbbbbbbbbbbb",
            leak_person=True,
        ),
        _row(
            "eval/s/0002",
            person="q",
            cloth="c3",
            target="t3",
            split="eval",
            shard="eval-00000-of-00020",
            leak_person=False,
        ),
    ]
    df = pd.DataFrame(rows)
    pairs = build_candidates(df, include_tier_d=False)
    assert pairs["leakage_person"].any()
    assert pairs["cross_split"].any()
    official = official_eval_ids(df)
    controlled = leakage_controlled_eval_ids(df)
    assert official == sorted(["eval/s/0001", "eval/s/0002"])
    assert controlled == ["eval/s/0002"]
    assert official == official_eval_ids(df)  # deterministic


def test_same_target_rejected() -> None:
    a = _row("train/s/0000", person="p", cloth="c1", target="t1")
    b = _row("train/s/0001", person="p", cloth="c2", target="t1", garment=(110.0, 60.0, 10.0))
    assert build_pair_record(a, b, tier="C", group_key="g") is None


def test_pilot_respects_shard_cap() -> None:
    rows = []
    for i in range(8):
        rows.append(
            _row(
                f"train/s/{i:04d}a",
                person=f"p{i}",
                cloth=f"c{i}a",
                target=f"t{i}a",
                shard=f"train-{i:05d}-of-00406",
                garment=(100.0, 60.0, 10.0),
            )
        )
        rows.append(
            _row(
                f"train/s/{i:04d}b",
                person=f"p{i}",
                cloth=f"c{i}b",
                target=f"t{i}b",
                shard=f"train-{i:05d}-of-00406",
                garment=(110.0, 60.0, 10.0),
                phash="bbbbbbbbbbbbbbbb",
            )
        )
    pairs = build_candidates(pd.DataFrame(rows), include_tier_d=False)
    pilot = select_pilot_pairs(pairs, n_pairs=10, max_shards=3, seed=0)
    shards = set(pilot["anchor_shard_id"]) | set(pilot["counterfactual_shard_id"])
    assert len(pilot) >= 1
    assert len(shards) <= 3


def test_phash_hamming() -> None:
    assert phash_hamming("0", "0") == 0
    assert phash_hamming("0", "1") == 1


def test_shortcut_audit_runs() -> None:
    rows = [
        _row("train/s/0000", person="p", cloth="c1", target="t1", garment=(100.0, 60.0, 10.0)),
        _row("train/s/0001", person="p", cloth="c2", target="t2", garment=(110.0, 60.0, 10.0), phash="bbbbbbbbbbbbbbbb"),
    ]
    pairs = build_candidates(pd.DataFrame(rows), include_tier_d=False)
    audit = shortcut_audit(pairs)
    assert audit["n_pairs"] >= 1
    assert "verdict" in audit


def test_materializer_sample_lookup(tmp_path: Path) -> None:
    df = pd.DataFrame(
        [
            {
                "sample_id": "eval/eval-00000-of-00020/0000",
                "source_split": "eval",
                "source_shard_id": "eval-00000-of-00020",
                "source_row_id": 0,
                "person_sha256": "aa",
                "garment_sha256": "bb",
                "target_sha256": "cc",
            }
        ]
    )
    path = tmp_path / "m.parquet"
    df.to_parquet(path, index=False)
    row = locate_sample(path, "eval/eval-00000-of-00020/0000")
    assert row["source_shard_id"] == "eval-00000-of-00020"
    assert row["source_row_id"] == 0
    with pytest.raises(KeyError):
        locate_sample(path, "missing")
