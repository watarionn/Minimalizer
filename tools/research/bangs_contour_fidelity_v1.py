"""Contour fidelity audit: test source-geometry trace tolerances, don't invent pixels."""
import argparse,json,os,sys
from pathlib import Path
from xml.etree import ElementTree as ET
import cv2,numpy as np
from PIL import Image,ImageDraw
from semantic_art_mixer_v1 import load_assets,sha256
from semantic_art_mixer_v3_source_masks import load_observed_masks
from bangs_continuity_source_bridge import extract
from bangs_source_tonal_width_v2 import tonal_layers
from bangs_full_strand_continuity_v3 import verify_continuity
from remove_subject_skin_underlay import NS

EPS=(0.6,0.3,0.0)
def trace(mask,epsilon):
    binary=mask.astype(np.uint8)*255
    contours,_=cv2.findContours(binary,cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)
    chunks=[];vertices=0
    for contour in contours:
        if len(contour)<3 or cv2.contourArea(contour)<3: continue
        simplified=cv2.approxPolyDP(contour,epsilon,True).reshape(-1,2) if epsilon else contour.reshape(-1,2)
        if len(simplified)<3:continue
        chunks.append("M "+" L ".join(f"{int(x)} {int(y)}" for x,y in simplified)+" Z")
        vertices+=len(simplified)
    return " ".join(chunks),len(chunks),vertices

def build_svg(layers,eps,path):
    root=ET.Element("{%s}svg"%NS,{"width":"340","height":"340","viewBox":"0 0 340 340"})
    count=verts=0
    for mask,color,kind in layers:
        pathdata,n,v=trace(mask,eps)
        if not pathdata:
            if kind=="observed-base":raise ValueError("No source base")
            continue
        ET.SubElement(root,"{%s}path"%NS,{"d":pathdata,"fill":"#%02x%02x%02x"%color,
            "fill-rule":"evenodd","data-part":"hair","data-layer":kind})
        count+=n;verts+=v
    ET.ElementTree(root).write(path,encoding="utf-8",xml_declaration=True)
    return count,verts

def main():
    p=argparse.ArgumentParser()
    for n in ("root","prior","out"):p.add_argument("--"+n,type=Path,required=True)
    a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    src,_,_=load_assets(a.root)
    masks,_=load_observed_masks()
    _,whole=extract(src,masks)
    layers,_=tonal_layers(src,whole)
    folder=Path(os.environ.get("LOCALAPPDATA",""))/"Minimalizer/research/resvg-py-0.5.0"
    if not folder.is_dir():raise RuntimeError("Isolated resvg renderer unavailable")
    sys.path.insert(0,str(folder));import resvg_py
    versions=[]
    for eps in EPS:
        label=str(eps).replace(".","p")
        svg=out/f"source_only_e{label}.svg"
        n,verts=build_svg(layers,eps,svg)
        png=out/f"source_only_e{label}.png"
        png.write_bytes(resvg_py.svg_to_bytes(svg_path=str(svg),width=680,height=680))
        alpha=np.asarray(Image.open(png).convert("RGBA").resize((340,340)).getchannel("A"))>=128
        covered=int(np.sum(alpha&whole));outside=int(np.sum(alpha&~whole))
        versions.append({"epsilon":eps,"contours":n,"vertices":verts,"covered":covered,
                         "missing":int(whole.sum())-covered,"outside":outside,
                         "coverage":round(covered/int(whole.sum()),5),
                         "rows":verify_continuity(whole,alpha),"svg":svg.name,
                         "svg_sha":sha256(svg),"png":png.name,"png_sha":sha256(png)})
    # Compare to measured previous canonical v3, never silently loosen the
    # no-expansion rule. Choose best zero-excess candidate by source coverage.
    candidates=[z for z in versions if z["outside"]==0]
    selected=max(candidates,key=lambda z:(z["covered"],-z["vertices"])) if candidates else None
    before=Image.open(a.prior/"whole_full.png").convert("RGB").resize((340,340))
    gallery=Image.new("RGB",(1380,425),"#f1f1ee");draw=ImageDraw.Draw(gallery)
    gallery.paste(src.convert("RGB"),(12,14))
    gallery.paste(before,(355,14))
    titles=["REFERENCE","V3 / PRIOR"]
    for i,z in enumerate(versions[:2]):
        alpha=Image.open(out/z["png"]).convert("RGBA").resize((340,340))
        tile=Image.new("RGBA",(340,340),"white");tile.alpha_composite(alpha)
        gallery.paste(tile.convert("RGB"),(698+i*343,14))
        titles.append("eps "+str(z["epsilon"])+" coverage "+str(z["coverage"]))
    for i,label in enumerate(titles):
        draw.text((15+i*343,368),label,fill="#213029")
    gallerypath=out/"comparison_contour_epsilon.png";gallery.save(gallerypath,optimize=True)
    report={"status":"RESEARCH_HOLD","source_pixels":int(whole.sum()),
            "prior_v3_covered":601,"prior_v3_excess":0,
            "variants":versions,"best_zero_excess":selected["epsilon"] if selected else None,
            "face_unresolved":True,"local_public_unchanged":True,
            "artifacts":[{"name":p.name,"sha256":sha256(p)} for p in sorted(out.iterdir()) if p.is_file() and p.suffix in (".svg",".png")]}
    (out/"manifest.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"variants":[{k:v for k,v in z.items() if k in ("epsilon","contours","vertices","covered","missing","outside","coverage")} for z in versions],"best_zero_excess":report["best_zero_excess"]}))
if __name__=="__main__":main()
