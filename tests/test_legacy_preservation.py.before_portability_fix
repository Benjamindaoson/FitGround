from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FROZEN_SHA256 = {
    "docs/FIT_CLEAN_DATA_CONTRACT.md": "20b51326b7f666df4a628c63b74ae70799a61d2f1d290273e6f84063cb375ef1",
    "docs/EXPERIMENTAL_CONTRACT_v0.1.md": "b19805ac7f2998db40d5b19615dc86c508f8f3e57f29eab32c6d4d4d830c5e16",
    "docs/EXPERIMENTAL_CONTRACT_v0.2.md": "84080c0cf373bc691fdc68b0aa9a0877db5bccb954ca2c4c21d33d361c99a7ab",
    "docs/GPU_E0_EXECUTION_ADDENDUM_v0.2.1.md": "fe7e7515d55746f4d2c37fddce5d4206a45379ca8b58a0fbe6081faf015f7d92",
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
    for relative_path, expected_sha256 in FROZEN_SHA256.items():
        actual_sha256 = hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()
        assert actual_sha256 == expected_sha256, relative_path
