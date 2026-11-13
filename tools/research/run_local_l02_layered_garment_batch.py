"""Run the layered garment solver on the signed H04/H06/H08 source-only batch."""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
from PIL import Image

from tools.research.local_l02_layered_garment_solver import solve_layered_garment
from tools.research.local_l02_source_owner_reconstruction import ARM_CLASS_IDS


def sha(data: bytes | np.ndarray) -> str:
    raw = data if isinstance(data, bytes) else data.tobytes(order="C")
    return hashlib.sha256(raw).hexdigest()


def run_case(
    *, case_id: str, source_path: Path, source_sha256: str, raw_npz_path: Path,
    raw_npz_sha256: str, class_map_path: Path, class_map_sha256: str, output_dir: Path,
) -> dict:
    source_bytes = source_path.read_bytes()
    if sha(source_bytes) != source_sha256:
        raise ValueError(f"SIGNED_SOURCE_SHA_MISMATCH:{case_id}")
    with Image.open(source_path) as image:
        rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    source_alpha = rgba[:, :, 3] != 0
    with np.load(raw_npz_path, allow_pickle=False) as raw:
        masks = raw["detection_masks"].astype(bool)
        classes = raw["class_ids"]
        confidences = raw["confidences"]
        raw_alpha = raw["source_alpha"].astype(bool)
    if sha(raw_npz_path.read_bytes()) != raw_npz_sha256:
        raise ValueError(f"RAW_NPZ_SHA_MISMATCH:{case_id}")
    if masks.shape[1:] != source_alpha.shape or not np.array_equal(raw_alpha, source_alpha):
        raise ValueError(f"RAW_SOURCE_SHAPE_OR_ALPHA_MISMATCH:{case_id}")
    with np.load(class_map_path, allow_pickle=False) as class_map:
        class_ids = class_map["class_ids"]
    if sha(class_ids) != class_map_sha256 or class_ids.shape != source_alpha.shape:
        raise ValueError(f"CLASS_MAP_SHA_OR_SHAPE_MISMATCH:{case_id}")
    arm_mask = np.isin(class_ids, tuple(ARM_CLASS_IDS)) & source_alpha
    result = solve_layered_garment(
        source_alpha=source_alpha,
        detection_masks=masks,
        detection_classes=classes,
        detection_confidences=confidences,
        arm_mask=arm_mask,
        detection_masks_sha256=sha(masks.astype(np.uint8)),
        arm_mask_sha256=sha(arm_mask.astype(np.uint8)),
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    array_path = output_dir / f"{case_id}_LAYERED_GARMENT_OWNER_PRIVATE.npz"
    np.savez_compressed(
        array_path,
        owner=result.owner,
        unknown=result.unknown.astype(np.uint8),
        source_alpha=source_alpha.astype(np.uint8),
        outerwear_observed=result.outerwear_observed.astype(np.uint8),
        underlayer_observed=result.underlayer_observed.astype(np.uint8),
        arm_mask=arm_mask.astype(np.uint8),
        detection_masks=masks.astype(np.uint8),
        detection_classes=classes,
        detection_confidences=confidences,
        class_ids=class_ids,
    )
    receipt = {
        "schema": "minimalizer/local-l02/layered-garment-solver/v1",
        "case_id": case_id,
        "source_sha256": source_sha256,
        "source_shape": list(rgba.shape),
        "raw_npz": raw_npz_path.name,
        "raw_npz_sha256": raw_npz_sha256,
        "class_map_sha256": class_map_sha256,
        "source_only": True,
        "human_masks_used_in_inference": False,
        "review_json_used_in_inference": False,
        "frozen_owner_used_in_inference": False,
        "unknown_not_treated_as_negative": True,
        "detection_masks_sha256": sha(masks.astype(np.uint8)),
        "arm_mask_sha256": sha(arm_mask.astype(np.uint8)),
        "owner_array_sha256": sha(result.owner),
        "unknown_array_sha256": sha(result.unknown.astype(np.uint8)),
        "underlayer_observed_sha256": sha(result.underlayer_observed.astype(np.uint8)),
        "fixed_confidence_threshold": 0.30,
        "fixed_contact_radius_px": 12,
        "fixed_min_sleeve_component_area": 32,
        "sleeve_decisions": [asdict(item) for item in result.sleeve_decisions],
        "accepted_sleeve_components": sum(item.decision == "ACCEPT_GARMENT_OVER_ARM_OCCLUSION" for item in result.sleeve_decisions),
        "owner_pixels": int(np.count_nonzero(result.owner)),
        "unknown_pixels": int(result.unknown.sum()),
        "quality": result.quality,
        "Phase4": result.phase4,
        "L02": result.l02,
        "production": result.production,
        "candidate_array": array_path.name,
        "candidate_array_sha256": sha(array_path.read_bytes()),
    }
    receipt_path = output_dir / f"{case_id}_LAYERED_GARMENT_RECEIPT.json"
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--class-map-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--case", action="append", required=True, help="case|source|source_sha|classmap|classmap_sha")
    args = parser.parse_args()
    results = []
    for raw_case in args.case:
        case_id, source, source_sha, class_map, class_sha = raw_case.split("|", 4)
        raw_path = args.raw_dir / f"{case_id}_FASHIONPEDIA_RAW_SOURCE_ONLY_PRIVATE.npz"
        raw_sha = sha(raw_path.read_bytes())
        results.append(run_case(
            case_id=case_id,
            source_path=Path(source),
            source_sha256=source_sha,
            raw_npz_path=raw_path,
            raw_npz_sha256=raw_sha,
            class_map_path=Path(class_map),
            class_map_sha256=class_sha,
            output_dir=args.output_dir,
        ))
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
