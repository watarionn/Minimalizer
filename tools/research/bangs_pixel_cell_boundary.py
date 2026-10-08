"""Pixel-cell SVG tracing: exact 340x340 observed-source footprint.

Use cv2 contours on an enlarged nearest-neighbor mask; contours run along
pixel-cell edges rather than original-pixel centers. SVG has NO facial plate,
no invented orange outside input, and no raster image embedding.
"""
from __future__ import annotations
import argparse,json,os,sys
from pathlib import Path
from xml.etree import ElementTree as ET
import cv2,numpy as np
from PIL import Image,ImageDraw
from semantic_art_mixer_v1 import load_assets,sha256
from semantic_art_mixer_v3_source_masks import load_observed_masks
from bangs_continuity_source_bridge import extract
from bangs_source_tonal_width_v2 import tonal_layers
from remove_subject_skin_underlay import NS

def pixel_cell_path(mask):
    """Find pixel-cell union boundaries at half-unit coordinates using 2x masks."""
    padded=np.pad(mask.astype(np.uint8),1)
    scaled=cv2.resize(padded,None,fx=2,fy=2,interpolation=cv2.INTER_NEAREST)
    contours,hier=cv2.findContours(scaled,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    commands=[];vertices=0
    # Pixel edge contours are shifted half a source pixel so coordinates
    # describe the UNION of source pixel cells, not their centers.
    for c in contours:
        if len(c)<3 or cv2.contourArea(c)<2:continue
        pts=c.reshape(-1,2)
        pts=(pts.astype(np.float64)-1.5)/2.0
        commands.append("M "+" L ".join(f"{x:g} {y:g}" for x,y in pts)+" Z")
        vertices+=len(pts)
    return " ".join(commands),len(commands),vertices

def build(layers,out):
    root=ET.Element("{%s}svg"%NS,{"viewBox":"0 0 340 340","width":"340","height":"340"})
    verts=0;contours=0
    for mask,color,kind in layers:
        d,n,v=pixel_cell_path(mask)
        if not d:continue
        ET.SubElement(root,"{%s}path"%NS,{"d":d,"fill":"#%02x%02x%02x"%color,
             "fill-rule":"evenodd","data-part":"hair","data-layer":kind})
        verts+=v;contours+=n
    ET.ElementTree(root).write(out,encoding="utf-8",xml_declaration=True)
    return verts,contours

def main():
    p=argparse.ArgumentParser()
    for n in ("root","out"):p.add_argument("--"+n,type=Path,required=True)
    a=p.parse_args()
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    original,_,_=load_assets(a.root);masks,_=load_observed_masks()
    _,whole=extract(original,masks)
    layers,_=tonal_layers(original,whole)
    folder=Path(os.environ.get("LOCALAPPDATA",""))/"Minimalizer/research/resvg-py-0.5.0"
    sys.path.insert(0,str(folder));import resvg_py
    records=[]
    for size,down in [(340,"native"),(680,"nearest"),(680,"bicubic")]:
        name=f"cell_{size}_{down}"
        svg=out/(name+".svg");vertices,contours=build(layers,svg)
        img=out/(name+".png")
        img.write_bytes(resvg_py.svg_to_bytes(svg_path=str(svg),width=size,height=size))
        with Image.open(img) as image:
            rgba=image.convert("RGBA")
            if size!=340:rgba=rgba.resize((340,340),
                Image.Resampling.NEAREST if down=="nearest" else Image.Resampling.BICUBIC)
            rendered=np.asarray(rgba.getchannel("A"))>=128
        covered=int((rendered&whole).sum())
        outside=int((rendered&~whole).sum())
        records.append({"variant":name,"source_covered":covered,
          "source_missing":int(whole.sum())-covered,"outside":outside,
          "vertices":vertices,"contours":contours,"svg_sha256":sha256(svg),
          "png_sha256":sha256(img)})
    # Compare pixel-cell results with prior 603/694 strict zero-excess baseline.
    board=Image.new("RGB",(1380,400),"#eee")
    board.paste(original.convert("RGB"),(12,14))
    d=ImageDraw.Draw(board)
    d.text((12,367),"ORIGINAL 694 pixels",fill="#232b27")
    for i,r in enumerate(records):
        with Image.open(out/(r["variant"]+".png")) as inp:
            tile=inp.convert("RGBA")
            if tile.size!=(340,340):
                tile=tile.resize((340,340),Image.Resampling.NEAREST if r["variant"].endswith("nearest") else Image.Resampling.BICUBIC)
        white=Image.new("RGBA",(340,340),"white");white.alpha_composite(tile)
        board.paste(white.convert("RGB"),(355+340*i,14))
        d.text((355+340*i,367),f"{r['variant']} {r['source_covered']}/694 +{r['outside']}",fill="#232b27")
    gallery=out/"compare_pixel_cell_boundaries.png";board.save(gallery,optimize=True)
    feasible=[r for r in records if r["outside"]==0]
    best=max(feasible,key=lambda r:(r["source_covered"],-r["vertices"])) if feasible else None
    manifest={"stage":"Pixel-Cell Boundary v1","source_pixels":int(whole.sum()),
      "baseline_covered":603,"baseline_outside":0,"variants":records,
      "best_zero_excess":best["variant"] if best else None,
      "core_golden_pass":False,"no_new_hair_geometry":True,
      "artifacts":[{"name":f.name,"sha256":sha256(f)} for f in sorted(out.iterdir()) if f.is_file()]}
    (out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"variants":records,"best_zero_excess":manifest["best_zero_excess"]}))
if __name__=="__main__":main()
