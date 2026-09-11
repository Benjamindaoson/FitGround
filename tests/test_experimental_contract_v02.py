"""Phase 2.5 contract / schema validators — no generation, no training."""

from fitground.contracts import (
    HOLD_FIXED,
    REQUIRED_MATRIX_VARIABLES,
    SIZE_LEVELS,
    control_variable_matrix_path,
    load_yaml,
    validate_control_variable_matrix,
    validate_experimental_contract,
    validate_gpu_e0,
    validate_ladder_schema,
    validate_phase_2_5_contracts,
)


def test_control_variable_matrix_complete() -> None:
    errors = validate_control_variable_matrix()
    assert errors == []
    payload = load_yaml(control_variable_matrix_path())
    names = [row["name"] for row in payload["variables"]]
    assert set(REQUIRED_MATRIX_VARIABLES) <= set(names)
    for row in payload["variables"]:
        assert row["role"] in {"INDEPENDENT", "CONTROLLED", "OUTCOME", "NUISANCE", "UNOBSERVED"}
        assert row["can_hold_fixed"] in HOLD_FIXED


def test_ladder_schema_is_measurement_vector() -> None:
    assert validate_ladder_schema() == []
    from fitground.contracts import ladder_schema_path

    schema = load_yaml(ladder_schema_path())
    assert tuple(schema["ordered_conditions"]) == SIZE_LEVELS
    assert schema["intervention_type"] == "measurement_vector"


def test_gpu_e0_acceptance_gates_frozen() -> None:
    assert validate_gpu_e0() == []
    from fitground.contracts import gpu_e0_path

    spec = load_yaml(gpu_e0_path())
    assert spec["scale"]["n_conditions"] == 45
    assert spec["stages"]["stage_2"]["authorized_if_ready"] is False
    assert spec["tracks"]["primary"] == "TRACK_A_MEASUREMENT_ISOLATED"
    assert spec["tracks"]["secondary"] == "TRACK_B_NATURALISTIC"


def test_experimental_contract_v02_frozen_and_denies_training() -> None:
    assert validate_experimental_contract() == []
    from fitground.contracts import contract_yaml_path

    contract = load_yaml(contract_yaml_path())
    assert contract["status"] == "FROZEN"
    assert contract["go_nogo_logic"]["CONTROLLED_COUNTERFACTUAL_GENERATION"] == "PARTIAL"
    assert contract["go_nogo_logic"]["READY_FOR_GPU_E0"] == "YES"
    assert "VLM training" in contract["does_not_authorize"]
    assert "LoRA" in contract["does_not_authorize"]


def test_phase_2_5_bundle_validates() -> None:
    assert validate_phase_2_5_contracts() == []
