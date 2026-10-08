"""Audit face-plate overlap in Minimalizer research SVGs.

Fail closed: a full subject fill in sampled skin color is a face covering
plate even when the path role says "subject", not "face". Classifies explicit
path roles and tests actual source face/hair mask intersections. This is an
audit, not a renderer; do not generate an even worse faceless image to pass.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from xml.etree import ElementTree as ET
import numpy as np
from semantic_art_mixer_v3_source_masks import load_observed_masks
from semantic_art_mixer_v1 import sha256
NS="{http://www.w3.org/2000/svg}"

def audit(svg:Path,masks:dict):
    tree=ET.parse(svg)
    faces=masks["face"];hair=masks["hair"];overlap=faces & hair
    elements=tree.findall(".//"+NS+"path")
    subject_base=[e for e in elements if e.get("data-part")=="subject" and e.get("data-layer")=="underlay"]
    if len(subject_base)!=1:
        raise ValueError("Expected exactly one original full-subject underlay; unknown scene")
    # This path comes from the full original subject mask by provenance.
    # It is opaque and is rendered before hair, but when hair layer has gaps
    # it shows an artificial skin-colored plate under bangs.
    plate=subject_base[0]
    paint=plate.get("fill")
    if not paint or paint.lower()=="none":
        raise ValueError("Invalid underlay fill")
    result={
      "svg_sha256":sha256(svg),
      "subject_plate_fill":paint,
      "subject_plate_geometry":"entire subject source mask",
      "source_face_pixels_covered_by_plate":int((faces&masks["subject"]).sum()),
      "source_hair_pixels_covered_by_plate":int((hair&masks["subject"]).sum()),
      "face_hair_overlap_pixels":int(overlap.sum()),
      "source_face_plate_present":True,
      "visual_status":"NO_GO_FACE_PLATE",
      "do_not_promote":True,
      "no_change_to_original_artifacts":True,
      "remediation":"Do not insert another face-colored mask or use the subject skin-colored path as a hidden face patch; first construct non-face, per-part geometry; unresolved facial region must fail closed until a source-authorized no-feature vector base exists."
    }
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--svg",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    masks,prov=load_observed_masks()
    result=audit(a.svg,masks)
    result["mask_provenance"]=prov
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in ("visual_status","source_face_pixels_covered_by_plate","source_hair_pixels_covered_by_plate","face_hair_overlap_pixels")}))
if __name__=="__main__":
    main()
