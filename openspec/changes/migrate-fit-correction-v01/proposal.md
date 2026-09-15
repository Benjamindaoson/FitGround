## Why

FitGround's frozen legacy work proves FIT-Clean data provenance and a controlled TIGHT/REGULAR/LOOSE simulation-sanity protocol, but it does not represent the product decision: which precise garment correction should a technical designer make next. The product is now frozen around simulation-verified correction selection, so the repository needs a narrow correction contract without rewriting or relabeling legacy evidence.

## What Changes

- Add a v0.1 product and technical contract for multimodal fit correction of an already-problematic sample.
- Add machine-readable correction state, candidate-action, predicted-outcome, cause-hypothesis, and lattice schemas with explicit `NOT_RUN`, `NOT_VERIFIED`, and intended-versus-realized measurement states.
- Add a dry-run-only correction API, calibration framework, lattice builder/validator, and GPU smoke runner scaffold; no local physics execution is introduced.
- Reposition FIT-Clean, matched-pair counterfactuals, and Controlled Fit Ladder/E0 as legacy or simulation-intervention foundations.
- Add deterministic, local tests and a standard Python project definition so the repository can be installed and its checks can run from the current workspace.
- **BREAKING:** no existing data schema or frozen artifact changes; the project README changes from a measurement-grounding research framing to the correction-copilot product framing.

## Capabilities

### New Capabilities

- `fit-correction-contracts`: Defines valid correction state, V0.1 action space, outcome statuses, and deterministic correction lattices.
- `fit-correction-dry-run`: Builds plans and failure artifacts for correction calibration and GPU smoke execution without claiming a simulated result.
- `legacy-preservation`: Protects frozen FIT-Clean and E0 materials while positioning them as non-primary product assets.

### Modified Capabilities

- None.

## Impact

New code lives under `src/fitground/correction/`; new local CLIs live in `scripts/`; new tests live in `tests/`. Existing FIT-Clean pipeline, legacy counterfactual code, generated reports, experimental contracts, data files, and GPU E0 artifact bytes are preserved. Packaging metadata is added without new runtime dependencies.
