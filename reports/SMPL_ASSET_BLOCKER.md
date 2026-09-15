# SMPL / SMPL-X asset audit

**Status: HARD_BLOCKER_LICENSED_ASSET for parametric SMPL-X VTON bodies**

Searched (targeted, not a blind full-disk walk of conda pkgs):

- `/root/workspace/projects`
- `/root/workspace/external/FitVTON-source-tree`
- `/root/workspace/external/GarmentCode-source-tree`
- `/root/workspace/GarmentCode-source-tree`
- `/root/workspace/datasets`
- `/root/workspace/outputs`
- `GarmentCodeV2/human_model_files/{smpl,smplx}`
- `GarmentCodeV2/smplx/*.npz` (pose vectors only, ~3KB each — **not** model weights)

**Not found:** `SMPL_FEMALE.pkl`, `SMPL_MALE.pkl`, `SMPLX_FEMALE.npz/.pkl`, `SMPLX_MALE.npz/.pkl`.

Present instead:

- Template OBJ bodies: `assets/bodies/mean_all.obj`, `mean_female.obj`, `f_smpl_average_A40.obj`, …
- Pose npz under `GarmentCodeV2/smplx/` (FitVTON poses, not SMPL-X shape models)
- Body-part JSON maps under `human_model_files/`

FitVTON `docs/garmentcodev2.md` requires licensed SMPL/SMPL-X files for **local GarmentCodeVTON regeneration on SMPL-X bodies**. Those files were not downloaded from untrusted sources.

**Work that does not need the licensed pkl/npz:**

- Pattern generation + bust measurement on YAML `BodyParameters` + `mean_all.obj`
- Warp XPBD drape on the static `mean_all.obj` collider (`smpl_body=False`)

See `artifacts/smpl_asset_status.json`.
