"""Face Parts Only v1: feature-scoped source observation; absolutely no face-plane painting.

Research/diagnostic, NOT production. Original face AND fringe are initially owned by
the input source and never covered with a face-sized skin mask. Eye/nose/mouth
micro-masks are source-observed, not inferred anatomy. Brows are unverified.

A preserve = source pixels at all feature points, unchanged.
B simplify = only pixels in verified source micro-component masks can change,
   and replacement RGB must exist in the corresponding ORIGINAL component.
C suppress = FAIL CLOSED because a safe true omission needs verified source
   skin/background behind the facial mark; never inpaint or fill blindly.

Using the prior D result is optional *outside* all original face/hair pixels;
all masks and results are source-hash verified. Facial features remain forbidden
in current Minimalizer Core Golden; A/B are exploratory diagnostics ONLY.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from semantic_art_mixer_v1 import SOURCE_SHA, SIZE, load_assets, sha256
from semantic_art_mixer_v3_source_masks import (
    load_observed_masks, identify_eyes_from_source, facial_micro_observations,
    original_color_medoid
)

PARTS = ("eye_left", "eye_right", "nose", "mouth")
D_STYLE_REL = "SemanticArtMixer_v3_SourceMasks_20261008/02_mosaic_sparse_D_extended_parts.png"


def source_components(original: Image.Image, masks: dict):
    """Return only source-observed pixels, never face-wide or polygon fill masks."""
    face=masks["face"]
    hair=masks["hair"]
    eyes,eye_records=identify_eyes_from_source(original,face)
    micro=facial_micro_observations(original,face)
    rgb=np.asarray(original.convert("RGB"),dtype=np.uint8)
    hsv=cv2.cvtColor(rgb,cv2.COLOR_RGB2HSV)
    yy,xx=np.mgrid[:SIZE[1],:SIZE[0]]
    r,g,b=[rgb[:,:,i].astype(np.int16) for i in range(3)]

    # A nose candidate is a restricted, already source-observed connected color
    # set, not a drawn nose landmark/bounding rectangle.
    nose=(face&(xx>=165)&(xx<184)&(yy>=138)&(yy<155)&
          (r-g>=19)&(r-b>=26)&(g>=139)&(r>188))
    mouth=(face&(xx>=151)&(xx<190)&(yy>=152)&(yy<164)&
           (rgb.min(axis=2)<180)&(r-g>12))
    # Only components independently present in original are eligible.
    observed={"eye_left":eyes[0],"eye_right":eyes[1],"nose":nose,"mouth":mouth}
    safe={}
    occupied=np.zeros_like(face)
    audit={}
    for part in PARTS:
        component=observed[part] & face & ~hair & ~occupied
        if not component.any():
            raise ValueError("No safe source pixels for "+part)
        if part.startswith("eye") and component.sum()<12:
            raise ValueError("Insufficient original eye evidence")
        if part=="nose" and component.sum()<18:
            raise ValueError("Insufficient original nose evidence")
        if part=="mouth" and component.sum()<5:
            raise ValueError("Insufficient original mouth evidence")
        if component.any() and np.any(component & hair):
            raise AssertionError("Feature mask overlaps hair")
        safe[part]=component
        occupied |= component
        audit[part]={"original_pixels":int(component.sum()),"sha256_mask":hashlib.sha256(
            component.astype(np.uint8).tobytes()).hexdigest()}
    audit["brow"]={"status":"NOT_VERIFIED","render_allowed":False}
    audit["eye_observations"]=eye_records
    audit["nose_mouth_candidates"]=micro
    return safe,audit


def reduce_one_observed_part(source: np.ndarray, partmask: np.ndarray):
    """Nearest ORIGINAL RGB medoid only, no new pixel geometry."""
    values=source[partmask]
    if len(values)==0:
        raise ValueError("empty part")
    color=original_color_medoid(values)
    assert any(np.array_equal(color,c) for c in values)
    return color


def process_abc(original:Image.Image, masks:dict, style:Image.Image|None=None):
    """A/B may use v3-D on nonface/nonhair; C is a recorded rejection only."""
    src=np.asarray(original.convert("RGB"),dtype=np.uint8)
    feature,audit=source_components(original,masks)
    owner=masks["subject"]
    hair=masks["hair"]
    face=masks["face"]
    # Base starts from exact input original, not an artificial face-colored patch.
    base=src.copy()
    if style is not None:
        art=np.asarray(style.convert("RGB"),dtype=np.uint8)
        if art.shape!=src.shape:
            raise ValueError("D-reference image not source-aligned")
        nonface=owner&~face&~hair
        base[nonface]=art[nonface]
    a=base.copy()
    b=base.copy()
    painted=[]
    for part,mask in feature.items():
        # A deliberately leaves feature pixels untouched; never re-add them.
        assert np.array_equal(a[mask],src[mask])
        color=reduce_one_observed_part(src,mask)
        b[mask]=color
        painted.append({"part":part,"pixels":int(mask.sum()),
                        "source_medoid_rgb":color.astype(int).tolist()})
    changed=np.any(a!=b,axis=2)
    union=np.logical_or.reduce(list(feature.values()))
    if np.any(changed&~union):
        raise AssertionError("B painted outside observed tiny face components")
    if np.any(np.any(a!=src,axis=2)&(face|hair)) or np.any(np.any(b!=src,axis=2)&((face&~union)|hair)):
        raise AssertionError("Face geometry/fringe overwritten by a broad layer")
    # Source medoid of facial feature is NOT safe to use as missing-feature
    # background! A full suppression is impossible without observed underlay.
    c={"status":"BLOCKED_FAIL_CLOSED",
       "reason":"No observed skin underlay beneath individual eye/nose/mouth pixels; omission would require invented pixels",
       "generated_output":False,
       "brow_mask_unverified":True}
    return Image.fromarray(a),Image.fromarray(b),c,{
        "feature_audit":audit,"feature_rendering":painted,
        "b_changed_pixels":int(changed.sum()),
        "b_changed_outside_verified_features":int((changed&~union).sum()),
        "hair_pixels_changed_from_original_a":int(np.any(a[hair]!=src[hair],axis=1).sum()),
        "hair_pixels_changed_from_original_b":int(np.any(b[hair]!=src[hair],axis=1).sum()),
        "face_nonfeature_changed_from_original":int(np.any(b[face&~union]!=src[face&~union],axis=1).sum()),
        "face_or_hair_overlay_applied":False,
        "core_golden_facial_details_allowed":False,
    }


def create_gallery(original,a,b,out):
    items=[("ORIGINAL SOURCE",original),("A / PRESERVE",a),("B / PART ONLY",b)]
    w=450;h=520
    panel=Image.new("RGB",(w*3,h+84),"#EDECE7")
    d=ImageDraw.Draw(panel)
    d.text((20,17),"FACE PARTS ONLY  /  V1",fill="#202A24")
    d.text((20,44),"Original face and hair remain untouched; C suppression is blocked.",fill="#5A645A")
    for i,(label,im) in enumerate(items):
        x=i*w
        panel.paste(im.resize((420,420),Image.Resampling.NEAREST),(x+15,85))
        d.text((x+16,520),label,fill="#202A24")
    panel.save(out,optimize=True)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    root=args.root.resolve()
    output=args.out.resolve();output.mkdir(parents=True,exist_ok=True)
    original,_,input_assets=load_assets(root)
    masks,mask_records=load_observed_masks()
    previous=root/D_STYLE_REL
    style=None
    # If the previous D reference is used, tie it to its own manifest hash.
    if previous.exists():
        manifest=root/"SemanticArtMixer_v3_SourceMasks_20261008/manifest.json"
        saved=json.loads(manifest.read_text(encoding="utf-8"))
        match=[e for e in saved["outputs"] if e["file"]==previous.name]
        if len(match)!=1 or sha256(previous)!=match[0]["sha256"]:
            raise ValueError("D reference failed provenance verification")
        with Image.open(previous) as img:
            style=img.convert("RGB")
    a,b,c,stats=process_abc(original,masks,style)
    files={}
    for name,image in (("A_preserve.png",a),("B_observed_part_simplify.png",b)):
        dest=output/name;image.save(dest,optimize=True);files[name]=sha256(dest)
    image=output/"gallery_A_B_C_decision.png"
    create_gallery(original,a,b,image)
    mask_files={}
    components,_=source_components(original,masks)
    for part,mask in components.items():
        path=output/f"diagnostic_mask_{part}.png"
        Image.fromarray(mask.astype(np.uint8)*255,"L").save(path,optimize=True)
        mask_files[path.name]=sha256(path)
    manifest={
        "research":"Face Parts Only v1 / A preserve B simplify C fail closed",
        "source_sha256":SOURCE_SHA,
        "no_face_overlay":True,
        "hair_untouched":True,
        "brow":"not independently identified, fail closed",
        "production_integrated":False,
        "core_golden_rule":"facial_details forbidden; A/B research only",
        "input_masks":mask_records,
        "input_assets":input_assets,
        "baseline":"source plus authenticated D reference outside face/hair" if style else "source",
        "results":{"A":files["A_preserve.png"],"B":files["B_observed_part_simplify.png"],"C":c},
        "metrics":stats,
        "diagnostic_masks":mask_files,
        "gallery":{"file":image.name,"sha256":sha256(image)}
    }
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PASS","b_changed_pixels":stats["b_changed_pixels"],
                      "face_nonfeature_changes":stats["face_nonfeature_changed_from_original"],
                      "hair_a":stats["hair_pixels_changed_from_original_a"],
                      "hair_b":stats["hair_pixels_changed_from_original_b"],
                      "c_status":c["status"],"gallery_sha":manifest["gallery"]["sha256"]},ensure_ascii=False))


if __name__=="__main__":
    main()
