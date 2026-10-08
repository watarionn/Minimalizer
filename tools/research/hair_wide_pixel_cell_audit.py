"""Hair-wide pixel-cell audit, source-only and research-only.

The original Phase04 hair mask is kept immutable. The certified source-orange
forelock is unioned as a *derived* hair mask; do not expand arbitrary orange
elsewhere or fill unresolved facial skin. Measure original hair separately.
"""
import argparse,json,os,sys
from pathlib import Path
from xml.etree import ElementTree as ET
import numpy as np,cv2
from PIL import Image,ImageDraw
from semantic_art_mixer_v1 import load_assets,sha256
from semantic_art_mixer_v3_source_masks import load_observed_masks
from bangs_continuity_source_bridge import extract
from bangs_cell_vertex_reduction import polygons
from remove_subject_skin_underlay import NS,observed_color
def write_hair(mask,color,path,epsilon):
    data,n,verts=polygons(mask,epsilon)
    root=ET.Element("{%s}svg"%NS,{"width":"340","height":"340","viewBox":"0 0 340 340"})
    if not data:raise ValueError("Hair contour empty")
    ET.SubElement(root,"{%s}path"%NS,{"d":data,"fill":"#%02x%02x%02x"%color,
         "fill-rule":"evenodd","data-part":"hair","data-layer":"source-observed-wide-hair"})
    ET.ElementTree(root).write(path,encoding="utf-8",xml_declaration=True)
    return verts,n
def main():
    ap=argparse.ArgumentParser()
    for n in ("root","prior","out"):ap.add_argument("--"+n,type=Path,required=True)
    a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    source,_,_=load_assets(a.root);masks,_=load_observed_masks()
    _,fringe=extract(source,masks)
    old_hair=masks["hair"]&masks["subject"]
    derived=old_hair|fringe
    newly=derived&~old_hair
    if int(newly.sum())!=390:raise ValueError("unexpected added source hair")
    rgba=np.zeros((340,340,4),np.uint8);rgba[:,:,3]=derived.astype(np.uint8)*255
    Image.fromarray(rgba).save(out/"derived_hair_source_mask.png")
    folder=Path(os.environ.get("LOCALAPPDATA",""))/"Minimalizer/research/resvg-py-0.5.0"
    sys.path.insert(0,str(folder));import resvg_py
    palette=observed_color(source,old_hair)
    variants=[]
    for name,mask in (("original",old_hair),("corrected",derived)):
        for epsilon in (0.0,0.35,0.6):
            tag=f"{name}_{str(epsilon).replace('.','p')}"
            svg=out/(tag+".svg")
            verts,contours=write_hair(mask,palette,svg,epsilon)
            png=out/(tag+".png")
            png.write_bytes(resvg_py.svg_to_bytes(svg_path=str(svg),width=340,height=340))
            alpha=np.asarray(Image.open(png).convert("RGBA").getchannel("A"))>=128
            inmask=int((alpha&mask).sum());extra=int((alpha&~mask).sum())
            variants.append({"tag":tag,"mask_pixels":int(mask.sum()),"covered":inmask,
                 "missing":int(mask.sum())-inmask,"outside":extra,"vertices":verts,
                 "contours":contours,"svg_sha256":sha256(svg),"png_sha256":sha256(png)})
    # The previously corrected full character scene already has the fringe
    # overlay. This audit does NOT blindly lay one giant colored hair plane
    # over goggles, accessory, or skin and claim improvement.
    prior=Image.open(a.prior/"subject_with_verified_bangs.png").convert("RGB")
    compare=Image.new("RGB",(1040,396),"#efefed")
    for i,img in enumerate((source.convert("RGB"),prior,
          Image.open(out/"corrected_0p35.png").convert("RGBA"))):
        if img.mode=="RGBA":
            bg=Image.new("RGBA",img.size,"#f5eee4");bg.alpha_composite(img);img=bg.convert("RGB")
        compare.paste(img,(10+i*345,12))
    pen=ImageDraw.Draw(compare)
    for i,lbl in enumerate(("REFERENCE","PRIOR INCOMPLETE SCENE","CORRECTED HAIR-ONLY SVG")):
        pen.text((12+i*345,358),lbl,fill="#26352c")
    compare.save(out/"compare_wide_hair_audit.png",optimize=True)
    choices=[v for v in variants if v["tag"].startswith("corrected_") and v["outside"]==0]
    best=max(choices,key=lambda v:(v["covered"],-v["vertices"])) if choices else None
    report={"status":"RESEARCH_HOLD","source_hair_pixels":int(old_hair.sum()),
       "derived_source_hair_pixels":int(derived.sum()),"face_misclassified_fringe_pixels":int(newly.sum()),
       "source_orange_fringe_pixels":int(fringe.sum()),
       "variants":variants,"best_zero_excess":best["tag"] if best else None,
       "face_unresolved":True,"no_large_skin_or_hair_overlay_into_composite":True,
       "core_golden_pass":False,
       "artifacts":[{"name":p.name,"sha256":sha256(p)} for p in out.iterdir() if p.is_file()]}
    (out/"manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("source_hair_pixels","derived_source_hair_pixels","face_misclassified_fringe_pixels","best_zero_excess")}|{"variants":[{k:v for k,v in x.items() if k in ("tag","covered","missing","outside","vertices")} for x in variants]}))
if __name__=="__main__":main()
