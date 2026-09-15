# Failure-aware / abstention

Support set for the deployed rule: `body_name=mean_all`, `material=default`, action |Δ| ≤ 3 cm, simulation stable.

{
  "n": 633,
  "by_bucket": {
    "in_distribution_easy": {
      "n": 90,
      "abstain_rate": 0.0,
      "policy_accuracy": 1.0
    },
    "high_side_effect": {
      "n": 330,
      "abstain_rate": 0.6727272727272727,
      "policy_accuracy": 0.6727272727272727
    },
    "ood_body": {
      "n": 180,
      "abstain_rate": 1.0,
      "policy_accuracy": 1.0
    },
    "ood_material": {
      "n": 26,
      "abstain_rate": 1.0,
      "policy_accuracy": 1.0
    },
    "ambiguous": {
      "n": 7,
      "abstain_rate": 1.0,
      "policy_accuracy": 1.0
    }
  },
  "risk_coverage": [
    {
      "coverage": 1.0,
      "selective_accuracy": 0.8293838862559242,
      "abstention_rate": 0.0
    },
    {
      "coverage": 0.9004739336492891,
      "selective_accuracy": 0.8105263157894737,
      "abstention_rate": 0.0995260663507109
    },
    {
      "coverage": 0.8009478672985783,
      "selective_accuracy": 0.7869822485207101,
      "abstention_rate": 0.1990521327014218
    },
    {
      "coverage": 0.7014218009478673,
      "selective_accuracy": 0.7567567567567568,
      "abstention_rate": 0.2985781990521327
    },
    {
      "coverage": 0.6018957345971564,
      "selective_accuracy": 0.7165354330708661,
      "abstention_rate": 0.3981042654028436
    },
    {
      "coverage": 0.5023696682464455,
      "selective_accuracy": 0.660377358490566,
      "abstention_rate": 0.4976303317535545
    },
    {
      "coverage": 0.4028436018957346,
      "selective_accuracy": 0.5764705882352941,
      "abstention_rate": 0.5971563981042654
    },
    {
      "coverage": 0.3033175355450237,
      "selective_accuracy": 0.4479166666666667,
      "abstention_rate": 0.6966824644549763
    },
    {
      "coverage": 0.2037914691943128,
      "selective_accuracy": 0.4263565891472868,
      "abstention_rate": 0.7962085308056872
    },
    {
      "coverage": 0.10426540284360189,
      "selective_accuracy": 0.42424242424242425,
      "abstention_rate": 0.8957345971563981
    },
    {
      "coverage": 0.004739336492890996,
      "selective_accuracy": 0.3333333333333333,
      "abstention_rate": 0.995260663507109
    }
  ],
  "failure_detection_auroc": 0.9005524861878452,
  "abstention_precision": 1.0,
  "note": "Policy: abstain on OOD body/material/unstable sim/ambiguous candidates. Support = mean_all + default cloth."
}

Hero case 4 is the product behaviour: **AI refuses to recommend a correction** when the body is outside support.
