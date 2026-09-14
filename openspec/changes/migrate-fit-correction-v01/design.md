## Context

The existing repository is a provenance-preserving FIT-Clean data-engineering and measurement-grounding research workspace. Its usable assets are canonical measurements, image identities/hashes, quality checks, deterministic IDs, an observed matched-pair counterfactual diagnostic, and frozen E0 controlled-ladder contracts. It has no local GarmentCode, pattern-parameter mapping, physics simulator, renderer, or GPU runner implementation. The new user is a technical designer with an already-observed sample problem; the required decision is a small next-sample correction.

## Goals / Non-Goals

**Goals:**

- Represent a current multimodal fit state, a correction action, an unverified predicted outcome, a cause hypothesis, and a correction lattice without manufacturing simulation data.
- Restrict V0.1 actions to bust circumference, shoulder width, and sleeve length deltas in centimetres.
- Keep intended and realized deltas distinct in every code path.
- Provide deterministic JSON artifacts, dry-run execution plans, preserved failure artifacts, and resumable local runner behavior.
- Preserve every existing frozen artifact byte-for-byte.

**Non-Goals:**

- No GarmentCode mapping, simulation, rendering, calibration result, GPU execution, data download, MLLM training, or RLVR.
- No claim that legacy TIGHT/REGULAR/LOOSE levels equal precise atomic corrections.
- No product UI, consumer recommendation, VTO, return prediction, or wider commerce function.

## Decisions

1. **Use standard-library dataclasses and explicit validators.** Existing code is plain Python plus PyArrow/Pandas and has no validation framework. This keeps the correction contract portable and prevents a new dependency from becoming a prerequisite. Pydantic/JSON Schema generation were considered but are not needed for V0.1.
2. **Use `NOT_RUN` / `NOT_VERIFIED` as first-class status values.** A missing simulator cannot be represented by copied measurements or placeholder outcomes. An outcome with `NOT_RUN` has no after-state, no utility, and no oracle selection.
3. **Keep correction code separate from legacy `counterfactual`.** The old package observes and matches independently generated FIT samples. The new package constructs planned interventions. Combining them would imply an unsupported causal equivalence.
4. **Use deterministic SHA-256 IDs over canonical JSON.** IDs remain stable across process runs and make duplicate candidate checks, resume, and evidence linking auditable.
5. **Implement `apply_correction()` as an unverified planning boundary.** It returns a supported `CandidateCorrection` but does not mutate a garment or infer a realized measurement. A concrete backend adapter is postponed until GPU calibration proves a mapping.
6. **Treat missing backend execution as a preserved failure, not a silent no-op.** The smoke runner writes a structured failure artifact on non-dry invocation; `--resume` reads that artifact rather than erasing evidence.

## Risks / Trade-offs

- [Dataclass payloads are less expressive than a full schema platform] → Validator errors and test fixtures define the required wire contract now; promote to generated JSON Schema only when external interchange needs it.
- [No local simulator] → Every locally produced result remains `NOT_RUN`; readiness is blocked only on a verified GarmentCode-to-action mapping and backend execution.
- [Legacy E0 action semantics differ] → Documentation explicitly repositions E0 as intervention/simulation sanity and prohibits treating levels as direct action deltas.
- [No Git work tree] → Packaging and tests are made runnable, while branch/commit references remain unavailable rather than invented.

## Migration Plan

1. Add packaging metadata so the current source is importable from the present workspace.
2. Add tests first for contract validity, action rejection, deterministic IDs, lattice uniqueness, missing outcomes, dry-run, resume, and frozen hashes.
3. Add correction modules and dry-run CLIs without touching historical code paths or files.
4. Write v0.1 contracts, migration evidence, smoke plan, README, and pre-GPU gate.
5. Install locally without dependencies, run the full suite, run dry-runs, and rehash frozen artifacts.

Rollback is deletion of the newly added correction/docs/OpenSpec files; no legacy data or code requires reversal.

## Open Questions

- Which future GarmentCode pattern parameter(s) can be calibrated to each V0.1 action family?
- Which extracted region-fit state and side-effect metrics are valid for the simulated verifier?
- What concrete visual-disambiguation cases can be generated only after action calibration succeeds?
