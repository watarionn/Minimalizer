"""Number source-constrained goggle stroke hypotheses for independent visual review.

All 38 prior candidates get stable IDs; likely white-rim edges receive a
larger, separately numbered contact sheet. Source pixels only, no semantic
approval and no render authority.
"""
import argparse,json,collections
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from semantic_art_mixer_v1 import sha256
from goggle_contour_candidate_selection import classify
from goggle_stroke_material_classification import material
ROLES=("left_lens","right_lens","frame")
def enumerate_strokes(rgb,trace):
 items=[]
 for role in ROLES:
  for i,curve in enumerate(trace["roles"][role]):
   if classify(role,curve)!="candidate_requires_semantic_review":continue
   pts=np.asarray(curve["points"],dtype=int);x0,y0=pts.min(axis=0);x1,y1=pts.max(axis=0)
   items.append({"id":f"{role}-{i:02d}","role":role,"trace_index":i,
      "material_hypothesis":material(rgb,curve),"source_bbox_xyxy":[int(x0),int(y0),int(x1),int(y1)],
      "length":curve["length"],"semantic_verdict":"pending_independent_review",
      "source_verified_goggles":False})
 return items
def main():
 p=argparse.ArgumentParser()
 for n in ("source","traces","out"):p.add_argument("--"+n,type=Path,required=True)
 a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 source=Image.open(a.source).convert("RGB")
 trace=json.loads(a.traces.read_text(encoding="utf-8"))
 if trace["source_sha256"]!=sha256(a.source):raise ValueError("Frozen source mismatch")
 rgb=np.asarray(source)
 items=enumerate_strokes(rgb,trace)
 if len(items)!=38:raise ValueError("Prior candidate set drifted")
 # Isolate individual curves as numbered crops for human verification.
 favorites=[it for it in items if it["material_hypothesis"]=="possible_white_frame"]
 if len(favorites)!=6:raise ValueError("White-rim candidate count drifted")
 sheet=Image.new("RGB",(960,660),"#f2f1ee")
 pen=ImageDraw.Draw(sheet)
 for idx,it in enumerate(favorites):
  curve=trace["roles"][it["role"]][it["trace_index"]]
  x0,y0,x1,y1=it["source_bbox_xyxy"]
  pad=10;box=(max(0,x0-pad),max(0,y0-pad),min(340,x1+pad+1),min(340,y1+pad+1))
  im=source.crop(box).resize((300,240),Image.Resampling.NEAREST)
  draw=ImageDraw.Draw(im)
  points=[((p[0]-box[0])*300/(box[2]-box[0]),(p[1]-box[1])*240/(box[3]-box[1])) for p in curve["points"]]
  if len(points)>1:draw.line(points,fill="#00f0ca",width=3)
  left=(idx%3)*320;top=(idx//3)*325
  sheet.paste(im,(left+10,top+20))
  pen.text((left+10,top+268),it["id"]+" : WHITE RIM CANDIDATE",fill="#22332c")
 sheet.save(a.out/"six_white_frame_numbered_review.png",optimize=True)
 # Source-level numbered scene tracks original form, not a replacement image.
 full=source.copy();draw=ImageDraw.Draw(full)
 for it in items:
  x0,y0,x1,y1=it["source_bbox_xyxy"]
  draw.text((x0,max(0,y0-10)),it["id"].split("-")[-1],fill="#04ffd4")
 full.save(a.out/"all_stroke_ids_source.png",optimize=True)
 (a.out/"stroke_review_queue.json").write_text(json.dumps({"source_sha256":sha256(a.source),
  "trace_sha256":sha256(a.traces),"items":items,"approved":[]},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 counts=collections.Counter(it["material_hypothesis"] for it in items)
 report={"status":"NUMBERED_REVIEW_READY","candidates":len(items),"white_frame_review":len(favorites),
  "material_counts":dict(counts),"verified_goggle_strokes":0,"filled_svg_generated":False,
  "production_unchanged":True,
  "artifacts":[{"name":p.name,"sha256":sha256(p)} for p in sorted(a.out.iterdir()) if p.is_file()]}
 (a.out/"manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"status":report["status"],"white_ids":[x["id"] for x in favorites],"counts":dict(counts)}))
if __name__=="__main__":main()
