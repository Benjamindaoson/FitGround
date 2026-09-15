from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FROZEN_TEXT_SHA256 = {
    "docs/FIT_CLEAN_DATA_CONTRACT.md": "5f0684ae4833ad9d94800c7d71f51a9eadcf8c3ad1065379330fdea7e91971d7",
    "docs/EXPERIMENTAL_CONTRACT_v0.1.md": "b93dc276ed254f9db7a7d4feead750570f13a20e7377411307cc6b2514de6fb5",
    "docs/EXPERIMENTAL_CONTRACT_v0.2.md": "b12ffef7cd6670f17e461a13c13e2c32caf3a386b774b77060e71c0ea36ffa18",
    "docs/GPU_E0_EXECUTION_ADDENDUM_v0.2.1.md": "b7ebc46726b178422042927d928f1ee0d1337c386660200c21b03878d6942dd6",
    "artifacts/fit_clean_schema_v0.1.json": "07ee322cd054a5f98f7698810ae1876fd6654e9b830814bac7f8b6918919b6f7",
    "artifacts/data_engineering_v0.1_fingerprint.json": "8d415a35eff2dd666268fa1fa1a733ab173e0c2974b9733060a62a630774b5f2",
    "artifacts/experimental_contract_v0.1.yaml": "8a0f1b502a49d48be245cb99d46dc80956fc7cbd67742b7c4f937110a3f2f79e",
    "artifacts/experimental_contract_v0.2.yaml": "4a2e086922ba5f9717921405f6e45aa0fffcce98b8f585b0185857dbf52b4244",
    "artifacts/controlled_fit_ladder_schema_v0.2.yaml": "856b1b08e269916e58114d8972bc0a1ff41613feef141853279e5ed3be07247b",
    "artifacts/control_variable_matrix_v0.2.yaml": "cddf2bbfd6041ae49c7e80a6d1d645ee501d810294dc627752018efa5661043f",
    "artifacts/gpu_e0_pilot_v0.2.yaml": "d67dbd5209add14a65f641dbab8360d527497a0d2d51959b1e57ac2c59d7de67",
    "artifacts/gpu_e0_execution_v0.2.1.yaml": "724bea4962c0508b3654b3ae15c3e444c5cd2aa8ff5b77007e8abdaa3a03dfc1",
}


def test_frozen_legacy_bytes_are_unchanged() -> None:
    """Catches an accidental edit to frozen FIT-Clean or E0 evidence."""
    for relative_path, expected_sha256 in FROZEN_TEXT_SHA256.items():
        data = (ROOT / relative_path).read_bytes().replace(b"\r\n", b"\n")
        actual_sha256 = hashlib.sha256(data).hexdigest()
        assert actual_sha256 == expected_sha256, relative_path
