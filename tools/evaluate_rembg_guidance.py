from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from rembg import new_session, remove


def _subject_confidence(probability: np.ndarray) -> np.ndarray:
    """Confidence heuristic: high away from the uncertain 0.5 boundary."""
    return np.clip(2.0 * np.abs(probability - 0.5), 0.0, 1.0).astype(np.float32)


def _border_mask(shape: tuple[int, int], fraction: float = 0.05) -> np.ndarray:
    height, width = shape
    border_y = max(1, round(height * fraction))
    border_x = max(1, round(width * fraction))
    mask = np.zeros(shape, dtype=bool)
    mask[:border_y, :] = True
    mask[-border_y:, :] = True
    mask[:, :border_x] = True
    mask[:, -border_x:] = True
    return mask


def _component_stats(binary: np.ndarray) -> tuple[int, float]:
    from scipy import ndimage

    labels, count = ndimage.label(binary, structure=np.ones((3, 3), dtype=np.uint8))
    if count <= 0:
        return 0, 0.0
    areas = np.bincount(labels.ravel())[1:].astype(np.float64)
    total = float(areas.sum())
    return int(count), (float(areas.max() / total) if total > 0.0 else 0.0)


def _metrics(probability: np.ndarray, elapsed: float) -> dict[str, float | int]:
    binary = probability >= 0.5
    border = _border_mask(probability.shape)
    confidence = _subject_confidence(probability)
    components, largest_share = _component_stats(binary)
    return {
        "elapsed_seconds": float(elapsed),
        "subject_mean": float(probability.mean(dtype=np.float64)),
        "subject_area_ratio": float(binary.mean(dtype=np.float64)),
        "border_subject_mean": float(probability[border].mean(dtype=np.float64)),
        "border_subject_fraction": float(binary[border].mean(dtype=np.float64)),
        "ambiguous_fraction": float(((probability > 0.2) & (probability < 0.8)).mean()),
        "mean_confidence": float(confidence.mean(dtype=np.float64)),
        "component_count": components,
        "largest_component_share": largest_share,
    }


def _mask_from_rembg(image: Image.Image, session) -> tuple[np.ndarray, float]:
    started = time.perf_counter()
    mask = remove(image, session=session, only_mask=True)
    elapsed = time.perf_counter() - started
    if not isinstance(mask, Image.Image):
        mask = Image.fromarray(np.asarray(mask))
    probability = np.asarray(mask.convert("L"), dtype=np.float32) / 255.0
    return probability, elapsed


def _save_mask(probability: np.ndarray, path: Path) -> None:
    image = Image.fromarray(np.rint(probability * 255.0).astype(np.uint8), mode="L")
    image.save(path)


def _tile_preview(source: Image.Image, probability: np.ndarray, title: str) -> Image.Image:
    source_rgb = source.convert("RGB")
    mask = Image.fromarray(np.rint(probability * 255.0).astype(np.uint8), mode="L").convert("RGB")
    width = 320
    scale = width / float(source_rgb.width)
    height = max(1, round(source_rgb.height * scale))
    source_rgb = source_rgb.resize((width, height), Image.Resampling.LANCZOS)
    mask = mask.resize((width, height), Image.Resampling.BILINEAR)
    canvas = Image.new("RGB", (width * 2, height + 28), "white")
    canvas.paste(source_rgb, (0, 28))
    canvas.paste(mask, (width, 28))
    draw = ImageDraw.Draw(canvas)
    draw.text((6, 6), title, fill="black")
    return canvas


def _save_contact_sheet(tiles: list[Image.Image], path: Path, columns: int = 2) -> None:
    if not tiles:
        return
    tile_w = max(tile.width for tile in tiles)
    tile_h = max(tile.height for tile in tiles)
    rows = (len(tiles) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * tile_w, rows * tile_h), (232, 232, 232))
    for index, tile in enumerate(tiles):
        x = (index % columns) * tile_w
        y = (index // columns) * tile_h
        sheet.paste(tile, (x, y))
    sheet.save(path)


def evaluate_model(model: str, inputs: list[Path], output_dir: Path) -> dict:
    model_dir = output_dir / model
    mask_dir = model_dir / "masks"
    mask_dir.mkdir(parents=True, exist_ok=True)
    session = new_session(model)
    cases = []
    tiles: list[Image.Image] = []
    for path in inputs:
        with Image.open(path) as loaded:
            source = loaded.convert("RGB")
        probability, elapsed = _mask_from_rembg(source, session)
        metrics = _metrics(probability, elapsed)
        mask_path = mask_dir / f"{path.stem}_mask.png"
        _save_mask(probability, mask_path)
        cases.append({"name": path.stem, "source": str(path), "mask": str(mask_path), **metrics})
        title = f"{path.stem} | area={metrics['subject_area_ratio']:.3f} border={metrics['border_subject_fraction']:.3f}"
        tiles.append(_tile_preview(source, probability, title))

    numeric_keys = [key for key, value in cases[0].items() if isinstance(value, (int, float))]
    summary = {key: float(np.mean([float(case[key]) for case in cases])) for key in numeric_keys}
    summary["case_count"] = len(cases)
    report = {"model": model, "summary": summary, "cases": cases}
    (model_dir / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    _save_contact_sheet(tiles, model_dir / "contact_sheet.jpg")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate rembg masks as Minimalizer V2 analysis guidance.")
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument(
        "--models",
        nargs="+",
        default=("isnet-anime", "isnet-general-use", "u2net_human_seg"),
    )
    args = parser.parse_args()
    inputs = sorted(args.input_dir.glob("*.png"))
    if not inputs:
        raise SystemExit(f"no PNG inputs found in {args.input_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    reports = []
    for model in args.models:
        print(f"[rembg] evaluating {model} on {len(inputs)} images", flush=True)
        reports.append(evaluate_model(model, inputs, args.output_dir))
    combined = {"models": reports}
    (args.output_dir / "summary.json").write_text(json.dumps(combined, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
