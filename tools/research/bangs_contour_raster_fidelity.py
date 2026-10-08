"""Contour Raster Fidelity: isolate pixel centers, raster resolution, alpha resize.

Source-observed 694-pixel GC001 fringe only. No invented hair, face plane or
production changes. Compare SVG source path epsilon 0.6 with geometry
offset (0 vs +0.5), direct 340 and 680->340 resampling policies.
"""
import argparse,json,os,sys
from pathlib import Path
from xml.etree import ElementTree as ET
import numpy as np,cv2
from PIL import Image,ImageDraw
from semantic_art_mixer_v1 import load_assets,sha256
from semantic_art_mixer_v3_source_masks import load_observed_masks
from bangs_continuity_source_bridge import extract
from bangs_source_tonal_width_v2 import tonal_layers
from bangs_contour_fidelity_v1 import trace
from remove_subject_skin_underlay import NS

def make_svg(layers,path,offset):
    root=ET.Element("{%s}svg"%NS,{"viewBox":"0 0 340 340","width":"340","height":"340"})
    group=ET.SubElement(root,"{%s}g"%NS,{"transform":f"translate({offset} {offset})"})
    verts=0
    for area,color,kind in layers:
        d,n,v=trace(area,0.6)
        if not d:continue
        ET.SubElement(group,"{%s}path"%NS,{"d":d,"fill":"#%02x%02x%02x"%color,
                        "fill-rule":"evenodd","data-part":"hair"})
        verts+=v
    ET.ElementTree(root).write(path,encoding="utf-8",xml_declaration=True)
    return verts

def alpha_mask(rgba,size,method):
    img=Image.open(rgba).convert("RGBA")
    if img.size!=size:img=img.resize(size,resample=method)
    return np.asarray(img.getchannel("A"))>=128

def main():
    ap=argparse.ArgumentParser()
    for key in ("root","out"):ap.add_argument("--"+key,type=Path,required=True)
    a=ap.parse_args()
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    src,_,_=load_assets(a.root)
    masks,_=load_observed_masks()
    _,whole=extract(src,masks)
    layers,_=tonal_layers(src,whole)
    resvgroot=Path(os.environ.get("LOCALAPPDATA",""))/"Minimalizer/research/resvg-py-0.5.0"
    if not resvgroot.exists():raise RuntimeError("Isolated resvg not available")
    sys.path.insert(0,str(resvgroot));import resvg_py
    records=[]
    configurations=[(0,340,"direct"),(0,680,"nearest"),(0,680,"bilinear"),(0,680,"bicubic"),(0,680,"lanczos"),(0.5,340,"direct"),(0.5,680,"nearest"),(0.5,680,"lanczos")]
    methods={"nearest":Image.Resampling.NEAREST,"bilinear":Image.Resampling.BILINEAR,"bicubic":Image.Resampling.BICUBIC,"lanczos":Image.Resampling.LANCZOS}
    for offset,dim,sampling in configurations:
        tag=f"offset{str(offset).replace('.','p')}_{dim}_{sampling}"
        svg=out/(tag+".svg")
        vertices=make_svg(layers,svg,offset)
        png=out/(tag+".png")
        png.write_bytes(resvg_py.svg_to_bytes(svg_path=str(svg),width=dim,height=dim))
        observed=alpha_mask(png,(340,340),methods.get(sampling,Image.Resampling.NEAREST))
        overlap=int((observed&whole).sum())
        outside=int((observed&~whole).sum())
        records.append({"tag":tag,"offset":offset,"raster_dimension":dim,"sampling":sampling,
            "covered":overlap,"source_pixels":int(whole.sum()),"missing":int(whole.sum())-overlap,
            "outside":outside,"vertices":vertices,"svg_sha":sha256(svg),"png_sha":sha256(png)})
    safe=[x for x in records if x["outside"]==0]
    best=max(safe,key=lambda x:(x["covered"],-x["vertices"])) if safe else None
    board=Image.new("RGB",(1380,426),"#eeeeeb");pen=ImageDraw.Draw(board)
    board.paste(src.convert("RGB"),(10,15))
    for k,rec in enumerate(sorted(records,key=lambda x:(-x["covered"],x["outside"]))[:3]):
        img=Image.open(out/(rec["tag"]+".png")).convert("RGBA")
        if img.size!=(340,340):img=img.resize((340,340),methods.get(rec["sampling"],Image.Resampling.NEAREST))
        tile=Image.new("RGBA",(340,340),"white");tile.alpha_composite(img)
        board.paste(tile.convert("RGB"),(355+k*340,15))
        pen.text((355+k*340,367),f"{rec['tag']} {rec['covered']}/694 ex{rec['outside']}",fill="#27372c")
    pen.text((12,369),"ORIGINAL",fill="#27372c")
    gallery=out/"raster_fidelity_comparison.png";board.save(gallery,optimize=True)
    manifest={"stage":"Contour Raster Fidelity v1","source_pixels":int(whole.sum()),
       "previous_covered":601,"previous_outside":0,"records":records,
       "best_safe":best["tag"] if best else None,"golden_pass":False,
       "no_new_hair_geometry":True,"artifacts":[{"name":f.name,"sha256":sha256(f)} for f in sorted(out.iterdir()) if f.is_file()]}
    (out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"results":[{k:v for k,v in r.items() if k in ("tag","covered","missing","outside")} for r in records],"best_safe":manifest["best_safe"]}))
if __name__=="__main__":main()
