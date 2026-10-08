"""Research-only removal of the implicit full-subject skin-colored plate.

Parts are rendered directly from original-owned masks, not on a subject-wide
skin underlay. Unresolved face is deliberately not filled; the resulting hole
is a diagnostic NO-GO, NOT an accepted complete character. No inpainting,
facial-feature invention, raster embedding or production change.
"""
from __future__ import annotations
import argparse,json,os,sys
from pathlib import Path
from xml.etree import ElementTree as ET
import cv2
import numpy as np
from PIL import Image,ImageDraw
from semantic_art_mixer_v1 import SIZE,SOURCE_SHA,load_assets,sha256,observed_tie_mask
from semantic_art_mixer_v3_source_masks import load_observed_masks,original_color_medoid
from face_parts_only_v1 import source_components

NS="http://www.w3.org/2000/svg"
ET.register_namespace("",NS)
ORDER=("lower_body","torso","major_clothing","neck","left_arm","right_arm",
       "hair","accessory_or_held_object")
CAP={"lower_body":3,"torso":3,"major_clothing":5,"neck":2,"left_arm":3,
     "right_arm":3,"hair":5,"accessory_or_held_object":3}
MIN_COMPONENT=40


def observed_color(src,mask):
    return tuple(int(c) for c in original_color_medoid(
        np.asarray(src.convert("RGB"))[mask]))


def contours_path(mask):
    contours,_=cv2.findContours(mask.astype(np.uint8)*255,
                                cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    bits=[];vertices=0
    for c in contours:
        if len(c)<3 or cv2.contourArea(c)<3:continue
        c=cv2.approxPolyDP(c,0.6,True).reshape(-1,2)
        if len(c)<3:continue
        bits.append("M "+" L ".join(f"{int(x)} {int(y)}" for x,y in c)+" Z")
        vertices+=len(c)
    return " ".join(bits),len(bits),vertices


def region_colormasks(src,region,count):
    rgb=np.asarray(src.convert("RGB"),dtype=np.uint8)
    pixels=rgb[region]
    if len(pixels)<MIN_COMPONENT:return []
    training=pixels[::max(1,len(pixels)//1500)].astype(np.float32)
    cv2.setRNGSeed(23)
    _,_,centers=cv2.kmeans(training,count,None,
       (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER,30,0.1),
       1,cv2.KMEANS_PP_CENTERS)
    palette=[]
    for center in centers:
        idx=np.argmin(np.sum((pixels.astype(np.float32)-center)**2,axis=1))
        color=tuple(int(v) for v in pixels[idx])
        if color not in palette:palette.append(color)
    # IMPORTANT: squaring signed int16 channel differences overflows for
    # |delta| >= 182; this caused wrong nearest-palette ownership (orange hair
    # assigned pale colors, navy clothing assigned unrelated tones).
    delta=pixels[:,None,:].astype(np.int32)-np.asarray(palette,dtype=np.int32)[None,:,:]
    d=np.sum(delta*delta,axis=2,dtype=np.int64)
    ids=np.argmin(d,axis=1)
    freq=np.bincount(ids,minlength=len(palette))
    main=int(np.argmax(freq))
    layers=[(region,palette[main],"base")]
    classified=np.full(region.shape,-1,dtype=np.int16)
    classified[region]=ids
    for i,color in enumerate(palette):
        if i==main:continue
        n,labels,stats,_=cv2.connectedComponentsWithStats((classified==i).astype(np.uint8),8)
        eligible=np.zeros(region.shape,dtype=bool)
        for k in range(1,n):
            if stats[k,cv2.CC_STAT_AREA]>=MIN_COMPONENT:
                eligible|=(labels==k)
        if eligible.any():layers.append((eligible,color,"accent"))
    return layers


def assemble(src,masks,features,full_path,fg_path):
    owner=masks["subject"];face=masks["face"];hair=masks["hair"]
    forbidden=np.logical_or.reduce(list(features.values()))
    if np.any(forbidden&hair):raise ValueError("Source face features overlap hair")
    root=ET.Element("{%s}svg"%NS,{"width":"340","height":"340","viewBox":"0 0 340 340"})
    alpha=ET.Element("{%s}svg"%NS,{"width":"340","height":"340","viewBox":"0 0 340 340"})
    ET.SubElement(root,"{%s}rect"%NS,{"width":"340","height":"340",
                                     "fill":"#f5eee4","data-part":"background"})
    emitted=[]
    def put(mask,color,role,layer):
        data,n,vertices=contours_path(mask)
        if not data:return
        value="#%02x%02x%02x"%tuple(color)
        for parent in (root,alpha):
            ET.SubElement(parent,"{%s}path"%NS,{
                "d":data,"fill":value,"fill-rule":"evenodd",
                "data-part":role,"data-layer":layer})
        emitted.append({"role":role,"layer":layer,"contours":n,
                        "vertices":vertices,"pixels":int(mask.sum())})
    # Explicitly DO NOT insert the formerly implicit source-wide skin plate.
    # Its absence may reveal the SVG background through the unresolved face;
    # this is a diagnostic, not an attempt to reconstruct the hidden skin.
    # Build a deterministic ownership partition before any fill ordering.
    # Earlier version allowed torso, neck, sleeves and hair to paint across
    # competing source parts. Every pixel is owned once, in source geometry.
    # Face stays unresolved: neither a skin-color plate nor a face path.
    priority=("accessory_or_held_object","hair","left_arm","right_arm",
              "major_clothing","neck","torso","lower_body")
    owned=np.zeros(owner.shape,dtype=bool)
    tie=observed_tie_mask(src)
    owned|=tie
    # Fringe/hair must remain visible even where the coarse face mask overlaps.
    # Reserve only visible nonhair skin, never reserve hair under the face.
    owned|=(face & ~hair)
    regions={}
    for role in priority:
        incoming=masks[role]&owner&~owned
        regions[role]=incoming
        owned|=incoming
    residual=owner&~owned
    if residual.any():
        # Only source-observed nonface residual regions may be drawn.
        # The unresolved face is excluded from this residual, never filled.
        remaining=region_colormasks(src,residual,4)
        for layer,color,kind in remaining:
            put(layer,color,"residual_source","base" if kind=="base" else "accent")
    for role in reversed(priority):
        region=regions[role]
        if not region.any():continue
        for layer,color,kind in region_colormasks(src,region,CAP[role]):
            put(layer,color,role,kind)
    put(tie,observed_color(src,tie),"necktie","identity-accent")
    if np.any(np.logical_and.reduce((regions["hair"],regions["major_clothing"]))):
        raise AssertionError("Part ownership overlap")
    self_check={"no_subject_skin_underlay":True,
                "unresolved_face_pixels":int((face & ~hair & owner).sum()),
                "unresolved_hair_priority_pixels":int((hair & owner).sum()),
                "render_intentionally_incomplete":True,
                "residual_source_pixels":int(residual.sum()),
                "covered_source_pixels":int(owned.sum()),
                "priority":list(priority),
                "part_owned_pixels":{key:int(regions[key].sum()) for key in priority}}
    # Provenance metadata supplied in a separate file at the calling site.
    assemble.last_ownership=self_check
    for doc,path in ((root,full_path),(alpha,fg_path)):
        ET.ElementTree(doc).write(path,encoding="utf-8",xml_declaration=True)
        parsed=ET.parse(path)
        if (parsed.findall(".//{%s}image"%NS) or
            parsed.findall(".//{%s}path[@data-part='face']"%NS) or
            parsed.findall(".//{%s}path[@data-part='subject']"%NS)):
            raise AssertionError("Face/subject underlay or raster detected")
    return emitted


def preview(svg,png):
    folder=Path(os.environ.get("LOCALAPPDATA",""))/"Minimalizer/research/resvg-py-0.5.0"
    if not folder.is_dir():raise RuntimeError("Isolated resvg renderer missing")
    sys.path.insert(0,str(folder))
    import resvg_py
    png.write_bytes(resvg_py.svg_to_bytes(svg_path=str(svg),width=680,height=680))


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    source,_,sources=load_assets(a.root.resolve())
    masks,origins=load_observed_masks()
    features,audit=source_components(source,masks)
    full=out/"character_part_vector.svg"
    foreground=out/"character_foreground_alpha.svg"
    paths=assemble(source,masks,features,full,foreground)
    ownership=assemble.last_ownership
    png=out/"character_part_vector.png"
    fg_png=out/"character_foreground_alpha.png"
    preview(full,png);preview(foreground,fg_png)
    owner=masks["subject"]
    mask=np.asarray(Image.open(fg_png).convert("RGBA").resize(SIZE).getchannel("A"))>=128
    iou=int((mask&owner).sum())/int((mask|owner).sum())
    metrics={"svg_path_elements":len(paths),
             "svg_contours":sum(q["contours"] for q in paths),
             "svg_vertices":sum(q["vertices"] for q in paths),
             "silhouette_iou":round(iou,5),
             "false_positive_pixels":int((mask&~owner).sum()),
             "missing_subject_pixels":int((owner&~mask).sum()),
             "no_face_path":True,
             "no_subject_skin_underlay":True,
             "unresolved_face_is_background":True,
             "no_facial_features_drawn":True,
             "not_core_pass":True}
    board=Image.new("RGB",(1040,402),"#eeeeeb")
    dr=ImageDraw.Draw(board)
    board.paste(source.convert("RGB"),(10,15))
    art=Image.open(png).convert("RGB").resize(SIZE)
    board.paste(art,(355,15))
    dr.text((10,362),"ORIGINAL",fill="#222222")
    dr.text((355,362),"NO SKIN UNDERLAY / INCOMPLETE",fill="#222222")
    for j,text in enumerate(("SVG paths: "+str(metrics["svg_path_elements"]),
                             "Vertices: "+str(metrics["svg_vertices"]),
                             "Silhouette IoU: "+str(metrics["silhouette_iou"]),
                             "No subject-wide skin plate","FACE UNRESOLVED / NO-GO")):
        dr.text((720,80+j*45),text,fill="#222222")
    comparison=out/"comparison_source_vs_vector.png"
    board.save(comparison,optimize=True)
    manifest={"source_sha256":SOURCE_SHA,"source_masks":origins,"source_art":sources,
              "face_audit":audit,"metrics":metrics,"paths":paths,"ownership":ownership,
              "not_production":True,"generative_image_used":False,
              "artifacts":[{"name":p.name,"sha256":sha256(p)} for p in
                           (full,foreground,png,fg_png,comparison)]}
    (out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PASS",**metrics,**ownership,"comparison_sha":sha256(comparison)}))


if __name__=="__main__":
    main()
