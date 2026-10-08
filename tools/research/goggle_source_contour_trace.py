"""Source-edge-constrained candidate contours for visible goggles.

Extract *observed edges* in three manual review zones. They remain proposals:
a curve following a real pixel edge is not necessarily a semantic goggle.
No fill, mask ownership reassignment, or production SVG is permitted.
"""
import argparse,json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from semantic_art_mixer_v1 import sha256
from goggle_annotation_review import ZONES
def trace(source):
 rgb=np.asarray(source.convert("RGB"),dtype=np.uint8)
 gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
 results={}
 for name,(x0,y0,x1,y1) in ZONES.items():
  sub=gray[y0:y1,x0:x1]
  # Original-source edges only; no closed polygon interpolation.
  edges=cv2.Canny(sub,55,135,L2gradient=True)
  contours,_=cv2.findContours(edges,cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
  kept=[]
  for c in contours:
   if cv2.arcLength(c,False)<9:continue
   coords=[[int(p[0][0]+x0),int(p[0][1]+y0)] for p in c]
   kept.append({"length":round(float(cv2.arcLength(c,False)),2),"points":coords})
  results[name]=sorted(kept,key=lambda k:-k["length"])
 return results
def main():
 p=argparse.ArgumentParser()
 for n in ("source","out"):p.add_argument("--"+n,type=Path,required=True)
 a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 image=Image.open(a.source).convert("RGB")
 if image.size!=(340,340):raise ValueError("Expected 340x340 source")
 contours=trace(image)
 grid=Image.new("RGB",(1360,398),"#f1f1ef")
 grid.paste(image,(0,0))
 board=ImageDraw.Draw(grid);board.text((7,355),"ORIGINAL",fill="#222")
 diagnostics=[]
 for i,(role,curves) in enumerate(contours.items(),1):
  panel=image.copy();d=ImageDraw.Draw(panel)
  for c in curves[:12]:
   if len(c["points"])>=2:d.line([tuple(p) for p in c["points"]],fill="#00efbc",width=1)
  grid.paste(panel,(340*i,0));board.text((340*i+7,355),f"{role.upper()}: {len(curves)} EDGE CURVES",fill="#222")
  diagnostics.append({"role":role,"contours":len(curves),"largest_path_lengths":[v["length"] for v in curves[:5]],"source_pixels_only":True})
 output=a.out/"goggle_source_edge_traces.png";grid.save(output,optimize=True)
 # Preserve exact pixels of observed contours for later review; NEVER produce semantic polygons.
 (a.out/"source_edge_traces.json").write_text(json.dumps({"source_sha256":sha256(a.source),"roles":contours,
   "verified_visible_goggle_contours":False,"svg_render_authorized":False},ensure_ascii=False),encoding="utf-8")
 manifest={"stage":"Goggle Source Edge Traces","status":"HOLD_UNVERIFIED_PART_BOUNDARIES",
 "source_sha256":sha256(a.source),"diagnostics":diagnostics,"verified_lenses_frame":False,
 "svg_generated":False,"hair_owned_pixels_changed":0,
 "files":[{"name":q.name,"sha256":sha256(q)} for q in a.out.iterdir() if q.is_file()]}
 (a.out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"status":manifest["status"],"diagnostics":diagnostics}))
if __name__=="__main__":main()
