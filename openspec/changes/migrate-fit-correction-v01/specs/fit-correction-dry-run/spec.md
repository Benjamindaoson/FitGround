## ADDED Requirements

### Requirement: Calibration dry-run framework
The calibration CLI SHALL produce a plan containing intended delta, null realized delta, and `NOT_RUN` status when invoked with `--dry-run`.

#### Scenario: Dry-run calibration
- **WHEN** the calibration CLI is run with a supported action and `--dry-run`
- **THEN** it exits successfully without a GarmentCode invocation or realized measurement

### Requirement: Smoke-runner failure preservation
The smoke runner SHALL preserve a structured failure artifact if called without `--dry-run` while no verified simulation backend exists.

#### Scenario: Backend absent
- **WHEN** the smoke runner is invoked for a planned case without dry-run mode
- **THEN** it writes `SIMULATION_BACKEND_NOT_CONFIGURED` and exits nonzero

### Requirement: Resume-safe runner
The smoke runner SHALL return an existing plan or failure artifact without overwriting it when `--resume` identifies the same case/action run.

#### Scenario: Resume failure artifact
- **WHEN** a previous backend-absent failure artifact exists and the same invocation includes `--resume`
- **THEN** the runner reports the preserved artifact as resumed
