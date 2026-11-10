"""Source-only whole-image outerwear reconstruction for Lane A L02.

This is a candidate generator, not a production owner promotion.  It runs a
fixed Fashionpedia instance-segmentation model on signed source pixels, keeps
only the ontology's main outerwear classes, and assigns fresh owner IDs from
those semantic instances.  Sleeve detections are recorded as diagnostics but
never promoted to an outerwear owner because a sleeve can belong to an
underlayer or cuff.  Frozen owner arrays, human masks, review JSON, and
case-specific thresholds are deliberately not accepted.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image


class FashionpediaOuterwearHold(ValueError):
    """Raised when the source-only candidate cannot be authenticated."""


MODEL_REPO = "resoa/garment-detector-seg"
MODEL_REVISION = "38c0c6bbb27537a76cbbc94a710d8b82fd721b50"
MODEL_WEIGHTS_SHA256 = (
    "aafefc440ea8f3f388e894a898e4270a2eeb6e38a3c3ffd3751d07d0f30b26bb"
)

# Fashionpedia 46-class ontology IDs.  These IDs are fixed by the model
# ontology, not learned from H04/H06/H08 review material.
OUTERWEAR_CLASS_IDS = frozenset({3, 4, 5, 9, 12})  # cardigan, jacket, vest, coat, cape
SLEEVE_CLASS_ID = 31
FIXED_CONFIDENCE_THRESHOLD = 0.30


@dataclass(frozen=True)
class OuterwearComponent:
    owner_id: int
    area: int
    bbox_xywh: tuple[int, int, int, int]


@dataclass(frozen=True)
class OuterwearReconstruction:
    owner: np.ndarray
    unknown: np.ndarray
    observed: np.ndarray
    selected_main_instances: int
    selected_sleeve_instances: int
    attached_sleeve_pixels: int
    components: tuple[OuterwearComponent, ...]


def _sha256(data: bytes | np.ndarray) -> str:
    if isinstance(data, bytes):
        return hashlib.sha256(data).hexdigest()
    return hashlib.sha256(data.tobytes(order="C")).hexdigest()


def _validate_source_alpha(source_alpha: np.ndarray) -> None:
    if (
        type(source_alpha) is not np.ndarray
        or source_alpha.dtype != np.bool_
        or source_alpha.ndim != 2
        or not source_alpha.size
    ):
        raise FashionpediaOuterwearHold("INVALID_SOURCE_ALPHA")


def _validate_detections(
    *,
    source_alpha: np.ndarray,
    detection_masks: np.ndarray,
    class_ids: np.ndarray,
    confidences: np.ndarray,
) -> None:
    if (
        type(detection_masks) is not np.ndarray
        or detection_masks.dtype != np.bool_
        or detection_masks.ndim != 3
        or detection_masks.shape[1:] != source_alpha.shape
        or not detection_masks.shape[0]
    ):
        raise FashionpediaOuterwearHold("INVALID_DETECTION_MASKS")
    if (
        type(class_ids) is not np.ndarray
        or class_ids.dtype.kind not in "iu"
        or class_ids.ndim != 1
        or class_ids.shape[0] != detection_masks.shape[0]
        or np.any(class_ids < 0)
        or np.any(class_ids >= 46)
    ):
        raise FashionpediaOuterwearHold("INVALID_CLASS_IDS")
    if (
        type(confidences) is not np.ndarray
        or confidences.dtype.kind not in "fc"
        or confidences.ndim != 1
        or confidences.shape[0] != detection_masks.shape[0]
        or not np.isfinite(confidences).all()
        or np.any(confidences < 0)
        or np.any(confidences > 1)
    ):
        raise FashionpediaOuterwearHold("INVALID_CONFIDENCES")


def reconstruct_outerwear_owner(
    *,
    source_alpha: np.ndarray,
    detection_masks: np.ndarray,
    class_ids: np.ndarray,
    confidences: np.ndarray,
    confidence_threshold: float = FIXED_CONFIDENCE_THRESHOLD,
) -> OuterwearReconstruction:
    """Build a fresh outerwear owner map from source-only detections.

    The existing owner map is intentionally absent from this API.  Main
    garment instances are selected by fixed Fashionpedia ontology IDs.  A
    One owner is preserved for one detected garment instance even when
    occlusion splits it into several 8-connected pieces.  Sleeve detections
    remain diagnostic-only.  All remaining opaque pixels stay in ``unknown``
    and are not a negative observation.
    """
    _validate_source_alpha(source_alpha)
    _validate_detections(
        source_alpha=source_alpha,
        detection_masks=detection_masks,
        class_ids=class_ids,
        confidences=confidences,
    )
    if (
        type(confidence_threshold) is not float
        or not np.isfinite(confidence_threshold)
        or not 0 < confidence_threshold <= 1
        or confidence_threshold != FIXED_CONFIDENCE_THRESHOLD
    ):
        raise FashionpediaOuterwearHold("CASE_SPECIFIC_THRESHOLD_FORBIDDEN")

    main_instances: list[tuple[np.ndarray, float]] = []
    sleeve_instances: list[np.ndarray] = []
    selected_main = 0
    selected_sleeves = 0
    for mask, class_id, confidence in zip(detection_masks, class_ids, confidences):
        if float(confidence) < confidence_threshold:
            continue
        if int(class_id) in OUTERWEAR_CLASS_IDS:
            main_instances.append((mask & source_alpha, float(confidence)))
            selected_main += 1
        elif int(class_id) == SLEEVE_CLASS_ID:
            sleeve_instances.append(mask)
            selected_sleeves += 1

    main_instances.sort(key=lambda item: item[1], reverse=True)
    owner_groups = [mask.copy() for mask, _ in main_instances]
    attached_sleeves = np.zeros_like(source_alpha)

    observed = (
        np.logical_or.reduce(owner_groups)
        if owner_groups
        else np.zeros_like(source_alpha)
    )
    observed &= source_alpha

    if len(owner_groups) > 254:
        raise FashionpediaOuterwearHold("TOO_MANY_OWNER_COMPONENTS")
    owner = np.zeros(source_alpha.shape, dtype=np.uint8)
    components: list[OuterwearComponent] = []
    claimed = np.zeros_like(source_alpha)
    next_owner_id = 1
    for group_mask in owner_groups:
        group_mask = group_mask & source_alpha & ~claimed
        if not np.any(group_mask):
            continue
        owner[group_mask] = next_owner_id
        claimed |= group_mask
        ys, xs = np.where(group_mask)
        components.append(
            OuterwearComponent(
                owner_id=next_owner_id,
                area=int(group_mask.sum()),
                bbox_xywh=(
                    int(xs.min()),
                    int(ys.min()),
                    int(xs.max() - xs.min() + 1),
                    int(ys.max() - ys.min() + 1),
                ),
            )
        )
        next_owner_id += 1
    unknown = source_alpha & ~observed
    if np.any(owner != 0) and np.any(owner[~source_alpha] != 0):
        raise FashionpediaOuterwearHold("OWNER_OUTSIDE_SOURCE_ALPHA")
    return OuterwearReconstruction(
        owner=owner,
        unknown=unknown,
        observed=observed,
        selected_main_instances=selected_main,
        selected_sleeve_instances=selected_sleeves,
        attached_sleeve_pixels=int(attached_sleeves.sum()),
        components=tuple(components),
    )


def decode_signed_source(source_bytes: bytes, expected_sha256: str) -> np.ndarray:
    if type(expected_sha256) is not str or len(expected_sha256) != 64:
        raise FashionpediaOuterwearHold("SOURCE_SHA_REQUIRED")
    if _sha256(source_bytes) != expected_sha256:
        raise FashionpediaOuterwearHold("SIGNED_SOURCE_SHA_MISMATCH")
    try:
        with Image.open(__import__("io").BytesIO(source_bytes)) as image:
            return np.asarray(image.convert("RGBA"), dtype=np.uint8)
    except Exception as exc:  # pragma: no cover - PIL exception variants
        raise FashionpediaOuterwearHold("INVALID_SIGNED_SOURCE_IMAGE") from exc


def verify_model_weights(model_path: Path) -> str:
    if not isinstance(model_path, Path) or not model_path.is_file():
        raise FashionpediaOuterwearHold("MODEL_WEIGHTS_REQUIRED")
    digest = _sha256(model_path.read_bytes())
    if digest != MODEL_WEIGHTS_SHA256:
        raise FashionpediaOuterwearHold("MODEL_WEIGHTS_SHA_MISMATCH")
    return digest


def run_source_only_model(
    *, source_rgba: np.ndarray, model_path: Path
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    """Run RF-DETR-Seg without any human or frozen-owner input."""
    masks, class_ids, confidences, model_diagnostics = predict_source_only_detections(
        source_rgba=source_rgba, model_path=model_path
    )
    result = reconstruct_outerwear_owner(
        source_alpha=source_rgba[:, :, 3] != 0,
        detection_masks=masks,
        class_ids=class_ids,
        confidences=confidences,
    )
    diagnostics = {
        **model_diagnostics,
        "schema": "minimalizer/local-l02/fashionpedia-outerwear-reconstruction/v1",
        "source_only": True,
        "human_annotations_used": False,
        "review_json_used": False,
        "frozen_owner_used": False,
        "unknown_not_treated_as_negative": True,
        "owner_promotion_authorized": False,
        "quality": "UNASSESSED",
        "Phase4": "FAIL",
        "L02": "HOLD",
        "production": "NO_GO",
    }
    return result.owner, result.unknown, result.observed, class_ids, {
        **diagnostics,
        "selected_main_instances": result.selected_main_instances,
        "selected_sleeve_instances": result.selected_sleeve_instances,
        "attached_sleeve_pixels": result.attached_sleeve_pixels,
        "owner_components": [component.__dict__ for component in result.components],
        "owner_pixels": int(np.count_nonzero(result.owner)),
        "unknown_pixels": int(result.unknown.sum()),
        "owner_array_sha256": _sha256(result.owner),
        "unknown_array_sha256": _sha256(result.unknown.astype(np.uint8)),
        "observed_array_sha256": _sha256(result.observed.astype(np.uint8)),
    }


def predict_source_only_detections(
    *, source_rgba: np.ndarray, model_path: Path
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    """Return fresh Fashionpedia detections from the signed source only.

    This lower-level API exists so the component owner solver can consume
    instance masks instead of reusing a previously materialized owner array.
    """
    if (
        type(source_rgba) is not np.ndarray
        or source_rgba.dtype != np.uint8
        or source_rgba.ndim != 3
        or source_rgba.shape[2] != 4
    ):
        raise FashionpediaOuterwearHold("INVALID_SOURCE_RGBA")
    verify_model_weights(model_path)
    try:
        from rfdetr import RFDETRSegSmall
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise FashionpediaOuterwearHold("RFDETR_PACKAGE_REQUIRED") from exc
    rgb = np.rint(
        source_rgba[:, :, :3].astype(np.float32)
        * (source_rgba[:, :, 3:4].astype(np.float32) / 255.0)
        + 255.0 * (1.0 - source_rgba[:, :, 3:4].astype(np.float32) / 255.0)
    ).astype(np.uint8)
    image = Image.fromarray(rgb, mode="RGB")
    model = RFDETRSegSmall(
        pretrain_weights=str(model_path), num_classes=46
    )
    detections = model.predict(
        image, threshold=FIXED_CONFIDENCE_THRESHOLD
    )
    masks = np.asarray(detections.mask, dtype=bool)
    class_ids = np.asarray(detections.class_id, dtype=np.int64)
    confidences = np.asarray(detections.confidence, dtype=np.float32)
    return masks, class_ids, confidences, {
        "model_repo": MODEL_REPO,
        "model_revision": MODEL_REVISION,
        "model_weights_sha256": MODEL_WEIGHTS_SHA256,
        "confidence_threshold": FIXED_CONFIDENCE_THRESHOLD,
        "outerwear_class_ids": sorted(OUTERWEAR_CLASS_IDS),
        "sleeve_class_id": SLEEVE_CLASS_ID,
        "detection_count": int(masks.shape[0]),
        "detection_masks_sha256": _sha256(masks.astype(np.uint8)),
        "class_ids_sha256": _sha256(class_ids),
        "confidences_sha256": _sha256(confidences),
    }


def save_private_candidate(
    *,
    output_dir: Path,
    case_id: str,
    source_bytes: bytes,
    source_sha256: str,
    owner: np.ndarray,
    unknown: np.ndarray,
    observed: np.ndarray,
    diagnostics: dict[str, Any],
) -> tuple[Path, Path]:
    """Write candidate arrays and a receipt outside GitHub."""
    if not isinstance(output_dir, Path) or not case_id:
        raise FashionpediaOuterwearHold("PRIVATE_OUTPUT_REQUIRED")
    if _sha256(source_bytes) != source_sha256:
        raise FashionpediaOuterwearHold("SIGNED_SOURCE_SHA_MISMATCH")
    output_dir.mkdir(parents=True, exist_ok=True)
    array_path = output_dir / f"{case_id}_FASHIONPEDIA_OUTERWEAR_OWNER_PRIVATE.npz"
    receipt_path = output_dir / f"{case_id}_FASHIONPEDIA_OUTERWEAR_RECEIPT.json"
    np.savez_compressed(
        array_path,
        owner=owner.astype(np.uint8),
        unknown=unknown.astype(np.uint8),
        observed=observed.astype(np.uint8),
    )
    receipt = {
        **diagnostics,
        "case_id": case_id,
        "source_encoded_sha256": source_sha256,
        "array_file": array_path.name,
        "array_file_sha256": _sha256(array_path.read_bytes()),
        "source_bytes_not_saved_here": True,
    }
    receipt_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return array_path, receipt_path
