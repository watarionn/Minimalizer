"""Research-only: omit feature-intersecting SVG strokes, never cover face with a skin polygon.

Produce a real transparent SVG from source-observed Canny strokes. Every path
intersecting an observed eye/nose/mouth component is dropped in its entirety.
No raster embedded, no face plane painted, hair mask is protected: strokes
inside source hair are source-observed and never suppressed. Brows are not
verified and no claim of their elimination is made.

The empty space where facial strokes were omitted is TRANSPARENT: compositing
the SVG over source image would show the ORIGINAL eyes. This is structural SVG
omission, not source-photo inpainting or a final Minimalizer rendering.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from semantic_art_mixer_v1 import SIZE, SOURCE_SHA, load_assets, sha256
from semantic_art_mixer_v3_source_masks import load_observed_masks
from face_parts_only_v1 import source_components

SVGNS="http://www.w3.org/2000/svg"
ET.register_namespace("",SVGNS)


def paths_for_observed_edges(src: Image.Image, masks: dict, feature: dict):
    gray=cv2.cvtColor(np.asarray(src.convert("RGB")),cv2.COLOR_RGB2GRAY)
    edge=cv2.Canny(cv2.GaussianBlur(gray,(3,3),0),60,130,L2gradient=True)
    contours,_=cv2.findContours(edge,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
    forbidden=np.logical_or.reduce(list(feature.values()))
    hair=masks["hair"]
    face=masks["face"]
    subject=masks["subject"]
    keep=[]
    excluded=0
    ignored=0
    total=0
    for line in contours:
        length=cv2.arcLength(line,False)
        if length<7:
            ignored+=1
            continue
        simp=cv2.approxPolyDP(line,max(.65,.0015*length),False).reshape(-1,2)
        if len(simp)<2:
            ignored+=1
            continue
        points=[(int(x),int(y)) for x,y in simp]
        samples=np.zeros((SIZE[1],SIZE[0]),dtype=np.uint8)
        cv2.polylines(samples,[simp.reshape((-1,1,2)).astype(np.int32)],False,255,thickness=1)
        occupied=samples>0
        total+=1
        # Do NOT suppress hair strokes because of a nearby face part.
        # Drop strokes meeting confirmed facial component masks and only
        # if the contour actually occupies the source face.
        if np.any(occupied & forbidden & face & ~hair):
            excluded+=1
            continue
        if not np.any(occupied & subject):
            ignored+=1
            continue
        keep.append(points)
    if not keep or excluded<=0:
        raise ValueError("Expected observed source paths and some feature exclusions")
    return keep,{"candidate_paths":total,"retained_paths":len(keep),
                 "excluded_face_feature_intersecting_paths":excluded,
                 "other_filtered_paths":ignored,
                 "feature_pixels":int(forbidden.sum()),
                 "hair_pixels_in_feature_masks":int((forbidden&hair).sum())}


def make_svg(paths,output:Path):
    root=ET.Element("{%s}svg"%SVGNS,{
        "viewBox":"0 0 340 340","width":"340","height":"340",
        "data-provenance":"GC001-source-observed-lines-only",
    })
    group=ET.SubElement(root,"{%s}g"%SVGNS,{
        "fill":"none","stroke":"#1b2627","stroke-width":"0.95",
        "stroke-linecap":"round","stroke-linejoin":"round",
    })
    for points in paths:
        d="M "+" L ".join(f"{x} {y}" for x,y in points)
        ET.SubElement(group,"{%s}path"%SVGNS,{"d":d})
    ET.ElementTree(root).write(output,encoding="utf-8",xml_declaration=True)
    ET.parse(output)
    xml=output.read_text(encoding="utf-8").lower()
    if "<image" in xml or "data:image" in xml or "<rect" in xml or "<circle" in xml:
        raise AssertionError("SVG unexpectedly has raster, facial cover or circles")


def render_svg_preview(svg: Path, png: Path):
    try:
        import cairosvg
        cairosvg.svg2png(url=str(svg),write_to=str(png),output_width=680,output_height=680)
    except ImportError:
        # Reuse already-isolated pure rendering adapter, never add a dependency
        # to the Minimalizer production Worker.
        import os,sys
        isolated=Path(os.environ.get("LOCALAPPDATA",""))/"Minimalizer/research/resvg-py-0.5.0"
        if not isolated.is_dir():
            raise RuntimeError("Neither CairoSVG nor isolated resvg preview is available")
        sys.path.insert(0,str(isolated))
        import resvg_py
        png.write_bytes(resvg_py.svg_to_bytes(svg_path=str(svg),width=680,height=680))
    im=Image.open(png).convert("RGBA")
    if im.size!=(680,680):
        raise AssertionError("Preview dimensions wrong")
    if im.getpixel((0,0))[3]!=0:
        raise AssertionError("SVG should have transparent background")


def gallery(source:Image.Image,svg_preview:Path,output:Path,metrics:dict):
    sheet=Image.new("RGB",(1020,454),"#EBEBE7")
    d=ImageDraw.Draw(sheet)
    original=source.convert("RGB").resize((340,340))
    lines=Image.open(svg_preview).convert("RGBA").resize((340,340),Image.Resampling.LANCZOS)
    # White backing is a *preview canvas*, not part of SVG geometry or a face fill.
    blank=Image.new("RGBA",SIZE,"white")
    flat=Image.alpha_composite(blank,lines).convert("RGB")
    for idx,(name,im) in enumerate((("ORIGINAL",original),("STRUCTURAL SVG ONLY",flat))):
        sheet.paste(im,(idx*340,56))
        d.text((idx*340+12,407),name,fill="#25302a")
    d.text((685,78),"FACE PARTS ONLY",fill="#25302a")
    d.text((685,111),"Transparent SVG.",fill="#25302a")
    d.text((685,145),"No face cover-up.",fill="#25302a")
    d.text((685,179),"No raster embedded.",fill="#25302a")
    d.text((685,219),f"{metrics['retained_paths']} kept paths",fill="#25302a")
    d.text((685,251),f"{metrics['excluded_face_feature_intersecting_paths']} excluded paths",fill="#25302a")
    d.text((685,303),"NOT a full-character render.",fill="#8B3434")
    d.text((685,335),"Eyebrows unverified.",fill="#8B3434")
    sheet.save(output,optimize=True)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    output=args.out.resolve()
    output.mkdir(parents=True,exist_ok=True)
    source,_,input_evidence=load_assets(args.root.resolve())
    masks,mask_evidence=load_observed_masks()
    feature,audit=source_components(source,masks)
    paths,metrics=paths_for_observed_edges(source,masks,feature)
    svg=output/"observed_strokes_excluding_face_parts.svg"
    png=output/"transparent_svg_preview.png"
    comparison=output/"comparison_original_vs_structural_svg.png"
    make_svg(paths,svg)
    render_svg_preview(svg,png)
    gallery(source,png,comparison,metrics)
    record={
        "stage":"FaceParts SVG structural omission, independent research",
        "source_sha256":SOURCE_SHA,
        "source_mask_evidence":mask_evidence,
        "source_art_evidence":input_evidence,
        "facial_parts":audit,
        "metrics":metrics,
        "false_eye_creation_prevention":"reject any observed vector line intersecting identified feature pixels",
        "hair_face_overlay_count":0,
        "facial_cover_shapes":0,
        "raster_images_embedded":0,
        "has_source_skin_under_omitted_paths":False,
        "eyebrows_observed":False,
        "core_golden_pass":False,
        "not_full_character_render":True,
        "not_production_integrated":True,
        "artifacts":[{"file":p.name,"sha256":sha256(p)} for p in (svg,png,comparison)]
    }
    (output/"manifest.json").write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PASS",**metrics,"svg_sha":sha256(svg),"comparison_sha":sha256(comparison)}))


if __name__=="__main__":
    main()
