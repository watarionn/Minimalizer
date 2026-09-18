from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import mediapipe as mp
import numpy as np
from PIL import Image, ImageDraw
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

LABELS = ("background", "hair", "body-skin", "face-skin", "clothes", "others")
PALETTE = np.array([
    [20, 20, 20], [190, 120, 220], [235, 190, 160],
    [255, 220, 190], [90, 150, 230], [240, 190, 70],
], dtype=np.uint8)


def _segmenter(model_path: Path):
    options = vision.ImageSegmenterOptions(
        base_options=python.BaseOptions(model_asset_path=str(model_path)),
        running_mode=vision.RunningMode.IMAGE,
        output_confidence_masks=True,
        output_category_mask=True,
    )
    return vision.ImageSegmenter.create_from_options(options)


def _confidence_arrays(result) -> np.ndarray:
    channels = []
    for mask in result.confidence_masks:
        array = np.asarray(mask.numpy_view(), dtype=np.float32)
        if array.ndim == 3:
            array = array[..., 0]
        channels.append(array)
    return np.stack(channels, axis=0)


def _metrics(confidence: np.ndarray, elapsed: float) -> dict:
    category = np.argmax(confidence, axis=0)
    max_conf = np.max(confidence, axis=0)
    runner_up = np.partition(confidence, -2, axis=0)[-2]
    margin = max_conf - runner_up
    areas = {LABELS[i]: float(np.mean(category == i)) for i in range(len(LABELS))}
    foreground = category != 0
    return {
        "elapsed_seconds": float(elapsed),
        "mean_max_confidence": float(np.mean(max_conf)),
        "mean_margin": float(np.mean(margin)),
        "low_margin_fraction": float(np.mean(margin < 0.15)),
        "foreground_area_ratio": float(np.mean(foreground)),
        "class_area_ratio": areas,
    }


def _tile(source: Image.Image, category: np.ndarray, title: str) -> Image.Image:
    source = source.convert("RGB")
    color = Image.fromarray(PALETTE[category], mode="RGB")
    target_h = 280
    scale = target_h / source.height
    size = (max(1, round(source.width * scale)), target_h)
    source = source.resize(size, Image.Resampling.LANCZOS)
    color = color.resize(size, Image.Resampling.NEAREST)
    canvas = Image.new("RGB", (size[0] * 2, target_h + 28), "white")
    canvas.paste(source, (0, 28))
    canvas.paste(color, (size[0], 28))
    ImageDraw.Draw(canvas).text((6, 6), title, fill="black")
    return canvas


def _save_sheet(tiles: list[Image.Image], path: Path, columns: int = 2) -> None:
    width = max(tile.width for tile in tiles)
    height = max(tile.height for tile in tiles)
    rows = (len(tiles) + columns - 1) // columns
    sheet = Image.new("RGB", (width * columns, height * rows), (235, 235, 235))
    for index, tile in enumerate(tiles):
        sheet.paste(tile, ((index % columns) * width, (index // columns) * height))
    sheet.save(path, quality=92)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate MediaPipe multiclass semantics on Approved-18.")
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("model_path", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    print(f"input_dir={args.input_dir}", flush=True)
    inputs = sorted(args.input_dir.glob("*.png"))
    print(f"inputs={len(inputs)}", flush=True)
    if not inputs:
        raise SystemExit("no PNG inputs found")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    cases = []
    tiles: list[Image.Image] = []
    print(f"model={args.model_path}", flush=True)
    with _segmenter(args.model_path) as segmenter:
        print("labels:", segmenter.labels, flush=True)
        for path in inputs:
            with Image.open(path) as loaded:
                source = loaded.convert("RGB")
            array = np.asarray(source, dtype=np.uint8)
            started = time.perf_counter()
            result = segmenter.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=array))
            elapsed = time.perf_counter() - started
            confidence = _confidence_arrays(result)
            np.savez_compressed(
                args.output_dir / f"{path.stem}_confidence.npz",
                labels=np.asarray(LABELS),
                confidence=confidence.astype(np.float32),
            )
            metrics = _metrics(confidence, elapsed)
            category = np.argmax(confidence, axis=0)
            cases.append({"name": path.stem, **metrics})
            title = f"{path.stem} | fg={metrics['foreground_area_ratio']:.3f} conf={metrics['mean_max_confidence']:.3f}"
            tiles.append(_tile(source, category, title))
            print(f"[mediapipe] {path.stem}", flush=True)

    summary = {
        "case_count": len(cases),
        "mean_elapsed_seconds": float(np.mean([case["elapsed_seconds"] for case in cases])),
        "mean_max_confidence": float(np.mean([case["mean_max_confidence"] for case in cases])),
        "mean_margin": float(np.mean([case["mean_margin"] for case in cases])),
        "mean_low_margin_fraction": float(np.mean([case["low_margin_fraction"] for case in cases])),
        "mean_foreground_area_ratio": float(np.mean([case["foreground_area_ratio"] for case in cases])),
        "mean_class_area_ratio": {
            label: float(np.mean([case["class_area_ratio"][label] for case in cases]))
            for label in LABELS
        },
    }
    report = {"labels": LABELS, "summary": summary, "cases": cases}
    (args.output_dir / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    _save_sheet(tiles, args.output_dir / "contact_sheet.jpg")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
