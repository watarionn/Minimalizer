"""GC001 one-piece visor: independently source-reviewed contour annotation and SVG PoC.

Research only. Official high-res Kyoko art confirms one curved wraparound lens
and external light frame, rather than two discrete lens objects. The manually
reviewed source 340px contours below are conservative visible-region hypotheses,
NOT pixel-perfect ground truth or permission to extrapolate hidden material.
"""
from __future__ import annotations
import argparse,json,os,sys
from pathlib import Path
from xml.etree import ElementTree as ET
import cv2,numpy as np
from PIL import Image,ImageDraw
from semantic_art_mixer_v1 import load_assets,sha256
from remove_subject_skin_underlay import NS,region_colormasks
from bangs_cell_vertex_reduction import polygons

# Hand traced over the native 340x340 original and its pixel-zoom overlay.
# One continuous wraparound visor, not left/right lens instances.
OUTER=((105,76),(107,69),(112,62),(118,56),(126,50),(135,45),
       (143,42),(151,39),(159,37),(168,35),(175,34),(182,34),
       (190,36),(194,40),(197,47),(197,55),(194,61),(190,63),
       (184,65),(178,66),(172,68),(165,67),(157,63),(151,60),
       (146,59),(143,63),(140,69),(135,76),(127,85),(119,90),
       (113,91),(108,88),(105,83))
INNER=((109,74),(113,66),(118,60),(127,54),(136,48),(149,43),
       (160,40),(170,38),(181,38),(188,40),(192,45),(193,51),
       (191,56),(185,58),(173,61),(165,60),(154,57),(148,55),
       (143,55),(139,58),(137,64),(132,73),(125,81),(117,86),
       (113,85),(110,81),(108,77))
REFERENCE_HIGHRES_SHA="7300bf4f9b2baf4dd5452448bb9ec460004e82763a22a2eeecba4057d7b1c1a5"

def visible_masks():
    outer=np.zeros((340,340),dtype=np.uint8)
    inner=np.zeros_like(outer)
    cv2.fillPoly(outer,[np.asarray(OUTER,np.int32)],1)
    cv2.fillPoly(inner,[np.asarray(INNER,np.int32)],1)
    out=outer.astype(bool);lens=inner.astype(bool)
    if np.any(lens&~out):raise ValueError("Lens extends outside observed visor outline")
    frame=out&~lens
    if np.any(out[100:]):raise AssertionError("Source goggle annotation crossed independently verified inter-eye fringe")
    return out,lens,frame

def build_paths(source,lens,frame):
    layers=[];budget={}
    for role,area,k in (("visor_lens",lens,6),("visor_frame",frame,4)):
        # Exact source-sampled palette, no invented color.
        for region,rgb,kind in region_colormasks(source,area,k):
            d,n,v=polygons(region,0.35)
            if not d:continue
            layers.append((role,kind,d,rgb,n,v))
            budget.setdefault(role,{"paths":0,"vertices":0,"contours":0})
            budget[role]["paths"]+=1
            budget[role]["vertices"]+=v
            budget[role]["contours"]+=n
    if not any(x[0]=="visor_lens" for x in layers) or not any(x[0]=="visor_frame" for x in layers):
        raise AssertionError("A semantic visible visor part was lost")
    rgb_orig=np.asarray(source.convert("RGB"))
    for role,kind,d,color,n,v in layers:
        eligible=lens if role=="visor_lens" else frame
        if tuple(color) not in {tuple(p) for p in rgb_orig[eligible]}:
            raise AssertionError("Color not sampled from this source-visible semantic role")
    return layers,budget

def append_paths(root,layers):
    for role,kind,d,rgb,n,v in layers:
        ET.SubElement(root,"{%s}path"%NS,{"d":d,
          "fill":"#%02x%02x%02x"%rgb,"fill-rule":"evenodd",
          "data-part":role,"data-layer":"source-annotated-"+kind,
          "data-provenance":"GC001-manually-reviewed-visible-outline"})
    if (root.findall(".//{%s}path[@data-part='subject']"%NS)
       or root.findall(".//{%s}path[@data-part='face']"%NS)
       or root.findall(".//{%s}image"%NS)):
        raise AssertionError("No subject/face plate or raster embedding allowed")

def main():
    ap=argparse.ArgumentParser()
    for x in ("root","prior","out"):ap.add_argument("--"+x,type=Path,required=True)
    a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    source,_,_=load_assets(a.root)
    observed,lens,frame=visible_masks()
    layers,budget=build_paths(source,lens,frame)
    for name,mask in (("visor_observed_outer",observed),("visor_lens_review",lens),("visor_frame_review",frame)):
        Image.fromarray(mask.astype(np.uint8)*255).save(out/(name+".png"))
    # Isolated SOURCE-DERIVED VECTORS, with no raster content in SVG.
    standalone=ET.Element("{%s}svg"%NS,{"viewBox":"0 0 340 340","width":"340","height":"340"})
    append_paths(standalone,layers)
    isolated=out/"source_visored_onepiece.svg"
    ET.ElementTree(standalone).write(isolated,encoding="utf-8",xml_declaration=True)
    prior=a.prior/"source_tonal_clothing_scene.svg"
    document=ET.parse(prior)
    before_root=document.getroot()
    certified=[p for p in before_root if p.get("data-layer")=="source-bang-cell-verified"]
    if len(certified)!=3:raise ValueError("Verified inter-eye hair paths not present")
    # Goggles are source-visible atop front hair in this reference.
    append_paths(before_root,layers)
    full=out/"research_part_scene_with_visor.svg"
    document.write(full,encoding="utf-8",xml_declaration=True)
    paths=[p for p in before_root if p.get("data-layer")=="source-bang-cell-verified"]
    if len(paths)!=3:raise AssertionError("Certified bangs changed")
    for old,new in zip(certified,paths):
        if ET.tostring(old)!=ET.tostring(new):raise AssertionError("Certified bangs were modified")
    folder=Path(os.environ.get("LOCALAPPDATA",""))/"Minimalizer/research/resvg-py-0.5.0"
    if not folder.is_dir():raise RuntimeError("Isolated native SVG renderer unavailable")
    sys.path.insert(0,str(folder));import resvg_py
    def render(path,target):
        target.write_bytes(resvg_py.svg_to_bytes(svg_path=str(path),width=340,height=340))
        return np.asarray(Image.open(target).convert("RGBA"))
    solo=render(isolated,out/"source_visored_onepiece.png")
    actual_alpha=solo[:,:,3]>=128
    overlap=int(np.count_nonzero(actual_alpha&observed))
    excess=int(np.count_nonzero(actual_alpha&~observed))
    base=render(prior,out/"scene_before_visor.png")
    newer=render(full,out/"scene_after_visor.png")
    delta=np.any(base[:,:,:3]!=newer[:,:,:3],axis=2)
    safe=cv2.dilate(observed.astype(np.uint8),np.ones((5,5),np.uint8))>0
    out_of_roi=int(np.count_nonzero(delta&~safe))
    if out_of_roi:raise AssertionError(f"Scene changed outside reviewed goggle area: {out_of_roi}")
    if overlap<int(observed.sum())*.93:
        raise AssertionError("Vector paths lost too much visibly annotated goggle geometry")
    # Source, role overlay and full SVG comparison, all at native source pixels.
    rgb=np.asarray(source.convert("RGB"))
    colors=rgb.copy()
    colors[lens]=(0.6*colors[lens]+0.4*np.array((24,198,216))).astype(np.uint8)
    colors[frame]=(0.6*colors[frame]+0.4*np.array((218,62,172))).astype(np.uint8)
    board=Image.new("RGB",(1380,420),"#f1f0ed")
    for i,im in enumerate((source.convert("RGB"),Image.fromarray(colors),
             Image.fromarray(base[:,:,:3]),Image.fromarray(newer[:,:,:3]))):
        board.paste(im.convert("RGB"),(10+i*342,10))
    draw=ImageDraw.Draw(board)
    for i,label in enumerate(("ORIGINAL SOURCE","SOURCE-TRACED PARTS","PREVIOUS / FACE HOLE","VISOR / RESEARCH ONLY")):
        draw.text((10+i*342,364),label,fill="#23332b")
    comp=out/"compare_onepiece_visor_scene.png";board.save(comp,optimize=True)
    report={"stage":"GC001 ONE-PIECE VISOR SOURCE REVIEW","status":"RESEARCH_LOCAL_GEOMETRY_PASS_FULL_GOLDEN_HOLD",
        "visor_topology":"single_wraparound_lens_and_outer_frame",
        "old_two_independent_lenses_assumption_rejected":True,
        "topology_evidence_highres_SHA256":REFERENCE_HIGHRES_SHA,
        "geometry_provenance":"manual_visible_contour_native_340_source",
        "boundary_pixel_perfect_verified":False,
        "hidden_region_filled":False,"face_unresolved":True,
        "source_outer_pixels":int(observed.sum()),"reviewed_lens_pixels":int(lens.sum()),
        "reviewed_frame_pixels":int(frame.sum()),"standalone_rendered_source_pixels":overlap,
        "standalone_rendered_excess_pixels":excess,
        "part_render_coverage":round(overlap/int(observed.sum()),5),
        "source_derived_tonal_path_budget":budget,
        "source_certified_bangs_unchanged":True,
        "full_scene_changed_pixels":int(delta.sum()),"changed_outside_2px_visor_neighborhood":out_of_roi,
        "local_public_unmodified":True,"full_character_golden_pass":False,
        "artifacts":[{"name":p.name,"sha256":sha256(p)} for p in sorted(out.iterdir()) if p.suffix in (".png",".svg")]}
    (out/"manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("status","source_outer_pixels","reviewed_lens_pixels","reviewed_frame_pixels","standalone_rendered_source_pixels","standalone_rendered_excess_pixels","source_derived_tonal_path_budget","full_scene_changed_pixels","changed_outside_2px_visor_neighborhood")}))
if __name__=="__main__":main()
