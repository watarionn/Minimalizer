"""Source-part SVG ownership diagnostics, no modification to source or SVG."""
import argparse,json,os,sys
from pathlib import Path
import numpy as np,cv2
from PIL import Image,ImageDraw
from xml.etree import ElementTree as ET
from semantic_art_mixer_v1 import load_assets,sha256
from semantic_art_mixer_v3_source_masks import load_observed_masks
from remove_subject_skin_underlay import NS
PARTS=("face","hair","accessory_or_held_object","major_clothing","torso","neck","left_arm","right_arm","lower_body")
def main():
 p=argparse.ArgumentParser()
 for k in ("root","prior","out"):p.add_argument("--"+k,type=Path,required=True)
 a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
 source,_,_=load_assets(a.root);masks,_=load_observed_masks()
 scene=a.prior/"part_owned_tonal_hair_scene.svg"
 root=ET.parse(scene).getroot()
 if root.findall(".//{%s}path[@data-part='face']"%NS) or root.findall(".//{%s}path[@data-part='subject']"%NS):raise AssertionError("face plate in source scene")
 rdir=Path(os.environ.get("LOCALAPPDATA",""))/"Minimalizer/research/resvg-py-0.5.0"
 sys.path.insert(0,str(rdir));import resvg_py
 records=[];panels=[]
 for part in PARTS:
  mask=masks[part]&masks["subject"]
  # isolate DOM parts at original positions, no global compositing inferred
  solo=ET.Element("{%s}svg"%NS,{"width":"340","height":"340","viewBox":"0 0 340 340"})
  nodes=[p for p in root if p.get("data-part")==part]
  for node in nodes:solo.append(ET.fromstring(ET.tostring(node)))
  svg=out/(part+"_isolated.svg");ET.ElementTree(solo).write(svg,encoding="utf-8",xml_declaration=True)
  png=out/(part+"_isolated.png");png.write_bytes(resvg_py.svg_to_bytes(svg_path=str(svg),width=340,height=340))
  visible=np.asarray(Image.open(png).convert("RGBA").getchannel("A"))>=128
  overlap=int((mask&visible).sum());miss=int((mask&~visible).sum());extra=int((visible&~mask).sum())
  r={"part":part,"source_mask_pixels":int(mask.sum()),"svg_paths":len(nodes),
     "isolated_svg_coverage_pixels":overlap,"isolated_svg_missing_pixels":miss,
     "isolated_svg_extra_pixels":extra,"coverage_ratio":round(overlap/max(1,int(mask.sum())),5)}
  records.append(r)
  tile=Image.new("RGB",(340,340),"#eee8e1")
  tile.paste(Image.open(png).convert("RGBA"),(0,0),Image.open(png).convert("RGBA"))
  panels.append((part,tile,r))
 canvas=Image.new("RGB",(1360,1110),"#f2f1ed")
 for i,(part,img,info) in enumerate(panels):
  x=(i%4)*340;y=(i//4)*370
  canvas.paste(img,(x,y))
  ImageDraw.Draw(canvas).text((x+6,y+345),f"{part}: {info['isolated_svg_coverage_pixels']}/{info['source_mask_pixels']}",fill="#222")
 gallery=out/"part_isolation_grid.png";canvas.save(gallery,optimize=True)
 # overlap audit on masks: face/hair already known disjoint, accessory may overlap
 overlaps=[]
 for i,a_part in enumerate(PARTS):
  for b_part in PARTS[i+1:]:
   count=int((masks[a_part]&masks[b_part]&masks["subject"]).sum())
   if count:overlaps.append({"a":a_part,"b":b_part,"pixels":count})
 report={"status":"RESEARCH_DIAGNOSTIC","parts":records,"source_mask_overlap":overlaps,
  "no_skin_plate":True,"face_unresolved":True,"no_production_changes":True,
  "files":[{"name":q.name,"sha256":sha256(q)} for q in sorted(out.iterdir()) if q.is_file()]}
 (out/"manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"parts":records,"top_mask_overlaps":sorted(overlaps,key=lambda x:-x["pixels"])[:10]}))
if __name__=="__main__":main()
