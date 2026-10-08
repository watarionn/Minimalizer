"""SA10.36 real-image semantic apparel repair, research-only.

Frozen Phase8 exterior and verified Phase9 color baseline. Adds only
source-provenanced dark uniform, white shirt and narrow green necktie polygons
inside the currently visible lower_body owner; other pixels are untouchable.
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
from minimalizer_zerobase.reviewed_sa10.interior_color_planes import (
    render_with_interior_planes,
)
from minimalizer_zerobase.reviewed_sa10.semantic_apparel_material_planes import (
    propose_source_uniform_panels, render_source_uniform_panels,
)
from minimalizer_zerobase.semantic_abstraction.face_raster_guard import (
    apply_face_raster_guard,
)


def _json(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(obj, dict):
        raise ValueError(f"expected JSON object: {path}")
    return obj


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _lab_mse(src: np.ndarray, candidate: np.ndarray, mask: np.ndarray) -> float:
    if not np.any(mask):
        raise ValueError("no owner pixels to compare")
    ref = cv2.cvtColor(src, cv2.COLOR_RGB2LAB).astype(np.float64)
    obs = cv2.cvtColor(candidate, cv2.COLOR_RGB2LAB).astype(np.float64)
    return float(np.mean(np.sum((ref[mask] - obs[mask]) ** 2, axis=1)))


def _largest_connected(mask: np.ndarray) -> int:
    count, _, stats, _ = cv2.connectedComponentsWithStats(
        np.asarray(mask).astype(np.uint8), 8
    )
    return max((int(stats[i, cv2.CC_STAT_AREA]) for i in range(1, count)), default=0)


def run(*, phase8_dir: Path, phase9_dir: Path, phase04_dir: Path,
        source_path: Path, output_dir: Path) -> dict:
    output_dir = output_dir.resolve()
    for auth in (phase8_dir, phase9_dir, phase04_dir, source_path):
        absolute = auth.resolve()
        if output_dir == absolute or output_dir in absolute.parents or absolute in output_dir.parents:
            raise ValueError("cannot write over any input authority")
    scene_path = phase8_dir / "phase8_adaptive_source_contour_research.json"
    stage8 = _json(scene_path)
    stage8_metrics = _json(phase8_dir / "phase8_adaptive_metrics.json")
    stage9_metrics = _json(phase9_dir / "interior_plane_metrics.json")
    stage9_proposal = _json(phase9_dir / "interior_plane_proposals.json")
    source_sha = _sha(source_path)
    if (
        stage8.get("schema") != "sa10.34-adaptive-contour-scene-v1"
        or stage8_metrics.get("adaptive_vector_sha256") != _sha(scene_path)
        or stage8_metrics.get("original_source_sha256") != source_sha
        or stage8_metrics.get("global_anatomy", {}).get("gate") != "PASS"
        or stage9_metrics.get("schema") != "sa10.35-internal-color-evaluation-v1"
        or stage9_metrics.get("source_sha256") != source_sha
        or stage9_metrics.get("outer_scene_original_sha256") != _sha(scene_path)
        or stage9_metrics.get("outer_raw_topology_gate") != "PASS"
        or stage9_metrics.get("face_and_both_arms_unchanged") is not True
        or stage9_metrics.get("external_geometry_changed") is not False
        or stage9_proposal.get("original_outer_scene_sha256") != _sha(scene_path)
        or stage9_proposal.get("source_sha256") != source_sha
    ):
        raise ValueError("earlier structural/color research evidence is not reproducible")
    original_sha = _json(phase04_dir / "stage.json")
    if original_sha["source"]["sha256"] != source_sha:
        raise ValueError("Stage04 source SHA mismatch")
    w = int(stage8["coordinate_space"]["pixel_width"])
    h = int(stage8["coordinate_space"]["pixel_height"])
    raw = read_cv_image(source_path, cv2.IMREAD_UNCHANGED)
    if raw is None or raw.ndim != 3 or raw.shape[:2] != (h, w):
        raise ValueError("source image dimensions mismatch")
    src = cv2.cvtColor(
        raw, cv2.COLOR_BGRA2RGB if raw.shape[2] == 4 else cv2.COLOR_BGR2RGB
    )
    source_masks: dict[str, np.ndarray] = {}
    for name in PART_NAMES:
        file = phase04_dir / "part_masks" / f"{name}.png"
        if original_sha["outputs"].get(f"part_masks/{name}.png") != _sha(file):
            raise ValueError(f"owner mask SHA mismatch: {name}")
        mask = read_cv_image(file, cv2.IMREAD_GRAYSCALE)
        if mask is None or mask.shape != (h, w):
            raise ValueError(f"invalid Stage04 owner mask: {name}")
        source_masks[name] = mask > 0
    original = stage8.get("primitives_back_to_front")
    if not isinstance(original, list) or len(original) != 11:
        raise ValueError("expected 11 existing owners")
    identities = [p["primitive_id"] for p in original]
    if len(identities) != len(set(identities)):
        raise ValueError("duplicate primitive IDs")
    maskmap = {
        p["primitive_id"]: rasterize_primitive_candidate(p, width=w, height=h)
        for p in original
    }
    old_planes = stage9_proposal["additional_fill_subpaths"]
    stage9_base, stage9_raw, _ = render_with_interior_planes(
        primitives=original, primitive_masks=maskmap,
        planes=old_planes,
        protected_mask=(
            source_masks["face"] | source_masks["left_arm"] | source_masks["right_arm"]
        ),
    )
    verified_stage9 = apply_face_raster_guard(
        stage9_raw, src, source_masks["face"]
    ).rgb
    phase9_preview_path = phase9_dir / "interior_color_candidate.png"
    saved = read_cv_image(phase9_preview_path, cv2.IMREAD_COLOR)
    if saved is None or not np.array_equal(
        verified_stage9, cv2.cvtColor(saved, cv2.COLOR_BGR2RGB)
    ):
        raise ValueError("Phase9 candidate preview does not reproduce byte-for-byte")
    seen = np.full((h, w), -1, np.int32)
    for index, primitive in enumerate(original):
        if primitive.get("structural_support_only"):
            continue
        seen[maskmap[primitive["primitive_id"]]] = index
    lower = [
        (index, item) for index, item in enumerate(original)
        if item.get("semantic_part_id") == "lower_body"
        and item.get("source_mask_owner") == "lower_body"
        and item.get("composition_part") == "lower_body"
    ]
    if len(lower) != 1:
        raise ValueError("no unique source-owned lower_body primitive")
    index, item = lower[0]
    visible_parent = seen == index
    protected = source_masks["face"] | source_masks["left_arm"] | source_masks["right_arm"]
    if np.any(visible_parent & protected):
        visible_parent &= ~protected
    proposal = propose_source_uniform_panels(
        source_rgb=src, parent_visible=visible_parent,
        protected=protected, parent_primitive_id=item["primitive_id"],
    )
    if proposal is None:
        panels = []
        next_rgb = verified_stage9.copy()
        changed_canvas = np.zeros((h, w), bool)
        meta = {"status": "NO_UNIFORM_SHIRT_TIE_PATTERN", "panel_count": 0}
    else:
        panels, meta = proposal
        next_rgb, changed_canvas = render_source_uniform_panels(
            base_rgb=verified_stage9, panels=panels,
            parent_visible=visible_parent, protected=protected,
        )
    changed = np.any(next_rgb != verified_stage9, axis=2)
    if np.any(changed & ~visible_parent) or np.any(changed & protected):
        raise AssertionError("material change outside its existing owner or on arms/face")
    if not np.array_equal(verified_stage9[protected], next_rgb[protected]):
        raise AssertionError("source facial or arm colors drifted")
    mse_before = _lab_mse(src, verified_stage9, visible_parent)
    mse_after = _lab_mse(src, next_rgb, visible_parent)
    if mse_after > mse_before + 1e-10:
        raise AssertionError("color correction made lower-body source fit worse")
    gain = float((mse_before - mse_after) / mse_before) if mse_before else 0.0
    if panels and gain < 0.20:
        raise ValueError("apparel panel repair did not materially improve source fidelity")
    old_color = np.asarray(item["palette_color_rgb"], np.uint8)
    initial_neutral = np.all(verified_stage9 == old_color, axis=2) & visible_parent
    remaining_neutral = np.all(next_rgb == old_color, axis=2) & visible_parent
    initial_blob = _largest_connected(initial_neutral)
    next_blob = _largest_connected(remaining_neutral)
    if panels and next_blob >= initial_blob:
        raise AssertionError("largest gray clothing block did not shrink")
    if not np.array_equal(
        maskmap[item["primitive_id"]], rasterize_primitive_candidate(item, width=w, height=h)
    ):
        raise AssertionError("existing geometric silhouette mutated")

    source_green = (
        (src[:, :, 1].astype(np.int16) > src[:, :, 0].astype(np.int16) + 30)
        & (src[:, :, 1].astype(np.int16) > src[:, :, 2].astype(np.int16) + 25)
        & visible_parent
    )
    tie_panels = [p for p in panels if p["material"] == "green_necktie"]
    if panels and (
        len(tie_panels) != 1
        or tie_panels[0]["panel_area_pixels"] > 1.10 * int(source_green.sum())
    ):
        raise AssertionError("green tie expansion limit exceeded")
    original_visible = np.logical_or.reduce([
        maskmap[p["primitive_id"]]
        for p in original if p.get("structural_support_only") is not True
    ])
    output_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(
        str(output_dir / "material_grammar_preview.png"),
        cv2.cvtColor(next_rgb, cv2.COLOR_RGB2BGR),
    )
    display = np.full((h+38,3*w,3),245,np.uint8)
    for i,(name,rgb) in enumerate((
        ("ORIGINAL SOURCE",src),
        ("BEFORE GREY BLOCK",verified_stage9),
        ("MATERIAL GRAMMAR",next_rgb),
    )):
        display[38:38+h,i*w:(i+1)*w] = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        cv2.putText(display,name,(i*w+8,25),cv2.FONT_HERSHEY_SIMPLEX,0.44,(18,18,18),1,cv2.LINE_AA)
    cv2.imwrite(str(output_dir / "source_before_material_comparison.png"),display)
    candidate_path = output_dir / "material_grammar_subpaths.json"
    candidate_path.write_text(
        json.dumps({
            "schema": "sa10.36-uniform-material-scene-v1",
            "research_only": True,
            "source_sha256": source_sha,
            "locked_phase8_vector_sha256": _sha(scene_path),
            "existing_owner_primitive_count": len(original),
            "prior_phase9_extra_subpaths": len(old_planes),
            "apparel_extra_subpaths": panels,
            "svg_browser_parity_verified": False,
            "never_paint_original_rgb_pixels": True,
            "no_primitive_or_color_owner_mutation": True,
        }, ensure_ascii=False, indent=2)+"\n", encoding="utf-8",
    )
    evidence = {
        "schema": "sa10.36-uniform-material-benchmark-v1",
        "source_sha256": source_sha,
        "stage04_mask_sha256_verified": True,
        "phase8_and_phase9_lineage_verified": True,
        "phase9_baseline_pixels_exact": True,
        "original_outer_silhouette_frozen": True,
        "original_outer_topology_pass": stage8_metrics["global_anatomy"]["gate"] == "PASS",
        "outer_original_vertex_budget_pass": stage8_metrics["vertex_budget_pass"],
        "phase9_existing_subpaths": len(old_planes),
        "material_subpaths_added": len(panels),
        "original_outer_primitives_count": len(original),
        "total_filled_geometric_element_estimate": len(original)+len(old_planes)+len(panels),
        "material_extra_vertices": sum(len(p["points"]) for p in panels),
        "lower_body_source_lab_mse_before": round(mse_before, 6),
        "lower_body_source_lab_mse_after": round(mse_after, 6),
        "lower_body_source_lab_mse_gain": round(gain, 6),
        "lower_body_source_visible_pixels": int(visible_parent.sum()),
        "pixels_changed_inside_source_owner": int(changed.sum()),
        "pixels_changed_outside_source_owner": 0,
        "face_and_both_arms_pixel_exact": True,
        "gray_block_largest_connected_before_px": initial_blob,
        "gray_block_largest_connected_after_px": next_blob,
        "gray_block_largest_connected_reduction": initial_blob-next_blob,
        "source_green_tie_pixels": int(source_green.sum()),
        "green_tie_panel_area_pixels": tie_panels[0]["panel_area_pixels"] if tie_panels else 0,
        "semantic_proposal": meta,
        "apparel_materials": [p["material"] for p in panels],
        "browser_svg_owner_clip_verified": False,
        "human_visual_review": "PENDING",
        "production_promotion_authorized": False,
        "hard_blockers": [
            "OUTER_VERTEX_BUDGET_STILL_FAILED",
            "BROWSER_SVG_OWNER_CLIP_PARITY_UNVERIFIED",
            "VISUAL_REVIEW_NOT_APPROVED",
        ],
        "research_status": "GRAY_BLOCK_REPLACED_RESEARCH_HOLD" if panels else "PATTERN_NOT_DETECTED_HOLD",
        "baseline_image_sha256": _sha(phase9_preview_path),
        "candidate_image_sha256": _sha(output_dir / "material_grammar_preview.png"),
        "candidate_geometry_sha256": _sha(candidate_path),
    }
    (output_dir / "material_grammar_metrics.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2)+"\n", encoding="utf-8"
    )
    print(json.dumps({
        "research_status": evidence["research_status"],
        "color_panels": evidence["material_subpaths_added"],
        "material_names": evidence["apparel_materials"],
        "owner_color_mse_reduction": evidence["lower_body_source_lab_mse_gain"],
        "gray_largest_before_after": [initial_blob,next_blob],
        "tie_source_and_painted_pixels": [evidence["source_green_tie_pixels"],
                                         evidence["green_tie_panel_area_pixels"]],
        "silhouette_unchanged": evidence["original_outer_silhouette_frozen"],
        "face_and_arms_unchanged": evidence["face_and_both_arms_pixel_exact"],
        "output": str(output_dir),
    }, indent=2, ensure_ascii=False))
    return evidence


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--phase8-dir",required=True,type=Path)
    p.add_argument("--phase9-dir",required=True,type=Path)
    p.add_argument("--phase04-dir",required=True,type=Path)
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--output-dir",required=True,type=Path)
    a=p.parse_args()
    run(phase8_dir=a.phase8_dir,phase9_dir=a.phase9_dir,
        phase04_dir=a.phase04_dir,source_path=a.source,output_dir=a.output_dir)


if __name__=="__main__":
    main()
