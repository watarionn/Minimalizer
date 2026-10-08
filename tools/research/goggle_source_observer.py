"""GC001 goggles: source chroma observer, no claim of complete segmentation.

Use source-only candidate pixels within a manually inspected goggles window,
never overlay guessed lens/glass on hair. Export evidence and uncertainty.
"""
import argparse,json,os
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from semantic_art_mixer_v1 import load_assets,sha256
from semantic_art_mixer_v3_source_masks import load_observed_masks

def observe(src):
 rgb=np.asarray(src.convert("RGB"),dtype=np.uint8)
 hsv=cv2.cvtColor(rgb,cv2.COLOR_RGB2HSV)
 yy,xx=np.mgrid[:340,:340]
 # Broad diagnostic region from prior independent study.
 roi=(xx>=104)&(xx<=240)&(yy>=38)&(yy<=103)
 # Candidate distinctive cooler blue/teal lens and warm yellow glass.
 # Candidates are observed pixels only, NOT goggles ground truth.
 cool=roi&(hsv[:,:,0]>=80)&(hsv[:,:,0]<=115)&(hsv[:,:,1]>=65)
 warm=roi&(hsv[:,:,0]>=16)&(hsv[:,:,0]<=40)&(hsv[:,:,1]>=65)
 bright=roi&(rgb.min(axis=2)>=215)&(rgb.max(axis=2)-rgb.min(axis=2)<=35)
 return roi,{"cool_lens_candidate":cool,"warm_lens_candidate":warm,"bright_frame_candidate":bright}

def main():
 p=argparse.ArgumentParser()
 for k in ("root","out"):p.add_argument("--"+k,type=Path,required=True)
 a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
 source,_,_=load_assets(a.root);masks,_=load_observed_masks()
 roi,candidates=observe(source)
 rgb=np.asarray(source.convert("RGB"))
 card=Image.new("RGB",(1360,398),"#f0f0ed")
 labels=["ORIGINAL","COOL SOURCE PIXELS","WARM SOURCE PIXELS","BRIGHT SOURCE PIXELS"]
 card.paste(source.convert("RGB"),(0,0))
 records=[]
 for j,(name,mask) in enumerate(candidates.items(),1):
  over=rgb.copy()
  over[roi&~mask]=(over[roi&~mask]*0.28).astype(np.uint8)
  card.paste(Image.fromarray(over),(j*340,0))
  counts=int(mask.sum())
  n,components,stats,_=cv2.connectedComponentsWithStats(mask.astype(np.uint8),8)
  big=[{"pixels":int(stats[k,cv2.CC_STAT_AREA]),"xywh":stats[k,:4].tolist()} for k in range(1,n) if stats[k,cv2.CC_STAT_AREA]>=8]
  records.append({"label":name,"observed_candidate_pixels":counts,"connected_components_at_least8":big,
       "overlap_source_hair":int((mask&masks["hair"]).sum()),
       "overlap_source_face":int((mask&masks["face"]).sum())})
  Image.fromarray(mask.astype(np.uint8)*255).save(out/(name+".png"))
 d=ImageDraw.Draw(card)
 for j,label in enumerate(labels):d.text((j*340+8,355),label,fill="#242a26")
 card.save(out/"goggles_source_candidates.png",optimize=True)
 report={"status":"OBSERVER_ONLY","verified_goggles_segmentation":False,
    "goggles_svg_generated":False,"candidate_observations":records,
    "part_mask_goggles_from_phase04":False,
    "no_generated_geometry":True,"full_character_golden_pass":False,
    "files":[{"name":x.name,"sha256":sha256(x)} for x in sorted(out.iterdir()) if x.is_file()]}
 (out/"manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"status":report["status"],"observations":records}))
if __name__=="__main__":main()
