## ADDED Requirements

### Requirement: P0 correction data sources are explicitly bounded

The repository SHALL document GarmentCode, FitVTON, GarmentCodeVTONDataset, and FittingEffectDataset as distinct source roles, including their limits for correction learning.

#### Scenario: Existing body variation data is considered for correction work

- **WHEN** an engineer prepares a training or lattice job using GarmentCodeVTONDataset
- **THEN** the job documentation SHALL state that its existing controls do not establish intended-to-realized V0.1 garment correction deltas

### Requirement: Acquired external sources are reproducible

The repository SHALL retain an acquisition receipt for every P0 external asset that specifies an official URI, immutable revision or commit, local destination, expected byte total where available, and observed local count/bytes.

#### Scenario: A GPU machine must recreate the P0 source set

- **WHEN** the receipt is read on another machine
- **THEN** it SHALL identify the exact source revision or commit and destination for every P0 source

### Requirement: Large non-P0 datasets remain excluded

This change SHALL NOT download full GarmentCodeData v2, FIT-100K, Dress-ED, CLOTH3D, TailorNet, or VITON-HD.

#### Scenario: Acquisition script or operator selects datasets

- **WHEN** P0 acquisition completes
- **THEN** the receipt SHALL list the excluded datasets and explain that they were not acquired by this change
