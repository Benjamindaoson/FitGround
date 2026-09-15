from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FROZEN_TEXT_SHA256 = {
    "docs/FIT_CLEAN_DATA_CONTRACT.md": "5f0684ae4833ad9d94800c7d71f51a9eadcf8c3ad1065379330fdea7e91971d7",
    "docs/EXPERIMENTAL_CONTRACT_v0.1.md": "b93dc276ed254f9db7a7d4feead750570f13a20e7377411307cc6b2514de6fb5",
    "docs/EXPERIMENTAL_CONTRACT_v0.2.md": "b12ffef7cd6670f17e461a13c13e2c32caf3a386b774b77060e71c0ea36ffa18",
    "docs/GPU_E0_EXECUTION_ADDENDUM_v0.2.1.md": "b7ebc46726b178422042927d928f1ee0d1337c386660200c21b03878d6942dd6",
}

FROZEN_BINARY_SHA256 = {
    "artifacts/fit_clean_schema_v0.1.json": "2b9d315ef7e89825819a18f562a03627f4b06438936b75e88acb980a103e47b1",
    "artifacts/data_engineering_v0.1_fingerprint.json": "8704fe48e2ad8a643522133366243a2c28715908339d19f86c5fca74bb18d917",
    "artifacts/experimental_contract_v0.1.yaml": "8c23fde934ae9cb295555abe26fcbbe7f01de644991eeca1b3c5dadc012a4485",
    "artifacts/experimental_contract_v0.2.yaml": "5bdb27d52bd8e13c3e07abb8f385b68b7cbbc9e64dae67395dd18f40dd1920bc",
    "artifacts/controlled_fit_ladder_schema_v0.2.yaml": "1506ec3fe15b45bcbefc1cd8c106ec9f7f5caabbf2bf4111cffc3e31d72abd47",
    "artifacts/control_variable_matrix_v0.2.yaml": "a86f62afee905fe9927eb27e40442ac88d2ac2fd3ff4ea1599dd17b90865e8f9",
    "artifacts/gpu_e0_pilot_v0.2.yaml": "bef7b571bc091093e02a77df5f63577a3ba47e95862a3cab5f1d3cb92d35ac78",
    "artifacts/gpu_e0_execution_v0.2.1.yaml": "3a187c4eedb18be75c667f9fe8e3ba6250b824c3b3b1075768dcb78313cba550",
}


def test_frozen_legacy_bytes_are_unchanged() -> None:
    """Catches an accidental edit to frozen FIT-Clean or E0 evidence."""
    for relative_path, expected_sha256 in FROZEN_TEXT_SHA256.items():
        data = (ROOT / relative_path).read_bytes().replace(b"\r\n", b"\n")
        actual_sha256 = hashlib.sha256(data).hexdigest()
        assert actual_sha256 == expected_sha256, relative_path

    for relative_path, expected_sha256 in FROZEN_BINARY_SHA256.items():
        actual_sha256 = hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()
        assert actual_sha256 == expected_sha256, relative_path
