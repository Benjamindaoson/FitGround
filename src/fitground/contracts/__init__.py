"""Validators for Phase 2.5 machine-readable contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from fitground.config import ARTIFACTS_DIR, PROJECT_ROOT

CONTROL_ROLES = {"INDEPENDENT", "CONTROLLED", "OUTCOME", "NUISANCE", "UNOBSERVED"}
HOLD_FIXED = {"YES", "NO", "PARTIAL", "UNKNOWN"}
SIZE_LEVELS = ("TIGHT", "REGULAR", "LOOSE")

REQUIRED_CONTRACT_KEYS = (
    "version",
    "status",
    "research_question",
    "primary_hypothesis",
    "null_hypothesis",
    "independent_variable",
    "controlled_variables",
    "tracks",
    "gpu_e0",
    "shortcut_tests",
    "statistical_plan",
    "go_nogo_logic",
    "does_not_authorize",
)

REQUIRED_MATRIX_VARIABLES = (
    "body_identity",
    "body_measurements",
    "pose",
    "garment_design_identity",
    "garment_geometry",
    "garment_size",
    "garment_measurements",
    "fabric_material",
    "texture",
    "color",
    "camera",
    "lighting",
    "render_seed",
    "background",
    "sim2real_seed_style",
    "target_geometry",
    "cloth_input_image",
)


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def control_variable_matrix_path() -> Path:
    return ARTIFACTS_DIR / "control_variable_matrix_v0.2.yaml"


def ladder_schema_path() -> Path:
    return ARTIFACTS_DIR / "controlled_fit_ladder_schema_v0.2.yaml"


def gpu_e0_path() -> Path:
    return ARTIFACTS_DIR / "gpu_e0_pilot_v0.2.yaml"


def contract_yaml_path() -> Path:
    return ARTIFACTS_DIR / "experimental_contract_v0.2.yaml"


def contract_md_path() -> Path:
    return PROJECT_ROOT / "docs" / "EXPERIMENTAL_CONTRACT_v0.2.md"


def validate_control_variable_matrix(data: dict[str, Any] | None = None) -> list[str]:
    payload = data if data is not None else load_yaml(control_variable_matrix_path())
    errors: list[str] = []
    variables = payload.get("variables")
    if not isinstance(variables, list):
        return ["control matrix missing variables list"]
    names = [item.get("name") for item in variables if isinstance(item, dict)]
    for required in REQUIRED_MATRIX_VARIABLES:
        if required not in names:
            errors.append(f"missing control variable: {required}")
    for item in variables:
        if not isinstance(item, dict):
            errors.append("variable entry is not a mapping")
            continue
        name = item.get("name", "<unknown>")
        if item.get("role") not in CONTROL_ROLES:
            errors.append(f"{name}: invalid role {item.get('role')!r}")
        if item.get("can_hold_fixed") not in HOLD_FIXED:
            errors.append(f"{name}: invalid can_hold_fixed {item.get('can_hold_fixed')!r}")
        for field in ("control_mechanism", "verification_source", "residual_confound"):
            if not item.get(field):
                errors.append(f"{name}: missing {field}")
    return errors


def validate_ladder_schema(data: dict[str, Any] | None = None) -> list[str]:
    payload = data if data is not None else load_yaml(ladder_schema_path())
    errors: list[str] = []
    if payload.get("ordered_conditions") != list(SIZE_LEVELS):
        errors.append("ordered_conditions must be TIGHT, REGULAR, LOOSE")
    if payload.get("intervention_type") != "measurement_vector":
        errors.append("intervention_type must be measurement_vector")
    for key in ("required_ladder_ids", "required_condition_fields", "within_ladder_invariants"):
        if key not in payload:
            errors.append(f"ladder schema missing {key}")
    invariants = payload.get("within_ladder_invariants") or {}
    if "body_id" not in (invariants.get("must_be_identical") or []):
        errors.append("body_id must be a within-ladder invariant")
    if "garment_bust_cm" not in (invariants.get("must_change") or []):
        errors.append("garment_bust_cm must change within a ladder")
    return errors


def validate_gpu_e0(data: dict[str, Any] | None = None) -> list[str]:
    payload = data if data is not None else load_yaml(gpu_e0_path())
    errors: list[str] = []
    scale = payload.get("scale") or {}
    if int(scale.get("n_conditions") or 0) != 45:
        errors.append("GPU E0 n_conditions must be 45 (3×5×3)")
    if payload.get("tracks", {}).get("primary") != "TRACK_A_MEASUREMENT_ISOLATED":
        errors.append("GPU E0 primary track must be TRACK_A_MEASUREMENT_ISOLATED")
    if payload.get("stages", {}).get("stage_2", {}).get("authorized_if_ready") is not False:
        errors.append("GPU E0 Stage 2 must not be pre-authorized")
    criteria = payload.get("acceptance_criteria") or {}
    required_criteria = (
        "generation_success_rate",
        "control_variable_consistency",
        "measurement_monotonicity",
        "target_uniqueness",
        "target_fit_change_visibility",
        "visual_leakage_severity",
        "reproducibility",
        "metadata_completeness",
    )
    for name in required_criteria:
        block = criteria.get(name)
        if not isinstance(block, dict):
            errors.append(f"missing acceptance criterion {name}")
            continue
        if name == "visual_leakage_severity":
            if "track_a" not in block or "track_b" not in block:
                errors.append("visual leakage must split Track A and Track B")
            continue
        for gate in ("GO", "PARTIAL", "NO_GO"):
            if gate not in block:
                errors.append(f"{name} missing {gate}")
    if payload.get("human_visual_protocol", {}).get("forbidden") != "VLM self-labeling of GO/NO-GO":
        errors.append("human protocol must forbid VLM self-labeling")
    return errors


def validate_experimental_contract(data: dict[str, Any] | None = None) -> list[str]:
    payload = data if data is not None else load_yaml(contract_yaml_path())
    errors: list[str] = []
    for key in REQUIRED_CONTRACT_KEYS:
        if key not in payload:
            errors.append(f"contract missing {key}")
    if payload.get("status") != "FROZEN":
        errors.append("v0.2 contract must be FROZEN")
    denied = payload.get("does_not_authorize") or []
    for item in ("VLM training", "LoRA", "DPO", "GRPO"):
        if item not in denied:
            errors.append(f"contract must deny {item}")
    logic = payload.get("go_nogo_logic") or {}
    if logic.get("CONTROLLED_COUNTERFACTUAL_GENERATION") != "PARTIAL":
        errors.append("generation verdict must be PARTIAL")
    if logic.get("READY_FOR_GPU_E0") != "YES":
        errors.append("READY_FOR_GPU_E0 must be YES")
    if logic.get("training_authorization") != (
        "DENIED until GPU E0 overall GO and a later contract says otherwise"
    ):
        errors.append("training must remain denied")
    tracks = payload.get("tracks") or {}
    if tracks.get("primary", {}).get("id") != "TRACK_A_MEASUREMENT_ISOLATED":
        errors.append("primary track id mismatch")
    if tracks.get("secondary", {}).get("id") != "TRACK_B_NATURALISTIC":
        errors.append("secondary track id mismatch")
    if not contract_md_path().is_file():
        errors.append("docs/EXPERIMENTAL_CONTRACT_v0.2.md missing")
    v01 = PROJECT_ROOT / "docs" / "EXPERIMENTAL_CONTRACT_v0.1.md"
    if v01.is_file() and "v0.2" in v01.read_text(encoding="utf-8")[:200]:
        errors.append("v0.1 markdown must not be replaced by v0.2")
    return errors


def validate_phase_2_5_contracts() -> list[str]:
    errors: list[str] = []
    errors.extend(validate_control_variable_matrix())
    errors.extend(validate_ladder_schema())
    errors.extend(validate_gpu_e0())
    errors.extend(validate_experimental_contract())
    return errors
