# Phase 2.5 Context Pack — GPU E0 Handoff

Read this first. Do not re-read the whole repository.

Evidence priority: frozen machine-readable artifact > frozen contract > final report > run report > README > comments.

---

## FROZEN FACTS

FIT-Clean v0.1: Train=100000, Eval=5000, Total=105000  
SHA256=`6b998bc4c62b53fe6a4d119cb351a49f140fa1733b432a5d8dd4f1b6a401d177`  
Do not modify. Source `Yuanhao-Harry-Wang/fitvto-100k` @ `5563646729edf148ed2b32c4b9c794d51a1bc828`.

Phase 2 (do not re-guess): TIER A=0; TIER B=1 exact+1 near; TIER C=1689 groups / 1729 pairs; 1574/1731 bust+length+sleeve all change; same-cloth measurements consistent; body measurements constant in person groups; appearance co-varies with measurements; pixel fit NOT VERIFIED; semantic identity NOT VERIFIED; near-dup DEFERRED; COUNTERFACTUAL_FEASIBILITY=PARTIAL.

Experimental Contract v0.1: PARTIAL / FROZEN — diagnosis only, no training. Do not overwrite.

Experimental Contract v0.2: FROZEN 2026-09-11.

GarmentCode pin: `maria-korosteleva/GarmentCode` @ `d449629979028123a5c4dc9e732a2ec19b7fce31`.

---

## WHAT FAILED

Released FIT-100K cannot identify `P(Y | do(measurement), controlled context)`. Native same-cloth multi-measurement pairs do not exist. TIER C is a garment swap. Official FIT generation **code is not public**. Official cloth `I_g` is VLM try-off from a sized try-on, so it leaks size. Univariate bust isolation is not the FIT resizing process.

---

## WHAT CHANGED

The object of work is no longer “find more released pairs.”

It is: construct Controlled Fit Ladders via documented GarmentCode **cross-drape** (pattern from source body A, drape on target body B), with explicit controls.

v0.2 adds PRIMARY Track A (measurement-isolated canonical/normalized cloth — FitGround overlay) and SECONDARY Track B (naturalistic size-specific cloth).

---

## CURRENT HYPOTHESIS

Holding body, design, pose, fabric, camera, and seed fixed, an ordered measurement-vector intervention TIGHT → REGULAR → LOOSE changes target geometry and human-visible fit. Later models (not authorized) must track measurements, not appearance alone.

Null: leftover appearance explains everything, or the ladder is not a real intervention.

---

## GPU E0 CONTRACT

Stage 1 only: **3 bodies × 5 designs × 3 levels = 45 conditions** (15 ladders).

Backend: public GarmentCode + FIT-documented cross-drape. Pin pose (A-pose if reposing missing) and one physics fabric.

Produce: patterns, draped meshes, synthetic renders, Track A canonical cloth, Track B size-specific cloth, metadata, human contact sheets.

Stage 2 Sim2Real: **blocked**.

GO/PARTIAL/NO-GO: `artifacts/gpu_e0_pilot_v0.2.yaml` (frozen before seeing results). Humans judge fit. No VLM self-label.

---

## DO NOT DO

- VLM training, LoRA, RM, DPO, GRPO, full benchmark training
- Large FIT-100K image download
- Modify FIT-Clean v0.1 or overwrite Experimental Contract v0.1
- Treat S/M/L as the intervention
- Claim “same design ⇒ appearance fixed”
- Promote INFERRED FIT capabilities to VERIFIED
- Start Stage 2 Sim2Real
- Change E0 success cutoffs after seeing renders

---

## SUCCESS GATE

CONTROLLED_COUNTERFACTUAL_GENERATION (this phase): **PARTIAL**  
READY_FOR_GPU_E0: **YES** = permission to run **Stage 1 generation pilot only**.

E0 overall GO (later): generation ≥90%, controls hold, bust/ease monotonic, distinct targets, humans see LOOSE>REGULAR, Track A not a size oracle, 3D hashes reproducible, metadata complete.

Training remains **DENIED** until E0 GO **and** a later contract.

---

## FILES TO READ NEXT

1. `docs/EXPERIMENTAL_CONTRACT_v0.2.md`
2. `artifacts/experimental_contract_v0.2.yaml`
3. `artifacts/gpu_e0_pilot_v0.2.yaml`
4. `artifacts/controlled_fit_ladder_schema_v0.2.yaml`
5. `artifacts/control_variable_matrix_v0.2.yaml`
6. `reports/FIT_GENERATION_MECHANISM_AUDIT.md`
7. `reports/decision_log_phase_2_5.md`

---

## A–G (compact)

**A Frozen:** FIT-Clean v0.1 + Phase 2 counts + v0.1 PARTIAL + v0.2 FROZEN.  
**B Verified:** observational identification fails; paper documents cross-drape; GarmentCode can freeze design.  
**C Rejected:** more released pairs; appearance-fixed-by-design; univariate bust; unpublished Sim2Real as official.  
**D Open:** realignment re-implementation; Track A proportion leak; tightness visibility; Sim2Real seeds.  
**E Goal:** controlled `do(measurement)` ladders.  
**F Prohibited:** training, big download, GPU beyond E0 Stage 1.  
**G Next:** GPU E0 Stage 1 only.
