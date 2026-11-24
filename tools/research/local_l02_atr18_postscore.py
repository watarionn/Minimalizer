"""Score a frozen SCHP-ATR18 class map against categorical review labels.

Research-only, post-inference diagnostic. This deliberately reports a broad
garment-vs-non-garment proxy and never creates or authorizes owner masks.
Unknown review pixels and transparent source pixels are excluded from scoring.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
from scipy import ndimage

MODEL_REVISION = "a54fa65e7e4f27f21011f652ffc0053ebb24b292"
MODEL_SHA256 = "4420d8db8c1f266967c89485786b01209f6d405f320fc0f87e8ced49392cefb5"
GARMENT_CLASS_IDS = frozenset((4, 5, 6, 7, 8, 9, 10, 17))
ARM_CLASS_IDS = frozenset((14, 15))


class PostscoreHold(ValueError):
    """The supplied frozen inference package cannot be safely postscored."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decode_review_mask(mask_rgba: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return green-positive, red-negative, and unknown pixels.

    Antialiased/blended colors and faint strokes are unknown, matching the
    existing H06/H08 independent-submission audit decoder.
    """
    if (not isinstance(mask_rgba, np.ndarray) or mask_rgba.dtype != np.uint8
            or mask_rgba.ndim != 3 or mask_rgba.shape[2] != 4):
        raise PostscoreHold("INVALID_REVIEW_RGBA")
    rgb = mask_rgba[..., :3].astype(np.int32)
    alpha = mask_rgba[..., 3]
    green = ((rgb[..., 1] >= 150) & (rgb[..., 1] > rgb[..., 0] * 1.5)
             & (rgb[..., 1] > rgb[..., 2] * 1.5) & (alpha >= 128))
    red = ((rgb[..., 0] >= 150) & (rgb[..., 0] > rgb[..., 1] * 1.5)
           & (rgb[..., 0] > rgb[..., 2] * 1.5) & (alpha >= 128))
    if np.any(green & red):
        raise PostscoreHold("AMBIGUOUS_REVIEW_COLOR")
    return green, red, ~(green | red)


def topology_counts(binary: np.ndarray) -> dict[str, int]:
    """Count 4/8-connected components and holes per the existing audit rule."""
    if not isinstance(binary, np.ndarray) or binary.ndim != 2 or binary.dtype != np.bool_:
        raise PostscoreHold("INVALID_TOPOLOGY_MASK")
    holes = ndimage.binary_fill_holes(binary) & ~binary
    return {
        "components4": int(ndimage.label(
            binary, ndimage.generate_binary_structure(2, 1))[1]),
        "components8": int(ndimage.label(
            binary, ndimage.generate_binary_structure(2, 2))[1]),
        "holes4": int(ndimage.label(
            holes, ndimage.generate_binary_structure(2, 1))[1]),
        "holes8": int(ndimage.label(
            holes, ndimage.generate_binary_structure(2, 2))[1]),
    }


def score_case(*, case: str, encoded_source: bytes, source_rgba: np.ndarray,
               review_mask_rgba: np.ndarray, class_ids: np.ndarray,
               receipt: dict[str, Any], review_mask_sha256: str) -> dict[str, Any]:
    """Score only known human labels after validating a frozen ATR18 receipt."""
    if (not isinstance(source_rgba, np.ndarray) or source_rgba.dtype != np.uint8
            or source_rgba.ndim != 3 or source_rgba.shape[2] != 4):
        raise PostscoreHold("INVALID_SOURCE_RGBA")
    if (not isinstance(class_ids, np.ndarray) or class_ids.dtype != np.uint8
            or class_ids.ndim != 2 or class_ids.shape != source_rgba.shape[:2]
            or review_mask_rgba.shape != source_rgba.shape):
        raise PostscoreHold("SOURCE_MASK_CLASS_MAP_SHAPE_MISMATCH")
    if not isinstance(receipt, dict):
        raise PostscoreHold("MISSING_FROZEN_INFERENCE_RECEIPT")
    checks = {
        "case": receipt.get("case") == case,
        "model_revision": receipt.get("model_revision") == MODEL_REVISION,
        "checkpoint": receipt.get("checkpoint_sha256") == MODEL_SHA256,
        "inference_frozen_before_postscore": receipt.get("postscore_not_yet_performed") is True,
        "labels_not_used_for_inference": receipt.get("human_annotations_used") is False
            and receipt.get("review_labels_used_for_inference") is False,
        "source_encoded_sha256": receipt.get("encoded_source_sha256") == sha256(encoded_source),
        "source_rgba_sha256": receipt.get("source_rgba_sha256")
            == sha256(source_rgba.tobytes()),
        "class_map_sha256": receipt.get("class_map_sha256_private")
            == sha256(class_ids.tobytes()),
        "observer_only": receipt.get("class_map_is_observer_output_not_owner_mask") is True
            and receipt.get("owner_modified") is False,
        "unknown_policy": receipt.get("unknown_not_treated_as_negative") is True,
    }
    if not all(checks.values()):
        failed = ",".join(k for k, ok in checks.items() if not ok)
        raise PostscoreHold(f"FROZEN_RECEIPT_CHECK_FAILED:{failed}")

    opaque = source_rgba[..., 3] > 0
    green, red, unknown = decode_review_mask(review_mask_rgba)
    known_positive = green & opaque
    known_negative = red & opaque
    unknown_opaque = unknown & opaque
    predicted_garment = np.isin(class_ids, tuple(GARMENT_CLASS_IDS)) & opaque
    predicted_arms = np.isin(class_ids, tuple(ARM_CLASS_IDS)) & opaque

    tp = int(np.count_nonzero(predicted_garment & known_positive))
    fp = int(np.count_nonzero(predicted_garment & known_negative))
    fn = int(np.count_nonzero(~predicted_garment & known_positive))
    tn = int(np.count_nonzero(~predicted_garment & known_negative))
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    iou = tp / (tp + fp + fn) if tp + fp + fn else None
    return {
        "case": case,
        "source_encoded_sha256": sha256(encoded_source),
        "source_rgba_sha256": sha256(source_rgba.tobytes()),
        "review_mask_sha256": review_mask_sha256,
        "class_map_sha256": sha256(class_ids.tobytes()),
        "labels_used_only_for_postscore": True,
        "source_opaque_pixels": int(opaque.sum()),
        "known_positive_pixels": int(known_positive.sum()),
        "known_negative_pixels": int(known_negative.sum()),
        "unknown_source_pixels": int(unknown_opaque.sum()),
        "known_label_coverage": float(
            (known_positive.sum() + known_negative.sum()) / max(1, opaque.sum())),
        "garment_class_ids": sorted(GARMENT_CLASS_IDS),
        "known_only_confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "precision": precision,
        "recall": recall,
        "iou": iou,
        "arm_predictions_on_known_negative": int(
            np.count_nonzero(predicted_arms & known_negative)),
        "human_positive_topology": topology_counts(known_positive),
        "predicted_garment_topology": topology_counts(predicted_garment),
        "formal_quality": "UNASSESSED",
        "Phase4": "FAIL",
        "L02": "HOLD",
        "production": "NO_GO",
    }


def load_case(case: str, source_path: Path, mask_path: Path,
              npz_path: Path) -> dict[str, Any]:
    encoded = source_path.read_bytes()
    source_rgba = np.asarray(Image.open(source_path).convert("RGBA"), dtype=np.uint8)
    mask_rgba = np.asarray(Image.open(mask_path).convert("RGBA"), dtype=np.uint8)
    with np.load(npz_path, allow_pickle=False) as archive:
        if set(archive.files) != {"class_ids", "receipt_json"}:
            raise PostscoreHold("UNEXPECTED_NPZ_FIELDS")
        class_ids = np.asarray(archive["class_ids"], dtype=np.uint8)
        receipt = json.loads(str(archive["receipt_json"].item()))
    return score_case(case=case, encoded_source=encoded, source_rgba=source_rgba,
                      review_mask_rgba=mask_rgba, class_ids=class_ids,
                      receipt=receipt, review_mask_sha256=sha256(mask_path.read_bytes()))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", nargs=4, action="append", required=True,
                        metavar=("ID", "SOURCE", "REVIEW_MASK", "FROZEN_NPZ"),
                        help="repeat for each frozen signed-source case")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cases = [load_case(case, Path(source), Path(mask), Path(npz))
             for case, source, mask, npz in args.case]
    if len({row["case"] for row in cases}) != len(cases):
        raise SystemExit("DUPLICATE_CASE_ID")
    report = {
        "schema": "minimalizer/local-l02/atr18-postscore-sourcefree/v1",
        "model_revision": MODEL_REVISION,
        "checkpoint_sha256": MODEL_SHA256,
        "scope": "exploratory broad garment-vs-non-garment proxy only; not six-capability or Phase4 approval",
        "unknown_pixels_scored_as_negative": False,
        "cases": cases,
        "quality": "UNASSESSED",
        "Phase4": "FAIL",
        "L02": "HOLD",
        "production": "NO_GO",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
