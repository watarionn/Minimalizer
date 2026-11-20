"""Run a source-only semantic parser capability probe.

This runner is deliberately narrower than the six-capability observer gate.
It freezes what a public semantic parser actually emits on the signed H06/H08
sources without turning missing labels into negative evidence.  It never reads
review masks, owner arrays, or phase labels while performing inference.

The output is research-only.  A parser that lacks a pairwise occlusion head or
an instance head is reported as HOLD; those fields are not reconstructed with
OR/AND rules or single-person assumptions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


SCHEMA = "minimalizer/local-l02/model-capability-probe/v1"
REQUIRED_CASES = ("H06", "H08")


class CapabilityProbeHold(ValueError):
    """Raised when the source-only probe cannot be frozen safely."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_source(path: Path) -> tuple[Image.Image, str]:
    if not path.is_file():
        raise CapabilityProbeHold(f"SOURCE_MISSING:{path}")
    source_sha = _sha256(path)
    try:
        image = Image.open(path).convert("RGB")
    except (OSError, ValueError) as exc:
        raise CapabilityProbeHold(f"SOURCE_DECODE_FAILED:{path.name}") from exc
    return image, source_sha


def _label_map(model: Any) -> dict[int, str]:
    raw = model.config.id2label
    result: dict[int, str] = {}
    for key, value in raw.items():
        try:
            index = int(key)
        except (TypeError, ValueError) as exc:
            raise CapabilityProbeHold("MODEL_LABEL_ID_INVALID") from exc
        result[index] = str(value).strip().lower()
    if not result:
        raise CapabilityProbeHold("MODEL_LABEL_MAP_MISSING")
    return result


def _infer(
    model: Any,
    processor: Any,
    image: Image.Image,
) -> tuple[np.ndarray, dict[str, Any]]:
    import torch

    inputs = processor(images=image, return_tensors="pt")
    with torch.inference_mode():
        logits = model(**inputs).logits
    logits = torch.nn.functional.interpolate(
        logits,
        size=(image.height, image.width),
        mode="bilinear",
        align_corners=False,
    )
    labels = logits.argmax(dim=1)[0].cpu().numpy().astype(np.uint16)
    names = _label_map(model)
    counts = {
        names[index]: int(np.count_nonzero(labels == index))
        for index in sorted(names)
        if int(np.count_nonzero(labels == index)) > 0
    }
    return labels, {
        "width": image.width,
        "height": image.height,
        "observed_labels": sorted(counts),
        "observed_label_pixel_counts": counts,
    }


def _capability_report(label_map: dict[int, str]) -> dict[str, Any]:
    labels = set(label_map.values())
    # These are declared heads, not inferred aliases.  In particular, a top
    # mask is never renamed to underlayer and a sleeve/arm union is forbidden.
    return {
        "outerwear": {
            "status": "AVAILABLE" if "coat_only_torso_region" in labels else "MISSING",
            "evidence_labels": ["coat_only_torso_region"] if "coat_only_torso_region" in labels else [],
        },
        "underlayer": {
            "status": "MISSING",
            "evidence_labels": [],
            "reason": "no explicit underlayer head",
        },
        "sleeve": {
            "status": "AVAILABLE" if {"left_sleeve_for_upper", "right_sleeve_for_upper"} <= labels else "MISSING",
            "evidence_labels": sorted(labels & {"left_sleeve_for_upper", "right_sleeve_for_upper"}),
        },
        "arm": {
            "status": "AVAILABLE" if {"left_arm", "right_arm"} <= labels else "MISSING",
            "evidence_labels": sorted(labels & {"left_arm", "right_arm"}),
        },
        "pairwise_occlusion": {
            "status": "MISSING",
            "evidence_labels": [],
            "reason": "semantic parser has no pairwise occlusion output",
        },
        "person_instance": {
            "status": "MISSING",
            "evidence_labels": [],
            "reason": "semantic parser has no instance-id output",
        },
    }


def run_probe(*, model_dir: Path, sources: dict[str, Path], output: Path) -> dict[str, Any]:
    if tuple(sources) != REQUIRED_CASES:
        raise CapabilityProbeHold("SOURCE_CASE_SET_INVALID")
    if output.exists():
        raise CapabilityProbeHold("REFUSE_OVERWRITE_RECEIPT")
    images: dict[str, tuple[Image.Image, str]] = {
        case: _load_source(path) for case, path in sources.items()
    }
    from transformers import AutoImageProcessor, SegformerForSemanticSegmentation

    processor = AutoImageProcessor.from_pretrained(model_dir)
    model = SegformerForSemanticSegmentation.from_pretrained(model_dir)
    model.eval()
    labels = _label_map(model)
    cases: dict[str, Any] = {}
    output.parent.mkdir(parents=True, exist_ok=True)
    for case in REQUIRED_CASES:
        image, source_sha = images[case]
        mask, evidence = _infer(model, processor, image)
        npz_path = output.parent / f"{case}_semantic_labels.npz"
        if npz_path.exists():
            raise CapabilityProbeHold(f"REFUSE_OVERWRITE_OUTPUT:{case}")
        np.savez_compressed(npz_path, semantic_labels=mask)
        cases[case] = {
            "source_sha256": source_sha,
            "semantic_labels_npz_sha256": _sha256(npz_path),
            **evidence,
        }
    report = {
        "schema": SCHEMA,
        "status": "CAPABILITY_HOLD_RESEARCH_ONLY",
        "model_dir": str(model_dir),
        "model_config_sha256": _sha256(model_dir / "config.json"),
        "label_map": {str(key): value for key, value in sorted(labels.items())},
        "capabilities": _capability_report(labels),
        "same_config_cases": list(REQUIRED_CASES),
        "human_labels_used_for_inference": False,
        "owner_arrays_used_for_inference": False,
        "unknown_policy": "separate_from_negative",
        "cases": cases,
        "phase4": "HOLD",
        "phase5": "NO_GO",
        "golden": "HOLD",
        "production": "NO_GO",
    }
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a source-only L02 model capability probe")
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--h06", type=Path, required=True)
    parser.add_argument("--h08", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run_probe(
            model_dir=args.model_dir,
            sources={"H06": args.h06, "H08": args.h08},
            output=args.output,
        )
    except CapabilityProbeHold as exc:
        print(json.dumps({"schema": SCHEMA, "status": "HOLD", "reason": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"schema": SCHEMA, "status": report["status"], "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
