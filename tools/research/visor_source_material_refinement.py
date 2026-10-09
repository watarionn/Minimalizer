"""Fail-closed source-material refinement of the GC001 manual one-piece visor.

The previous frame annotation included abundant *source-observed orange*.
Do not treat all manual frame pixels as silver paint. Try conservative source
RGB negative-control masks, preserve the one-piece lens and certified bangs,
and select ONLY if actual source RGB error improves. GC001 research only.
"""
import argparse,json,os,sys
from pathlib import Path
from xml.etree import ElementTree as ET
import cv2,numpy as np
from PIL import Image,ImageDraw
from semantic_art_mixer_v1 import load_assets,sha256
from goggle_single_visor_annotation import visible_masks,append_paths,NS
from remove_subject_skin_underlay import region_colormasks
from bangs_cell_vertex_reduction import polygons
from visor_source_boundary_rgb_audit import rgb_metrics

def source_masks(src):
    _,lens,frame=visible_masks()
    rgb=np.asarray(src.convert("RGB"),np.uint8)
    hsv=cv2.cvtColor(rgb,cv2.COLOR_RGB2HSV)
    warm=(hsv[:,:,0]<=24)&(hsv[:,:,1]>=105)
    spread=rgb.max(2).astype(np.int16)-rgb.min(2).astype(np.int16)
    pale=(rgb.min(2)>138)&(spread<91)&(rgb.mean(2)>178)
    masks={"original":frame,"exclude_warm":frame&~warm,
           "source_pale":frame&pale}
    return lens,frame,masks

def build(src,lens,frame_mask,frame_clusters):
    layers=[]
    for role,region,k in (("visor_lens",lens,6),("visor_frame",frame_mask,frame_clusters)):
        if int(region.sum())<k*20:raise ValueError("Candidate lacks enough observed source pixels")
        for owned,color,kind in region_colormasks(src,region,k):
            d,n,v=polygons(owned,0.35)
            if d:layers.append((role,kind,d,color,n,v))
    if not any(x[0]=="visor_frame" for x in layers):raise ValueError("All frame material lost")
    return layers

def replace_and_render(prior,src,lens,frame_mask,count,folder,outsvg,render):
    root=ET.parse(prior).getroot()
    old_bangs=[ET.tostring(q) for q in root if q.get("data-layer")=="source-bang-cell-verified"]
    if len(old_bangs)!=3:raise AssertionError("Expected 3 certified original fringe paths")
    previous=[x for x in root if x.get("data-part") in ("visor_lens","visor_frame")]
    if not previous:raise ValueError("Expected research visor paths to refine")
    for node in previous:root.remove(node)
    layers=build(src,lens,frame_mask,count)
    append_paths(root,layers)
    current_bangs=[ET.tostring(q) for q in root if q.get("data-layer")=="source-bang-cell-verified"]
    if old_bangs!=current_bangs:raise AssertionError("Original certified bangs were modified")
    ET.ElementTree(root).write(outsvg,encoding="utf-8",xml_declaration=True)
    png=outsvg.with_suffix(".png")
    png.write_bytes(render.svg_to_bytes(svg_path=str(outsvg),width=340,height=340))
    return png,layers

def main():
    p=argparse.ArgumentParser()
    for n in ("root","prior","out"):p.add_argument("--"+n,type=Path,required=True)
    a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    src,_,_=load_assets(a.root)
    lens,frame,variant_masks=source_masks(src)
    base=a.prior/"research_part_scene_with_visor.svg"
    old=np.asarray(Image.open(a.prior/"scene_after_visor.png").convert("RGB"))
    original=np.asarray(src.convert("RGB"),np.uint8)
    observed=lens|frame
    folder=Path(os.environ.get("LOCALAPPDATA",""))/"Minimalizer/research/resvg-py-0.5.0"
    sys.path.insert(0,str(folder));import resvg_py
    old_error=rgb_metrics(original,old,observed)
    old_frame_error=rgb_metrics(original,old,frame)
    rows=[]
    for name,mask in variant_masks.items():
        for palette_size in (4,6,8):
            if name=="original" and palette_size!=4:continue
            tag=f"{name}_palette{palette_size}"
            target=out/(tag+".svg")
            png,layers=replace_and_render(base,src,lens,mask,palette_size,folder,target,resvg_py)
            candidate=np.asarray(Image.open(png).convert("RGB"))
            outer_error=rgb_metrics(original,candidate,observed)
            frame_error=rgb_metrics(original,candidate,frame)
            lens_error=rgb_metrics(original,candidate,lens)
            changed=np.any(candidate!=old,axis=2)
            safe=cv2.dilate(observed.astype(np.uint8),np.ones((5,5),np.uint8))>0
            extra=int((changed&~safe).sum())
            if extra:raise AssertionError(f"Unrelated scene area changed in {tag}: {extra}")
            rows.append({"variant":tag,"source_frame_mask_pixels":int(mask.sum()),
               "source_original_frame_pixels":int(frame.sum()),
               "frame_source_mae":frame_error["source_rgb_mae"],
               "lens_source_mae":lens_error["source_rgb_mae"],
               "whole_visor_source_mae":outer_error["source_rgb_mae"],
               "frame_color_paths":sum(x[0]=="visor_frame" for x in layers),
               "all_visor_vertices":int(sum(x[5] for x in layers)),
               "changes_outside_reviewed_visor":extra,
               "svg":target.name,"png":png.name,
               "svg_sha256":sha256(target),"png_sha256":sha256(png)})
    reference_lens_mae=rgb_metrics(original,old,lens)["source_rgb_mae"]
    # Do NOT allow savings by deleting every pale rim. Retain >=40% of
    # manually marked frame AND no significant loss of lens accuracy.
    accepted=[r for r in rows if r["source_frame_mask_pixels"]>=0.40*int(frame.sum())
        and r["frame_source_mae"]<old_frame_error["source_rgb_mae"]
        and r["whole_visor_source_mae"]<old_error["source_rgb_mae"]
        and r["lens_source_mae"]<=reference_lens_mae+0.25
        and r["changes_outside_reviewed_visor"]==0]
    winner=min(accepted,key=lambda r:(r["whole_visor_source_mae"],r["all_visor_vertices"])) if accepted else None
    chosen=np.asarray(Image.open(out/winner["png"]).convert("RGB")) if winner else old
    figure=Image.new("RGB",(1380,420),"#f0efea")
    for i,im in enumerate((src.convert("RGB"),Image.fromarray(old),
            Image.fromarray(chosen),Image.fromarray(np.asarray(src.convert("RGB"))))):
        figure.paste(im.convert("RGB"),(10+i*342,10))
    draw=ImageDraw.Draw(figure)
    for i,label in enumerate(("REFERENCE ORIGINAL","BASELINE V1","WINNER / OR BASELINE","REFERENCE SOURCE")):
        draw.text((10+i*342,363),label,fill="#263429")
    comparison=out/"source_material_frame_variants.png"
    figure.save(comparison,optimize=True)
    manifest={"status":"SOURCE_MATERIAL_CORRECTION_PASS" if winner else "NO_CANDIDATE_IMPROVEMENT",
       "baseline_frame_mae":old_frame_error["source_rgb_mae"],
       "baseline_whole_visor_mae":old_error["source_rgb_mae"],
       "baseline_lens_mae":reference_lens_mae,
       "manually_annotated_frame_pixels":int(frame.sum()),
       "candidate_results":rows,"selected":winner,
       "source_specific_overfit_warning":True,
       "semantic_frame_boundary_verified":False,"full_character_golden_pass":False,
       "production_changed":False,"certified_inter_eye_bangs_unchanged":True,
       "files":[{"name":q.name,"sha256":sha256(q)} for q in sorted(out.iterdir()) if q.is_file() and q.suffix in (".png",".svg")]}
    (out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":manifest["status"],"baseline_frame_mae":manifest["baseline_frame_mae"],
      "baseline_whole_mae":manifest["baseline_whole_visor_mae"],
      "results":[{k:r[k] for k in ("variant","source_frame_mask_pixels","frame_source_mae","whole_visor_source_mae","lens_source_mae","all_visor_vertices")} for r in rows],
      "winner":{k:winner[k] for k in ("variant","source_frame_mask_pixels","frame_source_mae","whole_visor_source_mae","lens_source_mae","all_visor_vertices")} if winner else None}))
if __name__=="__main__":main()
