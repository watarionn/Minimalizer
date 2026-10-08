"""Reproducible, headless vsketch line-art study on the original GC001 image.

This is a LOCAL RESEARCH TOOL, not the production Minimalizer engine.
All strokes come from source-image edges / luminance. No image synthesis.
pip install in independent research target: vsketch 1.2.0 + vpype 1.15.0.
Export: original + three independent SVG/PNG and a 2x2 contact sheet.

Example:
  python -W error tools/research/vsketch_three_styles.py --source SOURCE --out OUTPUT
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from xml.etree import ElementTree

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageOps
import resvg_py
import vsketch

SOURCE_SHA = "75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e"
STYLES = ("contour_line", "hatch_shade", "sparse_outline")
SIZE = (340, 340)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_original(path: Path) -> np.ndarray:
    if sha256(path).lower() != SOURCE_SHA:
        raise ValueError("GC001 original image SHA-256 mismatch")
    with Image.open(path) as src:
        im = np.array(src.convert("RGB"), dtype=np.uint8)
    if tuple(im.shape[:2][::-1]) != SIZE:
        raise ValueError("Original dimensions must be 340x340")
    return im


def candidates(image: np.ndarray) -> list[dict]:
    """Strong contours from ORIGINAL luminance, with modest geometric simplification."""
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    smooth = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(smooth, threshold1=55, threshold2=125, L2gradient=True)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    found = []
    for contour in contours:
        length = float(cv2.arcLength(contour, closed=False))
        if length < 16:
            continue
        epsilon = max(0.75, length * 0.0025)
        simplified = cv2.approxPolyDP(contour, epsilon, closed=False)
        if len(simplified) < 3:
            continue
        points = [tuple(map(float, pt[0])) for pt in simplified]
        x, y, w, h = cv2.boundingRect(contour)
        if w * h < 18:
            continue
        found.append({"points": points, "length": length, "bbox": (x, y, w, h)})
    # Stable ranking by length, bounds, and number of vertices.
    return sorted(found, key=lambda c: (-c["length"], *c["bbox"], len(c["points"])))


def plot_contours(vsk: vsketch.Vsketch, shapes: list[dict], maximum: int, min_length: float) -> int:
    selected = [c for c in shapes if c["length"] >= min_length][:maximum]
    for c in selected:
        vsk.polygon(c["points"], close=False)
    return len(selected)


def draw_style(image: np.ndarray, style: str, svg: Path, png: Path) -> dict:
    sketch = vsketch.Vsketch()
    sketch.size(*SIZE, center=False)
    sketch.detail(1.25)
    sketch.stroke(1)
    contour_list = candidates(image)
    count = 0

    if style == "contour_line":
        count = plot_contours(sketch, contour_list, maximum=145, min_length=19)

    elif style == "hatch_shade":
        # Original brightness selects pen stroke length and density.
        # Strokes are clipped to their sampling cells, not inpainted.
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        for y in range(3, SIZE[1] - 3, 8):
            for x in range(3, SIZE[0] - 3, 8):
                patch = blurred[y-3:y+4, x-3:x+4]
                dark = 1.0 - float(patch.mean()) / 255.0
                if dark < 0.22:
                    continue
                # Midtones: short pen strokes; shadows: long strokes.
                extent = 1.5 + 4.0 * min(1.0, dark)
                sketch.line(x - extent, y + extent, x + extent, y - extent)
                count += 1
                if dark > 0.60:
                    sketch.line(x - extent + 2.0, y + extent,
                                x + extent + 2.0, y - extent)
                    count += 1
        # A smaller set of real source contours adds subject structure.
        count += plot_contours(sketch, contour_list, maximum=58, min_length=50)

    elif style == "sparse_outline":
        # Select prominent, relatively long original edges only.
        chosen = []
        for item in contour_list:
            x, y, w, h = item["bbox"]
            if item["length"] < 58 or max(w, h) < 9:
                continue
            # Avoid very similar double contours from Canny's two edges.
            overlapping = False
            for prev in chosen:
                xx, yy, ww, hh = prev["bbox"]
                delta = abs(x-xx) + abs(y-yy) + abs(w-ww) + abs(h-hh)
                if delta <= 10:
                    overlapping = True
                    break
            if overlapping:
                continue
            chosen.append(item)
            if len(chosen) >= 60:
                break
        for item in chosen:
            sketch.polygon(item["points"], close=False)
        count = len(chosen)
    else:
        raise ValueError("Unknown style: " + style)

    if count <= 0:
        raise RuntimeError("Empty drawing: " + style)

    # Use vsketch's native SVG writer rather than manually fabricating paths.
    sketch.save(str(svg), color_mode="none")
    ElementTree.parse(svg)
    xml = svg.read_text(encoding="utf-8")
    if "<image" in xml.lower() or "data:image" in xml.lower():
        raise AssertionError("Raster source image was embedded in the SVG")

    png.write_bytes(resvg_py.svg_to_bytes(svg_path=str(svg), width=680, height=680))
    with Image.open(png) as preview:
        if preview.size != (680, 680):
            raise AssertionError("Unexpected raster output dimensions")
        if preview.getbbox() is None:
            raise AssertionError("Empty PNG")
    return {
        "style": style, "primitive_count": count, "candidate_contours": len(contour_list),
        "svg": svg.name, "svg_sha256": sha256(svg), "svg_bytes": svg.stat().st_size,
        "png": png.name, "png_sha256": sha256(png), "png_bytes": png.stat().st_size,
    }


def comparison(source: Path, outputs: list[dict], out: Path) -> Path:
    thumb, pad, label_h = 440, 18, 40
    cell_w, cell_h = thumb + 2 * pad, thumb + 2 * pad + label_h
    grid = Image.new("RGB", (2 * cell_w, 2 * cell_h), "#eaeae8")
    pairs = [("Original / GC001", source)] + [
        (item["style"], out / item["png"]) for item in outputs
    ]
    for idx, (label, path) in enumerate(pairs):
        tile = Image.new("RGB", (cell_w, cell_h), "#ffffff")
        with Image.open(path) as source_img:
            im = ImageOps.contain(source_img.convert("RGBA"), (thumb, thumb), Image.Resampling.LANCZOS)
            bg = Image.new("RGB", im.size, "#fafaf8")
            bg.paste(im, mask=im.getchannel("A"))
            tile.paste(bg, (pad + (thumb - im.width)//2, pad + (thumb - im.height)//2))
        ImageDraw.Draw(tile).text((pad, thumb + pad + 10), label, fill="#222222")
        grid.paste(tile, ((idx % 2) * cell_w, (idx // 2) * cell_h))
    contact_sheet = out / "comparison_grid.png"
    grid.save(contact_sheet)
    return contact_sheet


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    options = parser.parse_args()
    src = options.source.resolve()
    pixels = load_original(src)
    folder = options.out.resolve()
    folder.mkdir(parents=True, exist_ok=True)
    saved_source = folder / "GC001_source.png"
    if src != saved_source:
        shutil.copy2(src, saved_source)
    if sha256(saved_source).lower() != SOURCE_SHA:
        raise RuntimeError("Copied source hash mismatch")
    produced = []
    for style in STYLES:
        produced.append(draw_style(pixels, style,
                                   folder / f"GC001_{style}.svg",
                                   folder / f"GC001_{style}.png"))
    grid = comparison(saved_source, produced, folder)
    manifest = {
        "project": "Minimalizer", "research": "vsketch-3-art-modes-headless-v1",
        "scope": "independent non-generative PoC, never Public/Local runtime",
        "library": "vsketch", "version": vsketch.__version__, "license": "MIT",
        "vpype_version": "1.15.0", "source_file": saved_source.name,
        "source_sha256": SOURCE_SHA, "source_size": SIZE,
        "image_generation_ai_used": False, "all_svg_paths_are_vector": True,
        "styles": produced,
        "comparison_grid": {
            "file": grid.name, "sha256": sha256(grid), "bytes": grid.stat().st_size
        },
    }
    (folder / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    print(json.dumps({
        "status": "PASS",
        "library_version": vsketch.__version__,
        "results": [(x["style"], x["primitive_count"]) for x in produced],
        "grid_sha256": manifest["comparison_grid"]["sha256"],
        "directory": str(folder)
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
