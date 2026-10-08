"""Goggles source edge/topology observer; not a verified semantic mask.

Analyze connected Canny contours in an explicitly tentative top-head ROI.
Export source overlays and topology; do not draw guessed frame/lens.
"""
import argparse,json
from pathlib import Path
import numpy as np,cv2
from PIL import Image,ImageDraw
from semantic_art_mixer_v1 import load_assets,sha256
from semantic_art_mixer_v3_source_masks import load_observed_masks

def inspect(source,masks):
 rgb=np.asarray(source.convert("RGB"))
 gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
 edges=cv2.Canny(gray,65,150,L2gradient=True)
 roi=np.zeros(gray.shape,np.uint8);roi[38:104,104:241]=255
 edges=cv2.bitwise_and(edges,roi)
 cs,hierarchy=cv2.findContours(edges,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
 hits=[]
 for i,c in enumerate(cs):
  x,y,w,h=cv2.boundingRect(c)
  length=cv2.arcLength(c,False)
  if length<12 or w<3 or h<3:continue
  color=tuple(map(int,rgb[y+h//2,x+w//2]))
  hits.append({"xywh":[int(x),int(y),int(w),int(h)],"length":round(float(length),2),
   "closed":bool(cv2.norm(c[0][0].astype(float)-c[-1][0].astype(float))<2),
   "hair_overlap_bbox":int(masks["hair"][y:y+h,x:x+w].sum()),"sample_original_rgb":color})
 return edges,sorted(hits,key=lambda q:-q["length"])

def main():
 ap=argparse.ArgumentParser()
 for key in ("root","out"):ap.add_argument("--"+key,type=Path,required=True)
 a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 source,_,_=load_assets(a.root);masks,_=load_observed_masks()
 edges,features=inspect(source,masks)
 Image.fromarray(edges).save(a.out/"source_goggle_window_edges.png")
 rgb=np.asarray(source.convert("RGB"))
 panel=source.copy().convert("RGB")
 draw=ImageDraw.Draw(panel)
 for hit in features[:20]:
  x,y,w,h=hit["xywh"];draw.rectangle((x,y,x+w-1,y+h-1),outline="#00eec5",width=1)
 panel.save(a.out/"goggle_edge_candidates.png",optimize=True)
 report={"status":"OBSERVER_ONLY","roi_xyxy":[104,38,240,103],
   "edge_candidate_count":len(features),"largest_candidates":features[:30],
   "lens_frame_verified":False,"goggle_mask_generated":False,"goggle_svg_generated":False,
   "hair_mask_not_reassigned":True,"full_character_golden_pass":False,
   "files":[{"name":p.name,"sha256":sha256(p)} for p in a.out.iterdir() if p.is_file()]}
 (a.out/"manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"status":report["status"],"candidate_count":len(features),
  "top5":features[:5],"lens_frame_verified":False}))
if __name__=="__main__":main()
