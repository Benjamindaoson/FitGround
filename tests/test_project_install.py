from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_project_metadata_declares_src_layout_package() -> None:
    """Catches loss of current-workspace importability after an editable install."""
    with (ROOT / "pyproject.toml").open("rb") as handle:
        metadata = tomllib.load(handle)
    assert metadata["project"]["name"] == "fitground"
    assert metadata["tool"]["setuptools"]["package-dir"] == {"": "src"}
