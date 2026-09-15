# Run 010 — Experimental Contract Freeze

**Run ID:** `run_010`  
**Stage:** Phase 7–8  
**Recorded:** 2026-09-11

## Question

Given TIER A = 0 and TIER C = 1,689 groups, should we freeze a contract and what GPU work does that authorize?

## Input

- Run 007–009 results
- Shortcut audit verdict `PARTIAL_CONFOUND`
- Split policy v0.1

## Execution

Wrote `reports/COUNTERFACTUAL_FEASIBILITY.md` with a **PARTIAL** verdict and froze `docs/EXPERIMENTAL_CONTRACT_v0.1.md` plus `artifacts/experimental_contract_v0.1.yaml`.

FIT-Clean v0.1 was not modified. No model was trained.

## Results

| Gate | Decision |
|------|----------|
| Feasibility | **PARTIAL** |
| Contract frozen | **Yes, at PARTIAL** |
| TIER A isolation experiment | Not authorized (unit missing) |
| TIER C diagnostic | Authorized as the experimental unit |
| VLM / LoRA / RM / DPO / GRPO | **Not authorized** |
| First GPU experiment | Frozen-encoder pair ranking probe (DEFERRED_TO_GPU) |
| Ready for GPU training stage | **No** |

## Interpretation

Freezing a PARTIAL contract is stricter than skipping the contract. It records what *may not* be claimed. GPU training remains closed until (a) visual sanity supports target fit change and (b) a separate decision upgrades the programme — which this freeze does not do.

## Decision

Stop at contract freeze + tests + visual-pilot attempt. Do not train.

## Artifacts

- `reports/COUNTERFACTUAL_FEASIBILITY.md`
- `docs/EXPERIMENTAL_CONTRACT_v0.1.md`
- `artifacts/experimental_contract_v0.1.yaml`

## Verification

Contract SHA/text review: research question, unit, IV, confound, splits, primary endpoint, failure criteria, and GPU ban are present. Manifest hash still `6b998bc4…0177`.

## What We Learned

An empty TIER A is itself a paper-relevant negative result: FIT does not implement same-visual-pair measurement ladders.

## Next

Human contact-sheet review of the shard-packed pilot. GPU probe only after that review, still without training.
