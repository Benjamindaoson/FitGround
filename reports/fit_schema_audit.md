# FIT Schema Audit

```json
{
  "format": "parquet",
  "image_representation": "struct<bytes: binary, path: string>",
  "image_resolution": "768x1024 RGB PNG (typical)",
  "measurement_unit": "cm",
  "raw_image_fields": {
    "cloth": "HF Image struct(bytes: binary, path: string) \u2014 layflat garment",
    "target": "HF Image struct(bytes: binary, path: string) \u2014 person wearing garment",
    "person": "HF Image struct(bytes: binary, path: string) \u2014 garment-agnostic person"
  },
  "raw_measurement_fields": {
    "body_bust": "float, cm",
    "body_height": "float, cm",
    "body_hips": "float, cm",
    "body_waist": "float, cm",
    "garment_bust": "float, cm",
    "garment_length": "float, cm",
    "garment_sleeve_length": "float, cm"
  },
  "canonical_mapping": {
    "body_height": "body_height_cm",
    "body_bust": "body_bust_cm",
    "body_waist": "body_waist_cm",
    "body_hips": "body_hips_cm",
    "garment_bust": "garment_bust_cm",
    "garment_length": "garment_length_cm",
    "garment_sleeve_length": "garment_sleeve_cm"
  },
  "eval_split": {
    "shards": 20,
    "expected_rows": 5000
  }
}
```
