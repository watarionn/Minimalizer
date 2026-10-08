"""Source-edge goggle shortlist from frozen contour JSON; diagnostic lines only.

Select edges that plausibly follow source goggles, but never promote edge lines
to a verified frame/lens semantic mask. No filled path or changed character.
"""
import argparse,json,math
from pathlib import Path
from xml.etree import ElementTree as ET
from PIL import Image,ImageDraw
from semantic_art_mixer_v1 import sha256
NS="http://www.w3.org/2000/svg"
def classify(role,curve):
 pts=curve["points"]
 if len(pts)<3:return "reject_short"
 xs=[p[0] for p in pts];ys=[p[1] for p in pts]
 x0,x1=min(xs),max(xs);y0,y1=min(ys),max(ys)
 w=x1-x0+1;h=y1-y0+1
 if y1>=95:return "reject_bang_overlap_risk"
 if role=="left_lens" and (x0<106 or x1>150):return "reject_outside_lens_review"
 if role=="right_lens" and (x0<143 or x1>197):return "reject_outside_lens_review"
 if role=="frame" and (x0<102 or x1>201):return "reject_outside_frame_review"
 if w<5 or h<3 or float(curve["length"])<18:return "reject_tiny_or_linear"
 return "candidate_requires_semantic_review"
def main():
 p=argparse.ArgumentParser()
 for k in ("source","traces","out"):p.add_argument("--"+k,type=Path,required=True)
 a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 original=Image.open(a.source).convert("RGB")
 raw=json.loads(a.traces.read_text(encoding="utf-8"))
 if raw.get("source_sha256")!=sha256(a.source):raise ValueError("Input source differs from traced source")
 sheet=Image.new("RGB",(1360,400),"#efefed");sheet.paste(original,(0,0))
 summary=[];svg=ET.Element("{%s}svg"%NS,{"width":"340","height":"340","viewBox":"0 0 340 340"})
 for i,role in enumerate(("left_lens","right_lens","frame"),1):
  panel=original.copy();draw=ImageDraw.Draw(panel)
  counts={}
  for idx,curve in enumerate(raw["roles"][role]):
   decision=classify(role,curve);counts[decision]=counts.get(decision,0)+1
   points=[tuple(p) for p in curve["points"]]
   if decision=="candidate_requires_semantic_review":
    draw.line(points,fill="#00efc0",width=1)
    # Open stroke only: candidate evidence, not material/geometry.
    ET.SubElement(svg,"{%s}polyline"%NS,{"points":" ".join(f"{x},{y}" for x,y in points),
     "stroke":"#00efc0","stroke-width":"0.6","fill":"none",
     "data-review-role":role,"data-status":"unverified"})
  sheet.paste(panel,(i*340,0))
  ImageDraw.Draw(sheet).text((i*340+6,355),f"{role}: {counts.get('candidate_requires_semantic_review',0)} REVIEW",fill="#222")
  summary.append({"role":role,"decisions":counts,"semantic_verified":False})
 ImageDraw.Draw(sheet).text((6,355),"SOURCE",fill="#222")
 image=a.out/"goggle_contour_shortlist.png";sheet.save(image,optimize=True)
 out_svg=a.out/"diagnostic_open_strokes.svg";ET.ElementTree(svg).write(out_svg,encoding="utf-8",xml_declaration=True)
 report={"status":"UNVERIFIED_OPEN_STROKES_ONLY","source_sha256":sha256(a.source),
         "traces_sha256":sha256(a.traces),"summary":summary,
         "semantic_goggles_mask":False,"filled_goggles_svg":False,"production_authority":False,
         "files":[{"name":q.name,"sha256":sha256(q)} for q in (image,out_svg)]}
 (a.out/"manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"status":report["status"],"summary":summary}))
if __name__=="__main__":main()
