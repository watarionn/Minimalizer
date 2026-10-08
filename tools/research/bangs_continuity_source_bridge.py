"""Bangs Continuity: recover only observed orange pixels across erroneous face mask.

GC001-specific research, NOT general segmentation, NOT a complete/Core PASS.
"""
from pathlib import Path
import argparse,json,os,sys
from xml.etree import ElementTree as ET
import cv2,numpy as np
from PIL import Image,ImageDraw
from semantic_art_mixer_v1 import load_assets,sha256
from semantic_art_mixer_v3_source_masks import load_observed_masks
from remove_subject_skin_underlay import contours_path,NS

def extract(source,masks):
    rgb=np.asarray(source.convert("RGB"),dtype=np.uint8)
    hsv=cv2.cvtColor(rgb,cv2.COLOR_RGB2HSV)
    yy,xx=np.mgrid[:340,:340]
    roi=(xx>=144)&(xx<=185)&(yy>=100)&(yy<=140)
    colored=roi&(hsv[:,:,0]<=22)&(hsv[:,:,1]>=100)&(
        rgb[:,:,0].astype(float)>rgb[:,:,1].astype(float)*1.3)&(
        rgb[:,:,1].astype(float)>rgb[:,:,2].astype(float)*1.25)
    n,labels,stats,_=cv2.connectedComponentsWithStats(colored.astype(np.uint8),8)
    components=[i for i in range(1,n) if stats[i,cv2.CC_STAT_AREA]>=100]
    if len(components)!=1:raise ValueError("Bangs component is ambiguous; fail closed")
    result=(labels==components[0]) & masks["subject"]
    missing=result & masks["face"] & ~masks["hair"]
    if missing.sum()<100:raise ValueError("Expected missing source hair inside face mask")
    # Required observed bridge from hair head/top down toward between-eye tip.
    if not (np.any(result[105:111,153:176]) and np.any(missing[122:132,155:176])):
        raise ValueError("Observed top-to-tip continuity is absent")
    if np.any(result&~roi):raise AssertionError("Unexpected mask expansion")
    return missing,result

def main():
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,required=True);p.add_argument("--prior",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();out=a.out;out.mkdir(parents=True,exist_ok=True)
    source,_,_=load_assets(a.root)
    masks,_=load_observed_masks()
    missing,whole=extract(source,masks)
    data,contours,vertices=contours_path(missing)
    if not data:raise ValueError("Could not vectorize verified missing hair")
    # Strict provenance: copy prior SVG, append no generated color or face fill.
    old=a.prior/"character_part_vector.svg"
    old_fg=a.prior/"character_foreground_alpha.svg"
    if not old.is_file() or not old_fg.is_file():raise FileNotFoundError("Prior known source SVG missing")
    source_arr=np.asarray(source.convert("RGB"),dtype=np.uint8)
    palette=np.unique(source_arr[missing],axis=0)
    colors,counts=np.unique(source_arr[missing],axis=0,return_counts=True)
    med=colors[np.argmax(counts)]
    # Use only actual observed source orange value.
    paint="#%02x%02x%02x"%tuple(map(int,med))
    outputs=[]
    for prior,name in ((old,"repaired_bangs.svg"),(old_fg,"repaired_foreground.svg")):
        root=ET.parse(prior).getroot()
        ET.SubElement(root,"{%s}path"%NS,{"d":data,"fill":paint,"fill-rule":"evenodd",
                    "data-part":"hair","data-layer":"original-fringe-source-repair",
                    "data-source":"GC001-connected-original-orange"})
        target=out/name;ET.ElementTree(root).write(target,encoding="utf-8",xml_declaration=True)
        if root.findall(".//{%s}path[@data-part='subject']"%NS) or root.findall(".//{%s}path[@data-part='face']"%NS):
            raise AssertionError("Subject face plate reintroduced")
        outputs.append(target)
    folder=Path(os.environ.get("LOCALAPPDATA",""))/"Minimalizer/research/resvg-py-0.5.0"
    sys.path.insert(0,str(folder));import resvg_py
    for path in outputs:
        (out/(path.stem+".png")).write_bytes(resvg_py.svg_to_bytes(svg_path=str(path),width=680,height=680))
    old_png=Image.open(a.prior/"character_part_vector.png").convert("RGB").resize((340,340))
    fixed=Image.open(out/"repaired_bangs.png").convert("RGB").resize((340,340))
    page=Image.new("RGB",(1040,390),"#f1f1ef")
    for i,image in enumerate((source,old_png,fixed)):page.paste(image,(10+i*345,14))
    d=ImageDraw.Draw(page)
    for i,title in enumerate(("SOURCE","PRIOR: CUT BANG","SOURCE-OBSERVED BRIDGE")):
        d.text((13+i*345,359),title,fill="#22302a")
    page.save(out/"comparison_bangs_continuity.png",optimize=True)
    observed=np.asarray(fixed,dtype=np.uint8)
    oldarr=np.asarray(old_png,dtype=np.uint8)
    delta=np.any(observed!=oldarr,axis=2)
    if np.any(delta & ~(cv2.dilate(missing.astype(np.uint8),np.ones((5,5),np.uint8))>0)):
        raise AssertionError("Repair alters pixels far beyond verified original fringe")
    data={"status":"RESEARCH_ONLY","source_missing_bang_pixels":int(missing.sum()),
          "connected_observed_orange_pixels":int(whole.sum()),
          "repaired_vector_contours":contours,"repaired_vector_vertices":vertices,
          "paint_rgb_from_source":med.tolist(),"fixed_changed_pixels":int(delta.sum()),
          "unresolved_face":True,"not_core_pass":True,
          "outputs":[{"name":f.name,"sha256":sha256(f)} for f in out.glob("*") if f.is_file() and f.suffix in (".svg",".png")]}
    (out/"manifest.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(data,ensure_ascii=False))
if __name__=="__main__":main()
