"""R17 genuine Chrome owner-by-owner SVG parity, independent of OpenCV.

No private coordinates or image files ever committed to GitHub. Reconstruct only
the existing source-owned polygon masks (and existing singleton/two-point rings)
to compare the private candidate with its actual frozen adaptive source in
real Chrome native and DPR2. A FAIL is not waived by OpenCV pixel equality.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from minimalizer_zerobase.reviewed_sa10.full_character_svg import _contour_mask_svg,_rgb
from verify_public_v34_svgo_chrome import chrome_driver,render_rgba,mismatched_pixels
from verify_public_r2_chrome import render_2x
from research_public_r12_exact_raster_prune import input_checks
from research_public_r17_consecutive_vertex_prune import sha,SCENE_SHA256

VERSION="public-r17-real-chrome-11-owner-boundary-parity-v1"

def svg_for_owner(primitive:dict)->str:
    mask,_=_contour_mask_svg(
        name="r17-owner",
        rings=primitive["parameters"]["rings"],width=340,height=340)
    col=_rgb(primitive["palette_color_rgb"])
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="340" height="340" '
            'viewBox="0 0 340 340" shape-rendering="crispEdges">'
            '<defs>'+mask+'</defs>'
            '<rect width="340" height="340" fill="#ffffff"/>'
            '<rect width="340" height="340" fill="'+col+
            '" mask="url(#r17-owner)"/></svg>')

def compare(case:str,source_file:Path,candidate_file:Path,out:Path)->dict:
    if out.exists():raise FileExistsError("R17 Chrome evidence already exists")
    raw=source_file.read_bytes()
    if sha(raw)!=SCENE_SHA256[case]:
        raise ValueError("R17 source frozen SHA mismatch")
    source=json.loads(raw)
    candidate=json.loads(candidate_file.read_text(encoding="utf-8"))
    originals,_,_,_=input_checks(case,source)
    if len(candidate["primitives_back_to_front"])!=11:
        raise ValueError("missing source owner from candidate")
    if candidate.get("production_authorized") is not False:
        raise ValueError("unapproved candidate claims production")
    rows=[]
    driver=chrome_driver()
    try:
        for before,after in zip(originals,candidate["primitives_back_to_front"]):
            if (before["source_mask_owner"]!=after["source_mask_owner"] or
                before["palette_color_rgb"]!=after["palette_color_rgb"]):
                raise ValueError("source owner or color modified")
            baseline_svg=svg_for_owner(before)
            candidate_svg=svg_for_owner(after)
            old340=render_rgba(driver,baseline_svg)
            new340=render_rgba(driver,candidate_svg)
            old680=render_2x(driver,baseline_svg)
            new680=render_2x(driver,candidate_svg)
            rows.append({
                "owner":before["source_mask_owner"],
                "sourceRingVertices":sum(len(r["points"]) for r in before["parameters"]["rings"]),
                "candidateRingVertices":sum(len(r["points"]) for r in after["parameters"]["rings"]),
                "chrome340DifferentPixels":mismatched_pixels(old340,new340),
                "chrome680DifferentPixels":mismatched_pixels(old680,new680),
            })
        chrome_version=driver.capabilities.get("browserVersion")
    finally:
        driver.quit()
    if len(rows)!=11:raise AssertionError("partial Chrome owner review")
    total_native=sum(r["chrome340DifferentPixels"] for r in rows)
    total_dpr2=sum(r["chrome680DifferentPixels"] for r in rows)
    decision={
      "version":VERSION,"case":case,
      "sourceSHA256":sha(raw),
      "candidatePrivateSHA256":sha(candidate_file.read_bytes()),
      "chromeVersion":chrome_version,
      "all11OriginalOwnersIndependentlyRendered":True,
      "ownerRows":rows,
      "sumOwnerChrome340DifferentPixels":total_native,
      "sumOwnerChrome680DifferentPixels":total_dpr2,
      "incrementalChromeNativeExact":total_native==0,
      "incrementalChromeDpr2Exact":total_dpr2==0,
      "officialStage04OriginalMaskChromeParityProven":False,
      "faceAndArmsSemanticQualityHumanSigned":False,
      "sourceStage8PolicyApproved":False,
      "productionPromoted":False,
      "releaseAuthorized":False,
      "status":"CHROME_OWNER_DIAGNOSTICS_COMPLETE_PRODUCT_HOLD",
    }
    out.mkdir(parents=True)
    (out/(case+"_r17_chrome_owner_differences.json")).write_text(
        json.dumps(decision,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return decision

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--case",choices=tuple(SCENE_SHA256),required=True)
    p.add_argument("--input-scene",type=Path,required=True)
    p.add_argument("--candidate-scene",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    x=p.parse_args()
    r=compare(x.case,x.input_scene,x.candidate_scene,x.out)
    print("R17_CHROME_OWNER_ACTUAL",x.case,
          "340px owner differences",r["sumOwnerChrome340DifferentPixels"],
          "680px owner differences",r["sumOwnerChrome680DifferentPixels"],
          "RELEASE_HOLD",flush=True)

if __name__=="__main__":main()
