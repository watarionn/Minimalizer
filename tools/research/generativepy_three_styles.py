"""Isolated generativepy art-mode research; NO Minimalizer runtime integration.

Requires generativepy==50.0, pycairo, numpy, Pillow.
Run:
  python tools/research/generativepy_three_styles.py
    --source GC001_source.png --out DIR

Outputs three SVG+PNG styles and a comparison contact sheet.
Input is the original image, never an AI-generated intermediary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
from pathlib import Path
from xml.etree import ElementTree

import numpy as np
from PIL import Image, ImageDraw, ImageOps
from generativepy.color import Color
from generativepy.drawing import make_image, make_svg, setup
from generativepy.geometry import Bezier, Circle, Polygon

SOURCE_SHA = "75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e"
STYLES = ("circle_field", "geometric_blocks", "flow_ribbons")
BACKGROUND = Color(0.97, 0.963, 0.948)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_source(path: Path) -> np.ndarray:
    if sha256(path).lower() != SOURCE_SHA:
        raise ValueError("Only the canonical GC001 original is accepted.")
    with Image.open(path) as img:
        pixels = np.array(img.convert("RGBA"), dtype=np.uint8)
    if pixels.shape[:2] != (340, 340):
        raise ValueError("Unexpected source dimensions.")
    return pixels


def region(pixels: np.ndarray, x: float, y: float, radius: int = 3) -> tuple[np.ndarray, float]:
    h, w = pixels.shape[:2]
    # Gradient probes may pass beyond the image at the right or bottom edge.
    # Clamp BEFORE slicing, otherwise an empty tile produces NaN colours.
    xx = min(w - 1, max(0, int(round(x))))
    yy = min(h - 1, max(0, int(round(y))))
    tile = pixels[max(0, yy-radius):min(h, yy+radius+1),
                  max(0, xx-radius):min(w, xx+radius+1)].astype(np.float32)
    alpha = tile[..., 3:4] / 255.0
    effective_alpha = float(alpha.mean())
    if effective_alpha < 0.01:
        return np.array((1.0, 1.0, 1.0), dtype=np.float32), 0.0
    rgb = (tile[..., :3] * alpha).sum(axis=(0, 1)) / max(1e-5, alpha.sum())
    return np.clip(rgb / 255.0, 0, 1), effective_alpha


def luminance(pixels: np.ndarray, x: float, y: float) -> float:
    rgb, _ = region(pixels, x, y, 2)
    return float(np.dot(rgb, (0.2126, 0.7152, 0.0722)))


def render_style(pixels: np.ndarray, style: str, svg: Path, png: Path) -> dict:
    h, w = pixels.shape[:2]
    count = 0

    def drawing(ctx, px_w, px_h, _frame, _count):
        nonlocal count
        setup(ctx, px_w, px_h, width=w, height=h, background=BACKGROUND)
        # Drawing order is fixed and based on original pixel colors.
        if style == "circle_field":
            step = 12
            for y in range(step // 2, h, step):
                for x in range(step // 2, w, step):
                    rgb, alpha = region(pixels, x, y, 4)
                    if alpha < 0.16:
                        continue
                    lum = float(np.dot(rgb, (0.2126, 0.7152, 0.0722)))
                    r = 2.0 + 3.4 * (1.0 - lum)
                    Circle(ctx).of_center_radius((x, y), r).fill(
                        Color(*map(float, rgb), min(1.0, 0.68 + 0.32 * alpha))
                    )
                    count += 1

        elif style == "geometric_blocks":
            step = 14
            for y in range(0, h, step):
                for x in range(0, w, step):
                    cx, cy = min(w-1, x + step * 0.5), min(h-1, y + step * 0.5)
                    rgb, alpha = region(pixels, cx, cy, 4)
                    if alpha < 0.16:
                        continue
                    dx = luminance(pixels, cx+5, cy) - luminance(pixels, cx-5, cy)
                    dy = luminance(pixels, cx, cy+5) - luminance(pixels, cx, cy-5)
                    direction = max(-0.32, min(0.32, math.atan2(dy, dx) * 0.12))
                    size = step * (0.8 + 0.1 * min(1.0, abs(dx) + abs(dy)))
                    pts = []
                    for ax, ay in [(-0.5,-0.5), (0.5,-0.5), (0.5,0.5), (-0.5,0.5)]:
                        ox, oy = ax * size, ay * size
                        pts.append((cx + ox*math.cos(direction) - oy*math.sin(direction),
                                    cy + ox*math.sin(direction) + oy*math.cos(direction)))
                    Polygon(ctx).of_points(pts).fill(
                        Color(*map(float, rgb), min(1.0, 0.75 + 0.25 * alpha))
                    )
                    count += 1

        elif style == "flow_ribbons":
            # Curves sampled from local luminance gradients, not invented features.
            # Each ribbon section remains constrained near the sample position.
            step_x, step_y = 10, 10
            for y in range(step_y // 2, h, step_y):
                for x in range(0, w, step_x):
                    cx = min(w-1, x + step_x * 0.5)
                    rgb, alpha = region(pixels, cx, y, 3)
                    if alpha < 0.15:
                        continue
                    lum = float(np.dot(rgb, (0.2126, 0.7152, 0.0722)))
                    vertical_gradient = luminance(pixels, cx, y+5) - luminance(pixels, cx, y-5)
                    drift = max(-3.2, min(3.2, vertical_gradient * 5))
                    a = (x, y)
                    b = (x+step_x*.35, y+drift)
                    c = (x+step_x*.65, y+drift)
                    d = (min(w, x+step_x), y)
                    Bezier(ctx).of_abcd(a,b,c,d).stroke(
                        Color(*map(float, rgb), min(1.0, 0.75 + 0.25 * alpha)),
                        line_width=3.2 + 3.1 * (1.0 - lum),
                    )
                    count += 1
        else:
            raise ValueError(style)

    # Generativepy's own SVG and PNG backends are both exercised.
    make_svg(str(svg), drawing, w, h)
    svg_count = count
    count = 0
    make_image(str(png), drawing, w * 2, h * 2)
    png_count = count
    if png_count != svg_count or count == 0:
        raise AssertionError("PNG and SVG drawing descriptions diverged or were empty")
    tree = ElementTree.parse(svg)
    ns = "{http://www.w3.org/2000/svg}"
    if tree.getroot().find(".//" + ns + "image") is not None:
        raise AssertionError("Raster image embedded in SVG")
    with Image.open(png) as preview:
        if preview.size != (w*2, h*2):
            raise AssertionError("Invalid PNG output dimensions")
    return {
        "style": style, "primitives": count,
        "svg": svg.name, "svg_sha256": sha256(svg), "svg_bytes": svg.stat().st_size,
        "png": png.name, "png_sha256": sha256(png), "png_bytes": png.stat().st_size,
    }


def make_comparison(original: Path, outputs: list[dict], out: Path) -> None:
    size, pad, foot = 440, 18, 54
    grid = Image.new("RGB", (2*(size+pad*2), 2*(size+pad*2+foot)), "#eeeeed")
    items = [("Original / GC001", original)] + [(o["style"], out / o["png"]) for o in outputs]
    for idx, (label, source) in enumerate(items):
        tile = Image.new("RGB", (size+pad*2, size+pad*2+foot), "#ffffff")
        with Image.open(source) as img:
            art = ImageOps.contain(img.convert("RGBA"), (size,size), Image.Resampling.LANCZOS)
            bg = Image.new("RGB", art.size, "#f7f6f2")
            bg.paste(art, mask=art.getchannel("A"))
            tile.paste(bg, (pad+(size-art.width)//2, pad+(size-art.height)//2))
        ImageDraw.Draw(tile).text((pad, size+pad+16), label, fill="#222222")
        grid.paste(tile, ((idx%2)*(size+pad*2), (idx//2)*(size+pad*2+foot)))
    grid.save(out / "comparison_grid.png")


def main() -> None:
    cli=argparse.ArgumentParser()
    cli.add_argument("--source", type=Path, required=True)
    cli.add_argument("--out", type=Path, required=True)
    args=cli.parse_args()
    original=args.source.resolve()
    arr=read_source(original)
    output=args.out.resolve()
    output.mkdir(parents=True, exist_ok=True)
    copied=output/"GC001_source.png"
    if original!=copied:
        shutil.copy2(original,copied)
    assert sha256(copied).lower()==SOURCE_SHA
    records=[]
    for mode in STYLES:
        svg=output/f"GC001_{mode}.svg"
        png=output/f"GC001_{mode}.png"
        records.append(render_style(arr, mode, svg, png))
    make_comparison(copied, records, output)
    manifest={
        "scope":"Generativepy isolated art study, not Minimalizer Core nor production engine",
        "package":"generativepy", "version":"50.0", "license":"MIT",
        "image_input":"GC001_source.png", "source_sha256":SOURCE_SHA,
        "source_size":[340,340],"all_non_generative":True,
        "models_loaded":False, "styling_rules":"deterministic original-image sampling",
        "styles":records,"comparison_grid":{
            "file":"comparison_grid.png",
            "sha256":sha256(output/"comparison_grid.png"),
            "bytes":(output/"comparison_grid.png").stat().st_size},
    }
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PASS","results":[(r["style"],r["primitives"]) for r in records],
                      "comparison_sha256":manifest["comparison_grid"]["sha256"]},ensure_ascii=False))

if __name__=="__main__":
    main()
