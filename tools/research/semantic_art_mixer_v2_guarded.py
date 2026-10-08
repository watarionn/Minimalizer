"""Semantic Art Mixer v2: protect a hand-localized GC001 face plane and observed outline.

Research-only. Uses SHA-verified original/Art Mode inputs from v1.
NO generated facial features, neural img2img, or invented subject geometry.
This is a *manual GC001 fixture*, not a general automatic face detector.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageOps

from semantic_art_mixer_v1 import (
    SIZE, SOURCE_SHA, TIE_ROI, DEFAULT_RECIPES, load_assets, observed_tie_mask,
    protect_original_tie, render as render_v1, validate_recipe, sha256, font
)

# Polygon inspected against original GC001 at 340x340. Includes forehead/face, excludes
# outside hair; actual skin mask is computed from ORIGINAL pixels, not polygon fill.
FACE_SEARCH_POLYGON = (
    (146,114),(163,106),(191,109),(205,121),(211,141),(207,162),
    (196,182),(180,194),(165,191),(147,178),(136,156),(139,134)
)
# Coarse, manually inspected subject visibility region. It only gates candidate ink
# from the original vsketch source; its perimeter is never drawn or used as a silhouette.
SUBJECT_SUPPORT_POLYGON = (
    (92,1),(209,1),(248,89),(274,125),(329,167),(329,213),
    (288,249),(312,340),(5,340),(12,278),(49,239),(74,187),
    (88,147),(73,96)
)


def polygon_mask(size: tuple[int,int], vertices) -> np.ndarray:
    img = np.zeros((size[1],size[0]),dtype=np.uint8)
    pts=np.asarray(vertices,dtype=np.int32)
    cv2.fillPoly(img,[pts],1)
    return img.astype(bool)


def source_face_plane(original: Image.Image):
    """Select observed face skin, bridge existing eyes as holes, build a flat color plane.

    Uses face ROI + original RGB skin threshold + largest connected source component +
    convex hull, clipped by the ROI. No new line segments or AI-created eyes.
    """
    src=np.asarray(original.convert("RGB"),dtype=np.uint8)
    if src.shape != (SIZE[1],SIZE[0],3):
        raise ValueError("Unexpected source dimensions")
    roi=polygon_mask(SIZE,FACE_SEARCH_POLYGON)
    R=src[:,:,0].astype(np.int16)
    G=src[:,:,1].astype(np.int16)
    B=src[:,:,2].astype(np.int16)
    skin=(R>=188)&(G>=140)&(B>=125)&((R-G)<=86)&((G-B)<=75)&roi
    closed=cv2.morphologyEx(skin.astype(np.uint8),cv2.MORPH_CLOSE,
                           cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(15,15)))
    n, lab, stats,_=cv2.connectedComponentsWithStats(closed,8)
    if n<2:
        raise ValueError("Original face skin has no detected connected region")
    cid=int(np.argmax(stats[1:,cv2.CC_STAT_AREA]))+1
    count=int(stats[cid,cv2.CC_STAT_AREA])
    if count<800:
        raise ValueError(f"Unexpectedly small observed skin component: {count}")
    ys,xs=np.where(lab==cid)
    pts=np.column_stack([xs,ys]).astype(np.int32)
    hull=cv2.convexHull(pts)
    plane=np.zeros((SIZE[1],SIZE[0]),dtype=np.uint8)
    cv2.fillConvexPoly(plane,hull,1)
    plane=(plane>0)&roi
    # Leave original face border as edge structure, not a generated polygon.
    plane=cv2.erode(plane.astype(np.uint8),np.ones((3,3),dtype=np.uint8))>0
    if not (1200 <= int(plane.sum()) <= 7000):
        raise ValueError(f"Face plane implausible: {int(plane.sum())}")
    # Select exactly an *existing* original RGB triplet, not a synthesized color.
    color_samples=src[skin & plane]
    values,frequencies=np.unique(color_samples,axis=0,return_counts=True)
    if len(values)==0:
        raise ValueError("No original skin color samples in face plane")
    flat_rgb=tuple(int(x) for x in values[np.argmax(frequencies)])
    return plane, roi, flat_rgb


def visible_ink_mask(source: Image.Image) -> np.ndarray:
    img=np.asarray(source.convert("RGBA"),dtype=np.uint8)
    # vsketch PNG is transparent outside actual paths. Never interpret invisible RGB
    # as ink; it otherwise creates a full-frame dark rectangle.
    alpha=img[:,:,3].astype(np.float32)/255.0
    rgb=img[:,:,:3].astype(np.float32)
    luma=(0.2126*rgb[:,:,0]+0.7152*rgb[:,:,1]+0.0722*rgb[:,:,2])/255.0
    return np.clip((1.0-luma)*alpha,0.0,1.0)


def compose_guarded(recipe, original: Image.Image, assets, tie_mask):
    """Return legacy and guarded outputs plus metrics; never modify v1 artifacts."""
    recipe=validate_recipe(recipe)
    unguarded_before,_,_=render_v1(recipe,original,assets,tie_mask)
    face,face_roi,flat_color=source_face_plane(original)
    subject=polygon_mask(SIZE,SUBJECT_SUPPORT_POLYGON)

    # Start with selected independently generated Shape. Texture is opt-in and
    # follows the earlier deterministic colored-dot overlay, but only around
    # the coarse subject support region (outside region retains source-derived Shape).
    base=assets["shape."+recipe["shape"]].convert("RGB")
    from semantic_art_mixer_v1 import add_texture
    if recipe["texture"]!="none":
        textured=add_texture(base,assets["texture."+recipe["texture"]],opacity=0.13)
        base=Image.composite(textured,base,Image.fromarray(subject.astype("uint8")*255,"L"))

    raw=np.asarray(base,dtype=np.float32).copy()
    blocked_face_strokes=0
    selected_ink=np.zeros((SIZE[1],SIZE[0]),dtype=np.float32)

    if recipe["stroke"]!="none":
        ink=visible_ink_mask(assets["stroke."+recipe["stroke"]])
        blocked_face_strokes=int(np.count_nonzero((ink>0.1)&face_roi))
        selected_ink=np.maximum(selected_ink,ink*subject*(~face_roi))
    # Universal structure guide from observed sparse original contour geometry.
    # It is not an automatically produced silhouette mask: this is a source-ink
    # overlay that improves consistency and must still pass separate Golden gates.
    support_ink=visible_ink_mask(assets["stroke.sparse"])*subject*(~face_roi)
    selected_ink=np.maximum(selected_ink,support_ink*0.85)

    ink_alpha=np.clip(selected_ink*0.79,0,0.79).astype(np.float32)
    ink_color=np.array([24,31,32],dtype=np.float32)
    raw=(raw*(1.0-ink_alpha[:,:,None])+ink_color*ink_alpha[:,:,None])
    composed=np.uint8(np.clip(np.rint(raw),0,255))
    # No facial ink/texture/eyes. Face is a single observed original RGB color,
    # constrained to the original skin-plane geometry (no inferred features).
    composed[face]=np.asarray(flat_color,dtype=np.uint8)
    face_dark_count=int(np.count_nonzero(np.mean(composed[face],axis=1)<125))
    if face_dark_count:
        raise AssertionError("Unexpected dark drawn facial features in protected face")
    guarded_unlocked=Image.fromarray(composed,"RGB")
    guarded_locked,color_gate=protect_original_tie(guarded_unlocked,original,tie_mask)

    # The silhouette support path is tracked independently of tie and face.
    # All selected sparse-outline pixels outside facial exclusion remain present.
    source_support_pixels=int(np.count_nonzero(support_ink>0.1))
    ink_selected_pixels=int(np.count_nonzero(selected_ink>0.1))
    if source_support_pixels<100 or ink_selected_pixels<source_support_pixels:
        raise AssertionError("Observed subject outline overlay unexpectedly missing")

    # Crop for regression checks; v1 vs v2 doesn't change original source.
    metrics={
      **color_gate,
      "face_roi_pixels":int(face_roi.sum()),
      "face_skin_plane_pixels":int(face.sum()),
      "face_flat_rgb_from_original":list(flat_color),
      "face_dark_pixels_after":face_dark_count,
      "facial_stroke_source_pixels_suppressed":blocked_face_strokes,
      "source_sparse_support_ink_pixels":source_support_pixels,
      "final_selected_ink_pixels":ink_selected_pixels,
      "outline": "observed vsketch sparse ink, manual subject gate (not automatic silhouette)",
      "face": "single original observed skin color, no eyes/nose/mouth drawn",
      "no_generated_pixels": True,
    }
    return unguarded_before,guarded_locked,metrics,face


def write_gallery(items,output: Path):
    width,cols,size,pad,caption=1080,3,300,18,76
    cellw=width//cols
    rows=(len(items)+cols-1)//cols
    cellh=size+caption+2*pad
    sheet=Image.new("RGB",(width,110+rows*cellh),"#EBECE8")
    d=ImageDraw.Draw(sheet)
    d.text((28,25),"MINIMALIZER / OUTLINE + FACE GUARD",font=font(32,True),fill="#24312D")
    d.text((28,73),"Original  /  previous  /  guarded     -     4 recipes",font=font(17),fill="#666C69")
    for i,(label,path) in enumerate(items):
        x=(i%cols)*cellw
        y=110+(i//cols)*cellh
        d.rounded_rectangle((x+7,y+4,x+cellw-7,y+cellh-6),radius=6,fill="#FCFCFA",outline="#D6D8D2")
        with Image.open(path) as img:
            art=ImageOps.contain(img.convert("RGB"),(size,size),Image.Resampling.LANCZOS)
        sheet.paste(art,(x+(cellw-art.width)//2,y+12+(size-art.height)//2))
        d.text((x+17,y+size+30),label,font=font(16,True),fill="#27302C")
    sheet.save(output,optimize=True)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    root=args.root.resolve()
    out=args.out.resolve()
    out.mkdir(parents=True,exist_ok=True)
    original,assets,verified=load_assets(root)
    tie=observed_tie_mask(original)
    records=[]
    orig_file=out/"00_original.png"
    original.save(orig_file,optimize=True)
    gallery_rows=[]
    for idx,recipe in enumerate(DEFAULT_RECIPES):
        prev,guarded,metrics,face=compose_guarded(recipe,original,assets,tie)
        name=recipe["id"]
        before=out/(name+"_v1.png")
        after=out/(name+"_face_outline_guard.png")
        maskfile=out/(name+"_face_mask.png")
        prev.save(before,optimize=True)
        guarded.save(after,optimize=True)
        Image.fromarray(np.uint8(face)*255,"L").save(maskfile,optimize=True)
        # Repeat ORIGINAL per recipe so each comparison row contains exactly
        # the same reference, its legacy output and the newly guarded result.
        gallery_rows.extend([("ORIGINAL / GC001",orig_file),
                             ("V1 / "+name,before),
                             ("GUARDED / "+name,after)])
        records.append({"id":name,"recipe":recipe,"metrics":metrics,
                        "before":{"file":before.name,"sha256":sha256(before)},
                        "guarded":{"file":after.name,"sha256":sha256(after)},
                        "face_mask":{"file":maskfile.name,"sha256":sha256(maskfile)}})
    gallery_path=out/"gallery_v1_vs_face_outline_guard.png"
    write_gallery(gallery_rows,gallery_path)
    m={"project":"Semantic Art Mixer v2 research-only face+outline guard",
       "input_source_sha256":SOURCE_SHA,
       "assets":verified,
       "no_generative_img2img":True,
       "automatic_semantic_face_detection":False,
       "automatic_silhouette_segmentation":False,
       "production_integrated":False,
       "results":records,
       "gallery":{"file":gallery_path.name,"sha256":sha256(gallery_path)}}
    (out/"manifest.json").write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PASS","recipes":len(records),
       "faces":[r["metrics"]["face_skin_plane_pixels"] for r in records],
       "face_dark":[r["metrics"]["face_dark_pixels_after"] for r in records],
       "suppressed_source_strokes":[r["metrics"]["facial_stroke_source_pixels_suppressed"] for r in records],
       "support":[r["metrics"]["source_sparse_support_ink_pixels"] for r in records],
       "tie_mismatch":[r["metrics"]["tie_pixels_changed_after"] for r in records],
       "gallery_sha256":m["gallery"]["sha256"]},ensure_ascii=False))


if __name__=="__main__":
    main()
