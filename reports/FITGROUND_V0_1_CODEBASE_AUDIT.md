# FitGround V0.1 Codebase Audit

**Audit date:** 2026-09-15
**Scope:** Entire local `D:\FitGround` tree excluding virtualenv/cache bytecode, with source navigation through CodeGraph and direct inspection of contracts, artifacts, scripts, tests, reports, and runtime files.
**Evidence rule:** Existing generated reports/artifacts are treated as historical evidence, not as current product claims.

## Executive finding

The repository originally solved a different, narrower research problem: make a deterministic, auditable FIT-Clean v0.1 manifest from FIT-100K; inspect observed measurement distributions and image leakage; then construct matched, mostly person-held garment-swap pairs for a **measurement-grounding diagnostic**. Its later frozen design specifies a **Controlled Fit Ladder** for a GPU E0 pilot, but this local tree contains only its contracts and validators—not GarmentCode, a simulator, a renderer, or a GPU execution implementation.

The new product instead needs a correction decision loop for a known-bad current sample: `(state, candidate action) -> simulated next fit state -> lowest-regret action`. The old measurement/provenance pipeline is valuable foundation, but the observed matched-pair task and the TIGHT/REGULAR/LOOSE ladder are not the correction product's primary dataset or action interface.

### Decision key

| Label | Meaning in this audit |
|---|---|
| `KEEP` | Correct as-is and retained in the product foundation |
| `ADAPT` | Reused with changed framing or a narrow interface addition |
| `DEPRECATE` | Preserved but no longer a primary product path |
| `REPLACE` | Historical primary purpose is superseded by a new product construct |
| `NEW_REQUIRED` | Missing capability added by this migration |
| `GPU_ONLY_VERIFY` | Interface/spec exists, but truth requires future calibrated GPU verification |

## Current repository structure and runtime flow

```text
FIT-100K shards
  -> FIT-Clean streaming / quality / hashes / checkpoints
  -> canonical parquet manifest
  -> closure audits + reports + fingerprint
  -> observed matched counterfactual candidates + pilot materialization

Frozen design-only branch:
  Controlled TIGHT/REGULAR/LOOSE ladder contract
  -> future public GarmentCode cross-drape GPU E0 (not implemented locally)
```

The validated interactive evidence map is [FITGROUND_EXISTING_RUNTIME_ARCHITECTURE.html](/D:/FitGround/docs/architecture/FITGROUND_EXISTING_RUNTIME_ARCHITECTURE.html). It is an audit orientation artifact, not a claim that its planned GPU branch executes.

## File and module classification

| Path | Old Purpose | New Relevance | Decision | Required Change |
|---|---|---|---|---|
| `FitGround.md` | Long-form product/research concept note | Contains useful product intuition but is not the repository entrypoint or frozen contract | `DEPRECATE` | Keep as historical ideation; use new README/contracts for current scope |
| `README.md` | Missing | Current project entrypoint | `NEW_REQUIRED` | Created with correction-first scope and legacy positioning |
| `pyproject.toml` | Missing; only stale egg-info exists | Required to run current workspace tests/install | `NEW_REQUIRED` | Created with existing dependency set and `src` layout |
| `src/fitground/config.py` | FIT-Clean paths, thresholds, counterfactual constants | FIT-Clean remains source/provenance foundation | `KEEP` | Do not add correction/simulation assumptions here |
| `src/fitground/data/schema.py` | FIT-Clean Arrow schema | Reusable measurement/image identity vocabulary, not correction schema | `KEEP` | Consume as upstream source only |
| `src/fitground/data/measurements.py` | Canonicalize FIT dimensions in cm | Reusable measurement normalization | `KEEP` | Do not infer V0.1 action calibration from raw fields |
| `src/fitground/data/features.py` | Bust ease and length ratio | Useful baseline feature foundation | `ADAPT` | Future baseline may consume it; not an outcome predictor |
| `src/fitground/data/identity.py` | Stable sample/image IDs | Directly useful provenance pattern | `KEEP` | Reuse deterministic-ID discipline |
| `src/fitground/data/images.py` | Decode/hash FIT image bytes | Upstream visual integrity mechanism | `KEEP` | Future visual assets retain references/hashes |
| `src/fitground/data/quality.py` | FIT-Clean VALID/SUSPICIOUS/INVALID | Upstream input quality gate | `KEEP` | Keep distinct from correction verification status |
| `src/fitground/data/duplicates.py` | Image duplicate/leakage annotation | Training/evaluation hygiene | `KEEP` | Apply when future lattice data gets splits |
| `src/fitground/data/download.py` | FIT shard retrieval | Existing source material only | `DEPRECATE` | Do not run for correction phase or download more data |
| `src/fitground/data/disk_guard.py` | Download/storage guard | General safe pipeline utility | `KEEP` | Reuse if future data generation requires local storage |
| `src/fitground/data/memory.py` | RSS limits/tracking | General pipeline resilience | `KEEP` | Reuse in future GPU orchestration only if applicable |
| `src/fitground/data/eval_checkpoint.py` | Eval stream checkpoints | FIT-Clean resiliency | `KEEP` | Preserve historical pipeline |
| `src/fitground/data/fit_checkpoint.py` | Full FIT stream checkpoints | FIT-Clean resiliency | `KEEP` | Preserve historical pipeline |
| `src/fitground/data/stream_core.py` | Bounded image-row processing | FIT-Clean build path | `KEEP` | No correction responsibility |
| `src/fitground/data/shard_processor.py` | Shard record transformation | FIT-Clean build path | `KEEP` | No correction responsibility |
| `src/fitground/data/eval_pipeline.py` | Eval manifest processing/audits | FIT-Clean evidence | `KEEP` | Preserve |
| `src/fitground/data/fit_stream_pipeline.py` | 105K FIT-Clean streaming pipeline | FIT-Clean foundation | `KEEP` | Preserve; do not re-run as a correction generator |
| `src/fitground/data/pipeline.py` | Older full pipeline orchestration | Historical ingestion path | `DEPRECATE` | Use stream pipeline for legacy rebuild only |
| `src/fitground/data/sample_lookup.py` | Locate materializable FIT sample | Useful evidence lookup | `ADAPT` | Future lattice should use explicit current-state refs, not assume FIT row |
| `src/fitground/audit/eda.py` | Distribution visualizations | Dataset profile/baseline evidence | `KEEP` | Preserve as observational analysis |
| `src/fitground/audit/readiness.py` | FIT data readiness decision | Old data-engineering gate | `DEPRECATE` | Do not use as product/GPU correction readiness |
| `src/fitground/closure/audit.py` | FIT-Clean closure and leakage reports | Provenance/quality evidence | `KEEP` | Preserve immutable historical reports |
| `src/fitground/audit.py` | Audit CLI wrapper | Legacy audit entrypoint | `DEPRECATE` | No correction role |
| `src/fitground/contracts/__init__.py` | Validate frozen v0.2 ladder/E0 YAML | Essential frozen-history guard | `KEEP` | Keep validation isolated from new correction contracts |
| `src/fitground/counterfactual/schema.py` | Observed pair columns/IDs | Similar evidence patterns, wrong product unit | `DEPRECATE` | Do not reuse as correction lattice schema |
| `src/fitground/counterfactual/discovery.py` | Discover same-person/cloth grouping | Proves observational data limitation | `KEEP` | Retain as legacy evidence; no causal promotion |
| `src/fitground/counterfactual/controls.py` | Confound/control scoring for pairs | Useful research hygiene pattern | `ADAPT` | Future lattice controls must be action/outcome-specific |
| `src/fitground/counterfactual/matching.py` | Build matched garment-swap pairs | Not an intervention/action generator | `DEPRECATE` | Preserve for diagnostic only |
| `src/fitground/counterfactual/validation.py` | Pair uniqueness/delta validation | Useful validation shape but different semantics | `ADAPT` | Use new lattice validator for action/outcome completeness |
| `src/fitground/counterfactual/pilot.py` | Select shard-bounded visual pair pilot | Legacy sanity sampling | `DEPRECATE` | Keep materialized pilot evidence unchanged |
| `src/fitground/correction/schema.py` | Missing | Current state/action/outcome/hypothesis/lattice contracts | `NEW_REQUIRED` | Created; exact V0.1 action/status rules |
| `src/fitground/correction/api.py` | Missing | Correction application boundary | `NEW_REQUIRED` | Created as non-mutating, `NOT_VERIFIED` planner |
| `src/fitground/correction/lattice.py` | Missing | Candidate/outcome lattice foundation | `NEW_REQUIRED` | Created; emits only `NOT_RUN` outcomes locally |
| `src/fitground/correction/validation.py` | Missing | Lattice uniqueness/completeness evidence gate | `NEW_REQUIRED` | Created; complete-outcome validation is explicit |
| `scripts/run_pipeline.py` | Full FIT data engineering | Historical source build | `DEPRECATE` | Do not use as correction pipeline |
| `scripts/run_fit_stream.py` | FIT-Clean streamed build/resume | Historical source build | `KEEP` | Preserve as legacy rerun tool |
| `scripts/run_eval_audit.py` | Eval audit | Historical evidence | `KEEP` | Preserve |
| `scripts/run_closure_audit.py` | Closure audit | Historical evidence | `KEEP` | Preserve |
| `scripts/validate_manifest.py` | FIT-Clean row-count check | Data foundation verification | `KEEP` | Preserve |
| `scripts/generate_schema_artifact.py` | Generate frozen FIT-Clean schema | Frozen data-contract maintenance | `KEEP` | Do not run against/version-bump v0.1 without authorization |
| `scripts/generate_data_engineering_fingerprint.py` | Hash and gate FIT-Clean finalization | Historical evidence/reproducibility | `KEEP` | Preserve; its Git field is unavailable in this local copy |
| `scripts/build_source_manifest.py` | Source shard manifest | Dataset provenance | `KEEP` | Preserve |
| `scripts/materialize_samples.py` | Retrieve selected FIT image assets | Legacy evidence materialization | `ADAPT` | Future lattice visual refs can use equivalent hash-safe extraction |
| `scripts/materialize_counterfactual_pilot.py` | Contact sheets for observed pairs | Legacy visual sanity | `DEPRECATE` | Preserve output; not correction data generation |
| `scripts/discover_counterfactual_structure.py` | Discover old matching structure | Historical limitation evidence | `KEEP` | Preserve |
| `scripts/build_counterfactual_candidates.py` | Generate old matched pairs | Measurement-grounding diagnostic | `DEPRECATE` | No new runs for correction product |
| `scripts/analyze_memory_trend.py` | FIT stream RSS analysis | Data-engineering operational evidence | `KEEP` | Preserve |
| `scripts/env_audit.py` | Linux `/workspace` environment audit | Non-portable legacy helper | `REPLACE` | Use normal project commands; no correction dependency |
| `scripts/calibrate_correction_action.py` | Missing | Intended-to-realized calibration framework | `NEW_REQUIRED` | Created dry-run-only; backend mapping remains `GPU_ONLY_VERIFY` |
| `scripts/build_correction_lattice.py` | Missing | Serialize planned lattices | `NEW_REQUIRED` | Created without synthetic after-state |
| `scripts/validate_correction_lattice.py` | Missing | Validate planned/complete lattice distinction | `NEW_REQUIRED` | Created |
| `scripts/run_fit_correction_smoke.py` | Missing | GPU correction smoke orchestration contract | `NEW_REQUIRED` | Created dry-run/failure-preserving shell; execution is `GPU_ONLY_VERIFY` |
| `artifacts/fit_clean_schema_v0.1.json` | Frozen FIT-Clean wire schema | Upstream measurement/provenance asset | `KEEP` | Hash-protected; no edit |
| `artifacts/data_engineering_v0.1_fingerprint.json` | Frozen FIT-Clean fingerprint | Evidence of source generation | `KEEP` | Hash-protected; no edit |
| `artifacts/counterfactual_*_v0.1.json` | Old observed-pair discovery/validation evidence | Historical feasibility evidence | `KEEP` | Preserve; no causal upgrade |
| `artifacts/experimental_contract_v0.1.yaml` | Frozen measurement-grounding diagnostic contract | Legacy research history | `KEEP` | Hash-protected; not product contract |
| `artifacts/experimental_contract_v0.2.yaml` | Frozen controlled-ladder research contract | Simulation intervention foundation | `KEEP` | Hash-protected; not V0.1 action calibration |
| `artifacts/controlled_fit_ladder_schema_v0.2.yaml` | TIGHT/REGULAR/LOOSE ladder schema | Legacy/simulation sanity | `ADAPT` | Reposition only; retain labels and bytes |
| `artifacts/control_variable_matrix_v0.2.yaml` | E0 controls | Useful simulator experiment rigor | `KEEP` | Preserve; reuse concepts later |
| `artifacts/gpu_e0_pilot_v0.2.yaml` | Frozen 3x5x3 GPU E0 plan | Legacy GPU simulation sanity plan | `DEPRECATE` | Do not call product smoke plan or execute under this migration |
| `artifacts/gpu_e0_execution_v0.2.1.yaml` | Frozen E0 causal/leakage addendum | Historical execution contract | `KEEP` | Hash-protected; not changed |
| `artifacts/fit_correction_smoke_plan_v0.1.yaml` | Missing | New chest/shoulder/sleeve plan | `NEW_REQUIRED` | Created plan only; all outcomes `NOT_RUN` |
| `schemas/fit_correction_v0.1.schema.json` | Missing | Machine-readable correction contract | `NEW_REQUIRED` | Created alongside Python validators |
| `docs/FIT_CLEAN_DATA_CONTRACT.md` | FIT-Clean frozen contract | Upstream provenance | `KEEP` | Hash-protected |
| `docs/EXPERIMENTAL_CONTRACT_v0.1.md` | Old measurement-grounding contract | Historical research | `KEEP` | Hash-protected |
| `docs/EXPERIMENTAL_CONTRACT_v0.2.md` | Controlled ladder contract | Simulation sanity/intervention foundation | `ADAPT` | Position as legacy foundation only |
| `docs/GPU_E0_EXECUTION_ADDENDUM_v0.2.1.md` | Frozen E0 execution semantics | Historical/GPU methodology guard | `KEEP` | Hash-protected |
| `docs/context/*` | GPU handoff guidance | Superseded as current product handoff | `DEPRECATE` | Preserve; point new work to V0.1 contracts |
| `docs/LOCAL_WINDOWS_HANDOFF.md` | Legacy clone/test/data instructions | Partly reusable local setup evidence | `ADAPT` | README now supplies current correction quick start |
| `docs/MATERIALIZE_SAMPLES.md` | FIT sample materialization instructions | Legacy evidence operation | `KEEP` | Preserve |
| `docs/DATA_LICENSE_AND_ATTRIBUTION.md` | FIT source licensing policy | Required source-data boundary | `KEEP` | Preserve |
| `docs/FITGROUND_PRODUCT_CONTRACT_v0.1.md` | Missing | Frozen business/product boundary | `NEW_REQUIRED` | Created |
| `docs/FITGROUND_TECHNICAL_CONTRACT_v0.1.md` | Missing | Frozen correction technical boundary | `NEW_REQUIRED` | Created |
| `reports/*` existing audits/evidence/runs | Historical observed evidence | Essential provenance and negative findings | `KEEP` | No overwrite/delete; new audit files are additive |
| `reports/FIT_GENERATION_MECHANISM_AUDIT.md` | GarmentCode/FIT mechanism audit | Correct warning that official code is unavailable | `KEEP` | Use as `GPU_ONLY_VERIFY` evidence |
| `reports/FITGROUND_V0_1_*.md` | Missing | New audit/migration/readiness reports | `NEW_REQUIRED` | Created additively |
| `tests/test_counterfactual.py` | Old observed-pair validation | Regression protection for legacy diagnostic | `KEEP` | Preserve |
| `tests/test_experimental_contract_v02.py` | Frozen ladder contract validation | Critical preservation guard | `KEEP` | Preserve |
| `tests/test_{schema,measurements,identity,quality,features}.py` | FIT-Clean contract/unit tests | Data foundation regression protection | `KEEP` | Preserve |
| `tests/test_{eval_pipeline,eval_streaming,closure_audit,failure_injection,memory,determinism}.py` | Data engineering checks | Historical resilience/reproducibility | `KEEP` | Preserve |
| `tests/test_correction_schema.py` | Missing | Correction contract verification | `NEW_REQUIRED` | Created |
| `tests/test_correction_scripts.py` | Missing | Dry-run/failure/resume verification | `NEW_REQUIRED` | Created |
| `tests/test_legacy_preservation.py` | Missing | Frozen-byte regression gate | `NEW_REQUIRED` | Created |
| `src/fitground.egg-info/` | Stale build metadata references old location/description | Unsafe as project definition | `REPLACE` | `pyproject.toml` becomes source of truth; regenerate only through packaging |
| `.codegraph/` | Local navigation index | Non-authoritative developer aid | `KEEP` | Do not treat as evidence or commit requirement |
| `.venv/`, `.pytest_cache/`, `cache/` | Local runtime/cache state | Not source/product artifacts | `DEPRECATE` | Exclude from publication and audit claims |
| `.github/`, CI configs | Not present | No automated CI gate | `NEW_REQUIRED` | Optional future delivery work; not needed for pre-GPU correction scope |

## What is absent

No local source or script implements GarmentCode integration, Warp/physics simulation, a render pipeline, pattern-parameter mutation, realized garment measurement extraction, a VLM/MLLM baseline, model training, or a correction outcome extractor. Existing references to these are contracts or reports, not executable implementations.

No `.git` directory exists at this checkout. The local branch, commit SHA, clean/dirty status, and original `gpu-e0-ready-v0.2.1` ref cannot be established from this filesystem. Frozen file hashes are used instead for this migration's preservation proof.
