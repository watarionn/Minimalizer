"""SA10.34 source-evidence adaptive vector simplification, research-only.

Depends on signed Stage04 original owner masks and the preceding exact
source-derived polygon candidate, then enforces the historical full-scene
silhouette IoU as a stricter-than-policy nonregression constraint.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import cv2
import numpy as np

from minimalizer_zerobase.image_io import read_cv_image
from minimalizer_zerobase.parts.decomposition import PART_NAMES
from minimalizer_zerobase.reviewed_sa10.topology_constrained_vector_simplifier import (
    adapt_exact_contours,
)
from minimalizer_zerobase.semantic_abstraction.face_raster_guard import apply_face_raster_guard
from minimalizer_zerobase.simplification.artifacts import _render


def load(path: Path) -> dict:
    result = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(result, dict):
        raise ValueError("evidence must be JSON object")
    return result


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def run(
    *, exact_dir: Path, phase04_dir: Path,
    original_image: Path, baseline_evidence: Path, output_dir: Path,
) -> dict:
    exact = load(exact_dir / "phase8_source_contour_research.json")
    first = load(exact_dir / "phase8_exact_replay_metrics.json")
    previous = load(baseline_evidence)
    source_hash = digest(original_image)
    if source_hash != exact.get("source_sha256") or source_hash != previous.get("provenance", {}).get("source_hash"):
        raise ValueError("baseline and exact source hash mismatch")
    if previous.get("reproduction_pass") is not True:
        raise ValueError("earlier historical baseline is not reproducible")
    if first.get("full_anatomy", {}).get("gate") != "PASS" or first.get("source_raster_exact") is not True:
        raise ValueError("exact topology restoration is not verified")
    expected_scene_hash = first.get("candidate_vector_scene_sha256")
    if digest(exact_dir / "phase8_source_contour_research.json") != expected_scene_hash:
        raise ValueError("exact candidate bytes no longer match recorded evidence")
    width, height = exact["coordinate_space"]["pixel_width"], exact["coordinate_space"]["pixel_height"]
    raw = read_cv_image(original_image, cv2.IMREAD_UNCHANGED)
    if raw is None or raw.shape[:2] != (height, width):
        raise ValueError("original RGB source shape mismatch")
    original_rgb = cv2.cvtColor(raw, cv2.COLOR_BGRA2RGB if raw.shape[2] == 4 else cv2.COLOR_BGR2RGB)
    owner_masks = {}
    for owner in PART_NAMES:
        path = phase04_dir / "part_masks" / f"{owner}.png"
        if digest(path) != exact.get("source_part_mask_sha256", {}).get(owner):
            raise ValueError(f"Stage04 source mask changed: {owner}")
        raster = read_cv_image(path, cv2.IMREAD_GRAYSCALE)
        if raster is None or raster.shape != (height, width):
            raise ValueError(f"invalid owner mask: {owner}")
        owner_masks[owner] = raster > 0
    candidates = exact.get("primitives_back_to_front")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("source exact scene has no primitive records")
    source_by_id = {}
    for rec in candidates:
        owner = rec.get("source_mask_owner")
        if owner not in owner_masks or rec.get("source_mask_replay") is not True:
            raise ValueError("replay owner evidence missing")
        source_by_id[rec["primitive_id"]] = owner_masks[owner]
    historical_iou = previous["global"]["global_anatomy_gate"]["metrics"]["silhouette_iou"]
    budgets = first["old_vertices"]
    updated, masks, evidence = adapt_exact_contours(
        candidates, source_by_id, owner_masks, width=width, height=height,
        minimum_global_iou=historical_iou,
        original_ring_budget=budgets["ring_vertices"],
        original_component_budget=budgets["component_vertices"],
    )
    if [p["primitive_id"] for p in updated] != [p["primitive_id"] for p in candidates]:
        raise AssertionError("adaptive candidate primitive order changed")
    source_groups = [(p["semantic_part_id"],p["composition_part"],p["palette_color_rgb"],p.get("structural_support_only"))
                     for p in candidates]
    updated_groups = [(p["semantic_part_id"],p["composition_part"],p["palette_color_rgb"],p.get("structural_support_only"))
                     for p in updated]
    if source_groups != updated_groups:
        raise AssertionError("adaptive candidate material/owner/support policy changed")
    rgb = _render(width=width,height=height,primitives=tuple(updated),masks=masks)
    guarded = apply_face_raster_guard(rgb, original_rgb, owner_masks["face"])
    if guarded.changed_outside_face_pixels:
        raise AssertionError("face guard unauthorized changes")
    output_dir = output_dir.resolve()
    if any(output_dir == target.resolve() or target.resolve() in output_dir.parents
           for target in (phase04_dir, exact_dir)):
        raise ValueError("adaptive research outputs must not overwrite any input authorities")
    output_dir.mkdir(parents=True,exist_ok=True)
    scene_path=output_dir/"phase8_adaptive_source_contour_research.json"
    preview_path=output_dir/"phase8_adaptive_contour_preview.png"
    metrics_path=output_dir/"phase8_adaptive_metrics.json"
    scene_payload={
        "schema":"sa10.34-adaptive-contour-scene-v1",
        "research_only":True,
        "production_authorized":False,
        "original_source_sha256":source_hash,
        "coordinate_space":exact["coordinate_space"],
        "primitives_back_to_front":updated,
        "no_new_primitive":True,
        "no_new_material_or_owner":True,
    }
    scene_path.write_text(json.dumps(scene_payload,ensure_ascii=False,sort_keys=True,separators=(",",":")),encoding="utf-8")
    if not cv2.imwrite(str(preview_path),cv2.cvtColor(guarded.rgb,cv2.COLOR_RGB2BGR)):
        raise ValueError("failed to write geometry preview")
    evidence["original_source_sha256"]=source_hash
    evidence["historical_baseline_silhouette_iou"]=historical_iou
    evidence["adaptive_preview_sha256"]=digest(preview_path)
    evidence["adaptive_vector_sha256"]=digest(scene_path)
    evidence["owner_material_primitive_invariants"]=True
    evidence["input_artifacts_unchanged"]=True
    evidence["face_guard_changed_outside_mask_pixels"]=0
    metrics_path.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":evidence["status"],
        "global_gate":evidence["global_anatomy"]["gate"],
        "global_iou":evidence["global_anatomy"]["metrics"]["silhouette_iou"],
        "ring_vertices_old":first["old_vertices"]["ring_vertices"],
        "ring_vertices_exact":evidence["original_exact_source_ring_vertices"],
        "ring_vertices_adaptive":evidence["candidate_vertices"]["ring_vertices"],
        "accepted_edits":evidence["accepted_edit_count"],
        "budget_pass":evidence["vertex_budget_pass"],
        "blockers":evidence["blockers"],
        "output":str(output_dir),
    },indent=2,ensure_ascii=False))
    return evidence


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--exact-dir",required=True,type=Path)
    p.add_argument("--phase04-dir",required=True,type=Path)
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--baseline-evidence",required=True,type=Path)
    p.add_argument("--output-dir",required=True,type=Path)
    args=p.parse_args()
    result=run(exact_dir=args.exact_dir,phase04_dir=args.phase04_dir,
               original_image=args.source,baseline_evidence=args.baseline_evidence,
               output_dir=args.output_dir)
    if result["global_anatomy"]["gate"]!="PASS":
        raise SystemExit(2)


if __name__=="__main__":
    main()
