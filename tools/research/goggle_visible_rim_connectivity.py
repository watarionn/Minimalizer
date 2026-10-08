"""Observed white-rim connectivity audit, no invented bridge or fill."""
import argparse,json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from semantic_art_mixer_v1 import sha256
def audit(source,seed):
 rgb=np.asarray(source.convert("RGB"),np.uint8);base=np.asarray(seed.convert("L"))>0
 vals=rgb.astype(np.int16);spread=vals.max(2)-vals.min(2)
 pale=(vals.min(2)>138)&(spread<91)&(vals.mean(2)>178)
 # Search only near already source-supported rim, never connect through hair.
 nearby=cv2.dilate(base.astype(np.uint8),np.ones((7,7),np.uint8))>0
 candidate=pale&nearby
 n,labels,stats,_=cv2.connectedComponentsWithStats(candidate.astype(np.uint8),8)
 comps=[{"area":int(stats[i,cv2.CC_STAT_AREA]),"bbox":stats[i,:4].tolist(),"touches_previous":bool(np.any(base&(labels==i)))} for i in range(1,n)]
 return candidate,sorted(comps,key=lambda x:-x["area"])
def main():
 p=argparse.ArgumentParser()
 for k in ("source","seed","out"):p.add_argument("--"+k,type=Path,required=True)
 a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 src=Image.open(a.source).convert("RGB");seed=Image.open(a.seed).convert("L")
 if src.size!=(340,340) or seed.size!=src.size:raise ValueError("Canonical size mismatch")
 cand,components=audit(src,seed)
 orig=np.asarray(seed)>0
 gained=cand&~orig
 panel=Image.new("RGB",(1020,391),"#eee")
 panel.paste(src,(0,0))
 overlay=np.asarray(src).copy()
 overlay[orig]=[45,215,175];overlay[gained]=[246,214,54]
 panel.paste(Image.fromarray(overlay),(340,0))
 panel.paste(Image.fromarray((cand*255).astype(np.uint8)).convert("RGB"),(680,0))
 d=ImageDraw.Draw(panel)
 for i,label in enumerate(("SOURCE","GREEN OLD / YELLOW SOURCE NEIGHBORS","UNVERIFIED PALE CONNECTIVITY")):d.text((340*i+5,356),label,fill="#222")
 panel.save(a.out/"visible_rim_connectivity.png")
 Image.fromarray((cand*255).astype(np.uint8)).save(a.out/"candidate_connected_pale_pixels.png")
 report={"status":"SOURCE_NEIGHBOR_CONNECTIVITY_ONLY","original_pixels":int(orig.sum()),"candidate_pixels":int(cand.sum()),"new_observed_pale_pixels":int(gained.sum()),"components":components,"semantic_rim_verified":False,"hidden_bridge_inferred":False,"filled_svg_generated":False,"production_changed":False,"source_sha256":sha256(a.source)}
 (a.out/"manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({k:v for k,v in report.items() if k!="components"}|{"component_count":len(components),"top_components":components[:8]}))
if __name__=="__main__":main()
