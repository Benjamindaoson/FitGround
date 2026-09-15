# FitGround V0.1 Matching Dataset Scout

**Checked:** 2026-09-15
**Question:** Which public dataset best matches FitGround's correction problem: diagnose a current fit problem, apply a precise garment correction, predict the simulated next fit state, and select the lowest-side-effect intervention?

## Decision

No public dataset found in this scan is a ready-made `Counterfactual Fit Correction Lattice` with all of:

```text
current visual/body/garment/material state
+ named centimetre correction action
+ realized garment delta
+ simulated after-state
+ region side effects
+ utility / oracle correction
```

The closest *generation substrate* is **GarmentCodeData v2**, not FIT-100K. It supplies made-to-measure bodies, sewing patterns, material variation, 3D garments, and the GarmentCode/Warp family of generation tools. FitGround must still generate its own controlled before/action/after lattice from that substrate.

## Candidate comparison

| Candidate | Verified public facts | FitGround field coverage | What it can be used for | Critical gap | Download decision |
|---|---|---|---|---|---|
| **GarmentCodeData v2** | 115,000 3D made-to-measure garments; corresponding sewing patterns; diverse body shapes; 3 materials; open-source XPBD draping pipeline | Body: YES; garment/pattern: YES; material: YES; visual/3D: YES; V0.1 action/result: NO | **Primary simulator substrate.** Select a supported top/shirt program, apply an explicit pattern-parameter mutation, measure realized bust/shoulder/sleeve change, then render the resulting lattice. | Does not publish FitGround's V0.1 action family, realized delta, side-effect labels, or oracle ranking. | **Highest-priority candidate; do not download until its v2 license, exact archive size, and top-garment action mapping are verified on the GPU execution machine.** |
| **GarmentCodeVTONDataset** | 51,878 viewer rows / 5.34 GB; simulated GarmentCodeV2 renders; 19 garment units; female/male body folders and reference renders | Visual: YES; fit variation: PARTIAL; body/garment continuous cm values: NOT_VERIFIED; action/result: NO | Secondary visual representation baseline or qualitative sanity subset. | Its public card calls the license `other`; no V0.1 pattern mutation, realized centimetre delta, or intervention outcome field is documented. | **Optional; defer.** It is small enough for a later bounded download but is not the correction-training dataset. |
| **CLOTH3D / ChaLearn 3D+Texture extension** | Simulated garments across body shapes, poses, garment sizes/tightness, topology, and fabrics; extension has 2M+ rendered frames and SMPL parameters; registration required | 3D/body/material: YES; sewing pattern: NO/NOT DOCUMENTED; action/result: NO | Geometry, material, and visual robustness research. | Does not provide the named correction action and realized-after measurement required by FitGround. | **Do not download for P0.** Registration and large scale are not justified before atomic-action calibration. |
| **FIT / fitvto-100k** | 105,000 image triplets plus body/garment measurements; 196.98 GiB public preview | Visual/body/garment measurement: YES; material/pattern/action/result: NO | Legacy multimodal or measurement baseline after a correction dataset exists. | Observational VTO data: no intervention, no after-state for a known correction, no side-effect/oracle label. | **Do not download.** Too large for the current disk and structurally insufficient for correction supervision. |
| **Dress-ED** | 146,460 garment/person edited-image quadruplets with language instructions; 56.33 GiB; manual-gated access | Before/after visual and text edit: YES; body measurements/physical action/realized delta: NO | Later image-editing auxiliary experiment only. | Edits are image-generation/instruction labels, not calibrated pattern changes or simulated physical outcomes. | **Do not download for FitGround V0.1.** |
| **FittingEffectDataset** | 111 MB / 699 imagefolder rows on its current public card; MIT label | Real try-on visual evidence: YES; correction action/result labels: NO | Lightweight real-visual evaluation/probe set. | Local inspection at the pinned revision confirms `tryon_triples_all.csv` has 3,350 data rows, but does not supply V0.1 intended/realized correction deltas or side-effect labels. | **Acquire as P0 auxiliary evaluation data; do not use as a correction lattice.** |

## Evidence sources

- [GarmentCodeData project page](https://igl.ethz.ch/projects/GarmentCodeData/) documents 115,000 made-to-measure garments, sewing patterns, body variation, three materials, and its XPBD pipeline.
- [GarmentCode official repository](https://github.com/maria-korosteleva/GarmentCode) documents the public code, body-measurement support, dataset v2, and parameter/body presets.
- [GarmentCodeVTONDataset card](https://huggingface.co/datasets/ZenoNing/GarmentCodeVTONDataset) documents 51,878 rows, 5.34 GB, simulated renders, 19 reference garment units, and `other` license metadata.
- [FitVTON project page](https://zenoning.github.io/FitVTON/) documents its 78K simulated triplets, but also states that its body-size control is based on 16 prototypes and is not centimetre-level continuous control.
- [CLOTH3D project repository](https://github.com/hbertiche/CLOTH3D) and the [ChaLearn extension description](https://chalearnlap.cvc.uab.cat/dataset/38/description/) document simulated body/pose/size/tightness/fabric variation and 3D metadata.
- [FIT-100K dataset card](https://huggingface.co/datasets/Yuanhao-Harry-Wang/fitvto-100k) documents the 105K image/measurement preview.
- [Dress-ED official repository](https://github.com/aimagelab/Dress-ED) documents its before/after visual instructions and structural/appearance editing categories.

## ModelScope availability

On 2026-09-15, the official ModelScope dataset OpenAPI returned zero exact matches for `fitvto`, `FIT-VTO`, `fit-aware`, `GarmentCodeVTONDataset`, `GarmentCodeData`, `FittingEffectDataset`, `CLOTH3D`, and `Dress-ED`. No ModelScope mirror is therefore treated as available or equivalent.

## Recommended data path

1. **P0 / GPU atomic-action gate:** use GarmentCode code and a deliberately selected GarmentCodeData-compatible top/shirt program to calibrate one action family, starting with `bust_circumference_delta_cm`. Generate only the 3 base states and 13 smoke candidates in the frozen smoke plan.
2. **P1 / pilot lattice:** after the action passes executability, measurement, monotonicity, locality, outcome-sensitivity, and reproducibility gates, generate 10--50 base states from the same program/material/body controls. This is the first FitGround training asset.
3. **Later auxiliary use:** evaluate whether GarmentCodeVTON's small visual corpus improves a visual encoder baseline. Keep it separate from physics-verified correction labels.
4. **Do not substitute:** FIT, CLOTH3D, Dress-ED, and generic VTO datasets may be valuable auxiliary data, but none should be relabeled as `CorrectionLattice` evidence.

## License and research boundary

The current use is personal, non-commercial research. This report does not treat a non-commercial license as a reason to reject a dataset for local research. For every candidate, retain its exact license and source revision before downloading; where a public card shows `other` or no explicit license, obtain the upstream terms before use. Do not redistribute raw source data through this repository.
