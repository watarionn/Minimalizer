"""Semantic Art Mixer v3: source-owned subject, face and anatomy masks.

Research only, non-generative. Reuses byte-verified source and existing Phase03/04
diagnostic masks from this repository. Source facial features are *observed* to
exclude them from rendering, never hallucinated or painted.

Trials:
 A Subject only: background separated and styles clipped, no face safety.
 B Subject + Face: exact source-observed face part plane, eyes never drawn.
 C Subject + Face + Parts: preserve source-derived hair/arm/material palettes.
 D Extended Parts: also observe neck, torso, lower body and small accessories.

These are test candidates, not production Minimalizer quality authorization.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from semantic_art_mixer_v1 import (
    SIZE, SOURCE_SHA, DEFAULT_RECIPES, load_assets, observed_tie_mask,
    protect_original_tie, validate_recipe, add_texture, sha256,
)
from semantic_art_mixer_v2_guarded import visible_ink_mask

ROOT = Path(__file__).resolve().parents[2]
MASK_REL = Path("docs/zerobase/diagnostics")
LABELS = ("face", "hair", "left_arm", "right_arm", "major_clothing",
          "torso", "neck", "lower_body", "accessory_or_held_object")
TRIALS = ("A_subject_clip", "B_face_parts_observed", "C_part_palette",
          "D_extended_parts")
EYE_HUE_LOW, EYE_HUE_HIGH = 35, 116


def mask_file(role: str) -> Path:
    if role == "subject":
        return ROOT / MASK_REL / "phase03/Hyakuto-Kyoko/03_subject_mask.png"
    if role not in LABELS:
        raise ValueError("Unknown semantic mask role: " + role)
    return ROOT / MASK_REL / "phase04/Hyakuto-Kyoko/part_masks" / f"{role}.png"


def load_observed_masks() -> tuple[dict[str,np.ndarray],list[dict]]:
    masks={}
    origin=[]
    for label in ("subject",*LABELS):
        path=mask_file(label)
        with Image.open(path) as img:
            arr=np.asarray(img.convert("L"),dtype=np.uint8)
        if arr.shape!=(SIZE[1],SIZE[0]):
            raise ValueError("Masks must be aligned to source 340x340: " + label)
        mask=arr>=127
        if mask.sum()<150:
            raise ValueError("Empty / inadequate mask: "+label)
        masks[label]=mask
        origin.append({"role":label,"file":str(path.relative_to(ROOT)).replace("\\","/"),
                       "sha256":sha256(path),"pixels":int(mask.sum())})
    # Face/arms sit in the reference subject, allowing small anti-alias margins.
    for role in ("face","hair","left_arm","right_arm"):
        support=float((masks[role]&masks["subject"]).sum())/float(masks[role].sum())
        if support<0.90:
            raise ValueError(f"{role} mask inconsistent with subject: {support:.3f}")
    return masks,origin


def identify_eyes_from_source(source: Image.Image, face: np.ndarray):
    """Color-grounded GC001 eye OBSERVATION only, never a renderer.

    Input face region comes from Phase04 mask. Hue components do not generalize
    to all character eyes; ambiguous observations must explicitly fail.
    """
    pixels=np.asarray(source.convert("RGB"),dtype=np.uint8)
    hsv=cv2.cvtColor(pixels,cv2.COLOR_RGB2HSV)
    y,x=np.mgrid[:SIZE[1],:SIZE[0]]
    tinted=(face&(x>132)&(x<212)&(y>121)&(y<156)&
            (hsv[:,:,0]>=EYE_HUE_LOW)&(hsv[:,:,0]<=EYE_HUE_HIGH)&
            (hsv[:,:,1]>=55)&(hsv[:,:,2]<248))
    n,lab,stats,centers=cv2.connectedComponentsWithStats(tinted.astype(np.uint8),8)
    candidates=[]
    for j in range(1,n):
        if int(stats[j,cv2.CC_STAT_AREA])>=12:
            candidates.append((int(j),int(stats[j,cv2.CC_STAT_AREA]),
                               (float(centers[j,0]),float(centers[j,1]))))
    candidates.sort(key=lambda v:v[2][0])
    if len(candidates)!=2:
        raise ValueError(f"Expected two observed GC001 eye-color components, got {len(candidates)}")
    if candidates[1][2][0]-candidates[0][2][0]<23:
        raise ValueError("Two eye components are not spatially separated")
    masks=[lab==i for i,_,_ in candidates]
    obs=[{"candidate": "left_of_image" if k==0 else "right_of_image",
          "observed_color_pixels":area,
          "center_source_xy":[round(cx,2),round(cy,2)],
          "visibility_role":"audit_only_not_rendered"}
         for k,(_,area,(cx,cy)) in enumerate(candidates)]
    return masks,obs


def original_color_medoid(colors: np.ndarray) -> np.ndarray:
    """Choose an ACTUALLY PRESENT RGB triplet closest to the median."""
    if not len(colors):
        raise ValueError("Empty source color population")
    a=colors.astype(np.float32)
    median=np.median(a,axis=0)
    score=np.sum((a-median)**2,axis=1)
    return colors[int(np.argmin(score))]


def face_plan(source: Image.Image, face: np.ndarray, eye_masks: list[np.ndarray], bands=3):
    """Piecewise tonal face from true face geometry and actual SOURCE skin colors.

    We never sample original eye pixels as paint; eyes are observations used to
    suppress detail, not to generate new eyes. 3 face tones by original y bands.
    """
    pixels=np.asarray(source.convert("RGB"),dtype=np.uint8)
    src=pixels.astype(np.int16)
    skin=(face&(src[:,:,0]>=180)&(src[:,:,1]>=140)&(src[:,:,2]>=115)&
          ((src[:,:,0]-src[:,:,1])>=2)&((src[:,:,0]-src[:,:,1])<=86)&
          ((src[:,:,1]-src[:,:,2])<=75))
    for eye in eye_masks:
        skin &= ~cv2.dilate(eye.astype(np.uint8),np.ones((7,7),np.uint8)).astype(bool)
    if skin.sum()<400:
        raise ValueError("Insufficient independently observed skin colors")
    ys,xs=np.where(face)
    lo,hi=int(ys.min()),int(ys.max())+1
    output=np.zeros_like(pixels)
    band_meta=[]
    all_skin=pixels[skin]
    for k in range(bands):
        y0=lo+(hi-lo)*k//bands
        y1=lo+(hi-lo)*(k+1)//bands
        subset=skin.copy()
        subset[:y0,:]=False
        subset[y1:,:]=False
        samples=pixels[subset] if subset.sum()>=15 else all_skin
        color=original_color_medoid(samples)
        band=face.copy()
        band[:y0,:]=False
        band[y1:,:]=False
        output[band]=color
        band_meta.append({"source_y":[y0,y1],"original_rgb":color.tolist(),
                          "pixels":int(band.sum())})
    if int((face&(np.mean(output,axis=2)<125)).sum()):
        raise AssertionError("Face fill unexpectedly contains dark eye-like regions")
    return output,band_meta


def source_part_palette(source: Image.Image, area: np.ndarray, n_colors: int):
    """Deterministic source-region medoid palette, no invented RGB or learned model."""
    rgb=np.asarray(source.convert("RGB"),dtype=np.uint8)
    values=rgb[area]
    if len(values)<80:
        raise ValueError("Too few source part pixels")
    # Match color centres on a regular deterministic subset and snap them back
    # to SOURCE RGB triplets. cv2 kmeans never becomes a rendered invented color.
    subset=values[::max(1,len(values)//2800)].astype(np.float32)
    cv2.setRNGSeed(101)
    _,labels,centers=cv2.kmeans(subset,n_colors,None,
                               (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER,70,0.01),
                               1,cv2.KMEANS_PP_CENTERS)
    palette=[]
    for center in centers:
        idx=int(np.argmin(np.sum((values.astype(np.float32)-center)**2,axis=1)))
        palette.append(values[idx])
    palette=np.unique(np.asarray(palette,dtype=np.uint8),axis=0)
    if not 1<=len(palette)<=n_colors:
        raise AssertionError("Palette budget exceeded")
    source_lab=cv2.cvtColor(rgb,cv2.COLOR_RGB2LAB).astype(np.float32)
    palette_lab=cv2.cvtColor(palette.reshape(1,-1,3),cv2.COLOR_RGB2LAB).reshape(-1,3).astype(np.float32)
    distances=np.sum((source_lab[:,:,None,:]-palette_lab[None,None,:,:])**2,axis=3)
    chosen=np.argmin(distances,axis=2)
    return palette[chosen], [list(map(int,color)) for color in palette]


def foreground_boundary(mask):
    eroded=cv2.erode(mask.astype(np.uint8),np.ones((3,3),np.uint8))>0
    return mask & ~eroded


def composite_trial(recipe, trial: str, original: Image.Image, assets, masks,
                    tie_mask, eye_mask_list, face_colors, cached_parts):
    recipe=validate_recipe(recipe)
    if trial not in TRIALS:
        raise ValueError(trial)
    src=np.asarray(original.convert("RGB"),dtype=np.uint8)
    subject=masks["subject"]
    face=masks["face"]
    # Non-stylized background is a softly median-filtered ORIGINAL, which
    # preserves the source red/orange layout without invented geometry.
    background=cv2.medianBlur(src,9)
    art=np.asarray(assets["shape."+recipe["shape"]].convert("RGB"),dtype=np.uint8)
    raw=np.where(subject[:,:,None],art,background)

    # Texture and ink drawn only ON pre-existing observed subject mask.
    work=Image.fromarray(raw,"RGB")
    if recipe["texture"]!="none":
        texture=add_texture(work,assets["texture."+recipe["texture"]],opacity=0.12)
        temp=np.asarray(texture)
        raw[subject]=temp[subject]

    # Sparse reference lines + requested per-recipe line style, clipped to
    # source subject. In B/C they NEVER enter Phase04 face mask.
    sparse=visible_ink_mask(assets["stroke.sparse"])
    selected=np.clip(sparse*0.60,0,1)
    if recipe["stroke"]!="none":
        selected=np.maximum(selected,visible_ink_mask(assets["stroke."+recipe["stroke"]])*0.48)
    allow=subject.copy()
    if trial!="A_subject_clip":
        allow &= ~face
    selected*=allow
    boundary=foreground_boundary(subject).astype(np.float32)
    # Boundary ink is based on actual SOURCE subject shape, not a guessed outline.
    selected=np.maximum(selected,boundary*0.47)
    if trial!="A_subject_clip":
        selected[face]=0.0

    raw=np.clip(raw.astype(np.float32)*(1.0-selected[:,:,None]*0.78)+
                np.array([32,35,39],dtype=np.float32)*selected[:,:,None]*0.78,0,255).astype(np.uint8)
    part_coverage={}
    if trial in ("C_part_palette", "D_extended_parts"):
        # Source-masked material planes override artistic style. D extends
        # ownership to core torso, neck and lower-body, after reviewing C.
        roles = (("major_clothing","left_arm","right_arm","hair")
                 if trial=="C_part_palette" else
                 ("lower_body","torso","major_clothing","neck",
                  "left_arm","right_arm","hair","accessory_or_held_object"))
        for role in roles:
            area=masks[role]&subject&~face
            paint,palette=cached_parts[role]
            raw[area]=paint[area]
            part_coverage[role]={"pixels":int(area.sum()),"source_palette":palette}
    face_bands=[]
    if trial!="A_subject_clip":
        paint,face_bands=face_colors
        own=face&subject
        raw[own]=paint[own]
    # Reassert subject ownership without touching background directly:
    # previous Color Lock only changes pixels already in subject tie region.
    clipped=Image.fromarray(raw,"RGB")
    out,tie_metrics=protect_original_tie(clipped,original,tie_mask)
    arr=np.asarray(out,dtype=np.uint8)
    face_dark=int(np.count_nonzero((arr.mean(axis=2)<125)&face))
    bg_pixel_changes_to_background=int(np.count_nonzero(np.any(arr[~subject]!=background[~subject],axis=1)))
    if bg_pixel_changes_to_background:
        raise AssertionError("Subject style leaked into background")
    if trial!="A_subject_clip" and face_dark:
        raise AssertionError("Face eye prevention failed")
    stats={
        **tie_metrics,"trial":trial,"reference_subject_pixels":int(subject.sum()),
        "style_leak_into_background_pixels":bg_pixel_changes_to_background,
        "source_face_mask_pixels":int(face.sum()),
        "face_dark_pixels":face_dark,
        "face_tone_bands":face_bands,
        "source_part_coverage":part_coverage,
        "facial_details_rendering":"forbidden; observed eye candidates only",
        "subject_mask_source":"repository phase03 source-derived",
        "face_mask_source":"repository phase04 source-derived",
        "generative_model_invoked":False,
    }
    return out,stats


def font(size,bold=False):
    path=Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf")
    return ImageFont.truetype(str(path),size) if path.exists() else ImageFont.load_default()


def gallery(original, outputs: list[dict], path: Path):
    cols=4
    side=340; cellw=365; cellh=432
    sheet=Image.new("RGB",(cols*cellw,70+4*cellh),"#ECECE8")
    dr=ImageDraw.Draw(sheet)
    dr.text((20,19),"GC001  /  SUBJECT - FACE - PART TRIALS",fill="#252D2C",font=font(29,True))
    for i,item in enumerate(outputs):
        x=i%cols*cellw
        y=70+(i//cols)*cellh
        dr.rounded_rectangle((x+7,y+7,x+cellw-7,y+cellh-9),radius=7,fill="#FAFAF8",outline="#CACBC7")
        with Image.open(item["file"]) as im:
            thumbnail=im.convert("RGB").resize((side,side),Image.Resampling.LANCZOS)
        sheet.paste(thumbnail,(x+(cellw-side)//2,y+14))
        dr.text((x+15,y+side+29),item["name"],fill="#26302B",font=font(16,True))
        dr.text((x+15,y+side+56),item.get("note",""),fill="#69736C",font=font(12))
    sheet.save(path,optimize=True)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    out=args.out.resolve()
    out.mkdir(parents=True,exist_ok=True)
    src,assets,existing_assets=load_assets(args.root.resolve())
    masks,mask_origin=load_observed_masks()
    eye_masks,eyes=identify_eyes_from_source(src,masks["face"])
    tie=observed_tie_mask(src)
    tones=face_plan(src,masks["face"],eye_masks)
    numcolors={"major_clothing":6,"left_arm":5,"right_arm":5,"hair":7,
               "torso":7,"neck":4,"lower_body":7,"accessory_or_held_object":4}
    parts={role: source_part_palette(src,masks[role]&masks["subject"],n) for role,n in numcolors.items()}

    # Transparent mask previews are evidence files only and are NEVER fed back
    # as new features or image-generated source.
    diagnostic=Image.new("RGB",(340*3,340),"white")
    colors={"subject":(72,140,235),"face":(248,182,100),"hair":(234,83,114)}
    source_np=np.asarray(src,dtype=np.uint8)
    for j,role in enumerate(("subject","face","hair")):
        frame=source_np.copy()
        mask=masks[role]
        frame[mask]=((frame[mask].astype(np.float32)*0.55+
                      np.asarray(colors[role])*0.45).astype(np.uint8))
        diagnostic.paste(Image.fromarray(frame),(340*j,0))
    diagnostic.save(out/"diagnostic_source_masks.png")

    # Red markers are *only* drawn on a separate evaluation audit.
    audit=src.convert("RGB").copy()
    draw=ImageDraw.Draw(audit)
    for eye in eyes:
        cx,cy=eye["center_source_xy"]
        draw.rectangle((int(cx)-8,int(cy)-7,int(cx)+8,int(cy)+7),
                       outline=(0,200,200),width=2)
    audit.save(out/"diagnostic_eye_observations_only.png")

    records=[]
    arr=[]
    for idx,recipe in enumerate(DEFAULT_RECIPES):
        for trial in TRIALS:
            im,metrics=composite_trial(recipe,trial,src,assets,masks,tie,eye_masks,tones,parts)
            name=f"{idx+1:02d}_{recipe['id']}_{trial}.png"
            dest=out/name
            im.save(dest,optimize=True)
            records.append({"recipe":recipe["id"],"trial":trial,"file":name,
                            "sha256":sha256(dest),"metrics":metrics})
            arr.append({"file":dest,"name":f"{idx+1:02d} {recipe['id']}",
                        "note":trial})
    atlas=out/"gallery_4recipes_3trials.png"
    gallery(src,arr,atlas)
    manifest={
        "experiment":"Semantic Art Mixer v3 / foreground-owner, face-part observer, source-material",
        "source_sha256":SOURCE_SHA,
        "source_mask_files":mask_origin,
        "research_assets":existing_assets,
        "eye_candidates_detected":eyes,
        "other_facial_classes":"not independently detected in this optical-only trial",
        "face_render_policy":"suppressed internal facial features; no fake eyes",
        "trial_descriptions":{
            "A_subject_clip":"source subject mask clips Shape/Stroke/Texture; face not yet protected, deliberately poor negative control",
            "B_face_parts_observed":"same subject clip plus phase04 exact face mask and three observed skin tones; eye candidate positions only audited",
            "C_part_palette":"subject, face and source hair/arms/uniform palette; original-derived material regions override heavy geometry",
            "D_extended_parts":"same provenance plus torso, neck, lower-body and observed small accessory masks"},
        "not_auto_semantic_segmentation":True,
        "not_production_integrated":True,
        "outputs":records,
        "gallery":{"file":atlas.name,"sha256":sha256(atlas),"bytes":atlas.stat().st_size}
    }
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PASS","outputs":len(records),
          "eye_observations":len(eyes),"subject_pixels":int(masks["subject"].sum()),
          "face_pixels":int(masks["face"].sum()),
          "background_leak":[r["metrics"]["style_leak_into_background_pixels"] for r in records],
          "face_dark":[r["metrics"]["face_dark_pixels"] for r in records],
          "tie_errors":[r["metrics"]["tie_pixels_changed_after"] for r in records],
          "gallery_sha256":manifest["gallery"]["sha256"]},ensure_ascii=False))

if __name__=="__main__":
    main()
