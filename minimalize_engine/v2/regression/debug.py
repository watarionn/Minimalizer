from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Mapping

import cv2
import numpy as np

from minimalize_engine.v2.pipeline import MinimalizerV2Result, SceneModel
from minimalize_engine.v2.primitive.scoring import rasterize_geometry


def _write_rgb(path: Path, rgb: np.ndarray) -> None:
    array = np.asarray(rgb, dtype=np.uint8)
    if array.ndim == 2:
        cv2.imwrite(str(path), array)
    else:
        cv2.imwrite(str(path), cv2.cvtColor(array, cv2.COLOR_RGB2BGR))


def _edge_rgb(edge: np.ndarray) -> np.ndarray:
    gray = np.rint(np.clip(edge, 0.0, 1.0) * 255.0).astype(np.uint8)
    return np.repeat(gray[:, :, None], 3, axis=2)


def _id_color(value: int) -> tuple[int, int, int]:
    return (
        48 + (value * 73) % 192,
        48 + (value * 151) % 192,
        48 + (value * 199) % 192,
    )


def _labels_rgb(labels: np.ndarray) -> np.ndarray:
    height, width = labels.shape
    result = np.zeros((height, width, 3), dtype=np.uint8)
    for region_id in np.unique(labels):
        result[labels == region_id] = _id_color(int(region_id))
    return result
def _palette_image(
    labels: np.ndarray,
    region_to_palette: Mapping[int, int],
    entries,
) -> np.ndarray:
    height, width = labels.shape
    result = np.zeros((height, width, 3), dtype=np.uint8)
    for region_id, palette_id in region_to_palette.items():
        result[labels == region_id] = entries[palette_id].rgb
    return result


def _render_geometry_scene(
    shape: tuple[int, int],
    geometries,
    palette_ids: Mapping[int, int],
    entries,
    visible: Mapping[int, bool] | None = None,
) -> np.ndarray:
    height, width = shape
    canvas = np.full((height, width, 3), 255, dtype=np.uint8)
    for region_id in sorted(geometries):
        if visible is not None and not visible.get(region_id, True):
            continue
        geometry = geometries[region_id]
        mask = rasterize_geometry(
            geometry,
            (height, width),
            origin=(0, 0),
            scale=2,
        )
        canvas[mask] = entries[palette_ids[region_id]].rgb
    return canvas


def _render_scene(scene: SceneModel) -> np.ndarray:
    entries = {entry.palette_id: entry for entry in scene.palette}
    geometries = {shape.region_id: shape.geometry for shape in scene.shapes}
    palette_ids = {shape.region_id: shape.palette_id for shape in scene.shapes}
    visible = {shape.region_id: shape.visible for shape in scene.shapes}
    return _render_geometry_scene(
        (scene.height, scene.width), geometries, palette_ids, entries, visible
    )


def _contour_image(result, preset: str) -> np.ndarray:
    pipeline = result.presets[preset]
    canvas = result.bundle.analysis_rgb.copy()
    for region_id in sorted(pipeline.contour.contours):
        color = _id_color(region_id)
        for loop in pipeline.contour.contours[region_id].loops:
            points = np.rint(loop).astype(np.int32).reshape(-1, 1, 2)
            cv2.polylines(canvas, [points], True, color, 1, cv2.LINE_AA)
    return canvas
def build_decision_summary(
    result: MinimalizerV2Result,
    preset: str,
) -> dict[str, object]:
    pipeline = result.presets[preset]
    primitive_rejections: Counter[str] = Counter()
    for region in pipeline.primitives.primitives.values():
        for candidate in region.candidates:
            primitive_rejections.update(candidate.rejection_reasons)
    budget_protection: Counter[str] = Counter()
    for info in pipeline.detail_budget.shape_info.values():
        budget_protection.update(info.protection_reasons)
    return {
        "preset": preset,
        "region_merge": {
            "initial_regions": result.region_merge.initial_region_count,
            "safe_merges": result.region_merge.safe_merge_count,
            "hierarchy_merges": result.region_merge.hierarchy_merge_count,
            "barrier_counts": dict(result.region_merge.metrics.barrier_counts),
        },
        "hierarchy_cut": {
            "selected_regions": pipeline.selection.cut.region_count,
            "visual_loss": pipeline.selection.cut.visual_loss,
            "objective": pipeline.selection.cut.objective,
            "max_hierarchy_height": pipeline.selection.cut.max_selected_hierarchy_height,
        },
        "contour": {
            "vertices": pipeline.contour.metrics.simplified_vertex_count,
            "rejected_candidates": pipeline.contour.metrics.rejected_candidate_count,
            "fallback_chains": pipeline.contour.metrics.fallback_chain_count,
            "protected_chains": pipeline.contour.metrics.protected_chain_count,
        },
        "primitive": {
            "counts": dict(pipeline.primitives.metrics.primitive_counts),
            "rejection_reasons": dict(sorted(primitive_rejections.items())),
        },
        "palette": {
            "palette_count": pipeline.palette.metrics.palette_count,
            "protected_relationships": pipeline.palette.metrics.protected_relationship_count,
            "repaired_splits": pipeline.palette.metrics.repaired_split_count,
            "relationships": [
                {
                    "regions": [item.region_a, item.region_b],
                    "delta_e": item.original_delta_e,
                    "delta_l": item.original_delta_l,
                    "protection": item.protection,
                    "reasons": list(item.reasons),
                }
                for item in pipeline.palette.relationships
            ],
        },
        "budget": {
            "actions": dict(Counter(pipeline.detail_budget.actions.values())),
            "visual_groups": pipeline.detail_budget.metrics.visual_group_count,
            "protected_shapes": pipeline.detail_budget.metrics.protected_shape_count,
            "protection_reasons": dict(sorted(budget_protection.items())),
            "budget_overflow": pipeline.detail_budget.metrics.budget_overflow,
        },
    }


def build_decision_log(result: MinimalizerV2Result, preset: str) -> dict[str, object]:
    pipeline = result.presets[preset]
    merge_nodes = []
    for node_id in result.region_merge.tree.merge_sequence:
        node = result.region_merge.tree.nodes[node_id]
        merge_nodes.append({
            "region_id": node.region_id,
            "children": [node.left_id, node.right_id],
            "raw_merge_cost": node.raw_merge_cost,
            "hierarchy_height": node.hierarchy_height,
            "stage": node.stage,
        })
    primitive = {}
    for region_id, region in sorted(pipeline.primitives.primitives.items()):
        primitive[str(region_id)] = {
            "selected": region.selected.geometry.kind,
            "objective": region.selected.objective,
            "candidates": [
                {
                    "kind": item.geometry.kind,
                    "eligible": item.eligible,
                    "objective": item.objective,
                    "rejection_reasons": list(item.rejection_reasons),
                }
                for item in region.candidates
            ],
        }
    budget = {}
    for region_id, info in sorted(pipeline.detail_budget.shape_info.items()):
        budget[str(region_id)] = {
            "importance": info.importance,
            "protection_reasons": list(info.protection_reasons),
            "action": pipeline.detail_budget.actions[region_id],
            "fallback_region": pipeline.detail_budget.fallback_region_by_region[region_id],
        }
    return {"preset": preset, "merge_nodes": merge_nodes, "primitive": primitive, "budget": budget}


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def write_debug_artifacts(
    result: MinimalizerV2Result,
    preset: str,
    output_dir: str | Path,
    *,
    level: str = "standard",
    reference_rgb: np.ndarray | None = None,
) -> dict[str, str]:
    if level not in {"none", "summary", "standard", "full"}:
        raise ValueError("unknown debug artifact level")
    if level == "none":
        return {}
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    pipeline = result.presets[preset]
    artifacts: dict[str, str] = {}
    summary = build_decision_summary(result, preset)
    summary_path = out / "decision_summary.json"
    _write_json(summary_path, summary)
    artifacts["summary"] = str(summary_path)
    decision_log_path = out / "decision_log.json"
    _write_json(decision_log_path, build_decision_log(result, preset))
    artifacts["decision_log"] = str(decision_log_path)

    rag_path = out / "rag_summary.json"
    _write_json(
        rag_path,
        {
            "initial_region_count": result.region_merge.initial_region_count,
            "initial_edge_count": result.region_merge.metrics.initial_edge_count,
            "evaluation_count": result.region_merge.metrics.evaluation_count,
            "barrier_counts": dict(result.region_merge.metrics.barrier_counts),
        },
    )
    artifacts["RAG"] = str(rag_path)
    hierarchy_path = out / "merge_hierarchy.json"
    _write_json(
        hierarchy_path,
        {
            "leaf_count": len(result.region_merge.tree.leaf_ids),
            "node_count": len(result.region_merge.tree.nodes),
            "root_ids": sorted(result.region_merge.tree.roots),
            "merge_sequence": list(result.region_merge.tree.merge_sequence),
        },
    )
    artifacts["Merge Hierarchy"] = str(hierarchy_path)
    if level == "summary":
        return artifacts

    images = {
        "Source": result.bundle.source_rgb,
        "Analysis": result.bundle.analysis_rgb,
        "Structural": result.bundle.structural_rgb,
        "Raw Edge": _edge_rgb(result.bundle.edge_raw),
        "Structural Edge": _edge_rgb(result.bundle.edge_structural),
        "Superpixels": _labels_rgb(result.region_merge.initial_labels),
        "Hierarchy Cut": _labels_rgb(pipeline.selection.labels),
        "Merged Regions": _labels_rgb(pipeline.selection.labels),
        "Contour": _contour_image(result, preset),
    }
    geometries = {
        region_id: item.selected.geometry
        for region_id, item in pipeline.primitives.primitives.items()
    }
    images["Primitive"] = _render_geometry_scene(
        pipeline.selection.labels.shape,
        geometries,
        pipeline.palette.region_to_palette,
        pipeline.palette.entries,
    )
    images["Palette"] = _palette_image(
        pipeline.selection.labels,
        pipeline.palette.region_to_palette,
        pipeline.palette.entries,
    )
    images["Budget"] = _palette_image(
        pipeline.selection.labels,
        pipeline.detail_budget.effective_palette_by_region,
        pipeline.palette.entries,
    )
    images["Final"] = _render_scene(pipeline.scene)
    if reference_rgb is not None:
        reference = np.asarray(reference_rgb, dtype=np.uint8)
        if reference.ndim != 3 or reference.shape[2] != 3:
            raise ValueError("reference_rgb must have shape (H, W, 3)")
        images["Reference"] = reference

    for name, image in images.items():
        filename = name.casefold().replace(" ", "_") + ".png"
        path = out / filename
        _write_rgb(path, image)
        artifacts[name] = str(path)

    if level == "full":
        initial_path = out / "initial_labels.npy"
        selected_path = out / "selected_labels.npy"
        np.save(initial_path, result.region_merge.initial_labels)
        np.save(selected_path, pipeline.selection.labels)
        artifacts["initial_labels"] = str(initial_path)
        artifacts["selected_labels"] = str(selected_path)
    return artifacts
