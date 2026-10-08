"""Collect all original GC001 and nineteen real Art Mode PNG results on two atlases.

No filter execution, no AI, no new imagery. Each input is checked against
its manifest before composing landscape 5x4 and mobile 2x10 view.
Run with Pillow-only dependencies from a scratch worktree:
 python tools/research/build_art_modes_19_gallery.py --root DRIVE_MINIMALIZER --out DRIVE_FOLDER
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw
from build_art_modes_gallery import source_info, draw_tile, BG, INK, MUTED, LINE, font

FAMILY_COLOR = {"imgrit": "#D47442", "mosaicpic": "#4C7F75",
                "pixora": "#926D3D", "Fusion": "#9B627F"}

DISPLAY = {
    "01_imgrit_voronoi.png": "VORONOI",
    "02_imgrit_warhol.png": "WARHOL COLORS",
    "03_mosaicpic_classic.png": "PALETTE CLASSIC",
    "04_mosaicpic_dithered.png": "PALETTE DITHER",
    "05_pixora_mean.png": "PIXEL MEAN",
    "06_pixora_mode.png": "PIXEL MODE",
    "07_fusion_mosaic_sketch.png": "MOSAIC SKETCH",
    "08_fusion_voronoi_pop.png": "VORONOI POP",
    "09_fusion_pixel_engraving.png": "PIXEL ENGRAVING",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sources(root: Path):
    old = source_info(root)
    original_manifest = json.loads(
        (root/"ArtModes_10Style_Gallery_20261008"/"manifest.json").read_text(encoding="utf-8")
    )
    by_file = {d["source_relative_path"]: d["sha256"] for d in original_manifest["sources"]}
    for row in old:
        key = row["source_relative_path"]
        if key not in by_file or sha(row["path"]) != by_file[key]:
            raise ValueError("Earlier 10-mode style file changed: " + key)

    newfolder = root/"NewLibrariesAndFusion_PoC_20261008"
    newmanifest = json.loads((newfolder/"manifest.json").read_text(encoding="utf-8"))
    new_styles = []
    for index, record in enumerate(newmanifest["records"][1:], start=len(old)):
        p = newfolder / record["file"]
        if not p.exists() or sha(p) != record["sha256"]:
            raise ValueError("New style output changed: " + record["file"])
        if record["file"] not in DISPLAY:
            raise ValueError("Unexpected style in manifest: " + record["file"])
        with Image.open(p) as im:
            im.verify()
        new_styles.append({
            "index": index, "family": record["family"],
            "style": DISPLAY[record["file"]], "primitives": record["label"],
            "path": p,
            "sha256":record["sha256"],
            "source_relative_path":str(p.relative_to(root)).replace("\\","/"),
            "color": FAMILY_COLOR[record["family"]],
        })
    allrows = old + new_styles
    if len(allrows)!=20:
        raise AssertionError(f"Expected original and nineteen style images; saw {len(allrows)}")
    if [r["family"] for r in allrows].count("Fusion")!=3:
        raise AssertionError("Three fusion examples missing")
    return allrows


def create_page(rows, dest, mobile=False):
    columns = 2 if mobile else 5
    tile_w,tile_h=(440,514) if mobile else (432,496)
    gap, margin, header, footer=(18,30,162,96) if mobile else (18,38,166,94)
    rows_count=len(rows)//columns
    width=columns*tile_w+(columns-1)*gap+margin*2
    height=header+rows_count*tile_h+(rows_count-1)*gap+footer
    canvas=Image.new("RGB",(width,height),BG)
    draw=ImageDraw.Draw(canvas)
    draw.text((margin,32),"MINIMALIZER / ART UNIVERSE",font=font(40 if mobile else 48,True),fill=INK)
    draw.text((margin,89),"1 ORIGINAL   +   19 STYLES   /   6 LIBRARY & FUSION GROUPS",
              font=font(17 if mobile else 20),fill=MUTED)
    draw.line((margin,134,width-margin,134),fill=INK,width=2)
    for i,item in enumerate(rows):
        col, row = i % columns, i // columns
        x=margin + col*(tile_w+gap)
        y=header + row*(tile_h+gap)
        draw_tile(draw, canvas, (x,y,tile_w,tile_h),item,i+1,"mobile" if mobile else "desktop")
    draw.line((margin,height-footer+24,width-margin,height-footer+24),fill=LINE,width=1)
    draw.text((margin,height-footer+45),"Existing results arranged only; no new drawing or generated image filling.",
              font=font(16),fill=MUTED)
    canvas.save(dest,format="PNG",optimize=True)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    root=args.root.resolve()
    output=args.out.resolve()
    output.mkdir(parents=True,exist_ok=True)
    allrows=sources(root)
    names=("gallery_19styles_landscape_5x4.png","gallery_19styles_mobile_2x10.png")
    for i,name in enumerate(names):
        create_page(allrows,output/name,mobile=(i==1))
    manifest={
        "project":"Minimalizer Art Universe / original plus nineteen art styles",
        "inputs":[
            {k:v for k,v in data.items() if k not in ("path","color")}
            for data in allrows
        ],
        "artifacts":[
            {"file":name,"bytes":(output/name).stat().st_size,"sha256":sha(output/name)}
            for name in names
        ],
        "all_inputs_sha256_verified":True,
        "source_artworks_reused_without_style_change":True,
        "style_count":19,
    }
    (output/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PASS","images":len(allrows),"styles":19,
                      "files":manifest["artifacts"]},ensure_ascii=False))


if __name__=="__main__":
    main()
