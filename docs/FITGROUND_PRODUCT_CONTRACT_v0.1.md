# FitGround Product Contract v0.1

**Status:** FROZEN FOR PRE-GPU CORRECTION FOUNDATION
**Product:** AI-Powered Multimodal Fit Correction for Technical Designers

## Business Problem

A technical designer has already identified a fit problem in a current sample. The decision that remains costly and uncertain is what small garment change to make in the next sample, how large it should be, and whether it will create a new problem elsewhere.

FitGround helps select the smallest correction most likely to make the next sample fit correctly. It is decision support for correction, not a detector that merely calls a sample tight or loose.

## User

The primary user is a **technical designer** reviewing a current physical or simulated sample with a known fit concern. Pattern makers and fit reviewers are downstream collaborators, not separate product personas in V0.1.

## Input

- Body measurements
- Garment measurements or geometry
- Current fit image or 3D visual evidence
- Material and garment metadata
- Garment type
- Fit intent
- A candidate garment correction

## Output

- Likely cause hypothesis with supporting evidence and verification status
- Ranked candidate corrections in the V0.1 action space
- Predicted next-fit regional state, side effects, confidence, and verification status
- The recommended correction only when an outcome/utility is available from a simulated verifier

An unexecuted local plan MUST be presented as `NOT_RUN` / `NOT_VERIFIED`; it is not a recommendation backed by simulation.

## Core Decision Loop

```text
Current sample fit problem
  -> Body + Garment + Visual + Material + Fit Intent
  -> Multimodal understanding
  -> Likely physical cause hypothesis
  -> Candidate correction
  -> Predict correction outcome
  -> Simulated verification
  -> Select lowest-regret correction
```

The core model target is `(s, a) -> s'`, where `s` is the current multimodal fit state, `a` is a garment correction, and `s'` is the predicted next fit state. Selecting `s -> a*` is downstream of outcome prediction.

## Non-goals

- Consumer sizing or fit recommendation
- Virtual try-on product
- Return prediction, merchandising, inventory allocation, PIM, agentic commerce, or global sizing
- A complete fashion platform or UI
- Claims that cause labels are absolute physical ground truth
- Treating the legacy TIGHT/REGULAR/LOOSE ladder as the product's final dataset
- MLLM training, SFT, DPO, GRPO, or RLVR in this phase

## Business KPI

**Simulation-Verified First-Pass Correction Rate** is the fraction of first-ranked corrections that, after simulation verification, reach target fit without unacceptable side effects.

Supporting metrics are Intervention Regret, Side-Effect Rate, and Correction Magnitude Error. Ordinary classification accuracy is not the North Star.
