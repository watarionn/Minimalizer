"""Fail-closed source-mask vs rendered-baseline mask comparison.

A diagnostic, not a production promotion gate. Uses identical canvas dimensions.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import cv2
import numpy as np


def binary_mask(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError(f"unreadable image: {path}")
    if image.ndim == 2:
        return image > 0
    if image.shape[2] == 4:
        return image[:, :, 3] > 0
    raise ValueError("RGB image has no explicit mask or alpha; refuse color-based inference")


def compare_masks(source: np.ndarray, candidate: np.ndarray) -> dict:
    if source.shape != candidate.shape or source.ndim != 2:
        raise ValueError("mask canvas mismatch")
    intersection = int(np.count_nonzero(source & candidate))
    union = int(np.count_nonzero(source | candidate))
    if not union:
        raise ValueError("both masks empty")
    return {
        "source_pixels": int(np.count_nonzero(source)),
        "candidate_pixels": int(np.count_nonzero(candidate)),
        "intersection_pixels": intersection,
        "union_pixels": union,
        "iou": intersection / union,
        "source_missing_pixels": int(np.count_nonzero(source & ~candidate)),
        "candidate_excess_pixels": int(np.count_nonzero(candidate & ~source)),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--source-mask", required=True, type=Path)
    p.add_argument("--baseline-mask", required=True, type=Path)
    p.add_argument("--candidate-mask", type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    source = binary_mask(args.source_mask)
    baseline = compare_masks(source, binary_mask(args.baseline_mask))
    result = {"baseline": baseline, "candidate": None, "status": "BASELINE_ONLY"}
    if args.candidate_mask:
        candidate = compare_masks(source, binary_mask(args.candidate_mask))
        result["candidate"] = candidate
        result["delta_iou"] = candidate["iou"] - baseline["iou"]
        result["status"] = "IMPROVED" if result["delta_iou"] > 1e-9 else "NO_PROVEN_IMPROVEMENT"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
