## 1. Local execution boundary

- [x] 1.1 Add standard `src`-layout package metadata without changing dependencies.
- [x] 1.2 Verify editable installation in the project `.venv`.

## 2. Correction contracts

- [x] 2.1 Add failing contract tests for required state fields, supported actions, intended/realized separation, and stable IDs.
- [x] 2.2 Implement the minimal correction schema and unverified action-planning API.
- [x] 2.3 Add deterministic lattice construction and complete-outcome validation.

## 3. Safe local execution tools

- [x] 3.1 Add calibration framework dry-run with null realized measurements.
- [x] 3.2 Add correction-lattice build and validation CLIs.
- [x] 3.3 Add smoke plan and runner with dry-run, failure preservation, and resume.

## 4. Product migration evidence

- [x] 4.1 Write product and technical contracts.
- [x] 4.2 Write file/module-level audit and legacy-to-new migration matrix.
- [x] 4.3 Update README and add pre-GPU readiness report.
- [x] 4.4 Add immutable historical hash checks.

## 5. Verification

- [x] 5.1 Run full pytest suite after editable installation.
- [x] 5.2 Run lattice, calibration, and smoke dry-runs.
- [x] 5.3 Rehash frozen history and inspect final change set.
