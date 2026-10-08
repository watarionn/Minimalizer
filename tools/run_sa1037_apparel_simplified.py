"""SA10.37 source-signed apparel ring simplification, no production mutation.

Consumes Stage36 signed material polygons, Stage9 RGB baseline, Stage8 frozen
outer polygons and Stage04 original owner evidence. Emits a strictly opt-in
geometric simplification preview and hard-gate diagnostics. No generated pixels.
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
from minimalizer_zerobase.reviewed_sa10.apparel_vertex_simplifier import (
    _simple_polygon, optimize_apparel_polygon_vertices,
)
from minimalizer_zerobase.reviewed_sa10.semantic_apparel_material_planes import (
    _rgb_mask_conditions, material_polygon_mask, render_source_uniform_panels,
)


def _json(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(obj, dict):
        raise ValueError(f"JSON object required: {path}")
    return obj


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _lab_error(source: np.ndarray, obs: np.ndarray, mask: np.ndarray) -> float:
    s = cv2.cvtColor(source, cv2.COLOR_RGB2LAB).astype(np.float64)
    o = cv2.cvtColor(obs, cv2.COLOR_RGB2LAB).astype(np.float64)
    return float(np.mean(np.sum((s[mask] - o[mask]) ** 2, axis=1)))


def run(*, stage36_dir: Path, stage8_dir: Path, stage9_dir: Path,
        stage04_dir: Path, source_path: Path, output_dir: Path) -> dict:
    output_dir = output_dir.resolve()
    for root in (stage36_dir, stage8_dir, stage9_dir, stage04_dir):
        parent = root.resolve()
        if output_dir == parent or output_dir in parent.parents or parent in output_dir.parents:
            raise ValueError("cannot overwrite or nest research output in input authority")
    if output_dir == source_path.resolve():
        raise ValueError("original source image cannot be overwritten")
    prev_record = _json(stage36_dir / "material_grammar_subpaths.json")
    prev_metrics = _json(stage36_dir / "material_grammar_metrics.json")
    stage8_scene = stage8_dir / "phase8_adaptive_source_contour_research.json"
    stage8 = _json(stage8_scene)
    stage8_metrics = _json(stage8_dir / "phase8_adaptive_metrics.json")
    stage04 = _json(stage04_dir / "stage.json")
    original_sha = _sha(source_path)
    if (
        prev_record.get("schema") != "sa10.36-uniform-material-scene-v1"
        or prev_metrics.get("schema") != "sa10.36-uniform-material-benchmark-v1"
        or prev_record.get("source_sha256") != original_sha
        or prev_metrics.get("source_sha256") != original_sha
        or prev_metrics.get("candidate_geometry_sha256") != _sha(stage36_dir / "material_grammar_subpaths.json")
        or prev_metrics.get("candidate_image_sha256") != _sha(stage36_dir / "material_grammar_preview.png")
        or stage8.get("original_source_sha256") != original_sha
        or prev_record.get("locked_phase8_vector_sha256") != _sha(stage8_scene)
        or stage8_metrics.get("adaptive_vector_sha256") != _sha(stage8_scene)
        or stage8_metrics.get("global_anatomy", {}).get("gate") != "PASS"
        or stage04.get("source", {}).get("sha256") != original_sha
    ):
        raise ValueError("source, Phase8 or Phase36 saved provenance mismatch")
    space = stage8.get("coordinate_space")
    if not isinstance(space, dict):
        raise ValueError("coordinate_space missing")
    h = int(space["pixel_height"])
    w = int(space["pixel_width"])
    raw = read_cv_image(source_path, cv2.IMREAD_UNCHANGED)
    if raw is None or raw.shape[:2] != (h, w):
        raise ValueError("original RGB source incompatible")
    if raw.ndim != 3 or raw.shape[2] not in (3,4):
        raise ValueError("original source must be RGB or RGBA")
    source_rgb = cv2.cvtColor(raw, cv2.COLOR_BGRA2RGB if raw.shape[2]==4 else cv2.COLOR_BGR2RGB)
    stage04_masks = {}
    for owner in PART_NAMES:
        path = stage04_dir / "part_masks" / f"{owner}.png"
        if stage04.get("outputs", {}).get(f"part_masks/{owner}.png") != _sha(path):
            raise ValueError(f"Stage04 owner mask SHA mismatch: {owner}")
        mask = read_cv_image(path, cv2.IMREAD_GRAYSCALE)
        if mask is None or mask.shape != (h, w):
            raise ValueError(f"Stage04 owner canvas mismatch: {owner}")
        stage04_masks[owner] = mask > 0
    parent_records = stage8.get("primitives_back_to_front")
    if not isinstance(parent_records, list) or len(parent_records) != 11:
        raise ValueError("expected original 11 untouched outer primitives")
    visible_owner = np.full((h, w), -1, np.int32)
    for index, primitive in enumerate(parent_records):
        if primitive.get("structural_support_only"):
            continue
        mask = rasterize_primitive_candidate(primitive, width=w, height=h)
        visible_owner[mask] = index
    owners = [
        (index, primitive) for index, primitive in enumerate(parent_records)
        if primitive.get("source_mask_owner") == "lower_body"
        and primitive.get("semantic_part_id") == "lower_body"
    ]
    if len(owners) != 1:
        raise ValueError("cannot uniquely determine lower_body owner")
    i, body = owners[0]
    protected = stage04_masks["face"] | stage04_masks["left_arm"] | stage04_masks["right_arm"]
    parent = (visible_owner == i) & ~protected
    prior_image_path = stage36_dir / "material_grammar_preview.png"
    prior_raw = read_cv_image(prior_image_path, cv2.IMREAD_COLOR)
    if prior_raw is None or prior_raw.shape[:2] != (h, w):
        raise ValueError("Stage36 image invalid")
    prior_rgb = cv2.cvtColor(prior_raw, cv2.COLOR_BGR2RGB)
    baseline_path = stage9_dir / "interior_color_candidate.png"
    if prev_metrics.get("baseline_image_sha256") != _sha(baseline_path):
        raise ValueError("signed Stage9 baseline RGB no longer matches")
    base_raw = read_cv_image(baseline_path, cv2.IMREAD_COLOR)
    if base_raw is None or base_raw.shape != prior_raw.shape:
        raise ValueError("Stage9 baseline image size mismatch")
    baseline_rgb = cv2.cvtColor(base_raw, cv2.COLOR_BGR2RGB)
    original_panels = prev_record.get("apparel_extra_subpaths")
    if not isinstance(original_panels, list):
        raise ValueError("signed apparel polygons missing")
    if prev_metrics["research_status"] == "GRAY_BLOCK_REPLACED_RESEARCH_HOLD":
        if len(original_panels)!=5 or body["primitive_id"]!=original_panels[0]["parent_primitive_id"]:
            raise ValueError("signed five panels have mismatched existing owner")
        rerendered, _ = render_source_uniform_panels(
            base_rgb=baseline_rgb, panels=original_panels,
            parent_visible=parent, protected=protected,
        )
    elif prev_metrics["research_status"] == "PATTERN_NOT_DETECTED_HOLD":
        if original_panels:
            raise ValueError("nonmatching character may not contain apparel subpaths")
        rerendered = baseline_rgb.copy()
    else:
        raise ValueError("unaccepted old research result")
    if not np.array_equal(rerendered, prior_rgb):
        raise AssertionError("cannot reproduce signed Stage36 RGB preview")

    if original_panels:
        new_panels, next_rgb, audit = optimize_apparel_polygon_vertices(
            original_panels=original_panels,
            source_rgb=source_rgb,
            baseline_rgb=baseline_rgb,
            owner_visible=parent, protected=protected,
            minimum_saved_vertices=1,
        )
        if audit["status"]!="RESEARCH_GEOMETRIC_VERTEX_REDUCTION_HOLD":
            # A negative result is documented but not quietly promoted as good.
            if not audit["all_filled_polygons_simple"]:
                raise ValueError("unrepaired SVG self-crossing polygon")
    else:
        new_panels, next_rgb = [], rerendered.copy()
        audit = {
            "schema": "sa10.37-topology-locked-apparel-geometry-v1",
            "status": "NONMATCHING_CASE_NO_OP",
            "original_total_vertices": 0,
            "candidate_total_vertices": 0,
            "saved_vertices": 0,
            "all_filled_polygons_simple": True,
            "outer_silhouette_unchanged": True,
            "material_precision_gate": True,
        }
    changed = np.any(next_rgb != prior_rgb, axis=2)
    if np.any(changed & ~parent) or np.any(changed & protected):
        raise AssertionError("SVG material optimization recolored outside existing owner")
    if not np.array_equal(prior_rgb[protected], next_rgb[protected]):
        raise AssertionError("original face and arms changed")
    if any(panel["color_rgb_observed"] != prev["color_rgb_observed"] for panel,prev in zip(new_panels,original_panels)):
        raise AssertionError("source-palette owner color changed")
    if len(new_panels)!=len(original_panels):
        raise AssertionError("existing semantic subpath count changed")
    before_mse = _lab_error(source_rgb,prior_rgb,parent)
    after_mse = _lab_error(source_rgb,next_rgb,parent)
    if after_mse > before_mse*1.02 + 1e-9:
        raise AssertionError("source color geometry degradation")
    for panel in new_panels:
        mask = material_polygon_mask(
            panel, parent_visible=parent, protected=protected,
        )
        if not np.any(mask):
            raise ValueError("lost material panel")

    output_dir.mkdir(parents=True,exist_ok=True)
    new_json_path = output_dir / "apparel_simplified_subpaths.json"
    png_path = output_dir / "apparel_simplified_preview.png"
    compare_path = output_dir / "apparel_simplified_3way.png"
    candidate = {
        "schema":"sa10.37-apparel-simplified-scene-v1",
        "research_only":True,
        "source_sha256":original_sha,
        "stage36_geometry_sha256":_sha(stage36_dir/"material_grammar_subpaths.json"),
        "stage8_outer_vector_sha256":_sha(stage8_scene),
        "original_outer_primitives":11,
        "apparel_subpaths_before":len(original_panels),
        "apparel_subpaths_after":len(new_panels),
        "apparel_material_polygons":new_panels,
        "source_palette_unchanged":True,
        "protected_regions_frozen":True,
        "browser_svg_verified":False,
    }
    new_json_path.write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if not cv2.imwrite(str(png_path),cv2.cvtColor(next_rgb,cv2.COLOR_RGB2BGR)):
        raise ValueError("unable to save research screenshot")
    board=np.full((h+38,3*w,3),245,np.uint8)
    for idx,(label,rgb) in enumerate((
        ("SOURCE",source_rgb),("PHASE36 APPAREL",prior_rgb),
        ("PHASE37 SIMPLIFIED",next_rgb),
    )):
        board[38:38+h,idx*w:(idx+1)*w]=cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR)
        cv2.putText(board,label,(idx*w+8,25),cv2.FONT_HERSHEY_SIMPLEX,0.44,(20,20,20),1,cv2.LINE_AA)
    cv2.imwrite(str(compare_path),board)
    evidence = {
        **audit,
        "case_source_sha256":original_sha,
        "Stage04_source_masks_verified":True,
        "Stage08_outer_sha_verified":True,
        "Stage36_material_provenance_verified":True,
        "Stage36_original_RGB_pixel_replay_equal":True,
        "original_apparel_color_lab_mse":round(before_mse,6),
        "optimized_apparel_color_lab_mse":round(after_mse,6),
        "apparel_lab_mse_improvement_from_stage36":round(float((before_mse-after_mse)/before_mse),6) if before_mse else 0.0,
        "pixels_modified_outside_lower_body_owner":0,
        "face_left_right_arm_rgb_unchanged":True,
        "existing_outer_primitive_count":len(parent_records),
        "apparel_subpaths_before":len(original_panels),
        "apparel_subpaths_after":len(new_panels),
        "existing_outer_vector_budget_pass":bool(stage8_metrics.get("vertex_budget_pass")),
        "candidate_preview_sha256":_sha(png_path),
        "candidate_geometry_sha256":_sha(new_json_path),
        "source_preview_comparison_sha256":_sha(compare_path),
        "human_visual_gate":"PENDING",
        "SVG_browser_clip_gate":"UNVERIFIED",
        "production_promotion_authorized":False,
        "remaining_blockers":[
            "EXISTING_OUTER_VECTOR_BUDGET_FAILED",
            "BROWSER_SVG_PARITY_UNVERIFIED",
            "HUMAN_VISUAL_SIGNOFF_MISSING",
        ],
    }
    (output_dir/"apparel_simplified_metrics.json").write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":evidence["status"],
        "source":original_sha,
        "vertices_before_after":[audit["original_total_vertices"],audit["candidate_total_vertices"]],
        "resolved_self_crossings":audit.get("baseline_self_intersecting_panels",[]),
        "result_crossings":audit.get("candidate_self_intersecting_panels",[]),
        "owner_lab_mse_improvement":evidence["apparel_lab_mse_improvement_from_stage36"],
        "face_arms_unchanged":True,
        "output":str(output_dir),
    },indent=2,ensure_ascii=False))
    return evidence


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--stage36-dir",required=True,type=Path)
    parser.add_argument("--stage8-dir",required=True,type=Path)
    parser.add_argument("--stage9-dir",required=True,type=Path)
    parser.add_argument("--stage04-dir",required=True,type=Path)
    parser.add_argument("--source",required=True,type=Path)
    parser.add_argument("--output-dir",required=True,type=Path)
    args=parser.parse_args()
    run(stage36_dir=args.stage36_dir,stage8_dir=args.stage8_dir,stage9_dir=args.stage9_dir,
        stage04_dir=args.stage04_dir,source_path=args.source,output_dir=args.output_dir)


if __name__=="__main__":
    main()
