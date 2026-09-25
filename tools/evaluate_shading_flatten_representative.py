from __future__ import annotations

import argparse
import json
from pathlib import Path
from time import perf_counter

import cv2
import numpy as np
from PIL import Image, ImageDraw

from local_worker import app as worker
from minimalize_engine.v2 import PipelineConfig, ShadingFlattenConfig, export_png, minimalize_v2
from minimalize_engine.v2.pipeline import LayeredPersonConfig


DEFAULT_ORDERS = (1, 9, 12, 14, 21, 39, 44, 74)
SETTINGS = (
    ("off", False, 55),
    ("sr45", True, 45),
    ("sr55", True, 55),
    ("sr65", True, 65),
)


def _visible_complexity(scene) -> tuple[int, int]:
    visible = [shape for shape in scene.shapes if shape.visible]
    vertices = 0
    for shape in visible:
        if shape.geometry.kind == "polygon":
            vertices += sum(len(loop) for loop in shape.geometry.loops)
    return len(visible), vertices


def _load_rgb_for_metric(path: Path, size: int = 128) -> np.ndarray:
    with Image.open(path) as image:
        rgba = image.convert("RGBA")
        bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        rgb = Image.alpha_composite(bg, rgba).convert("RGB")
    array = np.asarray(rgb, dtype=np.uint8)
    return cv2.resize(array, (size, size), interpolation=cv2.INTER_AREA)
def _diagnostic_similarity(output_path: Path, approved_path: Path) -> dict[str, float]:
    output = _load_rgb_for_metric(output_path)
    approved = _load_rgb_for_metric(approved_path)
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
        if union else 1.0
    )
    return {
        "color_similarity": color_similarity,
        "edge_iou": edge_iou,
        "edge_density_delta": abs(
            float(output_edges.mean()) - float(approved_edges.mean())
        ),
    }


def _make_contact_sheet(case_dir: Path, approved_path: Path, title: str) -> None:
    cells: list[tuple[str, Image.Image]] = []
    with Image.open(approved_path) as approved:
        cells.append(("APPROVED", approved.convert("RGBA")))
    for label, _enabled, _sr in SETTINGS:
        with Image.open(case_dir / f"{label}.png") as image:
            cells.append((label.upper(), image.convert("RGBA")))

    cell_size = 280
    header = 52
    sheet = Image.new(
        "RGB",
        (cell_size * len(cells), cell_size + header + 28),
        (235, 235, 235),
    )
    draw = ImageDraw.Draw(sheet)
    draw.text((8, 6), title, fill=(20, 20, 20))
    for index, (label, image) in enumerate(cells):
        white = Image.new("RGBA", image.size, (255, 255, 255, 255))
        composed = Image.alpha_composite(white, image).convert("RGB")
        composed.thumbnail((cell_size, cell_size))
        x = index * cell_size + (cell_size - composed.width) // 2
        y = header + (cell_size - composed.height) // 2
        sheet.paste(composed, (x, y))
        draw.text((index * cell_size + 8, header + cell_size + 4), label, fill=(20, 20, 20))
    sheet.save(case_dir / "contact_sheet.png")
def evaluate(corpus: Path, out_dir: Path, orders: tuple[int, ...]) -> list[dict[str, object]]:
    manifest = json.loads((corpus / "manifest.json").read_text(encoding="utf-8"))
    by_order = {int(case["order"]): case for case in manifest["cases"]}
    rows: list[dict[str, object]] = []

    for order in orders:
        case = by_order[order]
        character = case["character"]
        input_path = corpus / "inputs" / case["input_file"]
        approved_path = corpus / "references" / case["approved_file"]
        case_dir = out_dir / f"{order:02d}_{character}"
        case_dir.mkdir(parents=True, exist_ok=True)

        print(f"== {order:02d} {character} ==", flush=True)
        guidance_started = perf_counter()
        source_rgb, guidance, selection = worker._build_guidance(input_path)
        guidance_seconds = perf_counter() - guidance_started

        for label, enabled, sr in SETTINGS:
            started = perf_counter()
            config = PipelineConfig(
                analysis_max_side=worker.ANALYSIS_MAX_SIDE,
                shading_flatten=ShadingFlattenConfig(enabled=enabled, sr=sr),
                layered_person=LayeredPersonConfig(enabled=True),
            )
            result = minimalize_v2(
                source_rgb,
                presets=("minimal",),
                config=config,
                guidance=guidance,
            )
            exported = export_png(
                result,
                preset="minimal",
                include_facets=True,
                filename=f"{label}.png",
                preserve_source_alpha=True,
            )
            output_path = case_dir / exported.filename
            output_path.write_bytes(exported.content)

            scene = result.presets["minimal"].scene
            visible_shapes, polygon_vertices = _visible_complexity(scene)
            part_visible_shapes = 0
            part_polygon_vertices = 0
            for presets in result.person_part_presets.values():
                shapes, vertices = _visible_complexity(presets["minimal"].scene)
                part_visible_shapes += shapes
                part_polygon_vertices += vertices

            similarity = _diagnostic_similarity(output_path, approved_path)
            row = {
                "order": order,
                "character": character,
                "setting": label,
                "enabled": enabled,
                "sr": sr,
                "rtmlib_selected": selection is not None,
                "guidance_seconds": guidance_seconds,
                "pipeline_seconds": perf_counter() - started,
                "initial_regions": result.region_merge.initial_region_count,
                "selected_regions": len(result.presets["minimal"].selection.region_ids),
                "visible_shapes": visible_shapes,
                "polygon_vertices": polygon_vertices,
                "part_visible_shapes": part_visible_shapes,
                "part_polygon_vertices": part_polygon_vertices,
                "palette_count": len(scene.palette),
                "analysis_unique_colors": int(
                    len(np.unique(result.bundle.analysis_rgb.reshape(-1, 3), axis=0))
                ),
                "edge_raw_mean": float(result.bundle.edge_raw.mean()),
                **similarity,
            }
            rows.append(row)
            print(
                f"  {label}: regions={row['initial_regions']} "
                f"vertices={polygon_vertices} part_vertices={part_polygon_vertices} "
                f"color={row['color_similarity']:.6f} edge={row['edge_iou']:.6f}",
                flush=True,
            )
            (out_dir / "metrics.json").write_text(
                json.dumps(rows, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        _make_contact_sheet(case_dir, approved_path, f"{order:02d} {character}")

    return rows


def _summarize(rows: list[dict[str, object]]) -> dict[str, dict[str, float]]:
    summary: dict[str, dict[str, float]] = {}
    for label, _enabled, _sr in SETTINGS:
        selected = [row for row in rows if row["setting"] == label]
        summary[label] = {
            "cases": len(selected),
            "mean_initial_regions": float(np.mean([row["initial_regions"] for row in selected])),
            "mean_polygon_vertices": float(np.mean([row["polygon_vertices"] for row in selected])),
            "mean_part_polygon_vertices": float(np.mean([row["part_polygon_vertices"] for row in selected])),
            "mean_color_similarity": float(np.mean([row["color_similarity"] for row in selected])),
            "mean_edge_iou": float(np.mean([row["edge_iou"] for row in selected])),
            "mean_edge_density_delta": float(np.mean([row["edge_density_delta"] for row in selected])),
        }
    return summary
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus", type=Path)
    parser.add_argument("out_dir", type=Path)
    parser.add_argument("--orders", default=",".join(str(value) for value in DEFAULT_ORDERS))
    args = parser.parse_args()
    orders = tuple(int(value.strip()) for value in args.orders.split(",") if value.strip())
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows = evaluate(args.corpus, args.out_dir, orders)
    summary = _summarize(rows)
    (args.out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
