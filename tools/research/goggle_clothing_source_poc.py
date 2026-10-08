"""Source-observed goggles ROI audit + source-tonal clothing part-scene PoC.

Goggles ROI remains a diagnostic, NOT a proven segmentation. No new opaque
goggle shape is added until independent source mask evidence passes.
"""
import argparse,json,os,sys
from pathlib import Path
from xml.etree import ElementTree as ET
import cv2,numpy as np
from PIL import Image,ImageDraw
from semantic_art_mixer_v1 import load_assets,sha256
from semantic_art_mixer_v3_source_masks import load_observed_masks
from remove_subject_skin_underlay import NS,region_colormasks
from bangs_cell_vertex_reduction import polygons

def replace_roles(tree,source,masks):
 root=tree.getroot()
 records=[]
 for role,colors in (("major_clothing",5),("lower_body",4)):
  existing=[el for el in list(root) if el.get("data-part")==role]
  if not existing:raise ValueError("No old source-owned garment region")
  position=min(list(root).index(x) for x in existing)
  for el in existing:root.remove(el)
  mask=masks[role]&masks["subject"]
  layers=region_colormasks(source,mask,colors)
  for mask_layer,color,kind in layers:
   d,n,v=polygons(mask_layer,0.35)
   if not d:continue
   el=ET.Element("{%s}path"%NS,{"d":d,"fill":"#%02x%02x%02x"%color,"fill-rule":"evenodd",
        "data-part":role,"data-layer":"source-pixel-cell-"+kind})
   root.insert(position,el);position+=1
   records.append({"part":role,"kind":kind,"contours":n,"vertices":v,"rgb":color})
 if root.findall(".//{%s}path[@data-part='face']"%NS) or root.findall(".//{%s}path[@data-part='subject']"%NS) or root.findall(".//{%s}image"%NS):
  raise AssertionError("Face/subject plate or raster introduced")
 if len([p for p in root if p.get("data-layer")=="source-bang-cell-verified"])!=3:
  raise AssertionError("Certified fringe was lost")
 return records

def main():
 p=argparse.ArgumentParser()
 for k in ("root","prior","out"):p.add_argument("--"+k,type=Path,required=True)
 a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
 source,_,_=load_assets(a.root);masks,_=load_observed_masks()
 roi=np.zeros((340,340),bool);roi[38:104,104:241]=True
 # Candidate color/pixel evidence only; no invented goggles mask.
 src=np.asarray(source.convert("RGB"))
 rgb=src[roi]
 distinct=np.unique(rgb,axis=0).shape[0]
 roi_image=Image.fromarray(src.copy())
 draw=ImageDraw.Draw(roi_image);draw.rectangle((104,38,240,103),outline="#00e9a0",width=2)
 roi_image.save(out/"goggles_observation_window.png")
 base=a.prior/"part_owned_tonal_hair_scene.svg"
 doc=ET.parse(base)
 parts=replace_roles(doc,source,masks)
 svg=out/"source_tonal_clothing_scene.svg";doc.write(svg,encoding="utf-8",xml_declaration=True)
 renderdir=Path(os.environ.get("LOCALAPPDATA",""))/"Minimalizer/research/resvg-py-0.5.0"
 sys.path.insert(0,str(renderdir));import resvg_py
 before=out/"before.png";after=out/"after.png"
 before.write_bytes(resvg_py.svg_to_bytes(svg_path=str(base),width=340,height=340))
 after.write_bytes(resvg_py.svg_to_bytes(svg_path=str(svg),width=340,height=340))
 a0=np.asarray(Image.open(before).convert("RGB"));a1=np.asarray(Image.open(after).convert("RGB"))
 changed=np.any(a0!=a1,axis=2)
 owned=(masks["major_clothing"]|masks["lower_body"])&masks["subject"]
 allowed=cv2.dilate(owned.astype(np.uint8),np.ones((5,5),np.uint8))>0
 forbidden=int((changed&~allowed).sum())
 if forbidden:raise AssertionError(f"Garment changes outside source-owned masks: {forbidden}")
 compare=Image.new("RGB",(1040,392),"#eee")
 for i,im in enumerate([source.convert("RGB"),Image.fromarray(a0),Image.fromarray(a1)]):
  compare.paste(im,(10+i*345,14))
 d=ImageDraw.Draw(compare)
 for i,t in enumerate(("ORIGINAL","BEFORE SOURCE-TONAL CLOTHES","AFTER SOURCE-TONAL CLOTHES")):
  d.text((12+i*345,360),t,fill="#24312b")
 compare.save(out/"comparison_goggles_clothing.png",optimize=True)
 report={"status":"RESEARCH_HOLD","goggles_roi":[104,38,240,103],
         "goggles_candidate_pixels":int(roi.sum()),"goggles_roi_distinct_colors":int(distinct),
         "goggles_mask_verified":False,"garment_layers":parts,"scene_changed_pixels":int(changed.sum()),
         "changed_outside_garment_owned_masks":forbidden,
         "face_unresolved":True,"core_golden_pass":False,
         "files":[{"name":f.name,"sha256":sha256(f)} for f in sorted(out.iterdir()) if f.is_file()]}
 (out/"manifest.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print(json.dumps({"status":report["status"],"goggles_mask_verified":False,"goggles_roi_distinct_colors":distinct,
     "garment_layer_count":len(parts),"garment_svg_vertices":sum(p["vertices"] for p in parts),
     "scene_changed_pixels":report["scene_changed_pixels"],"changes_outside_garments":forbidden}))
if __name__=="__main__":main()
