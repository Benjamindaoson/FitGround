# FitGround V0.1 Migration Matrix

| Legacy function / asset | Old position | Position in new correction product | Decision | Required modification / boundary |
|---|---|---|---|---|
| FIT-Clean v0.1 | Main benchmark source and measurement foundation | Observational source, provenance, visual/measurement baseline input | `KEEP` | Do not alter schema/data; future lattices cite source IDs/hashes |
| FIT-Clean measurement extraction | Canonical body/garment values | Current-state input and measurement-only baseline feature source | `KEEP` | Reuse units/normalization, never infer action calibration |
| FIT-Clean quality checks | Dataset validity/quality | Upstream trust gate for future input selection | `KEEP` | Keep separate from simulated verification |
| FIT-Clean fingerprinting/provenance | Reproducibility closure | Immutable evidence and lineage pattern | `KEEP` | Preserve historic fingerprint; lattice adds its own provenance |
| Old counterfactual pipeline | Person-held observed pair-direction diagnostic | Legacy observational analysis / negative causal evidence | `DEPRECATE` | Do not call a matched garment swap a correction intervention |
| Counterfactual structure discovery | Establish availability of same-person/same-cloth records | Evidence explaining why new simulated lattice is necessary | `KEEP` | Preserve findings and reports |
| Counterfactual candidate matching | Build Tier A/B/C pairs | Legacy diagnostic only | `DEPRECATE` | New `CorrectionLattice` replaces it for planned actions |
| Counterfactual controls/shortcut audit | Confound scoring | General evaluation hygiene | `ADAPT` | Apply control logic to state/action/outcome provenance later |
| Controlled Fit Ladder | Hero controlled research intervention | `LEGACY / SIMULATION SANITY / INTERVENTION FOUNDATION` | `ADAPT` | Keep TIGHT/REGULAR/LOOSE bytes; do not map levels to atomic deltas |
| Tight/Regular/Loose classifier/ranking framing | Primary outcome hypothesis | Not a core product task | `DEPRECATE` | Fit-state classification can be auxiliary only |
| GarmentCode integration | Planned only through documents | Future physics-based simulated verifier backend | `GPU_ONLY_VERIFY` | Calibrate each action; no local adapter is fabricated |
| Simulation pipeline | Frozen E0 plan but absent local code | Produces before/action/after outcomes and verifies recommendations | `NEW_REQUIRED` | Runner scaffold added; backend remains unavailable |
| Render pipeline | Planned E0 outputs only | Future visual evidence/output extraction | `GPU_ONLY_VERIFY` | No local renderer found or created |
| Pattern/action mapping | Source-body sizing vector in E0 design | Required exact atomic V0.1 correction mapping | `NEW_REQUIRED` | Calibration framework records intended/realized/error/cross-region effects |
| Measurement extraction after change | Not implemented | Required realized-delta measurement | `NEW_REQUIRED` | Must run after calibrated pattern operation; null until then |
| Provenance/hashes | FIT images/shards/artifacts | Required lattice input/backend/output evidence | `ADAPT` | Reuse deterministic/hashing discipline; add lattice lineage |
| GPU E0 scripts/contracts | Frozen Stage 1 3x5x3 plan | Historical simulation sanity artifact | `KEEP` | Preserve; not current correction smoke execution |
| New correction smoke plan | Missing | Chest/shoulder/sleeve action matrix | `NEW_REQUIRED` | Created as planning-only YAML |
| Analysis code | FIT distributions, audit, old pair shortcuts | Baseline/data understanding | `ADAPT` | Future analysis must report FPCR/regret/side effects, not only accuracy |
| Training code | Absent; training explicitly denied | Future only: rule, XGBoost/MLP, MLLM, Counterfactual SFT | `NEW_REQUIRED` | Do not implement until simulated lattices pass gates |
| Physics-Verified RLVR | Mentioned only as future research | Future optional optimization | `DEPRECATE` | Not authorized/implemented before effective SFT and a separate contract |
| Existing tests | FIT-Clean, legacy pairs, E0 YAML validation | Regression protection and frozen-evidence checks | `KEEP` | Run unchanged; add correction contract/dry-run/preservation coverage |
| Product/technical contracts | Missing | V0.1 scope and wire-contract authority | `NEW_REQUIRED` | Created under `docs/` |

## Migration decision

The migration is additive and preserves the historical data-engineering and experimental evidence. The primary product object changes from an observed **measurement-grounding pair** or a 3-level sizing ladder to a **Counterfactual Fit Correction Lattice**:

```text
CurrentFitState
  + CandidateCorrection(action, intended delta, realized delta)
  -> PredictedFitOutcome(simulated after-state, side effects)
  -> Utility
  -> oracle / selected correction
```

Until a calibrated GPU backend supplies an after-state, the lattice is structurally valid but incomplete evidence, and no oracle/recommendation is generated.
