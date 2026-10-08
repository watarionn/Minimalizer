"""Reduce source-cell SVG bang vertices with strict alpha-footprint gate.

No face plate, no invented hair. Epsilon is only accepted when the *rendered*
footprint reproduces >=687 of the exact 694 source pixels with zero excess.
"""
import argparse,json,os,sys
from pathlib import Path
from xml.etree import ElementTree as ET
import cv2,numpy as np
from PIL import Image,ImageDraw
from semantic_art_mixer_v1 import load_assets,sha256
from semantic_art_mixer_v3_source_masks import load_observed_masks
from bangs_continuity_source_bridge import extract
from bangs_source_tonal_width_v2 import tonal_layers
from remove_subject_skin_underlay import NS

EPS=(0.0,0.1,0.2,0.35,0.5,0.75,1.0)
def polygons(mask,epsilon):
    binary=cv2.resize(np.pad(mask.astype(np.uint8),1),None,fx=2,fy=2,interpolation=cv2.INTER_NEAREST)
    contours,_=cv2.findContours(binary,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    parts=[];vertices=0
    for c in contours:
        if len(c)<3 or cv2.contourArea(c)<2:continue
        p=cv2.approxPolyDP(c,epsilon*2,True) if epsilon else c
        p=(p.reshape(-1,2).astype(np.float64)-1.5)/2
        if len(p)<3:continue
        parts.append("M "+" L ".join(f"{x:g} {y:g}" for x,y in p)+" Z")
        vertices+=len(p)
    return " ".join(parts),len(parts),vertices

def write_svg(layers,epsilon,path):
    root=ET.Element("{%s}svg"%NS,{"viewBox":"0 0 340 340","width":"340","height":"340"})
    verts=contours=0
    for mask,color,kind in layers:
        d,n,v=polygons(mask,epsilon)
        if not d:continue
        ET.SubElement(root,"{%s}path"%NS,{"d":d,"fill":"#%02x%02x%02x"%color,
            "fill-rule":"evenodd","data-part":"hair","data-layer":kind})
        verts+=v;contours+=n
    ET.ElementTree(root).write(path,encoding="utf-8",xml_declaration=True)
    return verts,contours

def main():
    ap=argparse.ArgumentParser()
    for n in ("root","out"):ap.add_argument("--"+n,type=Path,required=True)
    a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    src,_,_=load_assets(a.root);masks,_=load_observed_masks()
    _,source=extract(src,masks)
    layers,_=tonal_layers(src,source)
    folder=Path(os.environ.get("LOCALAPPDATA",""))/"Minimalizer/research/resvg-py-0.5.0"
    sys.path.insert(0,str(folder));import resvg_py
    rows=[]
    for epsilon in EPS:
        name="eps_"+str(epsilon).replace(".","p")
        svg=out/(name+".svg");vertices,contours=write_svg(layers,epsilon,svg)
        png=out/(name+".png")
        png.write_bytes(resvg_py.svg_to_bytes(svg_path=str(svg),width=340,height=340))
        alpha=np.asarray(Image.open(png).convert("RGBA").getchannel("A"))>=128
        covered=int((alpha&source).sum());extra=int((alpha&~source).sum())
        rows.append({"epsilon":epsilon,"covered":covered,"missing":int(source.sum())-covered,
          "outside":extra,"vertices":vertices,"contours":contours,
          "svg":svg.name,"svg_sha":sha256(svg),"png":png.name,"png_sha":sha256(png)})
    # Strict gate: never trade the already achieved 687px footprint for vertices.
    approved=[r for r in rows if r["covered"]>=687 and r["outside"]==0]
    selected=min(approved,key=lambda r:(r["vertices"],-r["covered"])) if approved else None
    byvertex=sorted(rows,key=lambda r:(r["vertices"],-r["covered"]))
    board=Image.new("RGB",(1380,430),"#eeeeeb");d=ImageDraw.Draw(board)
    board.paste(src.convert("RGB"),(12,14));d.text((12,371),"ORIGINAL / GC001",fill="#203126")
    samples=[rows[0],selected if selected else rows[0],byvertex[0]]
    for i,r in enumerate(samples):
        rgba=Image.open(out/r["png"]).convert("RGBA")
        canvas=Image.new("RGBA",(340,340),"white");canvas.alpha_composite(rgba)
        board.paste(canvas.convert("RGB"),(355+i*340,14))
        d.text((355+i*340,372),f"eps={r['epsilon']} {r['covered']}/694 {r['vertices']}v +{r['outside']}",fill="#203126")
    gallery=out/"compare_vertex_budget.png";board.save(gallery,optimize=True)
    manifest={"stage":"Bangs Cell Vertex Reduction","source_pixels":int(source.sum()),
      "baseline_covered":687,"baseline_vertices":485,"baseline_outside":0,
      "candidates":rows,"chosen":selected,"full_character_golden_pass":False,
      "artifacts":[{"name":p.name,"sha256":sha256(p)} for p in sorted(out.iterdir()) if p.is_file()]}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"candidates":[{k:v for k,v in x.items() if k in ("epsilon","covered","missing","outside","vertices","contours")} for x in rows],"chosen":{k:selected[k] for k in ("epsilon","covered","outside","vertices")} if selected else None}))
if __name__=="__main__":main()
