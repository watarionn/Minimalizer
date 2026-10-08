"""Image-only Minimalizer Art Modes research: imgrit, mosaicpic, Pixora and three fusions.

Exact original GC001 is used. No generative img2img or inpainting, no production imports.
Dependencies installed only in an isolated research target, never shipped with Browser.

python -W error tools/research/art_modes_new_libraries_poc.py \
  --root "G:/マイドライブ/chatGPT及びCodex用/Minimalizer" \
  --out "G:/マイドライブ/chatGPT及びCodex用/Minimalizer/NewLibrariesAndFusion_PoC_20261008"
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

import cv2
import imgrit
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont
from mosaicpic import ConversionSession, Palette, Color, load_image
from pixora import MeanBlock, ModeBlock, pixelize

SHA = "75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e"
ROOT_ORIGINAL = "SA1041_FullCharacterSVG_20261008/original_inputs/GC001_source.png"
W, H = 340, 340
VERSION = {"imgrit": "0.2.2", "mosaicpic": "0.6.0", "pixora": "0.4"}
BG = "#F4F2EC"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rgb(image):
    return image.convert("RGB")


def discover_palette(image: Image.Image, target=22):
    """Palette colors sampled solely from observed original pixels, including saturated details."""
    quantized = image.quantize(colors=target, method=Image.Quantize.MEDIANCUT)
    colors = quantized.convert("RGB").getcolors(maxcolors=256)
    if not colors:
        raise ValueError("Quantization produced no palette")
    choices = [col for _, col in sorted(colors, reverse=True)]
    a = np.asarray(image, dtype=np.uint8)
    hsv = cv2.cvtColor(a, cv2.COLOR_RGB2HSV)
    # Preserve bright greens and vivid blue regions when those colors exist.
    for lo, hi in ((36, 87), (90, 135), (0, 20)):
        mask = (hsv[:, :, 0] >= lo) & (hsv[:, :, 0] <= hi) & (hsv[:, :, 1] >= 100)
        points = a[mask]
        if len(points):
            med = tuple(int(x) for x in np.median(points, axis=0).astype(int))
            choices.append(med)
    clean = list(dict.fromkeys(tuple(map(int, c)) for c in choices))
    return Palette([Color(c, f"Original-{i:02d}") for i, c in enumerate(clean)]), clean


def resize_nearest(arr):
    return Image.fromarray(np.asarray(arr, dtype=np.uint8), mode="RGB").resize((W,H), Image.Resampling.NEAREST)


def tint_overlay(base, line_painting, intensity=0.85, spatial_mask=None):
    """Use actual dark strokes as ink alpha; do not modify its geometric paths."""
    line = line_painting.convert("RGBA").resize((W,H), Image.Resampling.LANCZOS)
    # vsketch's resvg preview is transparent outside the black ink.
    # RGB-conversion alone would turn those fully transparent pixels black,
    # falsely applying ink across the entire canvas.
    opaque_ink = np.asarray(line.getchannel("A"), dtype=np.float32) / 255.0
    on_white = Image.new("RGBA", (W,H), "#FFFFFF")
    on_white.alpha_composite(line)
    grayscale = np.asarray(on_white.convert("L"), dtype=np.uint8)
    darkness = 1.0 - grayscale.astype(np.float32)/255.0
    opacity = np.clip(darkness * opaque_ink * intensity, 0.0, 1.0)
    if spatial_mask is not None:
        opacity *= np.asarray(spatial_mask, dtype=np.float32)
    mask = Image.fromarray(np.uint8(np.round(opacity * 255)), mode="L")
    return Image.composite(Image.new("RGB", (W,H), "#181F1F"), rgb(base), mask)


def saturated_dots_overlay(base, dot_art):
    dot = rgb(dot_art).resize((W,H), Image.Resampling.BILINEAR)
    # Pyfreeform dots are colorful marks over near-white canvas; reveal only actual marks.
    diff = ImageChops.difference(dot, Image.new("RGB", (W,H), "#FFFFFF"))
    alpha = np.asarray(diff.convert("L")).astype(np.float32)/255.0
    alpha = np.clip(alpha * 0.7, 0, 0.72)
    return Image.composite(dot, rgb(base), Image.fromarray(np.uint8(alpha*255), mode="L"))


def perceptual_mask(original):
    """Source-observed local-contrast mask: suppress hatching in flat regions."""
    gray = cv2.cvtColor(np.asarray(original), cv2.COLOR_RGB2GRAY).astype(np.float32)
    mean = cv2.GaussianBlur(gray, (11, 11), 0)
    contrast = np.sqrt(np.maximum(0, cv2.GaussianBlur(gray**2, (11,11), 0) - mean**2))
    return np.clip((contrast - 7.0)/16.0, 0, 1)


def font(size, bold=False):
    path = Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf")
    return ImageFont.truetype(str(path), size) if path.is_file() else ImageFont.load_default()


def make_atlas(records, folder: Path, output_name: str, columns: int):
    tile_w, image_side, gap, pad, header = 356, 304, 16, 22, 127
    tile_h=414
    count=len(records)
    rows=(count + columns-1)//columns
    width=2*pad+columns*tile_w+(columns-1)*gap
    height=header+rows*tile_h+(rows-1)*gap+66
    sheet=Image.new("RGB", (width,height), "#E9E8E3")
    draw=ImageDraw.Draw(sheet)
    draw.text((pad,24),"MINIMALIZER  /  NEW ART LAB",font=font(34,True),fill="#222722")
    draw.text((pad,79),"One verified original • 3 libraries • 3 cross-style experiments",font=font(18),fill="#666B67")
    draw.line((pad,112,width-pad,112),fill="#333A34",width=2)
    for n,rec in enumerate(records):
        x=pad+(n%columns)*(tile_w+gap)
        y=header+(n//columns)*(tile_h+gap)
        draw.rounded_rectangle((x,y,x+tile_w,y+tile_h), radius=8, fill="#FCFCFA",outline="#C9CAC3",width=1)
        with Image.open(folder / rec["file"]) as im:
            image=rgb(im).resize((image_side,image_side), Image.Resampling.LANCZOS)
        sheet.paste(image,(x+(tile_w-image_side)//2,y+12))
        draw.line((x+15,y+326,x+tile_w-15,y+326),fill="#D8D8D3")
        draw.text((x+17,y+338),f'{n+1:02d}  /  {rec["family"].upper()}',font=font(16,True),fill="#65716F")
        draw.text((x+17,y+361),rec["label"],font=font(20,True),fill="#212522")
    draw.text((pad,height-39),"Independent deterministic art experiments. No AI img2img or new content.",font=font(16),fill="#626760")
    sheet.save(folder/output_name,optimize=True)


def run(root: Path, output: Path):
    source=root/ROOT_ORIGINAL
    if not source.exists() or sha(source).lower()!=SHA:
        raise ValueError("Canonical GC001 source missing or SHA mismatch")
    output.mkdir(parents=True,exist_ok=True)
    original=rgb(Image.open(source))
    if original.size!=(W,H):
        raise ValueError("Unexpected original image dimensions")
    original.save(output/"00_original.png")
    records=[]

    def save(name, family, label, image, **metrics):
        target=output/name
        result=rgb(image)
        if result.size!=(W,H):
            raise ValueError(f"Bad output dimensions: {name} {result.size}")
        result.save(target,optimize=True)
        records.append({"family":family,"label":label,"file":name,"sha256":sha(target),"bytes":target.stat().st_size,**metrics})
        return result

    save("00_original.png","Source","Kyoko / GC001",original,source_sha256=SHA)

    # imgrit: deterministic site sampling, and an independent palette reduction.
    random.seed(20261008)
    np.random.seed(20261008)
    voronoi=imgrit.voronoi_mosaic(original,num_regions=160,line_width=1,mode="color",random=True)
    voronoi=save("01_imgrit_voronoi.png","imgrit","Voronoi / 160 cells",voronoi,regions=160,seed=20261008)
    np.random.seed(20261008)
    warhol=save("02_imgrit_warhol.png","imgrit","Warhol / 7 colors",
                imgrit.warhol_effect(original,n_clusters=7),colors=7)

    # mosaicpic: source-based palette with observed saturated colors.
    palette, choices=discover_palette(original,24)
    image=load_image(str(source))
    session=ConversionSession(image,palette,canvas_size=(34,34))
    session.convert("classic")
    mosaic_classic=save("03_mosaicpic_classic.png","mosaicpic","Classic / source palette",
                        resize_nearest(session.canvas.to_array()),
                        palette_size=len(choices),similarity_delta_e=round(session.similarity_score,3))
    session.convert("dithered")
    mosaic_dithered=save("04_mosaicpic_dithered.png","mosaicpic","Dithered / source palette",
                         resize_nearest(session.canvas.to_array()),
                         palette_size=len(choices),similarity_delta_e=round(session.similarity_score,3))

    # Independent semantic-color preservation micro-test, not an automatic segmentation.
    # Pin a color sampled from a green source pixel in the observed central tie region.
    original_pixels=np.asarray(original,dtype=np.uint8)
    hsvp=cv2.cvtColor(original_pixels,cv2.COLOR_RGB2HSV)
    yy, xx=np.mgrid[:H,:W]
    tie_candidates=((xx>=140)&(xx<203)&(yy>=210)&(yy<335)&
                    (hsvp[:,:,0]>=33)&(hsvp[:,:,0]<=89)&(hsvp[:,:,1]>130)&
                    (original_pixels[:,:,1]>original_pixels[:,:,0]*1.15))
    ys,xs=np.where(tie_candidates)
    if not len(xs):
        raise AssertionError("No original green sample found in selected tie region")
    select=int(np.argmax(original_pixels[ys,xs,1].astype(int)-original_pixels[ys,xs,0].astype(int)))
    px,py=int(xs[select]),int(ys[select])
    cx,cy=px//10,py//10
    actual=tuple(int(i) for i in original_pixels[py,px,:])
    probe=ConversionSession(image,palette,canvas_size=(34,34))
    probe.convert("classic")
    before=[int(n) for n in probe.canvas.to_array()[cy,cx]]
    probe.pin(cx,cy,Color(actual,"Source-green-tie"))
    probe.reconvert("dithered",keep_pins=True)
    after=[int(n) for n in probe.canvas.to_array()[cy,cx]]
    if after!=list(actual) or (cx,cy) not in probe.get_pinned_cells():
        raise AssertionError("Pinned original tie color was not preserved across reconvert")
    pin_record={"coordinate_source":[px,py],"coordinate_cell":[cx,cy],
                "actual_original_rgb":list(actual),"before_rgb":before,
                "after_rgb":after,"preserved_after_dithered_reconvert":True,
                "not_a_semantic_segmentation":True}
    (output/"pin_probe.json").write_text(json.dumps(pin_record,indent=2)+"\n",encoding="utf-8")

    # pixora official API: independent source-based mean and mode block results.
    pixel_mean=save("05_pixora_mean.png","pixora","Mean Block / 10px",
                    pixelize(str(source),algorithm=MeanBlock(pixel_size=10)),pixel_size=10)
    pixel_mode=save("06_pixora_mode.png","pixora","Mode Block / 10px",
                    pixelize(str(source),algorithm=ModeBlock(pixel_size=10)),pixel_size=10)

    # Fusion A: preserve mosaic palette blocks and overlay *existing* original-derived vsketch lines.
    contour=root/"Vsketch_PoC_20261008"/"GC001_contour_line.png"
    hatch=root/"Vsketch_PoC_20261008"/"GC001_hatch_shade.png"
    dots=root/"PyFreeform_PoC_20261008"/"GC001_color_dots.png"
    for asset in (contour,hatch,dots):
        if not asset.is_file():
            raise FileNotFoundError(f"Existing research artifact missing: {asset}")

    sketch=save("07_fusion_mosaic_sketch.png","Fusion","Mosaic + Contour",
                tint_overlay(mosaic_classic,Image.open(contour),intensity=0.72),
                components=["mosaicpic-classic","vsketch-contour"])
    pop=save("08_fusion_voronoi_pop.png","Fusion","Voronoi + Color Dots",
             saturated_dots_overlay(voronoi,Image.open(dots)),
             components=["imgrit-voronoi","pyfreeform-color-dots"])
    engraving=save("09_fusion_pixel_engraving.png","Fusion","Pixel + Sparse Hatching",
                   tint_overlay(pixel_mean,Image.open(hatch),intensity=0.68,
                                spatial_mask=perceptual_mask(original)),
                   components=["pixora-mean","vsketch-hatch","source-local-contrast"])

    assert len(records)==10
    make_atlas(records,output,"gallery_landscape_5x2.png",columns=5)
    make_atlas(records,output,"gallery_mobile_2x5.png",columns=2)

    manifest={
        "project":"Minimalizer - 3 new art libraries + 3 fusion PoC",
        "source":"Original GC001 (untouched source bytes)",
        "source_sha256":SHA,
        "library_versions":VERSION,
        "license":{"imgrit":"BSD-3-Clause","mosaicpic":"MIT","pixora":"MIT"},
        "fusions_use_only_preexisting_observed_pixels_or_strokes":True,
        "minimalizer_production_changed":False,
        "tie_pin_probe":pin_record,
        "tie_pin_probe_sha256":sha(output/"pin_probe.json"),
        "records":records,
        "gallery":[{"file":f,"sha256":sha(output/f),"bytes":(output/f).stat().st_size}
                   for f in ("gallery_landscape_5x2.png","gallery_mobile_2x5.png")],
    }
    (output/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PASS","styles":len(records)-1,"fusions":3,
                      "delta_e":[r.get("similarity_delta_e") for r in records if r["family"]=="mosaicpic"],
                      "gallery_sha":[x["sha256"] for x in manifest["gallery"]]},ensure_ascii=False))


def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--root",type=Path,required=True)
    cli.add_argument("--out",type=Path,required=True)
    args=cli.parse_args()
    run(args.root,args.out)


if __name__=="__main__":
    main()
