from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from minimalize_engine import MinimalizeConfig, minimalize, minimalize_rinka_reference
from minimalize_engine.io.image_exporter import export_png
from minimalize_engine.io.svg_exporter import export_svg


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Compare stable Minimalizer output with the current Rinka Reference target style."
    )
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--end", type=int)
    p.add_argument("--max-side", type=int, default=320)
    p.add_argument("--level", type=int, default=4)
    p.add_argument("--target-palette", type=int)
    p.add_argument("--target-epsilon", type=float)
    p.add_argument("--target-shapes", type=int)
    p.add_argument(
        "--output-dir",
        default="examples/rinka_target_phase2",
        help="Path relative to the repository root unless absolute.",
    )
    return p


def _vertex_count(shape) -> int:
    if shape.shape_type == "polygon":
        return len(shape.points)
    if shape.shape_type == "rectangle":
        return 4
    if shape.shape_type in {"circle", "ellipse"}:
        return 4
    if shape.shape_type == "line":
        return len(shape.points) if shape.points else 2
    return len(shape.points)


def _scene_vertices(scene) -> int:
    return sum(_vertex_count(shape) for shape in scene.shapes)


def _ratio(before: int, after: int) -> float:
    if before <= 0:
        return 0.0
    return (before - after) / before


def _delta(before, after):
    if before is None or after is None:
        return None
    return float(after) - float(before)


def main() -> None:
    args = _parser().parse_args()
    root = ROOT
    corpus = root / "tests" / "assets" / "corpus"
    out = Path(args.output_dir)
    if not out.is_absolute():
        out = root / out
    out.mkdir(parents=True, exist_ok=True)

    target_overrides = {"analysis_max_side": args.max_side}
    if args.target_palette is not None:
        target_overrides["palette_colors"] = args.target_palette
    if args.target_epsilon is not None:
        target_overrides["contour_epsilon_ratio"] = args.target_epsilon
    if args.target_shapes is not None:
        target_overrides["target_max_shapes"] = args.target_shapes

    files = sorted(p for p in corpus.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES)
    subset = files[args.start : args.end]
    rows: list[dict] = []

    for path in subset:
        stable_config = MinimalizeConfig.from_level(
            args.level,
            analysis_max_side=args.max_side,
            enable_auto_retry=False,
            enable_character_auto_retry=False,
        )
        stable = minimalize(path, stable_config)
        target = minimalize_rinka_reference(path, args.level, **target_overrides)

        stem = path.stem
        export_png(stable, out / f"{stem}_stable.png")
        export_png(target, out / f"{stem}_rinka_target.png")
        export_svg(target, out / f"{stem}_rinka_target.svg")

        stable_shapes = len(stable.shapes)
        target_shapes = len(target.shapes)
        stable_vertices = _scene_vertices(stable)
        target_vertices = _scene_vertices(target)
        stable_quality = stable.metadata.get("quality", {})
        target_quality = target.metadata.get("quality", {})
        target_meta = target.metadata.get("target_style", {})
        cleanup = target_meta.get("cleanup", {})
        hierarchy = target_meta.get("opaque_hierarchy", {})
        zones = target_meta.get("opaque_zones", {})
        gesture = target_meta.get("gesture_abstraction", {})
        stable_identity = stable_quality.get("identity_score")
        target_identity = target_quality.get("identity_score")
        stable_silhouette = stable_quality.get("silhouette_similarity")
        target_silhouette = target_quality.get("silhouette_similarity")
        zone_source = zones.get("zone_source", zones.get("reason", "none"))
        subject_zones_enabled = bool(zones.get("enabled", False))
        structure_zones_enabled = subject_zones_enabled and zone_source == "character_structure"
        opaque_zones_enabled = subject_zones_enabled and zone_source == "accepted"

        row = {
            "file": path.name,
            "scene_mode": "subject" if stable.metadata.get("subject_mode") else "general",
            "target_style_version": target_meta.get("version"),
            "stable_shapes": stable_shapes,
            "target_shapes": target_shapes,
            "shape_reduction_ratio": round(_ratio(stable_shapes, target_shapes), 6),
            "stable_vertices": stable_vertices,
            "target_vertices": target_vertices,
            "vertex_reduction_ratio": round(_ratio(stable_vertices, target_vertices), 6),
            "target_cleanup_removed": cleanup.get("removed_count", 0),
            "target_cleanup_removed_thin": cleanup.get("removed_thin", 0),
            "target_cleanup_removed_micro": cleanup.get("removed_micro", 0),
            "target_cleanup_removed_isolated": cleanup.get("removed_isolated", 0),
            "target_structure_redundant_removed": target_meta.get("structure_redundant_removed", 0),
            "target_outfit_layer_merges": target_meta.get("outfit_layer_merges", 0),
            "target_gesture_simplified_shapes": gesture.get("simplified_shapes", 0),
            "target_gesture_vertices_removed": gesture.get("vertices_removed", 0),
            "target_gesture_anchored_simplifications": gesture.get("anchored_simplifications", 0),
            "target_gesture_hand_anchors": gesture.get("hand_anchors", 0),
            "target_face_fragments_removed": target_meta.get("face_fragments_removed", 0),
            "target_mass_merges": target_meta.get("mass_merges", 0),
            "target_background_removed": target_meta.get("background_removed", 0),
            "target_cap_removed": target_meta.get("cap_removed", 0),
            "opaque_hierarchy_enabled": bool(hierarchy.get("enabled", False)),
            "opaque_hierarchy_confidence": hierarchy.get("confidence", 0.0),
            "opaque_subject_area_ratio": hierarchy.get("subject_area_ratio", 0.0),
            "opaque_subject_shapes": hierarchy.get("subject_shapes", 0),
            "opaque_background_shapes": hierarchy.get("background_shapes", 0),
            "subject_zones_enabled": subject_zones_enabled,
            "subject_zone_source": zone_source,
            "subject_zone_shapes": zones.get("zone_shapes", 0),
            "structure_zones_enabled": structure_zones_enabled,
            "structure_zone_shapes": zones.get("zone_shapes", 0) if structure_zones_enabled else 0,
            "opaque_zones_enabled": opaque_zones_enabled,
            "opaque_zones_confidence": zones.get("confidence", 0.0) if opaque_zones_enabled else 0.0,
            "opaque_zone_shapes": zones.get("zone_shapes", 0) if opaque_zones_enabled else 0,
            "opaque_head_shapes": zones.get("head_shapes", 0) if opaque_zones_enabled else 0,
            "opaque_torso_shapes": zones.get("torso_shapes", 0) if opaque_zones_enabled else 0,
            "opaque_arm_shapes": zones.get("arm_shapes", 0) if opaque_zones_enabled else 0,
            "opaque_leg_shapes": zones.get("leg_shapes", 0) if opaque_zones_enabled else 0,
            "opaque_hair_shapes": zones.get("hair_shapes", 0) if opaque_zones_enabled else 0,
            "opaque_clothing_shapes": zones.get("clothing_shapes", 0) if opaque_zones_enabled else 0,
            "opaque_inferred_hair_shapes": zones.get("inferred_hair_shapes", 0) if opaque_zones_enabled else 0,
            "opaque_inferred_hair_mode": zones.get("inferred_hair_mode", "none") if opaque_zones_enabled else "none",
            "opaque_inferred_clothing_shapes": zones.get("inferred_clothing_shapes", 0) if opaque_zones_enabled else 0,
            "opaque_propagated_clothing_shapes": zones.get("propagated_clothing_shapes", 0) if opaque_zones_enabled else 0,
            "opaque_face_reference_source": zones.get("face_reference_source", "none") if opaque_zones_enabled else "none",
            "stable_quality": stable_quality.get("score"),
            "stable_identity": stable_identity,
            "stable_silhouette": stable_silhouette,
            "stable_minimality": stable_quality.get("minimality_score"),
            "target_pre_quality": target_quality.get("score"),
            "target_pre_identity": target_identity,
            "target_pre_silhouette": target_silhouette,
            "target_pre_minimality": target_quality.get("minimality_score"),
            "target_pre_identity_delta": _delta(stable_identity, target_identity),
            "target_pre_silhouette_delta": _delta(stable_silhouette, target_silhouette),
        }
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)

    suffix = f"{args.start}_{args.end if args.end is not None else 'end'}"
    json_path = out / f"report_{suffix}.json"
    csv_path = out / f"report_{suffix}.csv"
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    if rows:
        with csv_path.open("w", newline="", encoding="utf-8-sig") as fp:
            writer = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        identity_deltas = [r["target_pre_identity_delta"] for r in rows if r["target_pre_identity_delta"] is not None]
        silhouette_deltas = [r["target_pre_silhouette_delta"] for r in rows if r["target_pre_silhouette_delta"] is not None]
        summary = {
            "count": len(rows),
            "target_style_version": rows[0].get("target_style_version"),
            "target_overrides": target_overrides,
            "mean_shape_reduction_ratio": mean(r["shape_reduction_ratio"] for r in rows),
            "mean_vertex_reduction_ratio": mean(r["vertex_reduction_ratio"] for r in rows),
            "mean_target_pre_identity_delta": mean(identity_deltas) if identity_deltas else None,
            "worst_target_pre_identity_delta": min(identity_deltas) if identity_deltas else None,
            "mean_target_pre_silhouette_delta": mean(silhouette_deltas) if silhouette_deltas else None,
            "worst_target_pre_silhouette_delta": min(silhouette_deltas) if silhouette_deltas else None,
            "total_target_cleanup_removed": sum(r["target_cleanup_removed"] for r in rows),
            "total_target_structure_redundant_removed": sum(r["target_structure_redundant_removed"] for r in rows),
            "total_target_outfit_layer_merges": sum(r["target_outfit_layer_merges"] for r in rows),
            "total_target_gesture_simplified_shapes": sum(r["target_gesture_simplified_shapes"] for r in rows),
            "total_target_gesture_vertices_removed": sum(r["target_gesture_vertices_removed"] for r in rows),
            "total_target_gesture_anchored_simplifications": sum(r["target_gesture_anchored_simplifications"] for r in rows),
            "total_target_gesture_hand_anchors": sum(r["target_gesture_hand_anchors"] for r in rows),
            "total_target_face_fragments_removed": sum(r["target_face_fragments_removed"] for r in rows),
            "total_target_mass_merges": sum(r["target_mass_merges"] for r in rows),
            "total_target_background_removed": sum(r["target_background_removed"] for r in rows),
            "total_target_cap_removed": sum(r["target_cap_removed"] for r in rows),
            "opaque_hierarchy_enabled_count": sum(1 for r in rows if r["opaque_hierarchy_enabled"]),
            "mean_opaque_hierarchy_confidence": mean(r["opaque_hierarchy_confidence"] for r in rows if r["opaque_hierarchy_enabled"]) if any(r["opaque_hierarchy_enabled"] for r in rows) else 0.0,
            "total_opaque_subject_shapes": sum(r["opaque_subject_shapes"] for r in rows),
            "total_opaque_background_shapes": sum(r["opaque_background_shapes"] for r in rows),
            "subject_zones_enabled_count": sum(1 for r in rows if r["subject_zones_enabled"]),
            "structure_zones_enabled_count": sum(1 for r in rows if r["structure_zones_enabled"]),
            "total_subject_zone_shapes": sum(r["subject_zone_shapes"] for r in rows),
            "total_structure_zone_shapes": sum(r["structure_zone_shapes"] for r in rows),
            "opaque_zones_enabled_count": sum(1 for r in rows if r["opaque_zones_enabled"]),
            "mean_opaque_zones_confidence": mean(r["opaque_zones_confidence"] for r in rows if r["opaque_zones_enabled"]) if any(r["opaque_zones_enabled"] for r in rows) else 0.0,
            "total_opaque_zone_shapes": sum(r["opaque_zone_shapes"] for r in rows),
            "total_opaque_head_shapes": sum(r["opaque_head_shapes"] for r in rows),
            "total_opaque_torso_shapes": sum(r["opaque_torso_shapes"] for r in rows),
            "total_opaque_arm_shapes": sum(r["opaque_arm_shapes"] for r in rows),
            "total_opaque_leg_shapes": sum(r["opaque_leg_shapes"] for r in rows),
            "total_opaque_hair_shapes": sum(r["opaque_hair_shapes"] for r in rows),
            "total_opaque_clothing_shapes": sum(r["opaque_clothing_shapes"] for r in rows),
            "total_opaque_inferred_hair_shapes": sum(r["opaque_inferred_hair_shapes"] for r in rows),
            "opaque_geometry_hair_count": sum(1 for r in rows if r["opaque_inferred_hair_mode"] == "geometry_contrast"),
            "total_opaque_inferred_clothing_shapes": sum(r["opaque_inferred_clothing_shapes"] for r in rows),
            "total_opaque_propagated_clothing_shapes": sum(r["opaque_propagated_clothing_shapes"] for r in rows),
            "opaque_face_reference_count": sum(1 for r in rows if r["opaque_face_reference_source"] != "none"),
            "quality_note": "target_pre_* metrics are measured before the target-style post-process",
        }
        (out / f"summary_{suffix}.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
