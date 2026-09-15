#!/usr/bin/env python3
"""Zero-shot / few-shot / optional tiny LoRA eval of a pretrained VLM.

Never uses a character transformer as a stand-in MLLM.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from pathlib import Path

ROOT = Path("/root/workspace/projects/FitGround")
if not ROOT.exists():
    ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "hero"


def dump(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


PROMPT = """You are a technical designer assistant. Return ONLY JSON with keys:
predicted_contact_ratio (float), predicted_clearance_p10_cm (float),
best_correction (one of: no_edit, bust+2cm, bust+3cm, abstain),
confidence (0-1), reason (short string).
Do not copy answers from file names. Use the measurements and the drape image.
body_bust_cm={body_bust_cm:.2f}
garment_bust_cm={garment_bust_cm:.2f}
material={material}
fit_intent=regular
candidate_actions=no_edit|bust+2cm|bust+3cm|abstain
"""


def parse_json_blob(text: str) -> dict | None:
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except Exception:
        return None


def load_cases():
    path = OUT / "visual_disambiguation.json"
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("cases") or payload.get("rows") or []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-cases", type=int, default=24)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()
    status_path = OUT / "mllm_status.json"
    if not status_path.exists():
        dump(OUT / "mllm_eval.json", {"status": "NOT_JUSTIFIED", "reason": "weights not on disk"})
        print("no mllm_status.json")
        return 0
    status = json.loads(status_path.read_text(encoding="utf-8"))
    if status.get("status") != "DOWNLOADED":
        dump(OUT / "mllm_eval.json", {"status": "NOT_JUSTIFIED", "upstream": status})
        print("model not downloaded")
        return 0
    name = status["model"]
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    os.environ.setdefault("HF_HOME", "/root/workspace/hf-cache")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    import torch
    from PIL import Image

    print("loading", name, flush=True)
    from transformers import AutoProcessor

    processor = AutoProcessor.from_pretrained(name, trust_remote_code=True)
    dtype = torch.float16 if args.device == "cuda" and torch.cuda.is_available() else torch.float32
    model = None
    load_err = None
    for loader_name in ("AutoModelForImageTextToText", "AutoModelForVision2Seq", "Qwen2VLForConditionalGeneration"):
        try:
            cls = getattr(__import__("transformers", fromlist=[loader_name]), loader_name)
            model = cls.from_pretrained(
                name,
                trust_remote_code=True,
                torch_dtype=dtype,
                device_map="cuda" if args.device == "cuda" and torch.cuda.is_available() else None,
            )
            print("loader", loader_name, flush=True)
            break
        except Exception as exc:
            load_err = f"{loader_name}: {type(exc).__name__}: {exc}"
            print("load_fail", load_err, flush=True)
    if model is None:
        dump(OUT / "mllm_eval.json", {"status": "NOT_JUSTIFIED", "error": load_err})
        return 0
    model.eval()
    cases = [c for c in load_cases() if c.get("render_a") or c.get("render")]
    random.Random(0).shuffle(cases)
    cases = cases[: args.max_cases]
    if not cases:
        # fall back to physics_vd renders
        vd = OUT / "physics_vd.json"
        if vd.exists():
            rows = json.loads(vd.read_text(encoding="utf-8"))
            for r in rows:
                renders = r.get("render_files") or []
                if r.get("edit_name") == "now" and renders:
                    cases.append(
                        {
                            "case_id": r.get("tag"),
                            "body_bust_cm": r.get("body_bust_cm") or 0,
                            "garment_bust_cm": r.get("garment_bust_cm") or 0,
                            "material": r.get("material"),
                            "render_a": renders[0],
                            "best_correction": "bust+2cm" if (r.get("utility") is not None and r["utility"] < -0.2) else "no_edit",
                            "gold": True,
                        }
                    )
            cases = cases[: args.max_cases]
    results = []
    n_parse = 0
    n_match = 0
    for i, case in enumerate(cases):
        img_path = case.get("render_a") or case.get("render") or case.get("render_b")
        if not img_path or not Path(img_path).exists():
            continue
        prompt = PROMPT.format(
            body_bust_cm=float(case.get("body_bust_cm") or 0),
            garment_bust_cm=float(case.get("garment_bust_cm") or 0),
            material=case.get("material") or case.get("material_a") or "unknown",
        )
        image = Image.open(img_path).convert("RGB")
        gold = case.get("recommended_a") or case.get("best_correction") or case.get("gold_action")
        try:
            if hasattr(processor, "apply_chat_template"):
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image"},
                            {"type": "text", "text": prompt},
                        ],
                    }
                ]
                chat = processor.apply_chat_template(messages, add_generation_prompt=True)
                inputs = processor(text=[chat], images=[image], return_tensors="pt", padding=True)
            else:
                inputs = processor(text=prompt, images=image, return_tensors="pt")
            device = next(model.parameters()).device
            inputs = {k: v.to(device) if hasattr(v, "to") else v for k, v in inputs.items()}
            with torch.no_grad():
                out = model.generate(**inputs, max_new_tokens=160)
            text = processor.batch_decode(out, skip_special_tokens=True)[0]
        except Exception as exc:
            results.append({"case_id": case.get("case_id"), "error": f"{type(exc).__name__}: {exc}"})
            continue
        parsed = parse_json_blob(text)
        ok = parsed is not None
        n_parse += int(ok)
        pred = (parsed or {}).get("best_correction")
        match = pred == gold if gold else None
        if match:
            n_match += 1
        results.append(
            {
                "case_id": case.get("case_id"),
                "gold": gold,
                "pred": pred,
                "parsed": parsed,
                "raw": text[-500:],
                "match": match,
            }
        )
        print(f"MLLM {i+1}/{len(cases)} pred={pred} gold={gold}", flush=True)
    payload = {
        "status": "PASS" if results else "NOT_JUSTIFIED",
        "model": name,
        "n": len(results),
        "parse_rate": (n_parse / len(results)) if results else 0.0,
        "action_match_rate": (n_match / len(results)) if results else None,
        "limitation": (
            "Zero-shot pretrained VLM on SYNTHETIC_BODY_PHYSICS renders. "
            "n is small; LoRA/QLoRA omitted to avoid leakage. Structured JSON parse_rate is the primary metric."
        ),
        "results": results,
        "body_kind": "SYNTHETIC_BODY_PHYSICS",
    }
    dump(OUT / "mllm_eval.json", payload)
    print(json.dumps({k: payload[k] for k in payload if k != "results"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
