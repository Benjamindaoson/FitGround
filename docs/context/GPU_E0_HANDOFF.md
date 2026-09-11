# GPU E0 Handoff

Do not run from latest `main` by accident. Checkout the freeze tag.

```bash
git clone https://github.com/Benjamindaoson/FitGround.git
cd FitGround
git checkout gpu-e0-ready-v0.2.1
```

Then read only:

1. `docs/context/PHASE_2_5_CONTEXT.md`
2. `docs/EXPERIMENTAL_CONTRACT_v0.2.md`
3. `docs/GPU_E0_EXECUTION_ADDENDUM_v0.2.1.md`
4. `artifacts/gpu_e0_execution_v0.2.1.yaml`
5. `artifacts/gpu_e0_pilot_v0.2.yaml`

**Only allowed task:** GPU E0 Stage 1 — Controlled Counterfactual Generation Pilot  
3 bodies × 5 designs × 3 levels ≈ 45 conditions / 15 ladders

Do not train a VLM. Do not run LoRA / RM / DPO / GRPO. Do not start Sim2Real Stage 2.
