"""Measure actual source-pale rim component gaps and bangs occlusion evidence.

No shortest-path bridging, no guessed hidden geometry, no new filled SVG.
"""
import argparse,json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from semantic_art_mixer_v1 import sha256
def analyze(source,mask):
 rgb=np.asarray(source.convert("RGB"),np.uint8)
 fg=np.asarray(mask.convert("L"))>0
 n,labels,stats,_=cv2.connectedComponentsWithStats(fg.astype(np.uint8),8)
 parts=[]
 for i in range(1,n):
  area=int(stats[i,cv2.CC_STAT_AREA])
  if area<10:continue
  y,x=np.where(labels==i)
  parts.append({"id":i,"area":area,"bbox":stats[i,:4].tolist(),"points":np.column_stack((x,y))})
 parts.sort(key=lambda v:-v["area"])
 gaps=[]
 for i in range(len(parts)):
  for j in range(i+1,len(parts)):
   aa=parts[i]["points"];bb=parts[j]["points"]
   # closest source pixels only; not a proposed material connection.
   dist=np.sum((aa[:,None,:].astype(np.int32)-bb[None,:,:].astype(np.int32))**2,axis=2)
   u,v=np.unravel_index(np.argmin(dist),dist.shape)
   p=aa[u];q=bb[v];num=int(max(abs(p-q))+1)
   xx=np.rint(np.linspace(p[0],q[0],num)).astype(int);yy=np.rint(np.linspace(p[1],q[1],num)).astype(int)
   sampled=rgb[yy,xx].astype(np.int16)
   hsv=cv2.cvtColor(sampled.astype(np.uint8).reshape(-1,1,3),cv2.COLOR_RGB2HSV).reshape(-1,3)
   orange=(hsv[:,0]<=24)&(hsv[:,1]>=105)
   pale=(sampled.min(1)>138)&((sampled.max(1)-sampled.min(1))<91)&(sampled.mean(1)>178)
   gaps.append({"pair":[i,j],"minimum_pixel_gap":round(float(np.sqrt(dist[u,v])),3),
      "nearest_endpoints":[p.tolist(),q.tolist()],"sample_count":num,
      "source_orange_samples":int(orange.sum()),"source_pale_samples":int(pale.sum()),
      "semantic_occlusion_verified":False,"bridge_authorized":False})
 return parts,gaps
def main():
 p=argparse.ArgumentParser()
 for k in ("source","mask","out"):p.add_argument("--"+k,type=Path,required=True)
 a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 src=Image.open(a.source).convert("RGB");mask=Image.open(a.mask).convert("L")
 if src.size!=(340,340) or mask.size!=src.size:raise ValueError("Expected 340x340")
 parts,gaps=analyze(src,mask)
 panel=Image.new("RGB",(1020,390),"#eee");panel.paste(src,(0,0))
 over=np.asarray(src).copy();over[np.asarray(mask)>0]=[20,230,175]
 panel.paste(Image.fromarray(over),(340,0))
 d=ImageDraw.Draw(panel)
 for gap in gaps:
  p,q=gap["nearest_endpoints"]
  d.line([(680+p[0],p[1]),(680+q[0],q[1])],fill="#ef4d72",width=2)
  d.ellipse((680+p[0]-2,p[1]-2,680+p[0]+2,p[1]+2),fill="#f0dd3c")
  d.ellipse((680+q[0]-2,q[1]-2,680+q[0]+2,q[1]+2),fill="#f0dd3c")
 panel.paste(src,(680,0))
 # re-draw only diagnostic shortest-gap lines on source copy, not a rendered frame.
 for gap in gaps:
  p,q=gap["nearest_endpoints"]
  d.line([(680+p[0],p[1]),(680+q[0],q[1])],fill="#ef4d72",width=2)
 for i,t in enumerate(("SOURCE","OBSERVED PALE PIXELS","DIAGNOSTIC GAPS / NOT FRAME")):d.text((340*i+5,354),t,fill="#222")
 panel.save(a.out/"rim_gaps_source_review.png")
 report={"status":"GAP_OBSERVATION_ONLY","components":[{"area":x["area"],"bbox":x["bbox"]} for x in parts],
 "gaps":gaps,"occlusion_verified":False,"bridges_rendered":False,"production_changed":False,
 "source_sha256":sha256(a.source),"mask_sha256":sha256(a.mask)}
 (a.out/"manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"components":report["components"],"gaps":gaps}))
if __name__=="__main__":main()
