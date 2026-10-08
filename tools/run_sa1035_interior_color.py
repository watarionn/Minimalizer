"""SA10.35 opt-in, research-only, source-grounded interior-plane benchmark.

Outer geometry is the already verified Phase8 adaptive scene. It is frozen.
Generated output is NOT a production vector, and never bypasses the existing
vertex, SVG-browser or human visual gates.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import cv2
import numpy as np

from minimalizer_zerobase.composition.semantic import rasterize_primitive_candidate
from minimalizer_zerobase.image_io import read_cv_image
from minimalizer_zerobase.parts.decomposition import PART_NAMES
from minimalizer_zerobase.evaluation.source_silhouette_anatomy_gate import evaluate_source_silhouette_anatomy
from minimalizer_zerobase.reviewed_sa10.interior_color_planes import (
    INTERIOR_ELIGIBLE_OWNERS, PROTECTED_OWNERS,
    propose_interior_plane, render_with_interior_planes,
)
from minimalizer_zerobase.semantic_abstraction.face_raster_guard import apply_face_raster_guard


def _load(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(obj, dict):
        raise ValueError("expected JSON object")
    return obj


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _lab_mse(reference_rgb: np.ndarray, test_rgb: np.ndarray, mask: np.ndarray) -> float:
    if not np.any(mask):
        raise ValueError("cannot score empty owner mask")
    ref = cv2.cvtColor(reference_rgb, cv2.COLOR_RGB2LAB).astype(np.float64)
    test = cv2.cvtColor(test_rgb, cv2.COLOR_RGB2LAB).astype(np.float64)
    return float(np.mean(np.sum((ref[mask] - test[mask]) ** 2, axis=1)))


def run(
    *, adaptive_dir: Path, stage04_dir: Path, source_image: Path,
    output_dir: Path, max_extra_planes: int = 3,
) -> dict:
    if not 1 <= max_extra_planes <= 4:
        raise ValueError("research subplane count is limited to four")
    output_dir = output_dir.resolve()
    authorities = (adaptive_dir.resolve(), stage04_dir.resolve(), source_image.resolve())
    if any(output_dir == p or output_dir in p.parents or p in output_dir.parents for p in authorities):
        raise ValueError("isolated output directory required; cannot overwrite input")
    selected_path = adaptive_dir / "phase8_adaptive_source_contour_research.json"
    baseline = _load(selected_path)
    metrics = _load(adaptive_dir / "phase8_adaptive_metrics.json")
    hash_source = _sha(source_image)
    if (
        baseline.get("schema") != "sa10.34-adaptive-contour-scene-v1"
        or baseline.get("original_source_sha256") != hash_source
        or metrics.get("original_source_sha256") != hash_source
        or metrics.get("adaptive_vector_sha256") != _sha(selected_path)
        or metrics.get("global_anatomy", {}).get("gate") != "PASS"
        or metrics.get("raw_owner_topology_pass") is not True
        or metrics.get("opencv_vector_render_parity") is not True
    ):
        raise ValueError("unverified Phase8 geometry or source-provenance contract")
    space = baseline["coordinate_space"]
    w, h = int(space["pixel_width"]), int(space["pixel_height"])
    raw = read_cv_image(source_image, cv2.IMREAD_UNCHANGED)
    if raw is None or raw.ndim != 3 or raw.shape[:2] != (h, w):
        raise ValueError("source is not the expected RGB/RGBA image")
    if raw.shape[2] == 4:
        source = cv2.cvtColor(raw, cv2.COLOR_BGRA2RGB)
    elif raw.shape[2] == 3:
        source = cv2.cvtColor(raw, cv2.COLOR_BGR2RGB)
    else:
        raise ValueError("unsupported source channel count")
    stage04 = _load(stage04_dir / "stage.json")
    if stage04.get("source", {}).get("sha256") != hash_source:
        raise ValueError("Stage04 source checksum mismatch")
    original_masks: dict[str, np.ndarray] = {}
    for name in PART_NAMES:
        path = stage04_dir / "part_masks" / f"{name}.png"
        if stage04.get("outputs", {}).get(f"part_masks/{name}.png") != _sha(path):
            raise ValueError(f"Stage04 owner mask changed: {name}")
        mask = read_cv_image(path, cv2.IMREAD_GRAYSCALE)
        if mask is None or mask.shape != (h, w):
            raise ValueError(f"invalid Stage04 mask: {name}")
        original_masks[name] = mask > 0
    selected = baseline.get("primitives_back_to_front")
    if not isinstance(selected, list) or len(selected) != 11:
        raise ValueError("selected baseline must contain exactly 11 original primitives")
    protected = np.logical_or.reduce([original_masks[owner] for owner in PROTECTED_OWNERS])
    primitive_masks = {
        p["primitive_id"]: rasterize_primitive_candidate(p, width=w, height=h)
        for p in selected
    }
    whole_source = np.logical_or.reduce(list(original_masks.values()))
    visible = np.logical_or.reduce([
        primitive_masks[p["primitive_id"]]
        for p in selected if p.get("structural_support_only") is not True
    ])
    original_gate = evaluate_source_silhouette_anatomy(whole_source, visible, fragmentation_penalty=0.0)
    if original_gate["gate"] != "PASS":
        raise ValueError("outer geometry failed the original raw silhouette topology gate")
    potential: list[tuple[float, dict]] = []
    for p in selected:
        owner = p.get("semantic_part_id")
        if owner not in INTERIOR_ELIGIBLE_OWNERS or p.get("structural_support_only"):
            continue
        if p.get("source_mask_owner") != owner or p.get("source_mask_replay") is not True:
            raise ValueError(f"interior owner provenance invalid: {owner}")
        proposal = propose_interior_plane(
            owner=owner, parent_primitive_id=p["primitive_id"], source_rgb=source,
            owner_mask=primitive_masks[p["primitive_id"]],
            parent_palette_rgb=p["palette_color_rgb"], protected_mask=protected,
        )
        if proposal is not None:
            plane, _ = proposal
            absolute_gain = plane["relative_lab_mse_reduction"] * plane["before_lab_mse"] * plane["owner_area_pixels"]
            potential.append((absolute_gain, plane))
    potential.sort(key=lambda item: (-item[0], item[1]["owner"]))
    planes = [p for _, p in potential[:max_extra_planes]]
    base, recolored, plane_union = render_with_interior_planes(
        primitives=selected, primitive_masks=primitive_masks, planes=planes,
        protected_mask=protected,
    )
    guarded_baseline = apply_face_raster_guard(base, source, original_masks["face"])
    guarded_candidate = apply_face_raster_guard(recolored, source, original_masks["face"])
    base = guarded_baseline.rgb
    recolored = guarded_candidate.rgb
    if guarded_candidate.changed_outside_face_pixels != 0:
        raise AssertionError("face color guard modified outside face")
    if not np.array_equal(base[protected], recolored[protected]):
        raise AssertionError("protected face or arm RGB changed")
    if np.any(plane_union & ~visible) or np.any(plane_union & protected):
        raise AssertionError("interior changes escaped source-authorized canvas")
    changed = np.any(base != recolored, axis=2)
    if np.any(changed & ~plane_union):
        raise AssertionError("color was changed outside recorded interior polygons")
    if not np.array_equal(visible, np.logical_or.reduce([
        primitive_masks[p["primitive_id"]]
        for p in selected if p.get("structural_support_only") is not True
    ])):
        raise AssertionError("outer geometry was changed")
    owner_reports = {}
    for p in selected:
        owner = p.get("semantic_part_id")
        if owner not in INTERIOR_ELIGIBLE_OWNERS:
            continue
        mask = primitive_masks[p["primitive_id"]] & ~protected
        if not np.any(mask):
            continue
        old_mse = _lab_mse(source, base, mask)
        new_mse = _lab_mse(source, recolored, mask)
        if new_mse > old_mse + 1e-9:
            raise AssertionError("source-color fit worsened for an eligible owner")
        owner_reports[owner] = {
            "owner_pixels": int(mask.sum()),
            "source_lab_mse_before": round(old_mse, 6),
            "source_lab_mse_after": round(new_mse, 6),
            "lab_mse_relative_improvement": round(float((old_mse - new_mse) / old_mse), 6) if old_mse else 0.0,
            "added_interior_planes": int(any(plane["owner"] == owner for plane in planes)),
        }
    eligible = np.zeros((h, w), bool)
    for p in selected:
        if p.get("semantic_part_id") in INTERIOR_ELIGIBLE_OWNERS:
            eligible |= primitive_masks[p["primitive_id"]] & ~protected
    old_full = _lab_mse(source, base, eligible)
    new_full = _lab_mse(source, recolored, eligible)
    if new_full > old_full + 1e-8:
        raise AssertionError("overall eligible source-color fit worsened")
    metadata = {
        "schema": "sa10.35-internal-color-evaluation-v1",
        "source_sha256": hash_source,
        "outer_scene_original_sha256": _sha(selected_path),
        "source_stage04_provenance_verified": True,
        "outer_primitive_count_before": len(selected),
        "outer_primitive_count_after": len(selected),
        "external_geometry_changed": False,
        "outer_raw_topology_gate": original_gate["gate"],
        "outer_silhouette_iou": original_gate["metrics"]["silhouette_iou"],
        "observed_source_colors_only": True,
        "source_bitmap_painted": False,
        "no_face_eyes_mouth_rendered": True,
        "face_and_both_arms_unchanged": True,
        "pixels_changed_outside_outer_silhouette": 0,
        "pixels_changed_outside_interior_subplanes": 0,
        "interior_subplane_count": len(planes),
        "new_geometric_subpaths_counted": len(planes),
        "total_painted_geometric_elements_estimate": len(selected) + len(planes),
        "interior_subplane_vertices": sum(p["polygon_vertex_count"] for p in planes),
        "interior_edited_pixels": int(changed.sum()),
        "candidate_color_lab_mse_before": round(old_full, 6),
        "candidate_color_lab_mse_after": round(new_full, 6),
        "eligible_color_mse_improvement_ratio": round(float((old_full-new_full) / old_full), 6) if old_full else 0.0,
        "owner_reports": owner_reports,
        "planes": planes,
        "original_outer_vector_budget_pass": bool(metrics.get("vertex_budget_pass")),
        "browser_svg_clip_path_parity_verified": False,
        "human_visual_review": "PENDING",
        "production_promotion_authorized": False,
        "status": "RESEARCH_COLOR_IMPROVED_BUT_HOLD"
        if len(planes) and new_full < old_full else "HOLD_NO_SUITABLE_COLOR_PLANE",
        "hard_blockers": [
            "ORIGINAL_OUTER_VERTEX_BUDGET_FAILED",
            "BROWSER_SVG_CLIP_PATH_PARITY_NOT_VERIFIED",
            "HUMAN_VISUAL_REVIEW_NOT_APPROVED",
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "interior_plane_metrics.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    (output_dir / "interior_plane_proposals.json").write_text(json.dumps({
        "schema": "sa10.35-interior-overlay-scene-v1",
        "research_only": True,
        "source_sha256": hash_source,
        "original_outer_scene_sha256": _sha(selected_path),
        "unchanged_parent_primitive_ids": [p["primitive_id"] for p in selected],
        "unchanged_outer_scene_file": str(selected_path),
        "additional_fill_subpaths": planes,
        "clip_rule": "parent-existing-owner-mask-and-not-face-or-arms",
        "no_base_geometry_mutation": True,
        "browser_svg_unsupported_until_parity_verified": True,
    }, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    for path, image in (
        ("interior_color_baseline.png", base),
        ("interior_color_candidate.png", recolored),
    ):
        if not cv2.imwrite(str(output_dir / path), cv2.cvtColor(image, cv2.COLOR_RGB2BGR)):
            raise ValueError(f"unable to save research preview: {path}")
    board = np.full((h+39, w*3, 3), 246, dtype=np.uint8)
    images = (source, base, recolored)
    for idx, (name, image) in enumerate(zip(("SOURCE RGB", "OUTER FIXED", "INTERIOR RESEARCH"), images)):
        x = idx*w
        board[39:39+h, x:x+w] = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        cv2.putText(board, name, (x+7, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.46,
                    (18, 18, 18), 1, cv2.LINE_AA)
    if not cv2.imwrite(str(output_dir / "interior_color_comparison.png"), board):
        raise ValueError("unable to save research comparison")
    print(json.dumps({
        "status": metadata["status"],
        "source_sha256": hash_source,
        "outer_gate": metadata["outer_raw_topology_gate"],
        "color_planes": len(planes),
        "owners": [p["owner"] for p in planes],
        "vertices": metadata["interior_subplane_vertices"],
        "improvement": metadata["eligible_color_mse_improvement_ratio"],
        "protected_unchanged": metadata["face_and_both_arms_unchanged"],
        "output_dir": str(output_dir),
        "blockers": metadata["hard_blockers"],
    }, indent=2, ensure_ascii=False))
    return metadata


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--adaptive-dir", required=True, type=Path)
    p.add_argument("--phase04-dir", required=True, type=Path)
    p.add_argument("--source", required=True, type=Path)
    p.add_argument("--output-dir", required=True, type=Path)
    p.add_argument("--max-extra-planes", type=int, default=3)
    args = p.parse_args()
    run(adaptive_dir=args.adaptive_dir, stage04_dir=args.phase04_dir,
        source_image=args.source, output_dir=args.output_dir,
        max_extra_planes=args.max_extra_planes)


if __name__ == "__main__":
    main()
