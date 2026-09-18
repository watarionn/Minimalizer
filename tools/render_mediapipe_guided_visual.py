from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from minimalize_engine.v2 import AnalysisGuidance, SemanticGuide, render_scene
from minimalize_engine.v2.pipeline import PipelineConfig, minimalize_v2
from minimalize_engine.v2.rembg_guidance import subject_confidence_from_probability

LABELS = ("background", "hair", "body-skin", "face-skin", "clothes", "others")
MODEL_NAME = "selfie_multiclass_256x256"


def _load_rgb(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"), dtype=np.uint8)


def _load_probability(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("L"), dtype=np.float32) / 255.0


def _load_semantic(path: Path, subject_prob: np.ndarray) -> SemanticGuide:
    payload = np.load(path)
    labels = tuple(str(value) for value in payload["labels"].tolist())
    confidence = np.asarray(payload["confidence"], dtype=np.float32)
    if labels != LABELS:
        raise ValueError(f"unexpected MediaPipe labels: {labels}")
    if confidence.shape[1:] != subject_prob.shape:
        raise ValueError("MediaPipe confidence tensor must match source resolution")
    foreground = confidence[1:] * subject_prob[None, ...]
    return SemanticGuide(
        labels=labels[1:],
        confidence_maps=foreground.astype(np.float32),
        provider="mediapipe",
        model=MODEL_NAME,
    )


def _guidance(subject_prob: np.ndarray, semantic: SemanticGuide | None) -> AnalysisGuidance:
    return AnalysisGuidance(
        subject_prob=subject_prob,
        subject_confidence=subject_confidence_from_probability(subject_prob, power=2.0),
        semantic=semantic,
        subject_provider="rembg",
        subject_model="isnet-anime",
    )


def _fit_height(image: Image.Image, target_height: int) -> Image.Image:
    scale = target_height / image.height
    width = max(1, round(image.width * scale))
    return image.resize((width, target_height), Image.Resampling.LANCZOS)


def _triplet(source: np.ndarray, base: np.ndarray, guided: np.ndarray, title: str) -> Image.Image:
    images = [_fit_height(Image.fromarray(value), 300) for value in (source, base, guided)]
    width = sum(image.width for image in images)
    canvas = Image.new("RGB", (width, 330), "white")
    x = 0
    for image in images:
        canvas.paste(image, (x, 30))
        x += image.width
    ImageDraw.Draw(canvas).text((6, 7), title, fill="black")
    return canvas


def main() -> int:
    parser = argparse.ArgumentParser(description="Render source/rembg/rembg+MediaPipe V2 comparison sheet.")
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("rembg_mask_dir", type=Path)
    parser.add_argument("semantic_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--analysis-max-side", type=int, default=400)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    config = PipelineConfig(analysis_max_side=args.analysis_max_side)
    tiles: list[Image.Image] = []
    metrics = []
    for image_path in sorted(args.input_dir.glob("*.png")):
        name = image_path.stem
        print(f"[visual] {name}", flush=True)
        subject_prob = _load_probability(args.rembg_mask_dir / f"{name}_mask.png")
        semantic = _load_semantic(args.semantic_dir / f"{name}_confidence.npz", subject_prob)
        source = _load_rgb(image_path)
        base = minimalize_v2(source, presets=("minimal",), config=config, guidance=_guidance(subject_prob, None))
        guided = minimalize_v2(source, presets=("minimal",), config=config, guidance=_guidance(subject_prob, semantic))
        base_preset = base.presets["minimal"]
        guided_preset = guided.presets["minimal"]
        base_image = render_scene(base_preset.scene)
        guided_image = render_scene(guided_preset.scene)
        base_groups = base_preset.detail_budget.metrics.visual_group_count
        guided_groups = guided_preset.detail_budget.metrics.visual_group_count
        title = f"{name} | groups {base_groups}->{guided_groups} | palette {base_preset.palette.metrics.palette_count}->{guided_preset.palette.metrics.palette_count}"
        tiles.append(_triplet(source, base_image, guided_image, title))
        metrics.append({"name": name, "base_groups": base_groups, "guided_groups": guided_groups})
    width = max(tile.width for tile in tiles)
    height = sum(tile.height for tile in tiles)
    sheet = Image.new("RGB", (width, height), (235, 235, 235))
    y = 0
    for tile in tiles:
        sheet.paste(tile, (0, y))
        y += tile.height
    sheet.save(args.output_dir / "contact_sheet.jpg", quality=92)
    (args.output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps({
        "case_count": len(metrics),
        "mean_group_delta": float(np.mean([row["guided_groups"] - row["base_groups"] for row in metrics])),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
