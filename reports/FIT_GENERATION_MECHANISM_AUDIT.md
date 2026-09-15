# FIT Generation Mechanism Audit

**Date:** 2026-09-11  
**Purpose:** Verify what the official FIT / FIT-VTO generation pipeline can and cannot hold fixed, before freezing Experimental Contract v0.2.  
**This phase did not run generation.**

Evidence tags used below:

- `VERIFIED_FROM_CODE` — inspected public source at a pinned revision
- `VERIFIED_FROM_DOCS` — paper, project page, or Hugging Face dataset card
- `INFERRED` — reasonable reading, not directly stated
- `UNKNOWN` — not established from public materials

**Rule:** inferred capability is not treated as verified capability.

---

## 1. Sources

### 1.1 Official FIT dataset (released preview)

| Field | Value | Tag |
|-------|-------|-----|
| Hugging Face | `Yuanhao-Harry-Wang/fitvto-100k` | VERIFIED_FROM_DOCS |
| Pinned revision (FitGround freeze) | `5563646729edf148ed2b32c4b9c794d51a1bc828` | VERIFIED_FROM_CODE (FitGround `artifacts/source_manifest.json`) |
| Released size | Train 100,000 / Eval 5,000 | VERIFIED_FROM_DOCS + FitGround fingerprint |
| License | CC BY-NC-ND 4.0 | VERIFIED_FROM_DOCS |
| Project page | https://johannakarras.github.io/FIT/ | VERIFIED_FROM_DOCS |
| Paper | Karras, Wang, Li, Kemelmacher-Shlizerman, “FIT: A Large-Scale Dataset for Fit-Aware Virtual Try-On”, SIGGRAPH 2026; arXiv:2604.08526 | VERIFIED_FROM_DOCS |

Full paper dataset counts (1.13M / project-page 1,064,824 train + 5,000 test) are **not** the released FIT-100K preview. Do not mix them with FIT-Clean v0.1.

### 1.2 Official FIT generation code

| Question | Finding | Tag |
|----------|---------|-----|
| Is FIT dataset-generation code public? | **No public FIT generation repository found** (2026-09-11). Project page: “We will make all data and code publicly available.” | VERIFIED_FROM_DOCS (intent) + UNKNOWN (actual release) |
| Johanna Karras GitHub | DreamPose, Fashion-VDM, HoloGarment — **no FIT generator repo** | VERIFIED_FROM_DOCS |
| Fit-VTO training/inference code | Not found as a public repo | UNKNOWN / not released |

**Implication:** GPU E0 cannot “run official FIT scripts.” It can follow the **documented** procedure using **public GarmentCode**, plus FitGround-controlled metadata. Photoreal Sim2Real (`f_texture`, `f_paired`, Nano Banana Pro try-off) is **not** a verified runnable artifact.

### 1.3 Upstream public code that FIT cites

| Repository | Revision audited | Tag |
|------------|------------------|-----|
| https://github.com/maria-korosteleva/GarmentCode | `d449629979028123a5c4dc9e732a2ec19b7fce31` (main, 2025-06-29) | VERIFIED_FROM_CODE |
| Warp fork cited by GarmentCode docs | https://github.com/maria-korosteleva/NvidiaWarp-GarmentCode | VERIFIED_FROM_DOCS (link only; not line-audited here) |
| Flux.1-dev | Black Forest Labs HF model | VERIFIED_FROM_DOCS (FIT paper cites it; weights are not FIT code) |

Relevant GarmentCode files (VERIFIED_FROM_CODE via docs + repo layout):

- `pattern_sampler.py` — sample designs × bodies
- `pattern_fitter.py` — **fix design parameters**, vary bodies
- `pattern_data_sim.py` — Warp drape + render
- `docs/Running_data_generation.md` — pipeline contract
- `assets/design_params/*.yaml` — design programs
- `data_generation/Sim_props/` — material, camera, quality thresholds
- `dataset_properties_<tag>.yaml` — stores **random seed** for sampler replication

FIT-specific modifications (box-mesh realignment, two-step top/bottom drape, reposing, Flux retexturing, VLM try-off) are **not in public GarmentCode**. Those are VERIFIED_FROM_DOCS (paper) only.

---

## 2. End-to-end mechanism (as documented)

Paper Figure 2 / §3 (VERIFIED_FROM_DOCS):

1. **GarmentCode simulation** → synthetic try-on render `I_s`
2. **Composite normal map** `I_n` (Sapiens normals + Nano Banana Pro head/feet inpaint, then stitch)
3. **Text prompt** `p` from VLM (Gemini), including sampled fabric type
4. **Retexturing** `I_try-on = f_texture(I_n, p)` — Flux.1-dev LoRA
5. **Paired person** `I_p = f_paired(I_id, I_n', p')` — same body/pose, different garment
6. **Layflat** `I_g` from off-the-shelf VLM try-off of `I_try-on` (Nano Banana Pro)

Released HF triplets are `(cloth, person, target)` plus 7 cm measurements. That is the **output** of this pipeline, not a 3D experimental log.

---

## 3. Mechanism-by-mechanism

### 3.1 Garment generation

| Topic | Finding | Tag |
|-------|---------|-----|
| Engine | GarmentCode parametric sewing programs | VERIFIED_FROM_DOCS + VERIFIED_FROM_CODE |
| Design identity | Design parameter YAML can be held fixed (`pattern_fitter.py`) | VERIFIED_FROM_CODE |
| Pattern for a size | Pattern is generated **fitted to a chosen body** | VERIFIED_FROM_CODE + VERIFIED_FROM_DOCS |
| Unique designs (full FIT) | 158,483 unique top/garment designs | VERIFIED_FROM_DOCS |
| Linear mesh scaling as ill-fit method | Authors **reject** it; grading is nonlinear | VERIFIED_FROM_DOCS (§B.1) |

**Cannot claim from public FIT code:** exact template list used for FIT-100K. UNKNOWN.

### 3.2 Body generation

| Topic | Finding | Tag |
|-------|---------|-----|
| Parametric bodies | GarmentCode / CAESAR-based body samples | VERIFIED_FROM_DOCS |
| Full FIT body count | 168 shapes (82 men, 86 women), sizes XS–3XL | VERIFIED_FROM_DOCS |
| Measurements from body model | height, bust, waist, hips (cm) | VERIFIED_FROM_DOCS |
| Released FIT-100K unique body vectors | 105 (Phase 2 freeze) | inherited VERIFIED finding on FIT-Clean; not re-computed here |

Holding **one body_id** fixed across a ladder is supported by the documented parametric model. VERIFIED_FROM_DOCS.

### 3.3 Cross-draping (size intervention)

| Topic | Finding | Tag |
|-------|---------|-----|
| Procedure | Generate pattern on **source body A**; drape on **target body B** | VERIFIED_FROM_DOCS |
| Why | Simulates wearing a garment made for someone else | VERIFIED_FROM_DOCS |
| Box-mesh realignment | Required; FIT-specific vs default GarmentCode | VERIFIED_FROM_DOCS |
| Public GarmentCode implements FIT realignment? | **Not verified.** Default pipeline drapes a pattern on the body it was fitted to, or on default body (`--default_body`) | VERIFIED_FROM_CODE (docs describe fit-then-sim, not FIT cross-drape) |
| Two-step top/bottom drape | FIT modification so shirts are not fused to bottoms | VERIFIED_FROM_DOCS |
| Default GarmentCode | Stitches top+bottom into one mesh | VERIFIED_FROM_DOCS |

**GPU implication:** Stage 1 must **re-implement or approximate** FIT box-mesh realignment. That is an engineering risk, not a verified drop-in flag. Residual: simulation failures / penetrations.

### 3.4 Size-conditioning / garment measurements

| Topic | Finding | Tag |
|-------|---------|-----|
| `m_g` source | Extracted from **2D sewing pattern**, not from pixels | VERIFIED_FROM_DOCS |
| Top metrics | length (HPS–hem), bust circumference (width), sleeve length | VERIFIED_FROM_DOCS |
| Bottom metrics | waist, outseam — generated but FitGround FIT-Clean v0.1 only has 7 upper-body fields | VERIFIED_FROM_DOCS |
| Coarse XS–3XL | Visualization/grouping only, **not** used for Fit-VTO train/eval | VERIFIED_FROM_DOCS (§A.1) |
| Measurement correlation | Width increases often come with length/sleeve increases; Fit-VTO struggles at independent single-measurement edits | VERIFIED_FROM_DOCS (§6, Fig. 11c) |

**Contract implication:** intervention is a **measurement vector**, not a univariate bust do-operator, unless GPU E0 later proves single-axis control.

HF card text “measurements were estimated programmatically” is weaker than the paper. Prefer paper for generation SoT. Tag for HF wording: VERIFIED_FROM_DOCS (card), possibly incomplete.

### 3.5 Pose controls

| Topic | Finding | Tag |
|-------|---------|-----|
| Simulation pose | GarmentCode drape is **A-pose only** | VERIFIED_FROM_DOCS |
| FIT reposing | Custom pipeline; 528 target poses; **random** pose per sample in the dataset | VERIFIED_FROM_DOCS (§B.4) |
| Public reposing code | Not released | UNKNOWN |
| Can pose be held fixed? | **Yes in principle** if we disable random pose sampling and pin `pose_id`. **Not** the default FIT dataset procedure. | INFERRED from docs (controllability claimed) |

E0 **must pin pose**. Leaving FIT’s random pose would destroy the ladder.

### 3.6 Material / fabric / texture

| Topic | Finding | Tag |
|-------|---------|-----|
| Physics materials in GarmentCodeData | Typically a small set (paper: three textile materials in GarmentCodeData) | VERIFIED_FROM_DOCS (GarmentCodeData) |
| FIT fabric diversity | 72 fabric types injected into the **text prompt** at retexturing, because GarmentCode material control is limited | VERIFIED_FROM_DOCS (§3.3) |
| Photoreal texture | Generated by Flux LoRA, not a locked UV map from 3D | VERIFIED_FROM_DOCS |
| Deterministic texture given seed | UNKNOWN (diffusion + VLM) | UNKNOWN |

**Cannot hold photoreal fabric/texture strictly fixed** with the official Sim2Real stack as documented. Can hold **physics material** and **prompt fabric token** if Sim2Real is run with fixed prompt + seed — seed behavior UNKNOWN.

### 3.7 Camera / lighting / rendering

| Topic | Finding | Tag |
|-------|---------|-----|
| FIT views | Standardized front-facing, full-body or cropped, casual poses | VERIFIED_FROM_DOCS (§6) |
| GarmentCode render config | Resolution, texturing, **front camera location** in sim config | VERIFIED_FROM_CODE (docs) |
| FIT 3D render camera/lights | Not specified beyond “rendered” | UNKNOWN |
| Sim2Real lighting | Absorbed into Flux generation; not an explicit HDRI control | INFERRED |

3D-stage camera: **YES** if we own the GarmentCode render config. Photoreal camera/lighting: **PARTIAL / UNKNOWN**.

### 3.8 Random seeds

| Topic | Finding | Tag |
|-------|---------|-----|
| GarmentCode sampler seed | Stored in `dataset_properties_<tag>.yaml`; `--replicate` supported | VERIFIED_FROM_CODE |
| Warp simulation seed | Config-driven; exact bit-stability across GPUs UNKNOWN | UNKNOWN |
| Flux / LoRA seed | Not documented in the paper | UNKNOWN |
| Nano Banana Pro / Gemini | Not documented as deterministic | UNKNOWN |

**Reproducibility GO for E0 is defined on 3D mesh / sewing-pattern artifacts, not on photoreal pixels**, unless FIT code later exposes seeds.

### 3.9 Sim2Real stage

| Topic | Finding | Tag |
|-------|---------|-----|
| Geometry bridge | Normal maps, intended to preserve garment/body geometry | VERIFIED_FROM_DOCS |
| Head/feet composite | VLM inpaint on `I_s`, then stitch normals; body/garment normals untouched (authors’ claim) | VERIFIED_FROM_DOCS |
| Residual | Diffusion can still add pockets/seams/logos from text; wrinkle-level fidelity not independently verified here | INFERRED |
| Public checkpoints | Not found | UNKNOWN |

Sim2Real is **geometry-preserving by design claim**, not a verified pixel-deterministic control.

### 3.10 Layflat / cloth input image

| Topic | Finding | Tag |
|-------|---------|-----|
| Official `I_g` | VLM try-off: “Create an in-shop product image of the top garment only against a plain white background.” | VERIFIED_FROM_DOCS (§3.5, §F.3) |
| Input to try-off | `I_try-on` (worn garment, size-specific) | VERIFIED_FROM_DOCS |
| QA | Gemini 2.5 Flash layflat QA; failures regenerated via try-off | VERIFIED_FROM_DOCS (HF card) |
| Canonical size-normalized cloth in official pipeline | **Not described** | VERIFIED_FROM_DOCS (absence) |

**This is the critical negative finding for Track A as an official FIT replay:**  
the released cloth image is downstream of the worn, sized try-on. Absolute size **can leak** into `I_g`.

---

## 4. What can / cannot be held fixed

### 4.1 Can be held fixed (with stated mechanism)

| Variable | Mechanism | Tag |
|----------|-----------|-----|
| Body identity + body measurements | Pin `body_id` / parametric body | VERIFIED_FROM_DOCS |
| Garment **design** parameters | `pattern_fitter.py` + frozen YAML | VERIFIED_FROM_CODE |
| Target body for drape | Cross-drape onto one body B | VERIFIED_FROM_DOCS |
| Physics material (3D) | Frozen sim config | VERIFIED_FROM_CODE |
| 3D camera (GarmentCode) | Frozen render block in sim config | VERIFIED_FROM_CODE |
| Bottom garment geometry | Authors freeze bottoms when pairing | VERIFIED_FROM_DOCS |
| Pose | Pin `pose_id` (overrides FIT’s random 528-pose sample) | INFERRED as controllable; default FIT does **not** pin |

### 4.2 Cannot be held fixed (or not by official pipeline)

| Variable | Why | Tag |
|----------|-----|-----|
| Official photoreal `I_g` independent of size | Try-off from sized `I_try-on` | VERIFIED_FROM_DOCS |
| Photoreal texture/color/lighting | Flux + VLM; no public seed contract | UNKNOWN / PARTIAL |
| Univariate garment bust | Authors: measurements correlated; resizing is vector-like | VERIFIED_FROM_DOCS |
| Tightness appearance | GarmentCode tightness poorly differentiated | VERIFIED_FROM_DOCS |
| FIT box-mesh realignment as drop-in | Not in public GarmentCode | VERIFIED_FROM_CODE (absence) |
| Identity-preserving Sim2Real pixels | Unpublished `f_paired` | UNKNOWN |

### 4.3 Partial

| Variable | Notes |
|----------|-------|
| Garment geometry | Design fixed, **size-specific pattern geometry changes** — that is the intervention |
| Garment appearance | 3D untextured silhouette changes with size; photoreal cloth even more so |
| Fabric | Physics vs prompt-fabric are different layers |
| Render seed | 3D config yes; Sim2Real unknown |

---

## 5. Track A vs official pipeline

Official FIT **does not** emit a canonical, scale-normalized garment image plus independent measurement vector.

Track A is therefore:

- **NOT** a verified official FIT output mode (`VERIFIED_FROM_DOCS`)
- **CONDITIONALLY FEASIBLE** as a **FitGround generation overlay** on GarmentCode:
  - freeze design YAML
  - produce size-specific patterns via different source bodies
  - render a **canonical** cloth (bbox-normalized pattern or rest-shape render) shared or scale-normalized across the ladder
  - keep true cm measurements in metadata
  - simulate size-specific **targets** on the fixed body

Physical consistency:

- Canonical cloth **is not** the physical 2D pattern at that size if we normalize scale. That is an explicit **image–measurement split**.
- It is valid as a **measurement-isolation probe**, not as a claim that shoppers see one cloth image for all sizes.
- Mismatch risk: a later VTO trained on FIT-style size-leaking `I_g` may behave differently from a model given Track A inputs.

If GPU E0 cannot produce a canonical cloth whose **absolute scale** is visually stable while **targets** still change, Track A is NO-GO and only Track B remains.

---

## 6. What GPU E0 is allowed to treat as “official”

Allowed to implement from documents + public code:

1. Frozen garment design YAML
2. Pattern generation for multiple source bodies
3. Drape onto one target body (FIT cross-drape **as specified in the paper**, including realignment if we re-implement it)
4. Extract `m_g` from sewing patterns
5. Extract `m_p` from the body model
6. Ordered TIGHT / REGULAR / LOOSE by ease, not by S/M/L labels

Not allowed to pretend we ran:

- Unpublished Flux LoRA `f_texture` / `f_paired`
- Nano Banana Pro as a bit-exact FIT replica
- Released FIT-100K as if it were already a controlled ladder

---

## 7. Audit verdict

| Item | Verdict |
|------|---------|
| Official FIT **procedure** documented? | YES — VERIFIED_FROM_DOCS |
| Official FIT **code** runnable? | NO — not released |
| Upstream GarmentCode usable for a controlled 3D ladder? | YES — VERIFIED_FROM_CODE, with FIT cross-drape as extra work |
| Official cloth image size-isolated? | NO |
| Univariate measurement do-operator? | NO, not in general |
| Enough to design GPU E0 Stage 1? | YES |
| Enough to claim photoreal FIT replica? | NO |

**GENERATION_MECHANISM_AUDIT = PARTIAL**
