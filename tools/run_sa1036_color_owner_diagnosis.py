"""Diagnose visually dominant material mismatch in an existing research scene."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import cv2,numpy as np
from minimalizer_zerobase.composition.semantic import rasterize_primitive_candidate

def inspect(scene_path:Path, source_path:Path)->dict:
 scene=json.loads(scene_path.read_text(encoding="utf-8-sig"))
 records=scene["primitives_back_to_front"]
 width,height=scene["coordinate_space"]["pixel_width"],scene["coordinate_space"]["pixel_height"]
 raw=cv2.imread(str(source_path),cv2.IMREAD_UNCHANGED)
 if raw is None:raise ValueError("source missing")
 source=cv2.cvtColor(raw,cv2.COLOR_BGRA2RGB if raw.shape[2]==4 else cv2.COLOR_BGR2RGB)
 owner=np.full((height,width),-1,np.int32)
 for index,p in enumerate(records):
  if p.get("structural_support_only"):continue
  mask=rasterize_primitive_candidate(p,width=width,height=height)
  owner[mask]=index
 result={}
 for index,p in enumerate(records):
  mask=owner==index
  if not np.any(mask):continue
  ys,xs=np.where(mask)
  rgb=source[mask].astype(np.int16)
  spread=np.ptp(rgb,axis=1)
  white=(np.min(rgb,axis=1)>170)&(spread<50)
  dark=np.max(rgb,axis=1)<105
  green=(rgb[:,1]>rgb[:,0]+30)&(rgb[:,1]>rgb[:,2]+25)
  entry={
   "visible_pixels":int(mask.sum()),
   "bbox":[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())],
   "original_palette":p["palette_color_rgb"],
   "source_white_pixels":int(white.sum()),
   "source_dark_pixels":int(dark.sum()),
   "source_green_pixels":int(green.sum()),
   "white_fraction":round(float(white.mean()),5),
   "dark_fraction":round(float(dark.mean()),5),
   "source_neutral_fraction":round(float((spread<35).mean()),5),
  }
  if p.get("source_mask_owner") in ("lower_body","torso","major_clothing"):
   rows=[]
   for y1,y2 in ((185,220),(220,245),(245,275),(275,315),(315,340)):
    part=mask[y1:y2]
    arr=source[y1:y2][part].astype(np.int16)
    if len(arr):
     sep=np.ptp(arr,axis=1)
     white=np.min(arr,axis=1)>170
     rows.append({"y":[y1,y2],"visible":len(arr),"source_white_frac":round(float(np.mean(white&(sep<50))),4),"source_dark_frac":round(float(np.mean(np.max(arr,axis=1)<105)),4)})
   entry["vertical_bands"]=rows
  result[p.get("source_mask_owner") or p["primitive_id"]]=entry
 return result

def main()->None:
 p=argparse.ArgumentParser()
 p.add_argument("--scene",type=Path,required=True)
 p.add_argument("--source",type=Path,required=True)
 p.add_argument("--output",type=Path,required=True)
 a=p.parse_args()
 report=inspect(a.scene,a.source)
 a.output.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(report,indent=2))
if __name__=="__main__":main()
