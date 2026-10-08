"""Conservative classification of frozen goggles source strokes by observed RGB.

Labels are material *hypotheses* only, NOT validated goggles geometry. No
filled SVG, no face/skin paint, no production changes.
"""
import argparse,json,collections
from pathlib import Path
from xml.etree import ElementTree as ET
import numpy as np,cv2
from PIL import Image,ImageDraw
from semantic_art_mixer_v1 import sha256
from goggle_contour_candidate_selection import classify
NS="http://www.w3.org/2000/svg"
def material(rgb,curve):
 pts=np.asarray(curve["points"],np.int32)
 pix=rgb[pts[:,1],pts[:,0]]
 hsv=cv2.cvtColor(pix.reshape(-1,1,3),cv2.COLOR_RGB2HSV).reshape(-1,3)
 bright=(pix.min(axis=1)>=185)&((pix.max(axis=1)-pix.min(axis=1))<75)
 orange=(hsv[:,0]<=24)&(hsv[:,1]>=105)
 glare=(pix.mean(axis=1)>=205)
 frac=lambda a:float(a.mean())
 # High confidence only; otherwise preserve ambiguous review status.
 if frac(orange)>=.52:return "likely_hair_or_warm_material"
 if frac(bright)>=.50:return "possible_white_frame"
 if frac(glare)>=.50:return "possible_reflection"
 return "uncertain_lens_or_frame"
def main():
 p=argparse.ArgumentParser()
 for k in ("source","traces","out"):p.add_argument("--"+k,type=Path,required=True)
 a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 source=Image.open(a.source).convert("RGB");rgb=np.asarray(source)
 trace=json.loads(a.traces.read_text(encoding="utf-8"))
 if trace["source_sha256"]!=sha256(a.source):raise ValueError("Trace/source SHA mismatch")
 colors={"likely_hair_or_warm_material":"#e64c44","possible_white_frame":"#30c6e0",
 "possible_reflection":"#f4d34a","uncertain_lens_or_frame":"#b89aff"}
 svg=ET.Element("{%s}svg"%NS,{"viewBox":"0 0 340 340","width":"340","height":"340"})
 panel=Image.new("RGB",(1360,395),"#eee");panel.paste(source,(0,0));d=ImageDraw.Draw(panel)
 reports=[];tot=collections.Counter()
 for i,role in enumerate(("left_lens","right_lens","frame"),1):
  tile=source.copy();paint=ImageDraw.Draw(tile);counts=collections.Counter()
  for j,curve in enumerate(trace["roles"][role]):
   if classify(role,curve)!="candidate_requires_semantic_review":continue
   label=material(rgb,curve);counts[label]+=1;tot[label]+=1
   points=[tuple(x) for x in curve["points"]]
   paint.line(points,fill=colors[label],width=1)
   ET.SubElement(svg,"{%s}polyline"%NS,{"points":" ".join(f"{x},{y}" for x,y in points),
    "stroke":colors[label],"stroke-width":"0.65","fill":"none",
    "data-role-hypothesis":role,"data-material-hypothesis":label,
    "data-status":"unverified"})
  panel.paste(tile,(i*340,0));d.text((i*340+7,355),f"{role}: {sum(counts.values())} review strokes",fill="#222")
  reports.append({"role":role,"hypothesis_counts":dict(counts),"verified_goggle_strokes":0})
 d.text((7,355),"ORIGINAL",fill="#222")
 board=a.out/"stroke_material_hypotheses.png";panel.save(board,optimize=True)
 vector=a.out/"diagnostic_material_strokes.svg";ET.ElementTree(svg).write(vector,encoding="utf-8",xml_declaration=True)
 manifest={"status":"MATERIAL_HYPOTHESES_ONLY","counts":dict(tot),"roles":reports,
 "verified_goggles_strokes":0,"semantic_lens_frame_mask":False,"filled_svg":False,
 "face_hair_scene_unchanged":True,
 "files":[{"name":q.name,"sha256":sha256(q)} for q in (board,vector)]}
 (a.out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"counts":dict(tot),"verified_goggles_strokes":0}))
if __name__=="__main__":main()
