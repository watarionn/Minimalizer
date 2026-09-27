from __future__ import annotations

import argparse
import json
from pathlib import Path
from time import perf_counter

import cv2
import numpy as np
from PIL import Image

from local_worker import app as worker
from minimalize_engine.v2 import (
    PipelineConfig,
    ShadingFlattenConfig,
    ShadingFlattenGuardConfig,
    export_png,
    minimalize_v2,
)
from minimalize_engine.v2.pipeline import LayeredPersonConfig
import minimalize_engine.v2.pipeline as pipeline


def parse_orders(value: str | None) -> set[int] | None:
    if not value:
        return None
    selected: set[int] = set()
    for token in value.split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            start, end = token.split("-", 1)
            selected.update(range(int(start), int(end) + 1))
        else:
            selected.add(int(token))
    return selected


def visible_complexity(scene) -> tuple[int, int]:
    visible = [shape for shape in scene.shapes if shape.visible]
    vertices = 0
    for shape in visible:
        if shape.geometry.kind == "polygon":
            vertices += sum(len(loop) for loop in shape.geometry.loops)
    return len(visible), vertices


def polygon_structure(scene) -> dict[str, int]:
    visible = [shape for shape in scene.shapes if shape.visible]
    polygons = [shape for shape in visible if shape.geometry.kind == "polygon"]
    polygon_vertex_counts = [
        sum(len(loop) for loop in shape.geometry.loops)
        for shape in polygons
    ]
    loop_vertex_counts = [
        len(loop)
        for shape in polygons
        for loop in shape.geometry.loops
    ]
    return {
        "polygon_shapes": len(polygons),
        "max_polygon_vertices": max(polygon_vertex_counts, default=0),
        "max_loop_vertices": max(loop_vertex_counts, default=0),
        "max_loops_per_polygon": max(
            (len(shape.geometry.loops) for shape in polygons),
            default=0,
        ),
        "multi_loop_shapes": sum(
            len(shape.geometry.loops) > 1 for shape in polygons
        ),
    }


def load_rgb_for_metric(path: Path, size: int = 128) -> np.ndarray:
    with Image.open(path) as image:
        rgba = image.convert("RGBA")
        white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        rgb = Image.alpha_composite(white, rgba).convert("RGB")
    array = np.asarray(rgb, dtype=np.uint8)
    return cv2.resize(array, (size, size), interpolation=cv2.INTER_AREA)


def diagnostic_similarity(output_path: Path, approved_path: Path) -> dict[str, float]:
    output = load_rgb_for_metric(output_path)
    approved = load_rgb_for_metric(approved_path)

    output_blur = cv2.GaussianBlur(output, (9, 9), 0).astype(np.float32)
    approved_blur = cv2.GaussianBlur(approved, (9, 9), 0).astype(np.float32)
    mae = float(np.abs(output_blur - approved_blur).mean() / 255.0)
    color_similarity = max(0.0, 1.0 - mae)

    output_gray = cv2.cvtColor(output, cv2.COLOR_RGB2GRAY)
    approved_gray = cv2.cvtColor(approved, cv2.COLOR_RGB2GRAY)
    output_edges = cv2.Canny(output_gray, 70, 150) > 0
    approved_edges = cv2.Canny(approved_gray, 70, 150) > 0
    union = int(np.logical_or(output_edges, approved_edges).sum())
    edge_iou = (
        float(np.logical_and(output_edges, approved_edges).sum() / union)
        if union
        else 1.0
    )
    return {
        "color_similarity": color_similarity,
        "edge_iou": edge_iou,
        "edge_density_delta": abs(
            float(output_edges.mean()) - float(approved_edges.mean())
        ),
    }


def production_config(*, pathological_polygon_decimation: bool = True) -> PipelineConfig:
    return PipelineConfig(
        analysis_max_side=worker.ANALYSIS_MAX_SIDE,
        shading_flatten=ShadingFlattenConfig(
            enabled=worker.SHADING_FLATTEN_ENABLED,
            sr=worker.SHADING_FLATTEN_SR,
            hierarchical_parts=True,
        ),
        shading_flatten_guard=ShadingFlattenGuardConfig(
            enabled=worker.SHADING_FLATTEN_GUARD,
        ),
        layered_person=LayeredPersonConfig(
            enabled=True,
            semantic_geometric_mass=worker.GEOMETRIC_MASS_ENABLED,
            pathological_polygon_decimation=pathological_polygon_decimation,
        ),
    )
def run_observed(source_rgb, guidance, *, pathological_polygon_decimation: bool = True):
    events: list[dict[str, object]] = []
    current_part: dict[str, str | None] = {"name": None}
    original_build = pipeline._build_semantic_geometric_mass
    original_final = pipeline._semantic_geometric_mass_final_is_simpler

    def observed_build(baseline, *, part_name, part_mask):
        current_part["name"] = part_name
        return original_build(
            baseline,
            part_name=part_name,
            part_mask=part_mask,
        )

    def observed_final(baseline, candidate, **kwargs):
        before_shapes, before_vertices = visible_complexity(baseline.scene)
        after_shapes, after_vertices = visible_complexity(candidate.scene)
        accepted = original_final(baseline, candidate, **kwargs)
        events.append(
            {
                "part": current_part["name"],
                "accepted": bool(accepted),
                "before_shapes": before_shapes,
                "after_shapes": after_shapes,
                "before_vertices": before_vertices,
                "after_vertices": after_vertices,
                "vertex_savings": before_vertices - after_vertices,
            }
        )
        return accepted

    pipeline._build_semantic_geometric_mass = observed_build
    pipeline._semantic_geometric_mass_final_is_simpler = observed_final
    try:
        result = minimalize_v2(
            source_rgb,
            presets=("minimal",),
            config=production_config(pathological_polygon_decimation=pathological_polygon_decimation),
            guidance=guidance,
        )
    finally:
        pipeline._build_semantic_geometric_mass = original_build
        pipeline._semantic_geometric_mass_final_is_simpler = original_final

    return result, events


def percentile_ranks(values: list[float], *, higher_is_worse: bool = True) -> list[float]:
    if not values:
        return []
    arr = np.asarray(values, dtype=np.float64)
    order = np.argsort(arr, kind="stable")
    ranks = np.empty(len(arr), dtype=np.float64)
    if len(arr) == 1:
        ranks[:] = 0.0
    else:
        ranks[order] = np.linspace(0.0, 1.0, len(arr))
    if not higher_is_worse:
        ranks = 1.0 - ranks
    return [float(value) for value in ranks]


def update_rankings(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    clean = [row for row in rows if "error" not in row]
    if not clean:
        return rows

    metrics = {
        "part_vertices_rank": (
            [float(row["part_polygon_vertices"]) for row in clean],
            True,
        ),
        "part_shapes_rank": (
            [float(row["part_visible_shapes"]) for row in clean],
            True,
        ),
        "color_error_rank": (
            [float(row["color_similarity"]) for row in clean],
            False,
        ),
        "edge_iou_error_rank": (
            [float(row["edge_iou"]) for row in clean],
            False,
        ),
        "edge_density_rank": (
            [float(row["edge_density_delta"]) for row in clean],
            True,
        ),
    }
    rank_columns: dict[str, list[float]] = {}
    for name, (values, higher_is_worse) in metrics.items():
        rank_columns[name] = percentile_ranks(
            values,
            higher_is_worse=higher_is_worse,
        )

    for index, row in enumerate(clean):
        for name, values in rank_columns.items():
            row[name] = values[index]

        fragmentation = (
            0.65 * row["part_vertices_rank"]
            + 0.35 * row["part_shapes_rank"]
        )
        reference_divergence = (
            0.45 * row["color_error_rank"]
            + 0.35 * row["edge_iou_error_rank"]
            + 0.20 * row["edge_density_rank"]
        )
        row["fragmentation_score"] = float(fragmentation)
        row["reference_divergence_score"] = float(reference_divergence)
        row["priority_score"] = float(
            0.60 * fragmentation + 0.40 * reference_divergence
        )
        row["stagnation"] = bool(
            row["priority_score"] >= 0.60
            and not row["shading_flatten_accepted"]
            and row["geometry_accepted_events"] == 0
        )

    return rows


def write_checkpoint(path: Path, rows: list[dict[str, object]]) -> None:
    update_rankings(rows)
    clean = [row for row in rows if "error" not in row]
    ranking = sorted(
        clean,
        key=lambda row: float(row.get("priority_score", 0.0)),
        reverse=True,
    )
    payload = {
        "schema": "production-quality-scan-v1",
        "cases": len(rows),
        "errors": sum("error" in row for row in rows),
        "shading_accepted_cases": sum(
            bool(row.get("shading_flatten_accepted")) for row in clean
        ),
        "geometry_accepted_cases": sum(
            int(row.get("geometry_accepted_events", 0)) > 0 for row in clean
        ),
        "stagnation_cases": sum(bool(row.get("stagnation")) for row in clean),
        "top_priority": [
            {
                "order": row["order"],
                "character": row["character"],
                "priority_score": row.get("priority_score"),
                "fragmentation_score": row.get("fragmentation_score"),
                "reference_divergence_score": row.get("reference_divergence_score"),
                "part_polygon_vertices": row["part_polygon_vertices"],
                "part_visible_shapes": row["part_visible_shapes"],
                "color_similarity": row["color_similarity"],
                "edge_iou": row["edge_iou"],
                "edge_density_delta": row["edge_density_delta"],
                "shading_flatten_accepted": row["shading_flatten_accepted"],
                "shading_flatten_reasons": row["shading_flatten_reasons"],
                "geometry_accepted_events": row["geometry_accepted_events"],
                "stagnation": row.get("stagnation", False),
            }
            for row in ranking[:15]
        ],
        "rows": rows,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
def audit_case(
    *,
    input_path: Path,
    approved_path: Path,
    output_path: Path,
    pathological_polygon_decimation: bool = True,
) -> dict[str, object]:
    guidance_started = perf_counter()
    source_rgb, guidance, selection = worker._build_guidance(input_path)
    guidance_seconds = perf_counter() - guidance_started

    pipeline_started = perf_counter()
    result, geometry_events = run_observed(
        source_rgb,
        guidance,
        pathological_polygon_decimation=pathological_polygon_decimation,
    )
    pipeline_seconds = perf_counter() - pipeline_started

    exported = export_png(
        result,
        preset="minimal",
        include_facets=True,
        preserve_source_alpha=True,
        filename=output_path.name,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(exported.content)

    global_shapes, global_vertices = visible_complexity(
        result.presets["minimal"].scene
    )
    part_shapes = 0
    part_vertices = 0
    part_metrics: dict[str, dict[str, int]] = {}
    for name, presets in result.person_part_presets.items():
        scene = presets["minimal"].scene
        shapes, vertices = visible_complexity(scene)
        part_shapes += shapes
        part_vertices += vertices
        part_metrics[name] = {
            "visible_shapes": shapes,
            "polygon_vertices": vertices,
            **polygon_structure(scene),
        }

    accepted_geometry = [
        event for event in geometry_events if event["accepted"]
    ]
    similarity = diagnostic_similarity(output_path, approved_path)
    shading = result.shading_flatten_decision

    with Image.open(output_path) as image:
        rgba = np.asarray(image.convert("RGBA"))
        alpha = rgba[..., 3]

    return {
        "rtmlib_selected": selection is not None,
        "guidance_seconds": guidance_seconds,
        "pipeline_seconds": pipeline_seconds,
        "initial_regions": int(result.region_merge.initial_region_count),
        "selected_regions": len(
            result.presets["minimal"].selection.region_ids
        ),
        "global_visible_shapes": global_shapes,
        "global_polygon_vertices": global_vertices,
        "part_visible_shapes": part_shapes,
        "part_polygon_vertices": part_vertices,
        "part_metrics": part_metrics,
        "palette_count": len(result.presets["minimal"].scene.palette),
        "shading_flatten_evaluated": shading is not None,
        "shading_flatten_accepted": (
            bool(shading.accepted) if shading is not None else False
        ),
        "shading_flatten_reasons": (
            list(shading.reasons) if shading is not None else []
        ),
        "geometry_guard_events": geometry_events,
        "geometry_accepted_events": len(accepted_geometry),
        "geometry_vertex_savings": sum(
            int(event["vertex_savings"]) for event in accepted_geometry
        ),
        "preserves_source_alpha": exported.metadata.preserves_source_alpha,
        "transparent_fraction": float((alpha == 0).mean()),
        "partial_alpha_fraction": float(
            ((alpha > 0) & (alpha < 255)).mean()
        ),
        "pixel_sha256": exported.metadata.pixel_sha256,
        **similarity,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--orders")
    parser.add_argument("--images-dir", type=Path)
    parser.add_argument("--disable-pathological-polygon-decimation", action="store_true")
    args = parser.parse_args()

    manifest = json.loads(
        (args.corpus / "manifest.json").read_text(encoding="utf-8")
    )
    selected = parse_orders(args.orders)
    cases = [
        case
        for case in manifest["cases"]
        if int(case["order"]) < 59 or int(case["order"]) > 68
    ]
    if selected is not None:
        cases = [
            case for case in cases
            if int(case["order"]) in selected
        ]

    images_dir = args.images_dir or args.output.with_suffix("")
    rows: list[dict[str, object]] = []

    for index, case in enumerate(cases, 1):
        order = int(case["order"])
        character = str(case["character"])
        input_path = args.corpus / "inputs" / case["input_file"]
        approved_path = args.corpus / "references" / case["approved_file"]
        output_path = images_dir / f"{order:02d}_{character}.png"
        started = perf_counter()
        print(f"[{index}/{len(cases)}] {order:02d} {character}", flush=True)
        try:
            row = audit_case(
                input_path=input_path,
                approved_path=approved_path,
                output_path=output_path,
                pathological_polygon_decimation=not args.disable_pathological_polygon_decimation,
            )
            row.update(
                order=order,
                character=character,
                input_file=case["input_file"],
                approved_file=case["approved_file"],
                elapsed_s=round(perf_counter() - started, 3),
            )
        except Exception as exc:
            row = {
                "order": order,
                "character": character,
                "input_file": case["input_file"],
                "approved_file": case["approved_file"],
                "error": f"{type(exc).__name__}: {exc}",
                "elapsed_s": round(perf_counter() - started, 3),
            }
        rows.append(row)
        write_checkpoint(args.output, rows)
        print(
            "  part_vertices="
            f"{row.get('part_polygon_vertices')} "
            f"part_shapes={row.get('part_visible_shapes')} "
            f"color={row.get('color_similarity')} "
            f"edge={row.get('edge_iou')} "
            f"shading={row.get('shading_flatten_accepted')} "
            f"geometry={row.get('geometry_accepted_events')} "
            f"elapsed={row.get('elapsed_s')}s",
            flush=True,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
