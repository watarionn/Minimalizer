"""Semantic Art Mixer v4: source-mask-owned, per-part discrete planes and budgets.

Independent GC001 PoC; does not ship to production. Exact source silhouette is
composed as the final occupancy owner, never inferred from RGB threshold.
Original source RGB triplets only; no facial details and no generative imagery.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFont

from semantic_art_mixer_v1 import load_assets, observed_tie_mask, protect_original_tie, sha256
from semantic_art_mixer_v3_source_masks import (
    load_observed_masks, identify_eyes_from_source,face_plan,
    source_part_palette,foreground_boundary, original_color_medoid
)

ROLE_ORDER=("lower_body","torso","major_clothing","neck","left_arm",
            "right_arm","hair","accessory_or_held_object")
BUDGETS={"E3":3,"E5":5}
ROLE_HIGH={"hair":2,"major_clothing":2,"accessory_or_held_object":1}
REDUCE_VARIANTS=("flat","regional_median")


def coherent_palette(src,mask,palette_size,mode):
    """Color planes stay within exactly one source-owned part mask."""
    source=np.asarray(src.convert("RGB"),dtype=np.uint8)
    pixels,palette=source_part_palette(src,mask,palette_size)
    if mode=="flat":
        chosen=original_color_medoid(source[mask])
        pixels[mask]=chosen
        palette=[chosen.tolist()]
    elif mode=="regional_median":
        # A small median filter works only as a choice of existing palette
        # indices, not as a new color interpolator. Outside is irrelevant.
        lab=cv2.cvtColor(pixels,cv2.COLOR_RGB2LAB)
        med=cv2.medianBlur(lab,5)
        pal=np.asarray(palette,dtype=np.uint8)
        pal_lab=cv2.cvtColor(pal.reshape(1,-1,3),cv2.COLOR_RGB2LAB).reshape(-1,3)
        dist=np.sum((med.astype(np.int32)[:,:,None,:]-pal_lab[None,None,:,:].astype(np.int32))**2,axis=3)
        idx=np.argmin(dist,axis=2)
        pixels[mask]=pal[idx][mask]
    else:
        raise ValueError(mode)
    return pixels,palette


def component_count(rgb,mask):
    """Count connected same-RGB runs as a rough raster primitive proxy, NOT SVG polygons."""
    a=np.asarray(rgb,dtype=np.uint8)
    total=0
    values=np.unique(a[mask].reshape(-1,3),axis=0)
    for color in values:
        layer=mask & np.all(a==color,axis=2)
        count,*_=cv2.connectedComponentsWithStats(layer.astype(np.uint8),8)
        total+=count-1
    return total,int(len(values))


def render(source,masks,tie,face_img,budget,mode):
    rgb=np.asarray(source.convert("RGB"),dtype=np.uint8)
    owner=masks["subject"]
    background=cv2.medianBlur(rgb,9)
    # Avoid depending on any previous D-style paint. Rebuild from original
    # with source parts and their explicitly capped palettes.
    a=background.copy()
    a[owner]=rgb[owner]
    coverage={}
    for role in ROLE_ORDER:
        region=masks[role]&owner&~masks["face"]
        cap=max(2,budget+ROLE_HIGH.get(role,0))
        colors,palette=coherent_palette(source,region,cap,mode)
        a[region]=colors[region]
        coverage[role]={"source_pixels":int(region.sum()),"palette":palette,
                        "palette_budget":cap}
    face=masks["face"]&owner
    a[face]=face_img[face]
    # No newly introduced silhouettes. Exactly owned pixels can change.
    image=Image.fromarray(a,"RGB")
    protected,color=protect_original_tie(image,source,tie)
    result=np.asarray(protected,dtype=np.uint8)
    if np.any(result[~owner]!=background[~owner]):
        raise AssertionError("Source background ownership violation")
    if np.any(np.mean(result[face],axis=1)<125):
        raise AssertionError("Facial feature/no-eye gate failed")
    if np.any(result[tie]!=rgb[tie]):
        raise AssertionError("Tie RGB owner gate failed")
    # Separate arm masks and subject negative space are never expanded into.
    for role in ("left_arm","right_arm"):
        if not np.any(masks[role]&owner):
            raise AssertionError("Source arm missing")
    fg_evidence={"silhouette_owner_pixels":int(owner.sum()),
        "changed_outside_subject":int(np.any(result[~owner]!=background[~owner],axis=1).sum()),
        "left_arm_source_pixels":int((masks["left_arm"]&owner).sum()),
        "right_arm_source_pixels":int((masks["right_arm"]&owner).sum()),
        "face_dark_pixels":int((np.mean(result[face],axis=1)<125).sum()),
        "tie_original_rgb_mismatches":int(np.any(result[tie]!=rgb[tie],axis=1).sum()),
        "raster_regions":component_count(result,owner)[0],
        "raster_palette_colors":component_count(result,owner)[1],
        "rendered_svg":False}
    return protected,coverage,{**fg_evidence,**color}


def make_gallery(original,views,out):
    width=5*355
    im=Image.new("RGB",(width,470),"#ECECE8")
    d=ImageDraw.Draw(im)
    d.text((18,14),"SEMANTIC ART MIXER / V4: REGIONAL BUDGET",fill="#18221D")
    paths=[("Original",original)]+views
    for j,(label,img) in enumerate(paths):
        x=j*355
        scaled=img.convert("RGB").resize((330,330),Image.Resampling.LANCZOS)
        im.paste(scaled,(x+12,48))
        d.text((x+13,390),label,fill="#202820")
    im.save(out,optimize=True)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    output=args.out.resolve();output.mkdir(parents=True,exist_ok=True)
    original,_,src_assets=load_assets(args.root.resolve())
    masks,mask_evidence=load_observed_masks()
    eyes,_=identify_eyes_from_source(original,masks["face"])
    face_img,_=face_plan(original,masks["face"],eyes)
    tie=observed_tie_mask(original)
    results=[];gallery=[]
    for key,n in BUDGETS.items():
        for mode in REDUCE_VARIANTS:
            image,roles,metrics=render(original,masks,tie,face_img,n,mode)
            name=f"gc001_{key}_{mode}.png";path=output/name
            image.save(path,optimize=True)
            results.append({"file":name,"sha256":sha256(path),"budget":n,
                            "variant":mode,"parts":roles,"metrics":metrics})
            gallery.append((key+" / "+mode,image))
    gallery_path=output/"gallery_4_budget_variants.png"
    make_gallery(original,gallery,gallery_path)
    data={"name":"SemanticArtMixer_v4_source_owned_raster_budget",
          "not_vectorized":True,"not_production":True,
          "not_generalized_to_other_subjects":True,
          "source_masks":mask_evidence,"source_art_modes":src_assets,
          "results":results,"gallery":{"file":gallery_path.name,
          "sha256":sha256(gallery_path)}}
    (output/"manifest.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PASS","variants":len(results),
          "metrics":[(r["file"],r["metrics"]["raster_regions"],r["metrics"]["raster_palette_colors"]) for r in results],
          "gallery_sha":data["gallery"]["sha256"]},ensure_ascii=False))


if __name__=="__main__":
    main()
