from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean

from minimalize_engine import MinimalizeConfig, minimalize, minimalize_rinka_reference
from minimalize_engine.io.image_exporter import export_png
from minimalize_engine.io.svg_exporter import export_svg


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Compare the stable Minimalizer output with Rinka Reference Phase 1."
    )
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--end", type=int)
    p.add_argument("--max-side", type=int, default=320)
    p.add_argument("--level", type=int, default=4)
    p.add_argument(
        "--output-dir",
        default="examples/rinka_target_phase1",
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


def main() -> None:
    args = _parser().parse_args()
    root = Path(__file__).parents[1]
    corpus = root / "tests" / "assets" / "corpus"
    out = Path(args.output_dir)
    if not out.is_absolute():
        out = root / out
    out.mkdir(parents=True, exist_ok=True)

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
        target = minimalize_rinka_reference(
            path,
            args.level,
            analysis_max_side=args.max_side,
        )

        stem = path.stem
        export_png(stable, out / f"{stem}_stable.png")
        export_png(target, out / f"{stem}_rinka_phase1.png")
        export_svg(target, out / f"{stem}_rinka_phase1.svg")

        stable_shapes = len(stable.shapes)
        target_shapes = len(target.shapes)
        stable_vertices = _scene_vertices(stable)
        target_vertices = _scene_vertices(target)
        stable_quality = stable.metadata.get("quality", {})
        target_quality = target.metadata.get("quality", {})
        target_meta = target.metadata.get("target_style", {})
        cleanup = target_meta.get("cleanup", {})

        row = {
            "file": path.name,
            "scene_mode": "subject" if stable.metadata.get("subject_mode") else "general",
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
            "stable_quality": stable_quality.get("score"),
            "stable_identity": stable_quality.get("identity_score"),
            "stable_silhouette": stable_quality.get("silhouette_similarity"),
            "stable_minimality": stable_quality.get("minimality_score"),
            # These are intentionally labeled pre-target because the Phase-1
            # post-process does not yet have the source reference needed to
            # recompute the full quality evaluator after cleanup.
            "target_pre_quality": target_quality.get("score"),
            "target_pre_identity": target_quality.get("identity_score"),
            "target_pre_silhouette": target_quality.get("silhouette_similarity"),
            "target_pre_minimality": target_quality.get("minimality_score"),
        }
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False))

    suffix = f"{args.start}_{args.end if args.end is not None else 'end'}"
    json_path = out / f"report_{suffix}.json"
    csv_path = out / f"report_{suffix}.csv"
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    if rows:
        with csv_path.open("w", newline="", encoding="utf-8-sig") as fp:
            writer = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        summary = {
            "count": len(rows),
            "mean_shape_reduction_ratio": mean(r["shape_reduction_ratio"] for r in rows),
            "mean_vertex_reduction_ratio": mean(r["vertex_reduction_ratio"] for r in rows),
            "total_target_cleanup_removed": sum(r["target_cleanup_removed"] for r in rows),
            "quality_note": "target_pre_* metrics are measured before the Phase-1 target-style post-process",
        }
        (out / f"summary_{suffix}.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
