## Source roles

| Source | Role | Explicit ceiling |
| --- | --- | --- |
| GarmentCode | Parametric garment and measurement/calibration substrate | No verified mapping from V0.1 action to pattern parameters yet |
| FitVTON | Candidate Warp/GarmentCodeV2 pipeline bootstrap | Its existing body-variation controls are not direct garment-correction labels |
| GarmentCodeVTONDataset | Synthetic visual/pipeline bootstrap | Does not establish intended-to-realized centimeter actions |
| FittingEffectDataset | Small real visual evaluation/probe asset | Public card does not itself prove the paper-level triplet mapping |
| FIT-Clean | Auxiliary real visual/provenance asset | Not the primary intervention source |

## Reproducibility and integrity

Each remote asset is pinned by revision or source-archive commit.  The receipt records the official URI, expected bytes from the public API where available, local byte count, and verification status.  A successful download proves only byte acquisition; its semantic fields are inspected before any training or lattice construction.

## Storage boundary

Downloaded bytes are placed under `external/` and `data/external/`.  They are source material, not generated FitGround evidence.  No full GarmentCodeData or FIT-100K download is allowed in this change because neither fits the immediate correction-validation role or available storage budget.
