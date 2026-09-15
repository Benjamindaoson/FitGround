## Why

FitGround's correction contracts are locally ready, but its previous data positioning overemphasizes FIT-Clean and the legacy ladder.  The next GPU phase needs a reproducible synthetic-physics foundation and a small real-image evaluation asset without claiming that either is a calibrated correction lattice.

## What Changes

- Record GarmentCode and FitVTON as the P0 source and pipeline foundation, pinned to their checked-out source revisions.
- Acquire only the public, non-gated FitVTON companion datasets: GarmentCodeVTONDataset (about 5.34 GB advertised; 5,337,085,718 bytes at the verified revision) and FittingEffectDataset (about 111 MB advertised; 111,269,810 bytes at the verified revision).
- Add an acquisition receipt with source revisions, expected byte totals, local destinations, and validation status.
- Reposition FIT-Clean as an auxiliary real-visual asset and retain all historical artifacts unchanged.

## Non-Goals

- Do not download full GarmentCodeData v2, FIT-100K, Dress-ED, CLOTH3D, TailorNet, or VITON-HD.
- Do not run GPU physics, train a model, manufacture simulated outcomes, or claim centimeter-calibrated correction actions.
- Do not change frozen legacy evidence or the completed correction-contract migration.

## Impact

The change creates documentation and a source-acquisition receipt only.  Downloaded source and dataset bytes live in documented external directories and are not incorporated into frozen artifacts.
