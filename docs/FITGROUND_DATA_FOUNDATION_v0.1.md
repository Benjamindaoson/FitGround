# FitGround Data Foundation v0.1

## Decision

FitGround v0.1 is an AI fit-correction copilot, not an image-only virtual try-on benchmark.  Its source foundation is therefore organized around a future **before → garment modification → after** verifier, while preserving observational real-image assets as supplementary evidence.

This document records what is suitable to acquire before the GPU phase.  It does not claim that any acquired source already implements the V0.1 action contract or contains verified correction outcomes.

## P0 source roles

| Source | P0 role | What it supplies | Ceiling that must remain explicit |
| --- | --- | --- | --- |
| [GarmentCode](https://github.com/maria-korosteleva/GarmentCode) | Parametric garment and calibration substrate | Garment programs, design parameters, bodies, measurements, and the upstream route to GarmentCodeData v2 | No V0.1 action-to-pattern mapping or realized measurement is verified until calibration on the target backend. |
| [FitVTON](https://github.com/ZenoNing/FitVTON) | Candidate GarmentCodeV2/Warp pipeline bootstrap | Upstream setup, regeneration, inference, training, and evaluation implementation to inspect and adapt | The upstream control varies body fitting conditions; it is not, by itself, a garment modification or a centimeter-calibrated correction label. |
| [GarmentCodeVTONDataset](https://huggingface.co/datasets/ZenoNing/GarmentCodeVTONDataset) | Synthetic visual and pipeline-bootstrap asset | Public simulated GarmentCodeV2 try-on renders, represented as female, male, and reference folders | It does not establish `intended_delta_cm`, `realized_delta_cm`, a correction outcome, or an oracle action. |
| [FittingEffectDataset](https://huggingface.co/datasets/ZenoNing/FittingEffectDataset) | Small real-visual evaluation/probe asset | Public images plus a locally verified `tryon_triples_all.csv` containing 3,350 data rows | The triplets are try-on evaluation data, not `intended_delta_cm` / `realized_delta_cm` correction labels. |
| FIT-Clean v0.1 | Auxiliary real-visual/provenance asset | Existing source identities, canonical measurements, quality checks, fingerprints, and historical evidence | It is observational and must not be relabelled as a simulated correction lattice. |

## P0 acquisition set

The following four public sources are the entire acquisition set for this change:

| Asset | Immutable source reference | Local destination | Public expected content | Status after acquisition |
| --- | --- | --- | --- | --- |
| FitVTON source | GitHub source archive at commit `17078c64cc6f6984466bc31916e40421d97f3280` | `external/FitVTON-source-tree/ZenoNing-FitVTON-17078c6` | Candidate code path only | Needs source inspection and adapter design |
| GarmentCode source | GitHub source archive at commit `d449629979028123a5c4dc9e732a2ec19b7fce31` | `external/GarmentCode-source-tree/` | Parametric code path only | Needs action calibration |
| GarmentCodeVTONDataset | `f51b54db869fc4b1a7f32b017cdbfa80cb22956a` | `data/external/GarmentCodeVTONDataset` | 51,880 repository files; 5,337,085,718 bytes reported by the public Hub API | Synthetic bootstrap, not a correction lattice |
| FittingEffectDataset | `a1de636764dd7ce848737752e918ab3eec02ff03` | `data/external/FittingEffectDataset` | 703 repository files; 111,269,810 bytes reported by the public Hub API; local `tryon_triples_all.csv` has 3,350 data rows | Real-visual try-on probe; correction-label gap remains |

Source code is acquired as fixed-commit GitHub archives after shallow Git transport proved unsuitable on this host; neither archive initializes recursive submodules.  All dataset downloads are anonymous public downloads using the existing client, pinned by immutable revision, and retain its local metadata so an interrupted transfer can resume.

## Resuming the P0 dataset snapshots

Run the following from the FitGround repository root on this or a GPU machine after its project environment is ready.  It is deliberately anonymous (`token=False`); it neither reads nor needs a Hugging Face credential.  Re-running an incomplete command resumes the local snapshot rather than creating a new revision.

```powershell
$env:HF_HOME = "$PWD\.cache\huggingface"
$env:HF_XET_CACHE = "$PWD\.cache\huggingface\xet"
$env:HF_HUB_DISABLE_IMPLICIT_TOKEN = "1"
.\.venv\Scripts\python.exe -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='ZenoNing/GarmentCodeVTONDataset', repo_type='dataset', revision='f51b54db869fc4b1a7f32b017cdbfa80cb22956a', local_dir=r'D:\FitGround\data\external\GarmentCodeVTONDataset', token=False, max_workers=32)"
```

For the small real-visual probe, substitute `ZenoNing/FittingEffectDataset`, revision `a1de636764dd7ce848737752e918ab3eec02ff03`, and local directory `D:\FitGround\data\external\FittingEffectDataset`.  On a different drive, change only `local_dir` to that machine's absolute FitGround path.

## Deliberately excluded from this change

- Full GarmentCodeData v2 / 115K release: primary future generation substrate, but not required to inspect and adapt the FitVTON route.  It is not downloaded here.
- FIT-100K: a 196.98 GiB raw repository at inspected revision `5563646729edf148ed2b32c4b9c794d51a1bc828`; it does not fit safely on the available D: drive and is not a direct correction lattice.
- Dress-ED, CLOTH3D, TailorNet, DressCode/VITON-HD, and ChatGarment: not part of the minimally necessary P0 path.

The exclusion is an immediate data-role and capacity decision, not a conclusion that public research terms prohibit personal research.  Each source's upstream terms remain attached to the source and must be reviewed again before redistribution, publication, or using any derivative beyond the relevant terms.

## GPU admission gates

Before any GPU simulation produces a `SIMULATED` correction outcome, the implementation must prove all of the following:

1. A single V0.1 `CandidateCorrection` maps to an auditable GarmentCode/FitVTON parameter edit.
2. The simulator extracts a **measured** `realized_delta_cm`; it must not copy the intended delta.
3. The result records before/after visual evidence, material, simulator version/configuration, hashes, affected regions, and failure artifacts.
4. A correction lattice contains competing actions and controls, so diagnosis is evaluated by intervention predictive validity.
5. The existing `run_fit_correction_smoke.py` backend seam is replaced or adapted with those verified operations; no generic virtual-try-on result is treated as correction verification.

Until those gates pass, the sources above are input material only and FitGround remains `READY_FOR_GPU = NO`.
