# GarmentCodeV2 physics smoke

**Status: PASS** (static `mean_all.obj` body; SMPL pkl not used)

Command path: FitVTON `GarmentCodeV2` + NvidiaWarp-GarmentCode on RTX 4090.

| Item | Result |
| --- | --- |
| Garment | t-shirt.yaml `Shirt` |
| Body | `assets/bodies/mean_all.obj` + `mean_all.yaml` |
| Pose / gender | default static collider (not SMPL-X sequence) |
| GPU | cuda:0 |
| Box mesh | `debug3_boxmesh.obj` (1.1 MB) |
| Sim mesh | `debug3_sim.obj` (1.2 MB) |
| Renders | front, back, garment mask, body mask PNGs |
| Body-cloth intersections | 0 |
| Self-intersections | 14 (quality check did not mark fail) |
| Smoke steps | 80 (first compile ~70s + sim) |
| Follow-up lattice | 300 steps, static with 0 non-static vertices, ~11s/case after compile |

Patches required (documented, third-party FitVTON tree only):

1. `libigl>=2.5` `facet_components` returns `(n, C)` not `C`.
2. `Cloth.body_sequence` was assumed always present; static OBJ path used `None.any()`.
3. Submesh extraction used `body_sequence[0]` even for static bodies.

Artifacts: `artifacts/garmentcodev2_physics_smoke.json`, `artifacts/gpu/garmentcodev2_physics_smoke/`.
