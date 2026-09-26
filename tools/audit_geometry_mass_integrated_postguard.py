from __future__ import annotations

import argparse
import json
from pathlib import Path
from time import perf_counter

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


def scene_complexity(scene) -> tuple[int, int]:
    visible = [shape for shape in scene.shapes if shape.visible]
    vertices = 0
    for shape in visible:
        if shape.geometry.kind == "polygon":
            vertices += sum(len(loop) for loop in shape.geometry.loops)
    return len(visible), vertices


def preset_complexity(preset_result) -> tuple[int, int]:
    return scene_complexity(preset_result.scene)


def part_complexities(result) -> dict[str, dict[str, int]]:
    values: dict[str, dict[str, int]] = {}
    for name, presets in result.person_part_presets.items():
        shapes, vertices = scene_complexity(presets["minimal"].scene)
        values[name] = {
            "visible_shapes": shapes,
            "polygon_vertices": vertices,
        }
    return values
def make_config(*, geometry_mass: bool) -> PipelineConfig:
    return PipelineConfig(
        analysis_max_side=worker.ANALYSIS_MAX_SIDE,
        shading_flatten=ShadingFlattenConfig(
            enabled=True,
            sr=worker.SHADING_FLATTEN_SR,
            hierarchical_parts=True,
        ),
        shading_flatten_guard=ShadingFlattenGuardConfig(enabled=True),
        layered_person=LayeredPersonConfig(
            enabled=True,
            semantic_geometric_mass=geometry_mass,
        ),
    )


def summarize_result(result, exported) -> dict[str, object]:
    global_shapes, global_vertices = scene_complexity(
        result.presets["minimal"].scene
    )
    parts = part_complexities(result)
    return {
        "global_visible_shapes": global_shapes,
        "global_polygon_vertices": global_vertices,
        "part_visible_shapes": sum(v["visible_shapes"] for v in parts.values()),
        "part_polygon_vertices": sum(v["polygon_vertices"] for v in parts.values()),
        "parts": parts,
        "shading_flatten_evaluated": result.shading_flatten_decision is not None,
        "shading_flatten_accepted": (
            bool(result.shading_flatten_decision.accepted)
            if result.shading_flatten_decision is not None
            else False
        ),
        "shading_flatten_reasons": (
            list(result.shading_flatten_decision.reasons)
            if result.shading_flatten_decision is not None
            else []
        ),
        "pixel_sha256": exported.metadata.pixel_sha256,
        "png_sha256": exported.metadata.png_sha256,
        "preserves_source_alpha": exported.metadata.preserves_source_alpha,
    }


def run_variant(source_rgb, guidance, *, geometry_mass: bool):
    result = minimalize_v2(
        source_rgb,
        presets=("minimal",),
        config=make_config(geometry_mass=geometry_mass),
        guidance=guidance,
    )
    exported = export_png(
        result,
        preset="minimal",
        include_facets=True,
        preserve_source_alpha=True,
    )
    return result, exported, summarize_result(result, exported)
def run_geometry_mass_observed(source_rgb, guidance):
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
        before_shapes, before_vertices = preset_complexity(baseline)
        after_shapes, after_vertices = preset_complexity(candidate)
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
        result, exported, summary = run_variant(
            source_rgb,
            guidance,
            geometry_mass=True,
        )
    finally:
        pipeline._build_semantic_geometric_mass = original_build
        pipeline._semantic_geometric_mass_final_is_simpler = original_final

    return result, exported, summary, events


def part_deltas(before: dict, after: dict) -> dict[str, dict[str, int]]:
    names = sorted(set(before) | set(after))
    deltas: dict[str, dict[str, int]] = {}
    for name in names:
        left = before.get(name, {"visible_shapes": 0, "polygon_vertices": 0})
        right = after.get(name, {"visible_shapes": 0, "polygon_vertices": 0})
        shape_delta = right["visible_shapes"] - left["visible_shapes"]
        vertex_delta = right["polygon_vertices"] - left["polygon_vertices"]
        if shape_delta or vertex_delta:
            deltas[name] = {
                "shape_delta": shape_delta,
                "vertex_delta": vertex_delta,
                "vertex_savings": -vertex_delta,
            }
    return deltas
def write_checkpoint(path: Path, rows: list[dict[str, object]]) -> None:
    changed = [row for row in rows if row.get("changed")]
    payload = {
        "schema": "geometry-mass-integrated-post-final-guard-v2",
        "cases": len(rows),
        "changed_cases": len(changed),
        "candidate_cases": sum(
            bool(row.get("geometry_final_guard_accepted_events"))
            for row in rows
        ),
        "total_part_vertex_savings": sum(
            int(row.get("part_vertex_savings", 0)) for row in changed
        ),
        "rows": rows,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def audit_case(input_path: Path, case_dir: Path) -> dict[str, object]:
    source_rgb, guidance, selection = worker._build_guidance(input_path)

    mass_result, mass_png, mass, events = run_geometry_mass_observed(
        source_rgb,
        guidance,
    )
    accepted_events = [event for event in events if event["accepted"]]

    if not accepted_events:
        # Geometry Mass only replaces a cleaned part scene after this final
        # guard returns True. With zero accepted events, the Geometry-ON result
        # is definitionally the same final pipeline as Geometry-OFF, so avoid
        # a second full Shading-Guard execution.
        baseline = dict(mass)
        return {
            "rtmlib_selected": selection is not None,
            "changed": False,
            "baseline": baseline,
            "geometry_mass": mass,
            "geometry_final_guard_events": events,
            "geometry_final_guard_accepted_events": [],
            "baseline_inferred_from_no_accept": True,
            "part_deltas": {},
            "global_vertex_savings": 0,
            "part_vertex_savings": 0,
            "shading_decision_changed": False,
        }

    baseline_result, baseline_png, baseline = run_variant(
        source_rgb,
        guidance,
        geometry_mass=False,
    )

    changed = baseline["pixel_sha256"] != mass["pixel_sha256"]
    deltas = part_deltas(baseline["parts"], mass["parts"])

    if changed:
        case_dir.mkdir(parents=True, exist_ok=True)
        (case_dir / "baseline.png").write_bytes(baseline_png.content)
        (case_dir / "geometry_mass.png").write_bytes(mass_png.content)

    return {
        "rtmlib_selected": selection is not None,
        "changed": changed,
        "baseline": baseline,
        "geometry_mass": mass,
        "geometry_final_guard_events": events,
        "geometry_final_guard_accepted_events": accepted_events,
        "baseline_inferred_from_no_accept": False,
        "part_deltas": deltas,
        "global_vertex_savings": (
            baseline["global_polygon_vertices"] - mass["global_polygon_vertices"]
        ),
        "part_vertex_savings": (
            baseline["part_polygon_vertices"] - mass["part_polygon_vertices"]
        ),
        "shading_acceptance_changed": (
            baseline["shading_flatten_accepted"]
            != mass["shading_flatten_accepted"]
        ),
        "shading_reasons_changed": (
            baseline["shading_flatten_reasons"]
            != mass["shading_flatten_reasons"]
        ),
        "shading_decision_changed": (
            baseline["shading_flatten_accepted"]
            != mass["shading_flatten_accepted"]
            or baseline["shading_flatten_reasons"]
            != mass["shading_flatten_reasons"]
        ),
    }
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--orders")
    parser.add_argument("--images-dir", type=Path)
    args = parser.parse_args()

    selected = parse_orders(args.orders)
    manifest = json.loads(
        (args.corpus / "manifest.json").read_text(encoding="utf-8")
    )
    cases = [
        case
        for case in manifest["cases"]
        if case["order"] < 59 or case["order"] > 68
    ]
    if selected is not None:
        cases = [case for case in cases if case["order"] in selected]

    images_dir = args.images_dir or args.output.with_suffix("")
    rows: list[dict[str, object]] = []

    for index, case in enumerate(cases, 1):
        started = perf_counter()
        order = int(case["order"])
        character = str(case["character"])
        input_path = args.corpus / "inputs" / case["input_file"]
        case_dir = images_dir / f"{order:02d}_{character}"
        print(f"[{index}/{len(cases)}] {order:02d} {character}", flush=True)
        try:
            row = audit_case(input_path, case_dir)
            row.update(
                order=order,
                character=character,
                input_file=case["input_file"],
                elapsed_s=round(perf_counter() - started, 3),
            )
        except Exception as exc:
            row = {
                "order": order,
                "character": character,
                "input_file": case["input_file"],
                "changed": False,
                "error": f"{type(exc).__name__}: {exc}",
                "elapsed_s": round(perf_counter() - started, 3),
            }
        rows.append(row)
        write_checkpoint(args.output, rows)
        print(
            "  changed="
            f"{row.get('changed')} "
            f"accepted_events={len(row.get('geometry_final_guard_accepted_events', []))} "
            f"part_savings={row.get('part_vertex_savings', 0)} "
            f"shading_changed={row.get('shading_decision_changed', False)} "
            f"elapsed={row.get('elapsed_s')}s",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
