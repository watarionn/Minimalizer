"""Audit GC001 one-piece visor against *original source* edges/RGB.

Different from earlier self-IoU: evaluate the annotated visor perimeter against
native original-image edges, and real SVG RGB against source pixels. The mask
is a hand-reviewed approximation and must NOT be treated as ground truth.
Research-only: no geometry extrapolation, no image generation, no production.
"""
import argparse,json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw
from semantic_art_mixer_v1 import load_assets,sha256
from goggle_single_visor_annotation import visible_masks

SOURCE_EXPECTED="75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e"

def perimeter(mask):
    binary=np.asarray(mask,dtype=np.uint8)
    return (cv2.morphologyEx(binary,cv2.MORPH_GRADIENT,np.ones((3,3),np.uint8))>0)

def source_edges(rgb):
    gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
    smooth=cv2.GaussianBlur(gray,(3,3),0.5)
    edges=cv2.Canny(smooth,60,130,L2gradient=True)>0
    distance=cv2.distanceTransform((~edges).astype(np.uint8),cv2.DIST_L2,3)
    return edges,distance

def source_edge_metrics(border,distance):
    dist=distance[border]
    if not len(dist):raise ValueError("No source-annotated boundary")
    return {"edge_pixels":int(len(dist)),
       "source_canny_within_1px":round(float(np.mean(dist<=1.5)),5),
       "source_canny_within_2px":round(float(np.mean(dist<=2.5)),5),
       "source_canny_within_3px":round(float(np.mean(dist<=3.5)),5),
       "source_canny_distance_median_px":round(float(np.median(dist)),4),
       "source_canny_distance_p90_px":round(float(np.percentile(dist,90)),4)}

def rgb_metrics(source,render,mask):
    a=np.asarray(source,dtype=np.int16)
    b=np.asarray(render,dtype=np.int16)
    if a.shape!=b.shape or a.shape[:2]!=mask.shape:raise ValueError("RGB size mismatch")
    err=np.mean(np.abs(a-b),axis=2)[mask]
    if not len(err):raise ValueError("No reviewed pixels")
    return {"source_rgb_mae":round(float(err.mean()),3),
        "source_rgb_abs_p90":round(float(np.percentile(err,90)),3),
        "source_rgb_abs_gt_40_pct":round(float(np.mean(err>40)),5)}

def original_material_probe(source,mask):
    px=np.asarray(source,dtype=np.uint8)[mask]
    if not len(px):raise ValueError("No material pixels")
    hsv=cv2.cvtColor(px.reshape(-1,1,3),cv2.COLOR_RGB2HSV).reshape(-1,3)
    warm=(hsv[:,0]<=24)&(hsv[:,1]>=105)
    pale=(px.min(axis=1)>138)&((px.max(axis=1).astype(np.int16)-px.min(axis=1))<91)&(px.mean(axis=1)>178)
    return {"source_pixels":int(len(px)),
       "source_warm_orange_pct":round(float(warm.mean()),5),
       "source_pale_silver_pct":round(float(pale.mean()),5),
       "source_mean_rgb":np.rint(px.mean(axis=0)).astype(int).tolist()}

def audit(src,standalone,before,after):
    rgb=np.asarray(src.convert("RGB"),np.uint8)
    isolate=np.asarray(standalone.convert("RGBA"),np.uint8)
    b=np.asarray(before.convert("RGB"),np.uint8)
    a=np.asarray(after.convert("RGB"),np.uint8)
    observed,lens,frame=visible_masks()
    if rgb.shape[:2]!=(340,340) or isolate.shape[:2]!=(340,340):
        raise ValueError("Canonical source+render dimensions required")
    edge,dist=source_edges(rgb)
    roles={"visor_outer":observed,"visor_lens":lens,"visor_frame":frame}
    report={}
    for name,mask in roles.items():
        report[name]={
           "actual_source_boundary_alignment":source_edge_metrics(perimeter(mask),dist),
           "material_original":original_material_probe(rgb,mask),
           "isolated_svg_rgb_accuracy":rgb_metrics(rgb,isolate[:,:,:3],mask),
           "scene_prior_rgb_accuracy":rgb_metrics(rgb,b,mask),
           "scene_after_rgb_accuracy":rgb_metrics(rgb,a,mask)}
    # Exact mask raster agreement remains a different, self-referential gate.
    rendered_alpha=isolate[:,:,3]>=128
    report["self_mask_vectorization"]={
      "annotated_total":int(observed.sum()),
      "rendered_within_annotation":int((rendered_alpha&observed).sum()),
      "rendered_outside_annotation":int((rendered_alpha&~observed).sum())}
    report["source_edge_image"]=edge
    return report

def main():
    p=argparse.ArgumentParser()
    for n in ("root","prior","out"):p.add_argument("--"+n,type=Path,required=True)
    args=p.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    source,_,_=load_assets(args.root)
    # A canonical source from the earlier Golden research; no alternate pose replacement.
    canonical=args.root/"SA1041_FullCharacterSVG_20261008"/"original_inputs"/"GC001_source.png"
    if sha256(canonical)!=SOURCE_EXPECTED:raise AssertionError("Original GC001 SHA mismatch")
    file_names=("source_visored_onepiece.png","scene_before_visor.png","scene_after_visor.png")
    renders=[Image.open(args.prior/name) for name in file_names]
    report=audit(source,*renders)
    src_arr=np.asarray(source.convert("RGB"),np.uint8)
    outer,lens,frame=visible_masks()
    edge=report.pop("source_edge_image")
    # Four magnified panels: real source, source+annotation, Canny and RGB delta,
    # plus full-source reference. These are transparent *research overlays*.
    crop=(97,27,206,99);w,h=crop[2]-crop[0],crop[3]-crop[1]
    panel_w,panel_h=436,288
    palette=np.asarray(source.convert("RGB"),np.uint8).copy()
    draw_overlay=Image.fromarray(palette)
    pen=ImageDraw.Draw(draw_overlay)
    from goggle_single_visor_annotation import OUTER,INNER
    pen.line(list(OUTER)+[OUTER[0]],fill=(255,40,172),width=1)
    pen.line(list(INNER)+[INNER[0]],fill=(22,233,210),width=1)
    edges3=np.repeat((edge[:,:,None]*255).astype(np.uint8),3,axis=2)
    edge_image=Image.fromarray(edges3)
    after=np.asarray(renders[2].convert("RGB"),np.uint8)
    err=np.max(abs(src_arr.astype(np.int16)-after.astype(np.int16)),axis=2)
    heat=np.zeros(src_arr.shape,dtype=np.uint8)
    heat[:,:,0]=np.clip(err*3,0,255).astype(np.uint8)
    heat[:,:,1]=np.clip(255-err*4,0,255).astype(np.uint8)
    heat[:,:,2]=35
    outside=~cv2.dilate(outer.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
    heat[outside]=[236,236,232]
    sources=[source,draw_overlay,edge_image,Image.fromarray(heat)]
    names=["SOURCE (real pixels)","PINK outer / CYAN lens edge","SOURCE CANNY (not semantic GT)","AFTER RGB ABS ERROR (within visor)"]
    board=Image.new("RGB",(panel_w*4,345),"#f2f1ee")
    d=ImageDraw.Draw(board)
    for i,(img,title) in enumerate(zip(sources,names)):
        cut=img.crop(crop).resize((panel_w,panel_h),Image.Resampling.NEAREST)
        board.paste(cut,(i*panel_w,12))
        d.text((i*panel_w+8,311),title,fill="#172923")
    comparison=out/"visor_source_boundary_rgb_audit.png"
    board.save(comparison,optimize=True)
    report.update({"status":"SOURCE_EDGE_AND_RGB_AUDITED",
        "source_sha256":SOURCE_EXPECTED,
        "note":"Manual region boundaries are approximate; Canny support is not semantic ground truth.",
        "manual_boundary_semantic_gold_verified":False,
        "full_character_golden_pass":False,"production_changed":False,
        "source_bangs_modified":False,
        "files":[{"name":comparison.name,"sha256":sha256(comparison)}]})
    (out/"manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    summary={key:{"edge_2px":r["actual_source_boundary_alignment"]["source_canny_within_2px"],
                    "source_rgb_mae_after":r["scene_after_rgb_accuracy"]["source_rgb_mae"],
                    "source_rgb_mae_before":r["scene_prior_rgb_accuracy"]["source_rgb_mae"],
                    "warm_source_pct":r["material_original"]["source_warm_orange_pct"],
                    "pale_source_pct":r["material_original"]["source_pale_silver_pct"]}
              for key,r in report.items() if key in ("visor_outer","visor_lens","visor_frame")}
    print(json.dumps({"summary":summary,"vectorization":report["self_mask_vectorization"]},ensure_ascii=False))
if __name__=="__main__":main()
