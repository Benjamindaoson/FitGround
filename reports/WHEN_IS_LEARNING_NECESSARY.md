# When is learning necessary for fit correction?

## Finding

On the Shirt **trivial geometry regime** (bust circumference via `shirt.width.v`), the analytic inverse is exact to numerical noise. A Transition SFT MLP on the earlier 88-row lattice had MAE **0.47 cm**. Identity/intended-copy is not a learned success; it is the physics of this map.

Learning is not justified as a replacement for that inverse.

## TRIVIAL_REGIME

- Definition: 2D panel geometry, deterministic parameter → centimetre map, no material/pose interaction required to hit the measurement target.
- Analytic inverse MAE: {"n": 88, "mean": 9.85070610940139e-15, "std": 1.0413410181229966e-14, "lo": 7.751375299201092e-15, "hi": 1.1954074094236682e-14, "mae": 9.85070610940139e-15, "model": "analytic_inverse"}
- OLS/MLP proxy MAE: {"n": 88, "mean": 9.874905915403876e-15, "std": 9.37429901027263e-15, "lo": 7.993204237563417e-15, "hi": 1.174746315383171e-14, "mae": 9.874905915403876e-15, "model": "OLS_mlp_proxy"}
- Winner: **analytic_inverse**

## COMPLEX_REGIME

- Definition: same (or nearly same) body and garment measurements, but cloth bending / body proxy / drape change the next-state utility and therefore the best correction.
- Visual-disambiguation verdict: **VISION_NECESSITY_NOT_ESTABLISHED**
- Reason: best correction flips on some matched-measurement material pairs (n_pairs=33, n_flips=7), but held-out accuracy CIs overlap so vision necessity is not statistically established
- n_cases=71 n_pairs=33 n_flips=7
- Baselines: {
  "measurement_only": {
    "model": "measurement_only",
    "n_train": 49,
    "n_test": 10,
    "accuracy": 0.9,
    "acc_ci": {
      "n": 10,
      "mean": 0.9,
      "std": 0.31622776601683794,
      "lo": 0.7,
      "hi": 1.0
    }
  },
  "geometry_only": {
    "model": "geometry_only",
    "n_train": 49,
    "n_test": 10,
    "accuracy": 0.9,
    "acc_ci": {
      "n": 10,
      "mean": 0.9,
      "std": 0.31622776601683794,
      "lo": 0.7,
      "hi": 1.0
    }
  },
  "vision_only": {
    "model": "vision_physical_evidence",
    "n_train": 49,
    "n_test": 10,
    "accuracy": 1.0,
    "acc_ci": {
      "n": 10,
      "mean": 1.0,
      "std": 0.0,
      "lo": 1.0,
      "hi": 1.0
    }
  },
  "measurement+vision": {
    "model": "measurement+vision",
    "n_train": 49,
    "n_test": 10,
    "accuracy": 1.0,
    "acc_ci": {
      "n": 10,
      "mean": 1.0,
      "std": 0.0,
      "lo": 1.0,
      "hi": 1.0
    }
  }
}

## What this is not

This does not say "never train a VLM". It says: do not spend model capacity on the identity map, and do not claim vision is necessary until matched-measurement pairs actually change the optimal correction **and** a grouped split shows a gain.
