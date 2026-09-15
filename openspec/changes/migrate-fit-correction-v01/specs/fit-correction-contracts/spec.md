## ADDED Requirements

### Requirement: V0.1 correction state contract
The system SHALL validate a `CurrentFitState` with body, garment, visual assets, material, garment type, fit intent, regional fit state, and provenance. It SHALL reject missing required fields.

#### Scenario: Complete current state
- **WHEN** a caller constructs a state containing every required field
- **THEN** the state serializes deterministically to a machine-readable payload

#### Scenario: Missing visual evidence
- **WHEN** a caller constructs a state with no visual assets
- **THEN** validation raises a contract error

### Requirement: Limited correction action space
The system SHALL accept only `bust_circumference_delta_cm`, `shoulder_width_delta_cm`, and `sleeve_length_delta_cm` action families in V0.1.

#### Scenario: Unsupported action
- **WHEN** a caller requests `armhole_delta_cm`
- **THEN** the system rejects it as `NOT_SUPPORTED`

### Requirement: Intended and realized delta separation
The system SHALL preserve an intended delta independently from a realized delta and SHALL NOT infer or copy a realized value when calibration has not occurred.

#### Scenario: Uncalibrated correction
- **WHEN** `apply_correction` receives an intended bust delta of `3.0`
- **THEN** the candidate records `intended_delta_cm=3.0`, `realized_delta_cm=null`, and `verification_status=NOT_VERIFIED`

### Requirement: Deterministic correction lattice
The system SHALL construct a correction lattice with unique candidate IDs and `NOT_RUN` outcomes until a verified simulator produces results.

#### Scenario: Duplicate action candidate
- **WHEN** two candidates have the same action family and intended delta for one state
- **THEN** lattice validation rejects the duplicate ID

#### Scenario: Incomplete simulated outcome
- **WHEN** a caller requests complete-outcome validation for a `NOT_RUN` lattice
- **THEN** validation reports missing outcomes without fabricating an oracle action or utility
