# Counterfactual Shortcut Audit

**Status:** PARTIAL_CONFOUND  
**Pairs:** 1,731 (TIER B=2, TIER C=1,729)  
**Date:** 2026-09-11

This document attacks the candidate design. Evidence tags: OBSERVED / DERIVED / INTERPRETED / HYPOTHESIZED / VERIFIED.

## What would make the design invalid

If a reviewer can ignore images and still “solve” the pair using (a) a handful of `bust_ease_ratio` presets, (b) person/cloth identity, (c) shard/split/filename, (d) quality flags, or (e) duplicate targets, the measurement-grounding experiment is not identified.

## Attacks

### 1. Person identity

Within-pair person SHA256 is constant (**OBSERVED**, frac=1.0). Between-pair person identity varies (1,689 unique persons). Holding person is the point of TIER C, not a cheat. **Pass.**

### 2. Cloth identity / garment appearance

Within-pair cloth SHA256 is **never** constant (**OBSERVED**, frac=0.0). TIER A is empty. TIER B (visual family) has n=2. **Fail as isolation; pass as person-held garment swap with a recorded confound.**

### 3. Garment category proxy

FIT-Clean has no category label. 1,574/1,731 pairs change bust, length, and sleeve together (**OBSERVED**). That is a silhouette change, not a single-knob ease edit. **Fail as single-IV; recorded as `multi_variable_garment_change`.**

### 4. Measurement quantization / preset ease

Full 105K `bust_ease_ratio` has 11 unique values at 1dp (**OBSERVED**, previously reported in DE). Pair Δease_ratio has 5 unique 1dp values and 40 unique 2dp values. Fraction of pair deltas on a 0.05 grid: **0.038** (**OBSERVED**).

You **cannot** generally guess pair membership or magnitude from two or three preset codes. Quantization is a reporting caveat, not a disqualifying shortcut. Official FIT docs still do not confirm garment scaling presets (**HYPOTHESIZED**).

### 5. Source shard / row ordering / filename

Shard purity from ease 1dp = 0.16 (**OBSERVED**). `sample_id` encodes split/shard/row; models must not receive it as a feature (**DERIVED**). **Pass if sample_id is withheld.**

### 6. Split

`pair_split` purity from ease 1dp = 0.91 (**OBSERVED**). Mild. Cross-split pairs (173) are flagged and excluded from official pair-eval. **Pass with policy.**

### 7. Duplicate image / quality / missingness

All TIER C members are `duplicate_person_sha256=True` and `quality_status=SUSPICIOUS` **by the DE rule** that flags reused person images (**OBSERVED**). That flag cannot separate pairs. Missingness is not a separator (measurements complete). Target-in-pair duplicates are rejected (**VERIFIED**).

### 8. Extreme-value threshold

Anchor ease bins are populated across negative / near-zero / moderate / large (**OBSERVED**). Not a single-threshold experiment.

## Required corrections already applied

1. Person-image reuse is **not** counted as `duplicate_contamination` on TIER B/C (it is the experimental unit).
2. Cross-split and exact-image leakage flags travel with the pair.
3. Split policy keeps official 5K intact and adds `leakage_controlled_eval` (4,684).

## Residual unfixable confound

**Cloth image always changes with the measurement vector in TIER C.** No metadata-only control removes it. Only TIER B (n=2) holds garment appearance approximately.

## Verdict

The pair table is valid as a **person-held, measurement-varying garment-alternative diagnostic** with an explicit appearance confound. It is **not** valid as a controlled measurement intervention on a fixed (person, cloth) visual pair.
