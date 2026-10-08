"""GC001 fringe v2: source-observed widths, hair shadow and highlight layers.

This is a *local correction only*: it does not fill the face and does not
claim complete-character Golden quality. All palette colors and changed mask
pixels are traceable to the canonical source photograph.
"""
from __future__ import annotations
import argparse,json,os,sys
from pathlib import Path
from xml.etree import ElementTree as ET
import cv2,numpy as np
from PIL import Image,ImageDraw
from semantic_art_mixer_v1 import load_assets,sha256
from semantic_art_mixer_v3_source_masks import load_observed_masks
from bangs_continuity_source_bridge import extract
from remove_subject_skin_underlay import contours_path,NS

def tonal_layers(source,missing):
    rgb=np.asarray(source.convert("RGB"),dtype=np.uint8)
    samples=rgb[missing]
    if samples.shape[0]<100:raise ValueError("Insufficient source fringe")
    # Warm hair pixels are sampled from this particular observed missing strand.
    # 3 LAB clusters; representative colors are literal source RGB medoids.
    lab=cv2.cvtColor(rgb,cv2.COLOR_RGB2LAB)
    vals=lab[missing].astype(np.float32)
    cv2.setRNGSeed(812)
    _,labels,centers=cv2.kmeans(vals,3,None,
        (cv2.TERM_CRITERIA_MAX_ITER+cv2.TERM_CRITERIA_EPS,40,0.1),1,
        cv2.KMEANS_PP_CENTERS)
    amounts=np.bincount(labels[:,0],minlength=3)
    primary=int(amounts.argmax())
    colors=[]
    for k,center in enumerate(centers):
        sample_index=int(np.argmin(np.sum((vals-center)**2,axis=1)))
        colors.append(tuple(map(int,samples[sample_index])))
    layers=[(missing,colors[primary],"observed-base")]
    classmap=np.full(missing.shape,-1,dtype=np.int8)
    classmap[missing]=labels[:,0]
    for k in range(3):
        if k==primary:continue
        ccount,components,stats,_=cv2.connectedComponentsWithStats((classmap==k).astype(np.uint8),8)
        accepted=np.zeros(missing.shape,dtype=bool)
        for i in range(1,ccount):
            if stats[i,cv2.CC_STAT_AREA]>=6:
                accepted|=components==i
        if accepted.any():layers.append((accepted,colors[k],"observed-tone"))
    return layers,amounts.tolist()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--prior",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    original,_,_=load_assets(args.root)
    masks,_=load_observed_masks()
    missing,observed=extract(original,masks)
    layers,amounts=tonal_layers(original,missing)
    paths=[]
    for region,color,kind in layers:
        d,count,vertices=contours_path(region)
        if not d:raise ValueError("Empty tone path")
        paths.append((d,color,kind,count,vertices,region))
    prior={"full":args.prior/"repaired_bangs.svg","foreground":args.prior/"repaired_foreground.svg"}
    targets=[]
    for kind,previous in prior.items():
        doc=ET.parse(previous)
        root=doc.getroot()
        # v1 appended one source-derived repair in the last SVG path.
        v1=[p for p in root.findall(".//{%s}path"%NS) if p.get("data-layer")=="original-fringe-source-repair"]
        if len(v1)!=1:raise ValueError("Expected exactly one prior fringe bridge")
        root.remove(v1[0])
        for d,color,layer,_,_,_ in paths:
            paint="#%02x%02x%02x"%color
            ET.SubElement(root,"{%s}path"%NS,{
                "d":d,"fill":paint,"fill-rule":"evenodd",
                "data-part":"hair","data-layer":layer,
                "data-provenance":"original-GC001-source-fringe-only"})
        if root.findall(".//{%s}path[@data-part='face']"%NS) or root.findall(".//{%s}path[@data-part='subject']"%NS):
            raise AssertionError("Forbidden face/subject underlay")
        target=out/("tonal_"+kind+".svg")
        doc.write(target,encoding="utf-8",xml_declaration=True)
        targets.append(target)
    folder=Path(os.environ.get("LOCALAPPDATA",""))/"Minimalizer/research/resvg-py-0.5.0"
    if not folder.exists():raise RuntimeError("Isolated renderer missing")
    sys.path.insert(0,str(folder));import resvg_py
    for svg in targets:
        (out/(svg.stem+".png")).write_bytes(
            resvg_py.svg_to_bytes(svg_path=str(svg),width=680,height=680))
    before=Image.open(args.prior/"repaired_bangs.png").convert("RGB").resize((340,340))
    after=Image.open(out/"tonal_full.png").convert("RGB").resize((340,340))
    page=Image.new("RGB",(1040,390),"#f1f1ef")
    for i,img in enumerate((original,before,after)):page.paste(img,(10+i*345,14))
    pen=ImageDraw.Draw(page)
    for i,label in enumerate(("SOURCE / BANGS","V1 / ONE TONE","V2 / SOURCE TONAL REGIONS")):
        pen.text((12+i*345,359),label,fill="#26352e")
    page.save(out/"comparison_bangs_v1_vs_v2.png",optimize=True)
    change=np.any(np.asarray(before)!=np.asarray(after),axis=2)
    # Antialiasing can touch +/-2 px outside measured original region.
    expanded=cv2.dilate(missing.astype(np.uint8),np.ones((5,5),np.uint8))>0
    if np.any(change&~expanded):raise AssertionError("Changed pixels outside original hair region")
    rowwidths={str(y):int(missing[y].sum()) for y in range(108,135,2)}
    meta={"status":"RESEARCH_ONLY","core_golden_pass":False,"source_missing_bang_pixels":int(missing.sum()),
          "observed_bangs_pixels":int(observed.sum()),"tone_source_cluster_counts":amounts,
          "source_row_widths":rowwidths,"palette":[list(col) for _,col,_,_,_,_ in paths],
          "svg_layers":len(paths),"svg_contours":sum(p[3] for p in paths),
          "svg_vertices":sum(p[4] for p in paths),
          "render_change_from_v1":int(change.sum()),"render_change_outside_source_region":0,
          "unresolved_face":True,
          "files":[{"name":f.name,"sha256":sha256(f)} for f in sorted(out.iterdir()) if f.suffix in (".png",".svg")]}
    (out/"manifest.json").write_text(json.dumps(meta,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({k:meta[k] for k in ("status","svg_layers","svg_contours","svg_vertices","render_change_from_v1","source_row_widths")},ensure_ascii=False))
if __name__=="__main__":main()
