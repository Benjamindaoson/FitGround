# FitGround one-pager

**One sentence.** FitGround predicts how a garment modification changes fit and recommends the smallest effective correction for the next sample.

**Who.** Technical designers / 3D pattern engineers, not shoppers.

**Loop.** Evidence → cause hypothesis → candidate correction → counterfactual outcome → selection.

**What is real today.**

- Controllable bust intervention with measured realized Δcm
- Warp XPBD drape on static OBJ mannequins (`SYNTHETIC_BODY_PHYSICS`)
- Regional clearance / contact after unit alignment (body metres → cm)
- Observational and generated-pattern baselines, with negative results
- Next.js technical-designer workspace driven by artifacts, not mock chat

**What is explicitly not real.** SMPL-X parametric bodies, FIT-100K pixels, production deployment, proven vision necessity, MLLM LoRA until the download artifact says otherwise.

**How to run.** `make smoke` · `cd studio && npm run dev` · GPU: `python scripts/gpu/hero_pipeline.py`
