from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from minimalize_engine.v2 import AnalysisGuidance, render_scene
from minimalize_engine.v2.pipeline import PipelineConfig, minimalize_v2
from minimalize_engine.v2.rembg_guidance import subject_confidence_from_probability
from compare_groundedsam_guided_v2 import (
    _fused_guide,
    _load_probability,
    _mediapipe_guide,
)


def _load_rgb(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"), dtype=np.uint8)


def _tile(
    source: np.ndarray,
    baseline: np.ndarray,
    guided: np.ndarray,
    title: str,
) -> Image.Image:
    images = [Image.fromarray(source), Image.fromarray(baseline), Image.fromarray(guided)]
    target_height = 320
    resized: list[Image.Image] = []
    for image in images:
        scale = target_height / image.height
        resized.append(
            image.resize(
                (max(1, round(image.width * scale)), target_height),
                Image.Resampling.LANCZOS,
            )
        )
    canvas = Image.new(
        "RGB",
        (sum(image.width for image in resized), target_height + 30),
        "white",
    )
    x = 0
    for image in resized:
        canvas.paste(image, (x, 30))
        x += image.width
    ImageDraw.Draw(canvas).text((6, 7), title, fill="black")
    return canvas


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render source / Phase D / Phase E comparison triplets."
    )
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("rembg_mask_dir", type=Path)
    parser.add_argument("mediapipe_dir", type=Path)
    parser.add_argument("groundedsam_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--analysis-max-side", type=int, default=400)
    parser.add_argument("--names", nargs="*", default=[])
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    config = PipelineConfig(analysis_max_side=args.analysis_max_side)
    wanted = set(args.names)
    paths = [
        path
        for path in sorted(args.input_dir.glob("*.png"))
        if not wanted or path.stem in wanted
    ]
    if not paths:
        raise SystemExit("no matching PNG inputs")

    tiles: list[Image.Image] = []
    rows: list[dict] = []
    for path in paths:
        print(f"[visual] {path.stem}", flush=True)
        source = _load_rgb(path)
        subject_prob = _load_probability(
            args.rembg_mask_dir / f"{path.stem}_mask.png"
        )
        subject_confidence = subject_confidence_from_probability(
            subject_prob, power=2.0
        )
        mediapipe = _mediapipe_guide(
            args.mediapipe_dir / f"{path.stem}_confidence.npz",
            subject_prob,
        )
        fused = _fused_guide(
            args.mediapipe_dir / f"{path.stem}_confidence.npz",
            args.groundedsam_dir / f"{path.stem}_confidence.npz",
            subject_prob,
        )
        common = dict(
            subject_prob=subject_prob,
            subject_confidence=subject_confidence,
            subject_provider="rembg",
            subject_model="isnet-anime",
        )
        baseline = minimalize_v2(
            source,
            presets=("minimal",),
            config=config,
            guidance=AnalysisGuidance(semantic=mediapipe, **common),
        )
        guided = minimalize_v2(
            source,
            presets=("minimal",),
            config=config,
            guidance=AnalysisGuidance(semantic=fused, **common),
        )
        baseline_preset = baseline.presets["minimal"]
        guided_preset = guided.presets["minimal"]
        baseline_image = render_scene(baseline_preset.scene)
        guided_image = render_scene(guided_preset.scene)
        base_groups = baseline_preset.detail_budget.metrics.visual_group_count
        guided_groups = guided_preset.detail_budget.metrics.visual_group_count
        title = (
            f"{path.stem} | groups {base_groups}->{guided_groups} "
            "(source / Phase D / +Grounded-SAM)"
        )
        tiles.append(_tile(source, baseline_image, guided_image, title))
        rows.append(
            {
                "name": path.stem,
                "baseline_visual_groups": base_groups,
                "guided_visual_groups": guided_groups,
                "baseline_vertices": baseline_preset.contour.metrics.simplified_vertex_count,
                "guided_vertices": guided_preset.contour.metrics.simplified_vertex_count,
            }
        )

    width = max(tile.width for tile in tiles)
    height = sum(tile.height for tile in tiles)
    sheet = Image.new("RGB", (width, height), (235, 235, 235))
    y = 0
    for tile in tiles:
        sheet.paste(tile, (0, y))
        y += tile.height
    sheet.save(args.output_dir / "contact_sheet.jpg", quality=92)
    (args.output_dir / "metrics.json").write_text(
        json.dumps(rows, indent=2),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
