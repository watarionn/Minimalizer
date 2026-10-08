"""Assemble existing, independently produced Minimalizer Art Modes into a review atlas.

Uses only original PNG outputs; never re-renders or alters the source images.
Outputs a 4x3 landscape atlas, a 2x6 mobile atlas, and a SHA-verified manifest.

python tools/research/build_art_modes_gallery.py --root DRIVE_MINIMALIZER --out DRIVE_GALLERY
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ORIGINAL_SHA = "75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e"
STYLES = [
    ("Original", "SOURCE", "GC001", "PyFreeform_PoC_20261008", "GC001_source.png", None),
    ("pyfreeform", "COLOR DOTS", "1,223 cells", "PyFreeform_PoC_20261008", "GC001_color_dots.png", "#C67C48"),
    ("pyfreeform", "LINES", "1,222 cells", "PyFreeform_PoC_20261008", "GC001_lines.png", "#C67C48"),
    ("pyfreeform", "MOSAIC", "1,225 cells", "PyFreeform_PoC_20261008", "GC001_mosaic.png", "#C67C48"),
    ("pyfreeform", "SHAPES", "1,225 cells", "PyFreeform_PoC_20261008", "GC001_shapes.png", "#C67C48"),
    ("generativepy", "CIRCLE FIELD", "784 circles", "Generativepy_PoC_20261008", "GC001_circle_field.png", "#497F82"),
    ("generativepy", "GEOMETRIC BLOCKS", "624 quads", "Generativepy_PoC_20261008", "GC001_geometric_blocks.png", "#497F82"),
    ("generativepy", "FLOW / RIBBONS", "1,156 curves", "Generativepy_PoC_20261008", "GC001_flow_ribbons.png", "#497F82"),
    ("vsketch", "CONTOUR LINE", "145 contours", "Vsketch_PoC_20261008", "GC001_contour_line.png", "#686989"),
    ("vsketch", "HATCH SHADE", "2,167 strokes", "Vsketch_PoC_20261008", "GC001_hatch_shade.png", "#686989"),
    ("vsketch", "SPARSE OUTLINE", "60 contours", "Vsketch_PoC_20261008", "GC001_sparse_outline.png", "#686989"),
]

BG = "#ECECE7"
INK = "#232723"
MUTED = "#757873"
WHITE = "#FCFCFA"
PANEL = "#F6F5F1"
LINE = "#D9DAD4"


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def font(size: int, bold=False):
    family = ("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf")
    if Path(family).exists():
        return ImageFont.truetype(family, size)
    return ImageFont.load_default()


def source_info(root: Path) -> list[dict]:
    rows = []
    for i, (family, title, count, folder, basename, color) in enumerate(STYLES):
        p = root / folder / basename
        if not p.is_file():
            raise FileNotFoundError(f"Missing required source image: {p}")
        with Image.open(p) as img:
            img.verify()
        with Image.open(p) as img:
            if img.width < 150 or img.height < 150:
                raise ValueError("Unexpected small source: " + basename)
            dimension = [img.width, img.height]
        sha = hash_file(p)
        if i == 0 and sha.lower() != ORIGINAL_SHA:
            raise ValueError("Original GC001 source differs from Golden canonical file")
        rows.append({
            "index": i,
            "family": family,
            "style": title,
            "primitives": count,
            "path": p,
            "source_relative_path": f"{folder}/{basename}",
            "sha256": sha,
            "size": dimension,
            "color": color,
        })
    return rows


def fit_source(photo: Image.Image, width: int, height: int) -> Image.Image:
    rgba = ImageOps.contain(photo.convert("RGBA"), (width, height), Image.Resampling.LANCZOS)
    onwhite = Image.new("RGBA", rgba.size, "#FFFFFF")
    onwhite.alpha_composite(rgba)
    return onwhite.convert("RGB")


def draw_tile(draw: ImageDraw.ImageDraw, canvas: Image.Image, rect, source: dict | None, nth: int,
              page_type: str):
    x, y, w, h = rect
    draw.rounded_rectangle((x, y, x + w, y + h), radius=7, fill=WHITE, outline=LINE, width=2)
    padding = 15
    label_height = 119 if page_type == "mobile" else 103
    photo_area = h - label_height - 2*padding
    if source is None:
        draw.line((x+25, y+35, x+w-25, y+35), fill=INK, width=2)
        draw.text((x+28, y+52), "THE COLLECTION", fill=MUTED, font=font(22, True))
        for j, label in enumerate(["04   PYFREEFORM", "03   GENERATIVEPY", "03   VSKETCH"]):
            draw.text((x+28, y+114+j*44), label, fill=INK, font=font(21, True))
        draw.text((x+28, y+h-100), "ONE SOURCE. TEN DIRECTIONS.", fill=MUTED, font=font(17))
        draw.text((x+28, y+h-70), "No generative image filling.", fill=MUTED, font=font(16))
        return

    with Image.open(source["path"]) as img:
        fitted = fit_source(img, w - 2*padding, photo_area)
    image_x = x + (w-fitted.width)//2
    image_y = y + padding + (photo_area-fitted.height)//2
    canvas.paste(fitted, (image_x, image_y))
    baseline = y + h - label_height
    draw.line((x+padding, baseline-12, x+w-padding, baseline-12), fill=LINE, width=1)
    category = source["family"].upper()
    draw.text((x+padding+1, baseline), f"{nth:02d}  /  {category}", fill=source["color"] or MUTED,
              font=font(17, True))
    draw.text((x+padding, baseline+29), source["style"], fill=INK, font=font(24, True))
    draw.text((x+padding, baseline+64), source["primitives"], fill=MUTED, font=font(18))


def create_atlas(rows: list[dict], output: Path, mobile: bool) -> None:
    cols, num_rows = (2, 6) if mobile else (4, 3)
    tile_w, tile_h = (440, 514) if mobile else (432, 496)
    gap, margin, header, footer = (18, 30, 164, 96) if mobile else (22, 48, 166, 90)
    width = cols * tile_w + (cols-1)*gap + margin*2
    height = header + num_rows*tile_h + (num_rows-1)*gap + footer
    canvas = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(canvas)
    draw.text((margin, 35), "MINIMALIZER  /  ART ATLAS", fill=INK, font=font(38 if mobile else 46, True))
    draw.text((margin, 91), "GC001 / KYOKO     •     1 ORIGINAL     •     3 LIBRARIES     •     10 STYLES",
              fill=MUTED, font=font(16 if mobile else 20, False))
    draw.line((margin, 135, width-margin, 135), fill=INK, width=2)
    for idx in range(cols*num_rows):
        col, row = idx % cols, idx // cols
        x = margin + col*(tile_w+gap)
        y = header + row*(tile_h+gap)
        data = rows[idx] if idx < len(rows) else None
        draw_tile(draw, canvas, (x,y,tile_w,tile_h), data, idx+1, "mobile" if mobile else "desktop")
    draw.line((margin, height-footer+24, width-margin, height-footer+24), fill=LINE, width=2)
    draw.text((margin, height-footer+45),
              "Source pixel colors and line geometry are shown without further artistic edits.",
              fill=MUTED, font=font(17 if mobile else 18))
    canvas.save(output, format="PNG", optimize=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    rows = source_info(args.root.resolve())
    dests = [("gallery_landscape_4x3.png", False), ("gallery_mobile_2x6.png", True)]
    for name, mobile in dests:
        create_atlas(rows, args.out / name, mobile)
    manifest = {
        "project": "Minimalizer Art Modes / 10-style gallery",
        "created_at_jst": "2026-10-08",
        "source_sha256": ORIGINAL_SHA,
        "reference": "Original GC001 + 4 pyfreeform + 3 generativepy + 3 vsketch",
        "preserved_existing_png_content": True,
        "no_generative_ai": True,
        "sources": [{k:v for k,v in item.items() if k not in ("path", "color")} for item in rows],
        "artifacts": [
            {"filename": name, "sha256": hash_file(args.out/name),
             "bytes": (args.out/name).stat().st_size}
            for name, _ in dests
        ],
    }
    (args.out/"manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "source_images": len(rows),
        "libraries": sorted({row["family"] for row in rows if row["family"] != "Original"}),
        "artifacts": manifest["artifacts"],
        "output": str(args.out),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
