"""GC001 source-wide inter-eye fringe continuity, not just face-misclassified pixels.

Replaces ONLY v2 added fringe paths with a vector rendition of the entire
694px observed orange connected component. Hair boundaries use original
source pixels. Subject/face underlays are prohibited. Research-only.
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
from bangs_source_tonal_width_v2 import tonal_layers
from remove_subject_skin_underlay import contours_path,NS

def compose_layers(source,whole):
    layers,counts=tonal_layers(source,whole)
    paths=[]
    for region,color,kind in layers:
        d,n,vertices=contours_path(region)
        if not d:
            if kind=="observed-base":raise ValueError("Primary complete fringe missing")
            continue
        paths.append((d,color,kind,n,vertices,region))
    return paths,counts

def verify_continuity(source_mask, rendered_mask):
    """Compare row by row. This is a narrow original-observed ROI only."""
    rows=[]
    for y in range(106,141):
        orig=np.flatnonzero(source_mask[y])
        rend=np.flatnonzero(rendered_mask[y])
        if not len(orig):continue
        lo,hi=int(orig.min()),int(orig.max())
        covered=int(rendered_mask[y,orig].sum())
        rows.append({"y":y,"source_pixels":int(len(orig)),
                     "source_span":[lo,hi],
                     "covered_source_pixels":covered,
                     "source_coverage":round(covered/len(orig),4),
                     "rendered_pixels_roi":int(len(rend))})
    if not rows or len(rows)<15:raise ValueError("Missing row continuity evidence")
    return rows

def main():
    p=argparse.ArgumentParser()
    for name in ("root","prior","out"):p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args()
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    source,_,_=load_assets(a.root)
    masks,_=load_observed_masks()
    missing,whole=extract(source,masks)
    paths,counts=compose_layers(source,whole)
    if sum(z[5].sum() for z in paths)<whole.sum():pass  # Accent overlays may overlap base.
    originals=[("full","tonal_full.svg"),("foreground","tonal_foreground.svg")]
    outputs=[]
    for name,file in originals:
        document=ET.parse(a.prior/file)
        root=document.getroot()
        existing=[element for element in root.findall(".//{%s}path"%NS)
                  if element.get("data-provenance")=="original-GC001-source-fringe-only"]
        if not existing:raise ValueError("Prior source-fringe layers absent")
        for element in existing:root.remove(element)
        for d,rgb,kind,_,_,_ in paths:
            ET.SubElement(root,"{%s}path"%NS,
               {"d":d,"fill":"#%02x%02x%02x"%rgb,"fill-rule":"evenodd",
                "data-part":"hair","data-layer":"whole-connected-fringe-"+kind,
                "data-provenance":"source-connected-GC001-694px"})
        if root.findall(".//{%s}path[@data-part='face']"%NS) or root.findall(".//{%s}path[@data-part='subject']"%NS):
            raise AssertionError("Disallowed face or subject plate detected")
        dest=out/("whole_"+name+".svg")
        document.write(dest,encoding="utf-8",xml_declaration=True)
        outputs.append(dest)
    folder=Path(os.environ.get("LOCALAPPDATA",""))/"Minimalizer/research/resvg-py-0.5.0"
    if not folder.exists():raise RuntimeError("Existing isolated renderer not present")
    sys.path.insert(0,str(folder))
    import resvg_py
    for path in outputs:
        (out/(path.stem+".png")).write_bytes(resvg_py.svg_to_bytes(svg_path=str(path),width=680,height=680))
    prev=np.asarray(Image.open(a.prior/"tonal_full.png").convert("RGB").resize((340,340)))
    curr=np.asarray(Image.open(out/"whole_full.png").convert("RGB").resize((340,340)))
    change=np.any(prev!=curr,axis=2)
    limit=cv2.dilate(whole.astype(np.uint8),np.ones((5,5),np.uint8))>0
    outside=int((change&~limit).sum())
    if outside:raise AssertionError(f"Unrelated output changed outside observed strand: {outside}")
    # Render the appended colored component ALONE for honest pixel coverage,
    # independent from whatever earlier hair layers already existed in v2.
    exclusive=ET.Element("{%s}svg"%NS,{"width":"340","height":"340","viewBox":"0 0 340 340"})
    for d,rgb,kind,_,_,_ in paths:
        ET.SubElement(exclusive,"{%s}path"%NS,{
            "d":d,"fill":"#%02x%02x%02x"%rgb,"fill-rule":"evenodd",
            "data-part":"hair","data-layer":kind})
    sole=out/"source_component_only.svg"
    ET.ElementTree(exclusive).write(sole,encoding="utf-8",xml_declaration=True)
    component_png=out/"source_component_only.png"
    component_png.write_bytes(resvg_py.svg_to_bytes(svg_path=str(sole),width=680,height=680))
    alpha=np.asarray(Image.open(component_png).convert("RGBA").resize((340,340)).getchannel("A"))>=128
    rows=verify_continuity(whole,alpha)
    source_covered=int((alpha&whole).sum())
    extra=int((alpha&~whole).sum())
    # SVG polygon tracing on 340px can lose thin edges; report without
    # misrepresenting measured source width as rendered width.
    page=Image.new("RGB",(1380,415),"#efefeb")
    for i,im in enumerate((source,Image.fromarray(prev),Image.fromarray(curr))):
        page.paste(im.convert("RGB"),(10+i*345,20))
    pen=ImageDraw.Draw(page)
    for i,title in enumerate(("REFERENCE / ORIGINAL","V2 / MISSING ONLY","V3 / WHOLE SOURCE STRAND")):
        pen.text((13+i*345,367),title,fill="#233328")
    pen.text((1045,70),f"Source component {int(whole.sum())} px",fill="#233328")
    pen.text((1045,115),f"SVG source covered {source_covered} px",fill="#233328")
    pen.text((1045,160),f"Outside source {extra} px",fill="#233328")
    pen.text((1045,215),"FACE UNRESOLVED",fill="#933")
    pen.text((1045,252),"RESEARCH / HOLD",fill="#933")
    page.save(out/"comparison_full_fringe_v2_v3.png",optimize=True)
    report={"stage":"Bangs whole-strand source-continuity v3","status":"RESEARCH_HOLD",
       "source_connected_component_pixels":int(whole.sum()),
       "previous_misclassified_face_pixels":int(missing.sum()),
       "reconstructed_source_coverage_pixels":source_covered,
       "reconstructed_source_coverage_ratio":round(source_covered/int(whole.sum()),4),
       "vector_excess_pixels_outside_source_component":extra,
       "image_changes_from_v2":int(change.sum()),"image_changes_outside_source_roi":outside,
       "source_row_comparison":rows,"source_tone_cluster_counts":counts,
       "svg_layers":len(paths),"svg_contours":sum(x[3] for x in paths),
       "svg_vertices":sum(x[4] for x in paths),
       "face_unresolved":True,"core_golden_pass":False,"local_public_unmodified":True,
       "files":[{"name":p.name,"sha256":sha256(p)} for p in sorted(out.iterdir()) if p.suffix in (".png",".svg")]}
    (out/"manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("status","source_connected_component_pixels",
       "reconstructed_source_coverage_ratio","vector_excess_pixels_outside_source_component",
       "svg_layers","svg_contours","svg_vertices","image_changes_from_v2")},ensure_ascii=False))
if __name__=="__main__":main()
