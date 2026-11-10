"""Run the component owner solver on signed H04/H06/H08 sources.

The command accepts only signed source files and source-only class maps.  It
does not accept an existing owner array, human mask, review JSON, or a
case-specific threshold.  All output is intended for a private research
directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
from PIL import Image

from tools.research.local_l02_component_owner_solver import solve_component_owners
from tools.research.local_l02_fashionpedia_outerwear_reconstruction import (
    FIXED_CONFIDENCE_THRESHOLD,
    MODEL_REPO,
    MODEL_REVISION,
    MODEL_WEIGHTS_SHA256,
    OUTERWEAR_CLASS_IDS,
    predict_source_only_detections,
)
from tools.research.local_l02_source_owner_reconstruction import ARM_CLASS_IDS


def _sha(data: bytes | np.ndarray) -> str:
    raw = data if isinstance(data, bytes) else data.tobytes(order="C")
    return hashlib.sha256(raw).hexdigest()


def _load_rgba(path: Path, expected_sha: str) -> tuple[bytes, np.ndarray]:
    raw = path.read_bytes()
    if _sha(raw) != expected_sha:
        raise ValueError(f"SIGNED_SOURCE_SHA_MISMATCH:{path}")
    with Image.open(path) as image:
        return raw, np.asarray(image.convert("RGBA"), dtype=np.uint8)


def _load_class_map(path: Path, expected_sha: str, shape: tuple[int, int]) -> np.ndarray:
    with np.load(path, allow_pickle=False) as archive:
        if "class_ids" not in archive.files:
            raise ValueError(f"CLASS_MAP_KEY_MISSING:{path}")
        class_ids = np.asarray(archive["class_ids"])
    if class_ids.dtype != np.uint8 or class_ids.shape != shape:
        raise ValueError(f"CLASS_MAP_SHAPE_OR_DTYPE:{path}")
    if _sha(class_ids) != expected_sha:
        raise ValueError(f"CLASS_MAP_SHA_MISMATCH:{path}")
    return class_ids


def run_case(
    *,
    case_id: str,
    source_path: Path,
    source_sha: str,
    class_map_path: Path,
    class_map_sha: str,
    model_path: Path,
    output_dir: Path,
) -> dict:
    source_bytes, source_rgba = _load_rgba(source_path, source_sha)
    class_ids = _load_class_map(class_map_path, class_map_sha, source_rgba.shape[:2])
    source_alpha = source_rgba[:, :, 3] != 0
    arm_mask = np.isin(class_ids, tuple(ARM_CLASS_IDS)) & source_alpha

    masks, detection_classes, confidences, model_meta = predict_source_only_detections(
        source_rgba=source_rgba, model_path=model_path
    )
    if masks.ndim != 3 or masks.shape[1:] != source_alpha.shape:
        raise ValueError(f"DETECTION_SHAPE_MISMATCH:{case_id}")
    selected = (
        np.isin(detection_classes, tuple(OUTERWEAR_CLASS_IDS))
        & (confidences >= FIXED_CONFIDENCE_THRESHOLD)
    )
    instance_masks = masks[selected] & source_alpha[None, :, :]
    result = solve_component_owners(
        source_alpha=source_alpha,
        instance_masks=instance_masks,
        instance_masks_sha256=_sha(instance_masks),
        role_masks=(
            (
                "arm",
                arm_mask,
                _sha(arm_mask.astype(np.uint8)),
                "sapiens2-body-parts-source-only",
            ),
        ),
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    array_path = output_dir / f"{case_id}_COMPONENT_OWNER_PRIVATE.npz"
    receipt_path = output_dir / f"{case_id}_COMPONENT_OWNER_RECEIPT.json"
    np.savez_compressed(
        array_path,
        owner=result.owner,
        unknown=result.unknown.astype(np.uint8),
        source_alpha=source_alpha.astype(np.uint8),
        instance_masks=instance_masks.astype(np.uint8),
        arm_mask=arm_mask.astype(np.uint8),
        class_ids=class_ids,
    )
    receipt = {
        "schema": "minimalizer/local-l02/component-owner-solver/v1",
        "case_id": case_id,
        "source_sha256": source_sha,
        "source_shape": list(source_rgba.shape),
        "source_opaque_pixels": int(source_alpha.sum()),
        "class_map_sha256": class_map_sha,
        "class_map_path_name": class_map_path.name,
        "model_repo": MODEL_REPO,
        "model_revision": MODEL_REVISION,
        "model_weights_sha256": MODEL_WEIGHTS_SHA256,
        "confidence_threshold": FIXED_CONFIDENCE_THRESHOLD,
        "source_only": True,
        "human_masks_used_in_inference": False,
        "review_json_used_in_inference": False,
        "frozen_owner_used_in_inference": False,
        "underlayer_evidence_available": False,
        "instance_masks_sha256": _sha(instance_masks),
        "arm_mask_sha256": _sha(arm_mask.astype(np.uint8)),
        "selected_instance_count": int(instance_masks.shape[0]),
        "model_detection_meta": model_meta,
        "accepted_instances": list(result.accepted_instances),
        "contact_decisions": [asdict(item) for item in result.decisions],
        "owner_array_sha256": _sha(result.owner),
        "unknown_array_sha256": _sha(result.unknown.astype(np.uint8)),
        "source_only_solver": True,
        "unknown_not_treated_as_negative": result.unknown_not_treated_as_negative,
        "owner_promotion_authorized": result.owner_promotion_authorized,
        "quality": result.quality,
        "Phase4": result.phase4,
        "L02": result.l02,
        "production": result.production,
        "source_bytes_sha256_rechecked": _sha(source_bytes),
    }
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"array_path": str(array_path), "receipt_path": str(receipt_path), **receipt}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--case",
        action="append",
        required=True,
        help="case_id|source_path|source_sha256|class_map_npz|class_map_sha256",
    )
    args = parser.parse_args()
    results = []
    for raw in args.case:
        parts = raw.split("|", 4)
        if len(parts) != 5:
            raise SystemExit("--case must contain five pipe-separated fields")
        results.append(
            run_case(
                case_id=parts[0],
                source_path=Path(parts[1]),
                source_sha=parts[2],
                class_map_path=Path(parts[3]),
                class_map_sha=parts[4],
                model_path=args.model,
                output_dir=args.output_dir,
            )
        )
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

