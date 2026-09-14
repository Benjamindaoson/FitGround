# FitGround V0.1 Data Acquisition Decision

**Checked:** 2026-09-15
**Scope:** determine whether any source data should be downloaded before the V0.1 correction GPU gate. No secret was used, stored, or written to this repository.

## Decision

**Do not download the full FIT preview dataset.** It is not the data asset required to pass the next correction gate and it does not fit on the current drive. Licensing is recorded separately and is not the basis for this storage/phase decision.

**Do not download a ModelScope substitute.** The official ModelScope dataset OpenAPI returned no dataset for the exact identifiers or relevant aliases. The generic virtual-try-on results were different datasets, not validated mirrors and not substitutes for FIT.

## Source checks

| Source | Revision | Size | Relevance now | Decision |
|---|---:|---:|---|---|
| Hugging Face `Yuanhao-Harry-Wang/fitvto-100k` | `5563646729edf148ed2b32c4b9c794d51a1bc828` | 211,503,595,815 bytes / 196.98 GiB | Legacy FIT-Clean / VTO measurement source; has no V0.1 correction actions, simulated after-states, side effects, utilities, or oracle labels | **Do not download** |
| FIT train split | same | 187.61 GiB / 406 parquet shards | Not needed before correction-action calibration | **Do not download** |
| FIT eval split | same | 9.37 GiB / 20 parquet shards | Possible later legacy baseline/evaluation input, but not a correction lattice | **Defer** |
| Hugging Face `Yuanhao-Harry-Wang/FIT-assets` | `44f9ba27ea4f7992a57c68f95d82d90ab443a0f7` | 0.48 GiB / 10,337 files | Potential body/mesh assets, but no current runner dependency, no mapped V0.1 action backend, and no declared dataset-card license | **Defer until backend integration names the required files and license is confirmed** |
| ModelScope exact mirror | N/A | N/A | Official OpenAPI searches `fitvto`, `FIT-VTO`, and `fit-aware` each returned zero datasets | **No mirror found** |

The current `D:` volume has 207,483,760,640 bytes free (about 193.23 GiB). The FIT download is larger than the free space before cache, extraction, generated artifacts, or GPU environment overhead are considered.

## What the next GPU phase actually needs

The V0.1 correction Phase-1 smoke uses **three base states**, not 105,000 raw FIT samples:

| Base state | Candidate actions | Required evidence |
|---|---|---|
| CHEST | Bust +1/+2/+3; Shoulder +1 control; Sleeve -1 control | Before state, realized deltas, simulation/render outputs, regional outcomes, side effects, hashes |
| SHOULDER | Shoulder +1/+2; Bust +2 control; Sleeve -1 control | Same |
| SLEEVE | Sleeve -1/-2; Bust +2 control; Shoulder +1 control | Same |

The next dataset must be created by the calibrated correction backend:

```text
base state + candidate action
-> realized garment delta
-> simulated/rendered after-state
-> regional outcome + side effects
-> utility/ranking/oracle evidence
```

FIT-100K is useful only as a legacy multimodal/measurement asset for later baselines. It cannot replace this counterfactual lattice because it lacks a controlled action and its corresponding after-state.

## Training implication

No model training should begin after merely downloading FIT. The immediate GPU task is to calibrate a single precise action family, first demonstrating action executability, intended-versus-realized measurement accuracy, monotonicity, locality, treatment/control outcome sensitivity, and reproducibility. Only after that gate can the project generate the correction-lattice data required for SFT or any decision model.

## License boundary

The FIT-100K card declares `CC-BY-NC-ND-4.0`. The stated use here is personal, non-commercial research, so the `NC` term does not itself rule out local research use. Raw FIT data must not be redistributed or committed to this repository. The effect of the `ND` term on a planned trained model or released derived dataset is a separate question for the authors or legal review; this report makes no legal conclusion beyond the published label.
