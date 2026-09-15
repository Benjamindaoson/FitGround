# Phase 2.5 Decision Log

Each entry: Decision / Evidence / Alternatives / Why selected / What would invalidate it.

---

## D1. Released FIT-100K is not the sole counterfactual benchmark

**Decision.** Do not use released FIT-100K as the sole (or primary) counterfactual benchmark for measurement grounding.

**Evidence.** Phase 2 freeze: TIER A = 0; TIER C appearance and measurements co-vary; 1,574/1,731 pairs change bust+length+sleeve; same cloth SHA256 has consistent measurements (no “same image, new measurement” experiment). COUNTERFACTUAL_FEASIBILITY = PARTIAL.

**Alternatives considered.** Keep mining TIER C; construct TIER D nearest-neighbor garments; ignore appearance and treat measurements as if isolated.

**Why selected.** Additional observational pairs cannot convert `P(Y | different garment, different measurement)` into `P(Y | do(measurement), controlled context)`.

**Invalidated if.** A later audit of released data finds a large same-design, same-cloth, multi-measurement set (contradicts frozen TIER A = 0 and cloth-measurement consistency).

---

## D2. Official FIT generation code is unpublished; Stage 1 uses GarmentCode + paper procedure

**Decision.** GPU E0 Stage 1 implements documented cross-drape on public GarmentCode. Stage 2 Sim2Real is blocked.

**Evidence.** Project page promises code release; no public FIT generator repo on 2026-09-11. GarmentCode `d449629979028123a5c4dc9e732a2ec19b7fce31` is public. Paper §3.2 / Appendix B specifies cross-drape and box-mesh realignment.

**Alternatives.** Wait indefinitely for FIT code; pretend Flux LoRA is available; skip generation and keep observational pairs.

**Why selected.** Waiting forever leaves the scientific gap open. Claiming unofficial Sim2Real as “official FIT” would be a false verified capability.

**Invalidated if.** Authors release FIT generation code that cannot cross-drape a fixed design onto a fixed body at multiple sizes.

---

## D3. Primary track is Measurement-Isolated (Track A); Track B is secondary

**Decision.** PRIMARY = Track A (canonical/normalized cloth + measurement vector + size-specific target). SECONDARY = Track B (size-specific cloth). Track A is a FitGround overlay, not an official FIT output.

**Evidence.** Official `I_g` is VLM try-off from sized `I_try-on` (paper §3.5, prompt F.3). Phase 2: appearance co-varies with measurements. Track B alone cannot prove measurement grounding.

**Alternatives.** Only Track B (“more natural”); claim “same design ⇒ appearance fixed”; drop cloth images entirely (measurement-only).

**Why selected.** Isolation is the scientific need. Honesty requires saying official FIT does not already provide it. Measurement-only is a shortcut test, not the multimodal setting.

**Invalidated if.** GPU E0 Track A cloth remains a near-perfect size oracle (appearance-only solves the task), or canonical cloth is judged physically unusable. Then Track A is NO-GO.

---

## D4. Intervention is a measurement vector, ordered TIGHT → REGULAR → LOOSE

**Decision.** Do not label the intervention as univariate bust. Order conditions by `bust_ease_cm` / `garment_bust_cm`. Record length and sleeve deltas.

**Evidence.** Phase 2: 1,574/1,731 multivariable pairs. Paper §6 / Fig. 11c: width, length, sleeve correlated; Fit-VTO cannot independently edit single measurements well. Authors: S/M/L are visualization-only.

**Alternatives.** Force single-axis bust edits in the pattern DSL; use only S/M/L; random negatives first.

**Why selected.** Random negatives skip the ordered physical story. Fake univariate labeling would overclaim identification.

**Invalidated if.** E0 actually holds length and sleeve fixed while bust/ease still ladder — then a univariate bust sub-ladder can be added, not assumed now.

---

## D5. GPU E0 scale is 3 × 5 × 3 = 45, Stage 1 only

**Decision.** 3 bodies × 5 designs × 3 levels. Pin pose and fabric. Do not inflate. Do not run Sim2Real in E0.

**Evidence.** Minimum factorial for body, design, and ordered size. Photoreal stack unpublished. Author tightness limitation makes TIGHT vs REGULAR a known weak pair; 15 ladders are enough for a human contact-sheet audit.

**Alternatives.** 1×1×3 smoke test only; hundreds of conditions; photoreal-first.

**Why selected.** 45 is small enough to audit by hand and large enough to see if controls hold across designs/bodies. Photoreal-first would bake unpublished stochastic confounders into the first gate.

**Invalidated if.** Cross-drape is structurally impossible without a different factorial (e.g. must vary pose with size). Then revise the scale in v0.3, not by silent post-hoc change after seeing results.

---

## D6. Acceptance criteria frozen before GPU results

**Decision.** GO/PARTIAL/NO-GO cutoffs live in `artifacts/gpu_e0_pilot_v0.2.yaml` and this phase’s contract. Humans, not VLMs, judge visible fit.

**Evidence.** Phase 2 pixel-level fit is NOT VERIFIED. Changing criteria after seeing renders is a classic analysis crime.

**Alternatives.** Qualitative “looks good”; VLM-as-judge; criteria TBD after E0.

**Why selected.** Pre-registration is the point of a contract.

**Invalidated if.** A cutoff is physically impossible (e.g. 5% bbox rule unmeasurable). Then document a v0.3 amendment with the reason — do not silently edit v0.2.

---

## D7. CONTROLLED_COUNTERFACTUAL_GENERATION = PARTIAL; READY_FOR_GPU_E0 = YES

**Decision.** Design is sufficient to run Stage 1. It is not sufficient to claim an official photoreal FIT replica or to train.

**Evidence.** D2–D4 limitations plus frozen E0 spec.

**Alternatives.** NO-GO until FIT code drops; GO as if Sim2Real were solved.

**Why selected.** NO-GO would freeze work that public GarmentCode can already test. Full GO would overstate unverified photoreal control.

**Invalidated if.** Stage 1 is shown impossible on a GPU (cross-drape cannot hold design+body). Then READY_FOR_GPU_E0 should be revisited in a new contract, not by rewriting v0.2 after failure.

---

## D8. Do not overwrite v0.1 or FIT-Clean v0.1

**Decision.** New files only (`v0.2`). FIT-Clean SHA256 remains `6b998bc4…0177`.

**Evidence.** User freeze; fingerprint FROZEN.

**Alternatives.** Revise v0.1 in place to mention generation.

**Why selected.** v0.1 is an observational freeze. Mixing generations would erase the negative finding.

**Invalidated if.** FIT-Clean bytes change — that would be a data-engineering incident, not a v0.2 edit.
