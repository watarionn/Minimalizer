"""Audit existing AnimeSeg and frozen SA7.9 goggles evidence on GC001.

No new models, no geometry or mask generated for production. Existing observer
class 'accessory' is not automatically 'goggles'. Detect historical eye-as-
goggles hypotheses and source head ROI intersection. Fail closed.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np,cv2
from PIL import Image,ImageDraw
from semantic_art_mixer_v1 import sha256
CLASS_ACCESSORY=(128,128,0)
TOP_ROI=(104,38,241,104)
HISTORIC_BBOXES=((137,119,18,13),(185,120,24,12),(104,33,116,61))
def bbox_overlap(box,roi):
 x,y,w,h=box;x0,y0,x1,y1=roi
 return max(0,min(x+w,x1)-max(x,x0))*max(0,min(y+h,y1)-max(y,y0))
def audit(source,observer):
 src=np.asarray(source.convert("RGB"),np.uint8)
 mask=np.asarray(observer.convert("RGB"),np.uint8)
 if src.shape!=mask.shape or src.shape[:2]!=(340,340):raise ValueError("Canonical 340x340 source/mask required")
 accessory=np.all(mask==np.asarray(CLASS_ACCESSORY,np.uint8),axis=2)
 x0,y0,x1,y1=TOP_ROI
 roi=np.zeros(accessory.shape,bool);roi[y0:y1,x0:x1]=True
 top=accessory&roi
 n,labels,stats,_=cv2.connectedComponentsWithStats(top.astype(np.uint8),8)
 blobs=[{"pixels":int(stats[i,cv2.CC_STAT_AREA]),"xywh":stats[i,:4].tolist()} for i in range(1,n) if stats[i,cv2.CC_STAT_AREA]>=4]
 bboxes=[{"xywh":list(b),"overlap_px_with_goggle_window":bbox_overlap(b,TOP_ROI)} for b in HISTORIC_BBOXES]
 return accessory,top,{"observer_accessory_pixels":int(accessory.sum()),"accessory_in_goggle_window":int(top.sum()),"accessory_roi_components":blobs,"historic_eyewear_proposals":bboxes,"verified_goggle_mask":False,"semantic_role":"accessory_not_goggles","production_render_authority":False}
def main():
 ap=argparse.ArgumentParser()
 for key in ("source","mask","out"):ap.add_argument("--"+key,type=Path,required=True)
 a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 source=Image.open(a.source).convert("RGB");observer=Image.open(a.mask).convert("RGB")
 all_acc,top,report=audit(source,observer)
 base=source.copy();im=np.asarray(base).copy()
 im[top]=(0.45*im[top]+0.55*np.array([35,230,108])).astype(np.uint8)
 page=Image.new("RGB",(1020,400),"#efefed")
 for i,p in enumerate([source,Image.fromarray(im),Image.fromarray(np.repeat((top[:,:,None]*255).astype(np.uint8),3,axis=2))]):
  page.paste(p,(i*340,0))
 d=ImageDraw.Draw(page)
 for i,s in enumerate(("CANONICAL SOURCE","ANIMESEG ACCESSORY IN ROI","SOURCE-CLIPPED CANDIDATE")):d.text((i*340+6,357),s,fill="#222")
 page.save(a.out/"observer_accessory_head_audit.png",optimize=True)
 Image.fromarray(top.astype(np.uint8)*255).save(a.out/"observer_accessory_top_roi.png")
 report.update({"source_sha":sha256(a.source),"animeseg_mask_sha":sha256(a.mask),"status":"HOLD_SOURCE_EVIDENCE_ONLY",
      "source_artifacts":[{"name":p.name,"sha256":sha256(p)} for p in a.out.glob("*.png")]})
 (a.out/"manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(report,ensure_ascii=False))
if __name__=="__main__":main()
