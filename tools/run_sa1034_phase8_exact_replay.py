"""Generate *research-only* Phase8 exact source contour evidence and previews.

Never writes to source/Phase04/Phase11/baseline directories, never promotes.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

import cv2
import numpy as np

from minimalizer_zerobase.image_io import read_cv_image
from minimalizer_zerobase.parts.decomposition import PART_NAMES
from minimalizer_zerobase.semantic_abstraction.face_raster_guard import apply_face_raster_guard
from minimalizer_zerobase.simplification.artifacts import _render
from minimalizer_zerobase.reviewed_sa10.source_exact_vector_replay import (
    evaluate_exact_replay,
)
from tools.run_sa1032_gc001_owner_audit import audit_records, scene_records


def load_json(path: Path) -> dict:
    output = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(output, dict):
        raise ValueError(f"invalid JSON object: {path}")
    return output


def file_sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def run(
    *,
    case_dir: Path, source_path: Path, phase12_dir: Path, output_dir: Path,
) -> dict:
    output_dir = output_dir.resolve()
    for authority in (case_dir.resolve(), phase12_dir.resolve()):
        if output_dir == authority or authority in output_dir.parents or output_dir in authority.parents:
            raise ValueError("research output must be isolated from original authorities")
    stage04 = load_json(case_dir / "phase_04" / "stage.json")
    stage11 = load_json(case_dir / "phase_11" / "stage.json")
    stage12 = load_json(phase12_dir / "stage.json")
    source_hash = file_sha(source_path)
    if not all(stage.get("source", {}).get("sha256") == source_hash for stage in (
        stage04, stage11, stage12
    )):
        raise ValueError("source SHA contract mismatch")
    composition_path = case_dir / "phase_11" / "11_composition.json"
    if stage11.get("outputs", {}).get("11_composition.json") != file_sha(composition_path):
        raise ValueError("saved Phase11 composition has changed")
    scene_path = phase12_dir / "12_simplification.json"
    if stage12.get("outputs", {}).get(scene_path.name) != file_sha(scene_path):
        raise ValueError("saved original Phase12 scene has changed")
    scene = load_json(scene_path)
    width, height = (
        scene["coordinate_space"]["pixel_width"], scene["coordinate_space"]["pixel_height"]
    )
    original_records = scene_records(scene)
    audit = audit_records(original_records)
    if audit["status"] != "OWNER_AUDIT_PASS" or len(original_records) != 11:
        raise ValueError("selected scene owner/budget gate failed")
    source_raw = read_cv_image(source_path, cv2.IMREAD_UNCHANGED)
    if source_raw is None or source_raw.shape[:2] != (height, width):
        raise ValueError("source image canvas mismatch")
    if source_raw.shape[2] == 4:
        rgb = cv2.cvtColor(source_raw, cv2.COLOR_BGRA2RGB)
    else:
        rgb = cv2.cvtColor(source_raw, cv2.COLOR_BGR2RGB)
    masks = {}
    mask_hashes = {}
    for name in PART_NAMES:
        path = case_dir / "phase_04" / "part_masks" / f"{name}.png"
        if not path.exists():
            raise ValueError(f"missing source part mask: {name}")
        image = read_cv_image(path, cv2.IMREAD_GRAYSCALE)
        if image is None or image.shape != (height, width):
            raise ValueError(f"invalid source part mask: {name}")
        masks[name] = image > 0
        mask_hashes[name] = file_sha(path)
        if stage04.get("outputs", {}).get(f"part_masks/{name}.png") != mask_hashes[name]:
            raise ValueError(f"source-owned Stage04 mask checksum mismatch: {name}")
    updated, replay_masks, report = evaluate_exact_replay(
        original_records, masks, width=width, height=height,
    )
    if [r.get("primitive_id") for r in updated] != [
        r.get("primitive_id") for r in original_records
    ]:
        raise AssertionError("candidate IDs or primitive order changed")
    # Produce a deterministic geometry render, not an overlay or any source
    # pixel paste. Face color flattening uses the original existing guard.
    painted = _render(
        width=width, height=height, primitives=tuple(updated), masks=replay_masks
    )
    guarded = apply_face_raster_guard(painted, rgb, masks["face"])
    if guarded.changed_outside_face_pixels != 0:
        raise AssertionError("face guard painted unauthorized regions")

    output_dir.mkdir(parents=True, exist_ok=True)
    candidate_path = output_dir / "phase8_source_contour_research.json"
    preview_path = output_dir / "phase8_source_contour_preview.png"
    metrics_path = output_dir / "phase8_exact_replay_metrics.json"
    candidate = {
        "research_only": True,
        "promotion_authorized": False,
        "schema": "sa10.34-phase8-scene-observation-v1",
        "source_sha256": source_hash,
        "source_part_mask_sha256": mask_hashes,
        "selected_original_profile": scene["selected_name"],
        "coordinate_space": scene["coordinate_space"],
        "primitives_back_to_front": updated,
        "material_and_owner_count_unchanged": True,
        "render_from_serialized_geometry_only": True,
        "not_a_production_phase12_manifest": True,
    }
    candidate_path.write_text(
        json.dumps(candidate, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    if not cv2.imwrite(str(preview_path), cv2.cvtColor(guarded.rgb, cv2.COLOR_RGB2BGR)):
        raise ValueError("unable to write research-only preview")
    report["source_sha256"] = source_hash
    report["source_part_mask_sha256"] = mask_hashes
    report["selected_name"] = scene["selected_name"]
    report["baseline_primitive_count"] = len(original_records)
    report["provenance_owner_audit"] = audit["status"]
    report["phase11_composition_sha256"] = file_sha(composition_path)
    report["phase04_masks_verified_against_manifest"] = True
    report["original_scene_sha256"] = file_sha(scene_path)
    report["original_preview_sha256"] = file_sha(phase12_dir / "preview.png")
    report["candidate_vector_scene_sha256"] = file_sha(candidate_path)
    report["candidate_preview_sha256"] = file_sha(preview_path)
    report["candidate_preview_source_mask_pixel_overlay"] = False
    report["face_guard_changed_outside_mask_pixels"] = guarded.changed_outside_face_pixels
    report["preview_generated_using_official_phase12_renderer"] = True
    report["original_inputs_modified"] = False
    metrics_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "status": report["status"],
        "source": source_hash,
        "count": report["primitive_count_new"],
        "old": report["old_vertices"],
        "new": report["new_vertices"],
        "vertex_budget_pass": report["vertex_budget_pass"],
        "global_anatomy": report["full_anatomy"]["gate"],
        "silhouette_iou": report["full_anatomy"]["metrics"]["silhouette_iou"],
        "export_render_parity": report["opencv_polygon_export_render_parity"],
        "svg_degenerate_rings": report["degenerate_svg_rings"],
        "blockers": report["blockers"],
        "output_dir": str(output_dir),
    }, indent=2, ensure_ascii=False))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-dir", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--phase12-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    report = run(
        case_dir=args.case_dir, source_path=args.source,
        phase12_dir=args.phase12_dir, output_dir=args.output_dir,
    )
    if report["full_anatomy"]["gate"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
