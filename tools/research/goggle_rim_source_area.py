"""Local source-white-rim area candidates around six visually reviewed traces.

Candidate-only masks: require pixel proximity to original white rim strokes and
source-white colors. No inferred hidden frame or full goggles rendering.
"""
import argparse,json
from pathlib import Path
import numpy as np,cv2
from PIL import Image,ImageDraw
from semantic_art_mixer_v1 import sha256
from goggle_numbered_review import enumerate_strokes
IDS=("left_lens-04","right_lens-03","right_lens-08")
def local_rim(rgb,points):
 h,w=rgb.shape[:2];seed=np.zeros((h,w),np.uint8)
 pts=np.asarray(points,np.int32)
 for x,y in pts:cv2.circle(seed,(int(x),int(y)),2,255,-1)
 near=cv2.dilate(seed,np.ones((5,5),np.uint8))>0
 rgb16=rgb.astype(np.int16)
 spread=rgb16.max(2)-rgb16.min(2)
 # pale silver/white source pixels, not orange hair.
 pale=(rgb16.min(2)>138)&(spread<91)&(rgb16.mean(2)>178)
 return (near&pale)
def main():
 p=argparse.ArgumentParser()
 for n in ("source","traces","out"):p.add_argument("--"+n,type=Path,required=True)
 a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 src=Image.open(a.source).convert("RGB");rgb=np.asarray(src)
 trace=json.loads(a.traces.read_text(encoding="utf-8"))
 if trace["source_sha256"]!=sha256(a.source):raise ValueError("Source mismatch")
 items={x["id"]:x for x in enumerate_strokes(rgb,trace)}
 total=np.zeros((340,340),bool);metrics=[]
 for ident in IDS:
  it=items[ident];curve=trace["roles"][it["role"]][it["trace_index"]]
  mask=local_rim(rgb,curve["points"]);total|=mask
  metrics.append({"id":ident,"candidate_pale_pixels":int(mask.sum()),"semantic_verified":False})
 overlay=rgb.copy();overlay[total]=(overlay[total]*.45+np.array([0,245,185])*.55).astype(np.uint8)
 sheet=Image.new("RGB",(1020,390),"#eee")
 for i,im in enumerate((src,Image.fromarray(overlay),Image.fromarray((total*255).astype(np.uint8)).convert("RGB"))):sheet.paste(im,(340*i,0))
 d=ImageDraw.Draw(sheet)
 for i,name in enumerate(("SOURCE","SOURCE-PALE RIM CANDIDATE","UNVERIFIED AREA MASK")):d.text((i*340+6,355),name,fill="#222")
 sheet.save(a.out/"source_pale_rim_candidate.png")
 Image.fromarray((total*255).astype(np.uint8)).save(a.out/"source_pale_rim_mask.png")
 result={"status":"UNVERIFIED_SOURCE_PALE_AREA","source_sha256":sha256(a.source),
 "metrics":metrics,"candidate_union_pixels":int(total.sum()),"semantic_verified":False,
 "full_frame_mask":False,"filled_svg_authorized":False,"production_changed":False,
 "files":[{"name":f.name,"sha256":sha256(f)} for f in a.out.glob("*.png")]}
 (a.out/"manifest.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(result))
if __name__=="__main__":main()
