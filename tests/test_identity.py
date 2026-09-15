"""Tests for deterministic identity."""

from fitground.data.identity import make_image_identity, make_sample_id, shard_id_from_filename


def test_sample_id() -> None:
    sid = make_sample_id("eval", "eval-00000-of-00020", 42)
    assert sid == "eval/eval-00000-of-00020/0042"


def test_image_identity_includes_modality() -> None:
    ident = make_image_identity("person", "abc123")
    assert ident == "person:abc123"
    assert not ident.startswith("000000")


def test_shard_id_from_filename() -> None:
    assert shard_id_from_filename("eval-00000-of-00020.parquet") == "eval-00000-of-00020"
