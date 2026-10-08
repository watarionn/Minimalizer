"""Minimalizer Semantic Art Mixer v1, isolated non-generative research.

Unlike a stack of redundant mosaic filters, the four roles are independent:
Shape -> Stroke -> Texture -> Color Control. Uses only previously approved
original-derived research PNGs and original GC001 RGB for the tie lock.
Never import a production LocalWorker entrypoint or any generative model.

python -W error tools/research/semantic_art_mixer_v1.py \
  --root PRIVATE_DRIVE_MINIMALIZER --out PRIVATE_DRIVE_OUTPUT
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

SOURCE_SHA = "75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e"
SOURCE_REL = "SA1041_FullCharacterSVG_20261008/original_inputs/GC001_source.png"
SIZE = (340, 340)
TIE_ROI = (144, 219, 196, 340)  # x0, y0, x1, y1. GC001-specific, manually inspected.
# Each source comes from earlier actual, hash-recorded research. Not installed as a renderer.
ASSETS = {
    "shape.voronoi": ("NewLibrariesAndFusion_PoC_20261008", "01_imgrit_voronoi.png"),
    "shape.mosaic": ("NewLibrariesAndFusion_PoC_20261008", "03_mosaicpic_classic.png"),
    "shape.pixel": ("NewLibrariesAndFusion_PoC_20261008", "05_pixora_mean.png"),
    "shape.blocks": ("Generativepy_PoC_20261008", "GC001_geometric_blocks.png"),
    "stroke.contour": ("Vsketch_PoC_20261008", "GC001_contour_line.png"),
    "stroke.sparse": ("Vsketch_PoC_20261008", "GC001_sparse_outline.png"),
    "stroke.hatch": ("Vsketch_PoC_20261008", "GC001_hatch_shade.png"),
    "texture.dots": ("PyFreeform_PoC_20261008", "GC001_color_dots.png"),
}
ROLES = ("shape", "stroke", "texture", "color")
COLORS = ("none", "source_tie_lock")
DEFAULT_RECIPES = (
    {"id": "voronoi_ink_dots", "shape": "voronoi", "stroke": "contour", "texture": "dots", "color": "source_tie_lock"},
    {"id": "mosaic_sparse", "shape": "mosaic", "stroke": "sparse", "texture": "none", "color": "source_tie_lock"},
    {"id": "pixel_hatch_dots", "shape": "pixel", "stroke": "hatch", "texture": "dots", "color": "source_tie_lock"},
    {"id": "geometric_ink", "shape": "blocks", "stroke": "contour", "texture": "none", "color": "source_tie_lock"},
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_sha(root: Path, key: str) -> str:
    """Fetch the exact prior result SHA recorded by its own research manifest."""
    folder, name = ASSETS[key]
    manifest = json.loads((root / folder / "manifest.json").read_text(encoding="utf-8"))
    if folder == "NewLibrariesAndFusion_PoC_20261008":
        candidates = [(r["file"], r["sha256"]) for r in manifest["records"]]
    elif folder in ("Generativepy_PoC_20261008", "Vsketch_PoC_20261008"):
        candidates = [(r["png"], r["png_sha256"]) for r in manifest["styles"]]
    elif folder == "PyFreeform_PoC_20261008":
        candidates = [(r["file"], r["sha256"]) for r in manifest["png_previews"]]
    else:
        raise AssertionError(folder)
    result = [hash_value for file, hash_value in candidates if file == name]
    if len(result) != 1:
        raise ValueError(f"Source is absent or duplicated in its verified manifest: {key}")
    return result[0]


def load_assets(root: Path) -> tuple[Image.Image, dict[str, Image.Image], list[dict]]:
    original_path = root / SOURCE_REL
    if sha256(original_path).lower() != SOURCE_SHA:
        raise ValueError("GC001 original source SHA mismatch; abort")
    with Image.open(original_path) as img:
        original = img.convert("RGB")
    if original.size != SIZE:
        raise ValueError("Expected original GC001 dimensions 340x340")
    loaded, records = {}, []
    for key, (folder, name) in ASSETS.items():
        path = root / folder / name
        expected = manifest_sha(root, key)
        actual = sha256(path)
        if actual.lower() != expected.lower():
            raise ValueError(f"Asset has changed since its research manifest: {key}")
        with Image.open(path) as im:
            if im.width < 150 or im.height < 150:
                raise ValueError(f"Invalid source size: {key}")
            loaded[key] = im.convert("RGBA").resize(SIZE, Image.Resampling.LANCZOS)
        records.append({"role_asset": key, "path": f"{folder}/{name}", "sha256": actual})
    return original, loaded, records


def observed_green(pixels: np.ndarray) -> np.ndarray:
    """A measured HSV class, not a learned segmentation or a guessed part."""
    hsv = cv2.cvtColor(pixels, cv2.COLOR_RGB2HSV)
    return ((hsv[:, :, 0] >= 32) & (hsv[:, :, 0] <= 88) &
            (hsv[:, :, 1] >= 115) &
            (pixels[:, :, 1].astype(np.float32) > pixels[:, :, 0].astype(np.float32) * 1.12))


def roi_mask(size: tuple[int, int], roi: tuple[int, int, int, int]) -> np.ndarray:
    width, height = size
    x0, y0, x1, y1 = roi
    if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
        raise ValueError("Out-of-bounds / empty tie ROI")
    result = np.zeros((height, width), dtype=bool)
    result[y0:y1, x0:x1] = True
    return result


def observed_tie_mask(source: Image.Image, roi=TIE_ROI, min_pixels=80) -> np.ndarray:
    """Connected dominant source-green region INSIDE a predeclared manual tie ROI."""
    array = np.asarray(source.convert("RGB"), dtype=np.uint8)
    interest = observed_green(array) & roi_mask(source.size, roi)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(interest.astype(np.uint8), 8)
    if count <= 1:
        raise ValueError("No source tie region detected in manual ROI")
    selected = int(np.argmax(stats[1:, cv2.CC_STAT_AREA])) + 1
    area = int(stats[selected, cv2.CC_STAT_AREA])
    # A long necktie may legitimately occupy >30% of a narrow manual ROI.
    if not (min_pixels <= area <= 0.70 * (roi[2]-roi[0])*(roi[3]-roi[1])):
        raise ValueError(f"Implausible source tie mask size: {area}")
    return labels == selected


def protect_original_tie(
    rendered: Image.Image, source: Image.Image, mask: np.ndarray,
    roi: tuple[int, int, int, int] = TIE_ROI,
) -> tuple[Image.Image, dict]:
    """Restore source-observed tie RGB and prevent green growth within manual ROI.

    This is a research-level color constraint, not full automatic part segmentation.
    Pixels outside mask that became green within ROI are restored from the *original*.
    No synthetic values are invented, and source tie pixels retain exact original RGB.
    """
    original = np.asarray(source.convert("RGB"), dtype=np.uint8)
    result = np.asarray(rendered.convert("RGB"), dtype=np.uint8).copy()
    if original.shape != result.shape or mask.shape != original.shape[:2]:
        raise ValueError("Source, image and mask dimensions must agree")
    bounds = roi_mask(source.size, roi)
    target = observed_green(original) & bounds
    if np.any(mask & ~target):
        raise ValueError("Mask includes colors outside the observed original green region")
    outside_before = observed_green(result) & bounds & ~target
    changed_before = int(np.count_nonzero(np.any(result[mask] != original[mask], axis=1)))
    result[mask] = original[mask]
    # Restore only excess green within the declared small ROI; protect against
    # a broadened lime patch. This does not fix other colors or outside-ROI issues.
    result[outside_before] = original[outside_before]
    outside_after = observed_green(result) & bounds & ~target
    changed_after = int(np.count_nonzero(np.any(result[mask] != original[mask], axis=1)))
    metrics = {
        "roi": list(roi),
        "source_mask_pixels": int(mask.sum()),
        "tie_pixels_changed_before": changed_before,
        "tie_pixels_changed_after": changed_after,
        "green_pixels_outside_source_mask_before": int(outside_before.sum()),
        "green_pixels_outside_source_mask_after": int(outside_after.sum()),
        "restored_green_expansion_pixels": int(outside_before.sum()),
        "restoration_uses_original_rgb_only": True,
        "tie_mask_is_manual_roi_plus_connected_source_color": True,
    }
    if changed_after != 0 or outside_after.any():
        raise AssertionError("Source RGB protection or green growth limit failed")
    return Image.fromarray(result, "RGB"), metrics


def add_stroke(base: Image.Image, stroke: Image.Image, opacity=0.68) -> Image.Image:
    """Overlay black ink using its REAL premultiplied transparency, not RGB of alpha=0."""
    pixels = np.asarray(stroke.convert("RGBA"), dtype=np.uint8)
    alpha = pixels[:, :, 3].astype(np.float32) / 255.0
    luminance = np.asarray(stroke.convert("RGB").convert("L"), dtype=np.float32)/255.0
    ink = (1 - luminance) * alpha * float(opacity)
    a = np.uint8(np.clip(ink, 0, 1) * 255)
    return Image.composite(Image.new("RGB", SIZE, "#182122"), base.convert("RGB"), Image.fromarray(a, "L"))


def add_texture(base: Image.Image, texture: Image.Image, opacity=0.23) -> Image.Image:
    """Only sample existing source-derived colored dots; never erase regions as transparent black."""
    pixels = np.asarray(texture.convert("RGBA"), dtype=np.uint8)
    # Render source style over white, then evaluate visible colored shapes.
    bg = Image.new("RGBA", SIZE, "#FFFFFF")
    bg.alpha_composite(texture.convert("RGBA"))
    visible = bg.convert("RGB")
    array = np.asarray(visible, dtype=np.uint8)
    strength = (255 - np.mean(array.astype(np.float32), axis=2))/255.0
    mask = Image.fromarray(np.uint8(np.clip(strength * opacity * 255, 0, 255)), "L")
    return Image.composite(visible, base.convert("RGB"), mask)


def validate_recipe(recipe: Mapping[str, str]) -> dict[str, str]:
    required = {"id", *ROLES}
    if set(recipe) != required:
        raise ValueError(f"Recipe must have exactly these fields: {sorted(required)}")
    ident = recipe["id"]
    if not ident.isascii() or not ident.replace("_", "").isalnum() or not ident[0].isalpha():
        raise ValueError("Recipe identifier must be a safe ASCII identifier")
    shape = "shape." + recipe["shape"]
    if shape not in ASSETS:
        raise ValueError("Unknown shape: " + recipe["shape"])
    stroke = recipe["stroke"]
    texture = recipe["texture"]
    if stroke != "none" and "stroke."+stroke not in ASSETS:
        raise ValueError("Unknown stroke")
    if texture != "none" and "texture."+texture not in ASSETS:
        raise ValueError("Unknown texture")
    if recipe["color"] not in COLORS:
        raise ValueError("Unknown color controller")
    return dict(recipe)


def render(recipe: Mapping[str, str], source: Image.Image,
           assets: Mapping[str, Image.Image], mask: np.ndarray) -> tuple[Image.Image, Image.Image, dict]:
    config = validate_recipe(recipe)
    base = assets["shape."+config["shape"]].convert("RGB")
    if config["stroke"] != "none":
        base = add_stroke(base, assets["stroke."+config["stroke"]])
    if config["texture"] != "none":
        base = add_texture(base, assets["texture."+config["texture"]])
    unlocked = base.copy()
    if config["color"] == "source_tie_lock":
        locked, details = protect_original_tie(base, source, mask)
    else:
        locked = base
        details = {"source_mask_pixels": int(mask.sum()), "tie_color_protection": "disabled"}
    return unlocked, locked, details


def font(size, bold=False):
    p = Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf")
    return ImageFont.truetype(str(p), size) if p.is_file() else ImageFont.load_default()


def gallery(items: list[tuple[str, Path]], dest: Path):
    cols, thumb, xpad, ypad = 3, 300, 20, 100
    cell_w, cell_h = thumb+2*xpad, thumb+ypad
    lines = (len(items) + cols - 1)//cols
    page = Image.new("RGB", (cols*cell_w+48, lines*cell_h+136), "#EEEEE9")
    d = ImageDraw.Draw(page)
    d.text((28,24), "MINIMALIZER / SEMANTIC ART MIXER", font=font(32,True), fill="#253029")
    d.text((28,70), "Shape + Stroke + Texture + Color Lock  |  Original GC001", font=font(16), fill="#667066")
    for i, (label, path) in enumerate(items):
        x=24+(i%cols)*cell_w
        y=124+(i//cols)*cell_h
        d.rounded_rectangle((x,y,x+cell_w-7,y+cell_h-7), radius=8, fill="#FFFFFF", outline="#D5D8D0")
        with Image.open(path) as im:
            art = ImageOps.contain(im.convert("RGB"), (thumb,thumb), Image.Resampling.LANCZOS)
        page.paste(art,(x+xpad+(thumb-art.width)//2,y+12+(thumb-art.height)//2))
        d.line((x+10,y+thumb+25,x+cell_w-15,y+thumb+25),fill="#D5D8D0")
        d.text((x+12,y+thumb+40),label, font=font(17,True),fill="#303632")
    page.save(dest,optimize=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--recipes",type=Path,default=None)
    args = ap.parse_args()
    root=args.root.resolve()
    output=args.out.resolve()
    output.mkdir(parents=True,exist_ok=True)
    source, assets, sources = load_assets(root)
    mask = observed_tie_mask(source)
    recipes = json.loads(args.recipes.read_text(encoding="utf-8")) if args.recipes else list(DEFAULT_RECIPES)
    if not isinstance(recipes, list) or not recipes or len(recipes)>32:
        raise ValueError("Expected 1..32 recipes")
    checked=[validate_recipe(item) for item in recipes]
    ids=[r["id"] for r in checked]
    if len(ids)!=len(set(ids)):
        raise ValueError("Duplicate recipe identifiers")
    src_file = output/"00_original_GC001.png"
    source.save(src_file)
    items=[("ORIGINAL / GC001",src_file)]
    results=[]
    for recipe in checked:
        before, after, metrics = render(recipe,source,assets,mask)
        ident=recipe["id"]
        unprotected=output/(ident+"_without_lock.png")
        protected=output/(ident+"_tie_lock.png")
        before.save(unprotected,optimize=True)
        after.save(protected,optimize=True)
        items.extend([((ident+" / BEFORE").upper(),unprotected),
                      ((ident+" / PROTECTED").upper(),protected)])
        results.append({
            "recipe":recipe,"metrics":metrics,
            "unprotected":{"file":unprotected.name,"sha256":sha256(unprotected)},
            "protected":{"file":protected.name,"sha256":sha256(protected)},
        })
    gallery_path=output/"gallery_shape_stroke_texture_color.png"
    gallery(items,gallery_path)
    manifest={
        "project":"Minimalizer Semantic Art Mixer v1 / independent research",
        "source_sha256":SOURCE_SHA,
        "assets":sources,
        "roles":["Shape","Stroke","Texture","Color"],
        "color_lock_implementation":"manual GC001 ROI + connected original green mask + RGB restore",
        "not_semantic_segmentation":True,
        "not_production_integrated":True,
        "rendering_models_used":False,
        "results":results,
        "gallery":{"file":gallery_path.name,"sha256":sha256(gallery_path),"bytes":gallery_path.stat().st_size},
    }
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PASS","recipes":len(results),"tie_pixels":int(mask.sum()),
                      "unprotected_tie_errors":[r["metrics"].get("tie_pixels_changed_before") for r in results],
                      "lock_tie_errors":[r["metrics"].get("tie_pixels_changed_after") for r in results],
                      "gallery_sha256":manifest["gallery"]["sha256"]},ensure_ascii=False))


if __name__=="__main__":
    main()
