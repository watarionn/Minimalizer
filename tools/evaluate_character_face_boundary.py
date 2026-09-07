from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean

from minimalize_engine import MinimalizeConfig, minimalize
from minimalize_engine.io.image_exporter import export_png
from minimalize_engine.io.svg_exporter import export_svg


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Evaluate alpha10-dev3 Bang / Face Boundary Guard."
    )
    p.add_argument("--max-side", type=int, default=240)
    return p


def _config(max_side: int, *, enabled: bool, debug_dir: Path | None = None):
    return MinimalizeConfig.from_level(
        4,
        analysis_max_side=max_side,
        target_max_shapes=32,
        line_mode="none",
        enable_auto_retry=False,
        enable_character_auto_retry=False,
        enable_face_boundary_guard=enabled,
        debug_mode=debug_dir is not None,
        debug_output_dir=str(debug_dir) if debug_dir else None,
    )


def main() -> None:
    args = parser().parse_args()
    root = Path(__file__).parents[1]
    corpus = root / "tests/assets/corpus"
    out = root / "examples/face_boundary_alpha10_dev3"
    out.mkdir(parents=True, exist_ok=True)

    images = sorted(
        p for p in corpus.iterdir()
        if "_pr-img_" in p.name and p.suffix.lower() in {".png", ".webp", ".jpg", ".jpeg"}
    )

    rows = []
    review_names = {
        "Isaki-Riona_pr-img_01_a.png": "isaki",
        "Nerissa-Ravencroft_pr-img_01.webp": "nerissa",
        "Kikirara-Vivi_pr-img_01_a.webp": "vivi",
    }

    for path in images:
        review_key = review_names.get(path.name)
        debug_dir = out / f"debug_{review_key}" if review_key else None

        enabled_scene = minimalize(
            path,
            _config(args.max_side, enabled=True, debug_dir=debug_dir),
        )
        disabled_scene = minimalize(
            path,
            _config(args.max_side, enabled=False),
        )

        boundary = (
            enabled_scene.metadata["character"]["structure"]["metadata"]
            .get("face_boundary") or {}
        )
        diagnostics = boundary.get("diagnostics") or {}
        cq_on = enabled_scene.metadata["character_quality"]
        cq_off = disabled_scene.metadata["character_quality"]

        row = {
            "file": path.name,
            "boundary_score": boundary.get("boundary_score_hint"),
            "strategy": boundary.get("strategy"),
            "conflict_before": diagnostics.get("conflict_pixels_before", 0),
            "conflict_after": diagnostics.get("conflict_pixels_after", 0),
            "removed_hair_pixels": diagnostics.get("removed_hair_pixels", 0),
            "face_geometry_on": cq_on.get("face_geometry_score"),
            "face_geometry_off": cq_off.get("face_geometry_score"),
            "character_quality_on": cq_on.get("score"),
            "character_quality_off": cq_off.get("score"),
            "hair_shape_count_on": enabled_scene.metadata["character"]["details"]["hair"]["shape_count"],
            "hair_shape_count_off": disabled_scene.metadata["character"]["details"]["hair"]["shape_count"],
        }
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False))

        if review_key:
            export_png(enabled_scene, out / f"{review_key}_guard_on.png")
            export_svg(enabled_scene, out / f"{review_key}_guard_on.svg")
            export_png(disabled_scene, out / f"{review_key}_guard_off.png")
            export_svg(disabled_scene, out / f"{review_key}_guard_off.svg")

    applicable = [r for r in rows if r["boundary_score"] is not None]
    summary = {
        "version": "0.3.0-alpha10-dev3",
        "phase": "Phase 10.3 Bang / Face Boundary Guard",
        "character_images": len(rows),
        "boundary_applicable_images": len(applicable),
        "mean_boundary_score": mean(float(r["boundary_score"]) for r in applicable),
        "total_conflict_pixels_before": sum(int(r["conflict_before"]) for r in applicable),
        "total_conflict_pixels_after": sum(int(r["conflict_after"]) for r in applicable),
        "total_removed_hair_pixels": sum(int(r["removed_hair_pixels"]) for r in applicable),
        "images_with_boundary_correction": sum(int(r["conflict_before"]) > 0 for r in applicable),
        "mean_face_geometry_on": mean(float(r["face_geometry_on"]) for r in applicable if r["face_geometry_on"] is not None),
        "mean_face_geometry_off": mean(float(r["face_geometry_off"]) for r in applicable if r["face_geometry_off"] is not None),
        "mean_character_quality_on": mean(float(r["character_quality_on"]) for r in rows),
        "mean_character_quality_off": mean(float(r["character_quality_off"]) for r in rows),
    }

    with (out / "report.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    (out / "report.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("SUMMARY", json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
