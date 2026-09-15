# Technical architecture

```
Technical Designer Workspace (Next.js :43187)
        │  reads artifacts/demo/workspace.json
        ▼
Correction contracts (src/fitground/correction)
        │  intended_delta_cm ≠ realized_delta_cm
        ▼
GarmentCode worker (flux env)
        │  MetaGarment → specification JSON → panel measures
        ▼
SYNTHETIC_BODY_PHYSICS
        │  mean_all.obj / mean_female.obj / mean_male.obj / f_smpl_average_A40.obj
        │  smpl_body=False; body verts ×100 if metres
        ▼
Warp XPBD (FitVTON GarmentCodeV2 fork)
        │  sim OBJ + renders
        ▼
Fit outcomes (clearance, contact, wrinkle proxy, regional)
        ▼
Utility rank → recommendation / abstain
```

**Why not SMPL-X.** Licensed `.pkl`/`.npz` weights are not on disk. Repo-shipped average OBJs are used as collision mannequins and labeled. Physics does not stop.

**Why analytic inverse wins bust.** `shirt.width` is a multiplier of body bust, so intended centimetres are recoverable exactly from 2D panels. Learning is for regimes where material, pose, and body collision break that identity.
