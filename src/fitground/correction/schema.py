"""Machine-readable V0.1 fit-correction value contracts.

The contracts deliberately model unobserved execution as ``NOT_RUN`` and an
uncalibrated action as ``NOT_VERIFIED``. They never infer simulation results.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field, replace
from hashlib import sha256
from typing import Any

SUPPORTED_ACTION_FAMILIES = (
    "bust_circumference_delta_cm",
    "shoulder_width_delta_cm",
    "sleeve_length_delta_cm",
)
OUTCOME_STATUSES = ("NOT_RUN", "SIMULATED", "FAILED")
RENDER_STATUSES = ("NOT_RUN", "RENDERED", "FAILED", "NOT_APPLICABLE")
VERIFICATION_STATUSES = ("NOT_VERIFIED", "VERIFIED", "FAILED")
LATTICE_PROVENANCE_FIELDS = (
    "git_sha",
    "environment",
    "seed",
    "source_assets",
    "artifact_paths",
)


class ContractValidationError(ValueError):
    """A payload violates a V0.1 correction contract."""


def canonical_json(value: Any) -> str:
    """Stable JSON used for IDs and evidence hashing."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    return f"{prefix}_{sha256(canonical_json(dict(payload)).encode('utf-8')).hexdigest()[:16]}"


def _require_nonempty_mapping(name: str, value: Mapping[str, Any]) -> None:
    if not isinstance(value, Mapping) or not value:
        raise ContractValidationError(f"{name} must be a non-empty mapping")


def _require_nonempty_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ContractValidationError(f"{name} must be non-empty")


@dataclass(frozen=True)
class CurrentFitState:
    state_id: str
    body: Mapping[str, Any]
    garment: Mapping[str, Any]
    visual_assets: list[str]
    material: Mapping[str, Any]
    garment_type: str
    fit_intent: str
    region_fit_state: Mapping[str, Any]
    provenance: Mapping[str, Any]

    def __post_init__(self) -> None:
        _require_nonempty_text("state_id", self.state_id)
        for name in ("body", "garment", "material", "region_fit_state", "provenance"):
            _require_nonempty_mapping(name, getattr(self, name))
        if not isinstance(self.visual_assets, list) or not self.visual_assets or not all(
            isinstance(asset, str) and asset for asset in self.visual_assets
        ):
            raise ContractValidationError("visual_assets must contain at least one asset reference")
        _require_nonempty_text("garment_type", self.garment_type)
        _require_nonempty_text("fit_intent", self.fit_intent)
        if not self.provenance.get("source"):
            raise ContractValidationError("provenance.source is required")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> CurrentFitState:
        return cls(**dict(payload))


@dataclass(frozen=True)
class CandidateCorrection:
    action_family: str
    intended_delta_cm: float
    realized_delta_cm: float | None = None
    source_pattern_parameters: Mapping[str, Any] = field(default_factory=dict)
    candidate_id: str | None = None
    verification_status: str = "NOT_VERIFIED"

    def __post_init__(self) -> None:
        if self.action_family not in SUPPORTED_ACTION_FAMILIES:
            raise ContractValidationError(f"NOT_SUPPORTED action_family: {self.action_family}")
        if not isinstance(self.intended_delta_cm, (int, float)) or isinstance(self.intended_delta_cm, bool):
            raise ContractValidationError("intended_delta_cm must be numeric")
        if float(self.intended_delta_cm) == 0.0:
            raise ContractValidationError("intended_delta_cm must be non-zero")
        if self.realized_delta_cm is not None and not isinstance(self.realized_delta_cm, (int, float)):
            raise ContractValidationError("realized_delta_cm must be numeric or null")
        if self.verification_status not in VERIFICATION_STATUSES:
            raise ContractValidationError("invalid verification_status")

    def identified_for(self, state_id: str) -> CandidateCorrection:
        return replace(
            self,
            candidate_id=stable_id(
                "correction",
                {
                    "state_id": state_id,
                    "action_family": self.action_family,
                    "intended_delta_cm": float(self.intended_delta_cm),
                },
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> CandidateCorrection:
        return cls(**dict(payload))


@dataclass(frozen=True)
class PredictedFitOutcome:
    candidate_id: str
    region_before: Mapping[str, Any]
    region_after: Mapping[str, Any] | None
    direction: str | None
    magnitude: float | None
    side_effects: list[Mapping[str, Any]]
    confidence: float | None
    simulation_status: str
    render_status: str
    reproducibility: Mapping[str, Any]
    hashes: Mapping[str, str]
    provenance: Mapping[str, Any]

    def __post_init__(self) -> None:
        _require_nonempty_text("candidate_id", self.candidate_id)
        _require_nonempty_mapping("region_before", self.region_before)
        _require_nonempty_mapping("provenance", self.provenance)
        if not isinstance(self.reproducibility, Mapping):
            raise ContractValidationError("reproducibility must be a mapping")
        if not isinstance(self.hashes, Mapping) or not all(
            isinstance(name, str) and isinstance(digest, str) for name, digest in self.hashes.items()
        ):
            raise ContractValidationError("hashes must be a string-to-string mapping")
        if self.simulation_status not in OUTCOME_STATUSES:
            raise ContractValidationError("invalid simulation_status")
        if self.render_status not in RENDER_STATUSES:
            raise ContractValidationError("invalid render_status")
        if self.simulation_status == "SIMULATED" and not self.region_after:
            raise ContractValidationError("region_after is required for SIMULATED outcomes")
        if self.simulation_status == "NOT_RUN" and self.region_after is not None:
            raise ContractValidationError("NOT_RUN outcome cannot contain region_after")
        if self.simulation_status == "NOT_RUN" and self.render_status != "NOT_RUN":
            raise ContractValidationError("NOT_RUN simulation requires NOT_RUN render")
        if self.confidence is not None and not 0.0 <= float(self.confidence) <= 1.0:
            raise ContractValidationError("confidence must be in [0, 1]")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> PredictedFitOutcome:
        return cls(**dict(payload))


@dataclass(frozen=True)
class CauseHypothesis:
    cause: str
    supporting_evidence: list[str]
    confidence: float | None
    verification_status: str

    def __post_init__(self) -> None:
        _require_nonempty_text("cause", self.cause)
        if not self.supporting_evidence:
            raise ContractValidationError("supporting_evidence must not be empty")
        if self.confidence is not None and not 0.0 <= float(self.confidence) <= 1.0:
            raise ContractValidationError("confidence must be in [0, 1]")
        if self.verification_status not in VERIFICATION_STATUSES:
            raise ContractValidationError("invalid verification_status")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CorrectionLattice:
    lattice_id: str
    state_id: str
    candidate_actions: list[CandidateCorrection]
    outcomes: list[PredictedFitOutcome]
    utilities: Mapping[str, float | None]
    oracle_action: str | None
    ranking: list[str] | None
    verification_status: str
    provenance: Mapping[str, Any]

    def __post_init__(self) -> None:
        _require_nonempty_text("lattice_id", self.lattice_id)
        _require_nonempty_text("state_id", self.state_id)
        if not self.candidate_actions:
            raise ContractValidationError("candidate_actions must not be empty")
        candidate_ids = [candidate.candidate_id for candidate in self.candidate_actions]
        if any(identifier is None for identifier in candidate_ids):
            raise ContractValidationError("candidate_actions require candidate_id")
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ContractValidationError("duplicate candidate_id in lattice")
        outcome_ids = [outcome.candidate_id for outcome in self.outcomes]
        if len(outcome_ids) != len(set(outcome_ids)):
            raise ContractValidationError("duplicate outcome candidate_id in lattice")
        if not set(outcome_ids).issubset(set(candidate_ids)):
            raise ContractValidationError("outcome references unknown candidate")
        if self.oracle_action is not None and self.oracle_action not in candidate_ids:
            raise ContractValidationError("oracle_action references unknown candidate")
        if self.ranking is not None:
            if not isinstance(self.ranking, list) or set(self.ranking) != set(candidate_ids):
                raise ContractValidationError("ranking must contain every candidate exactly once")
            if len(self.ranking) != len(set(self.ranking)):
                raise ContractValidationError("ranking must contain every candidate exactly once")
        if self.oracle_action is not None and (not self.ranking or self.ranking[0] != self.oracle_action):
            raise ContractValidationError("oracle_action must be first in ranking")
        if self.verification_status not in VERIFICATION_STATUSES:
            raise ContractValidationError("invalid verification_status")
        _require_nonempty_mapping("provenance", self.provenance)
        missing_provenance = [field for field in LATTICE_PROVENANCE_FIELDS if field not in self.provenance]
        if missing_provenance:
            raise ContractValidationError(
                f"lattice provenance missing required fields: {', '.join(missing_provenance)}"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "lattice_id": self.lattice_id,
            "state_id": self.state_id,
            "candidate_actions": [candidate.to_dict() for candidate in self.candidate_actions],
            "outcomes": [outcome.to_dict() for outcome in self.outcomes],
            "utilities": dict(self.utilities),
            "oracle_action": self.oracle_action,
            "ranking": self.ranking,
            "verification_status": self.verification_status,
            "provenance": dict(self.provenance),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> CorrectionLattice:
        data = dict(payload)
        data["candidate_actions"] = [CandidateCorrection.from_dict(item) for item in data["candidate_actions"]]
        data["outcomes"] = [PredictedFitOutcome.from_dict(item) for item in data["outcomes"]]
        return cls(**data)
