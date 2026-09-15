# FitGround one-pager

**One sentence.** FitGround predicts how a garment modification changes fit and recommends the smallest effective correction for the next sample.

**Who.** Technical designers / 3D pattern engineers, not shoppers.

**Loop.** Pattern parameter → measured geometry → Warp cloth/body physics → fit metrics → counterfactual correction → decision utility → designer workspace.

**Six claims that are allowed only with artifacts.**

1. ±3 cm Shirt bust edits are millimetre-class calibratable (MAE ~0, 3× repeats exact).
2. Those edits change measurable cloth-body clearance/contact on a static mannequin.
3. On the trivial geometry regime, analytic inverse beats Transition SFT (0.00 vs 0.47 cm).
4. Vision/MLLM gain is an experiment on matched measurements + different drape, not a slogan.
5. OOD support is explicit: unseen body/material/unstable sim → abstain, labelled `SYNTHETIC_BODY_OOD`.
6. The Next.js workspace turns those results into “what should change in the next sample?”

**Split, always.** Parametric geometry PASS · `SYNTHETIC_BODY_PHYSICS` PASS · SMPL-X HARD_BLOCKED_LICENSE · real-human HARD_BLOCKED_LICENSE.

**How to run.** `make smoke` · `make benchmark-fast` · `cd studio && npm run dev -- -p 43187` · GPU: `bash scripts/gpu/run_closure.sh`
