"""Connectivity of observed source-pale goggle rim pixels. No gap filling."""
import argparse,json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from semantic_art_mixer_v1 import sha256
def audit(source,mask):
 rgb=np.asarray(source.convert("RGB"));binary=np.asarray(mask.convert("L"))>127
 n,labels,stats,centroids=cv2.connectedComponentsWithStats(binary.astype(np.uint8),8)
 components=sorted([{"pixels":int(stats[i,4]),"bbox_xywh":stats[i,:4].tolist(),
 "centroid_xy":[round(float(v),2) for v in centroids[i]]} for i in range(1,n)],key=lambda x:-x["pixels"])
 # Count source-pale components within 2 pixels of prior verified candidates,
 # without changing the candidate mask or connecting disconnected pieces.
 pale=(rgb.min(axis=2)>138)&((rgb.max(axis=2).astype(np.int16)-rgb.min(axis=2).astype(np.int16))<91)&(rgb.mean(axis=2)>178)
 near=cv2.dilate(binary.astype(np.uint8),np.ones((5,5),np.uint8))>0
 extension=pale&near&~binary
 n2,_,stats2,_=cv2.connectedComponentsWithStats(extension.astype(np.uint8),8)
 return components,extension,{"original_components":len(components),"largest_component_pixels":components[0]["pixels"] if components else 0,
 "original_pixels":int(binary.sum()),"neighbor_source_pale_pixels":int(extension.sum()),
 "neighbor_component_count":int(n2-1),"source_mask_unchanged":True}
def main():
 p=argparse.ArgumentParser()
 for name in ("source","mask","out"):p.add_argument("--"+name,type=Path,required=True)
 a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 source=Image.open(a.source).convert("RGB");mask=Image.open(a.mask).convert("L")
 if source.size!=(340,340) or mask.size!=source.size:raise ValueError("source/mask size mismatch")
 components,extension,metrics=audit(source,mask)
 src=np.asarray(source);panel=Image.new("RGB",(1020,390),"#eee")
 overlay=src.copy();b=np.asarray(mask)>127
 overlay[b]=(overlay[b]*.4+np.array([0,250,185])*.6).astype(np.uint8)
 overlay[extension]=(overlay[extension]*.5+np.array([255,50,185])*.5).astype(np.uint8)
 for i,img in enumerate((source,Image.fromarray(overlay),Image.fromarray((extension*255).astype(np.uint8)).convert("RGB"))):panel.paste(img,(i*340,0))
 d=ImageDraw.Draw(panel)
 for i,t in enumerate(("ORIGINAL","CYAN PREVIOUS / PINK NEIGHBOR","UNVERIFIED SOURCE-PALE NEIGHBORS")):d.text((340*i+4,355),t,fill="#222")
 panel.save(a.out/"rim_connectivity_source_audit.png")
 Image.fromarray((extension*255).astype(np.uint8)).save(a.out/"rim_neighbor_candidate.png")
 report={"status":"CONNECTED_SOURCE_COMPONENTS_AUDITED","metrics":metrics,
 "largest_components":components[:25],"candidate_extension_is_not_verified":True,
 "no_gap_filling":True,"filled_svg_authorized":False,"production_changed":False,
 "files":[{"name":q.name,"sha256":sha256(q)} for q in a.out.glob("*.png")]}
 (a.out/"manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"status":report["status"],"metrics":metrics,"largest_components":components[:4]}))
if __name__=="__main__":main()
