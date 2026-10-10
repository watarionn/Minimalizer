"""R19 conservative geometry-exact SVG encoding (no vertex changes).

R12-R18 found that vertex removal changes Chrome despite OpenCV parity. Instead,
try two alternate encodings of the EXACT SAME signed source points in SVG path
syntax: implicit absolute lineto and relative axis/diagonal lineto. Reject
anything that alters actual Chrome RGBA at 340 or 680. No generated imagery,
no new palette, no changed owner, no hidden historic vertex-budget waiver.
Output source-derived SVG only to private research directories.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from minimalizer_zerobase.reviewed_sa10.full_character_svg import (
    _contour_mask_svg,_rgb,
)
from minimalizer_zerobase.reviewed_sa10.source_exact_vector_replay import _vertex_budget
from research_public_r12_exact_raster_prune import input_checks
from research_public_r17_consecutive_vertex_prune import SCENE_SHA256
from verify_public_r17_chrome_owner import svg_for_owner
from verify_public_r18_dual_renderer_prune import chrome_candidates
from verify_public_v34_svgo_chrome import chrome_driver,render_rgba,mismatched_pixels
from verify_public_r2_chrome import render_2x

VERSION="public-r19-exact-signed-source-svg-path-serialization-v1"
ENCODINGS=("implicit-absolute","axis-relative")
PATH_RE=re.compile(r'(<path d=")([^"]+)(" fill="#ffffff" fill-rule="evenodd")')

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def finite_lattice(value:object)->int:
    if isinstance(value,bool) or not isinstance(value,(float,int)):
        raise ValueError("R19 only accepts signed numeric integral source lattice")
    integer=int(value)
    if value!=integer or abs(integer)>1000000:
        raise ValueError("R19 forbids fractional/new SVG geometry")
    return integer

def xy(point:list)->tuple[int,int]:
    if not isinstance(point,list) or len(point)!=2:
        raise ValueError("bad original source point")
    return finite_lattice(point[0]),finite_lattice(point[1])

def fnum(number:float|int)->str:
    return f"{number:g}"

def ring_d(points:list,mode:str)->str:
    """Serialize original vertex sequence, including explicit ring closure."""
    if mode not in ENCODINGS:raise ValueError("unknown vector representation")
    if len(points)<3:raise ValueError("source degenerate ring cannot be path")
    coords=[xy(point) for point in points]
    x0,y0=coords[0]
    head=f"M{fnum(x0+.5)},{fnum(y0+.5)}"
    if mode=="implicit-absolute":
        return head+"".join(f" {fnum(x+.5)},{fnum(y+.5)}" for x,y in coords[1:])+"Z"
    prev_x,prev_y=x0,y0
    parts=[head]
    for x,y in coords[1:]:
        dx,dy=x-prev_x,y-prev_y
        if dy==0 and dx!=0:parts.append(f"h{fnum(dx)}")
        elif dx==0 and dy!=0:parts.append(f"v{fnum(dy)}")
        elif dx==0 and dy==0:parts.append("l0,0")
        else:parts.append(f"l{fnum(dx)},{fnum(dy)}")
        prev_x,prev_y=x,y
    return "".join(parts)+"Z"

def owner_svg(primitive:dict,mode:str)->str:
    # Existing official Stage8 SVG builder owns masks, palette, and micro-rings.
    # Only replace the path-data string for >=3-vertex source rings.
    baseline=svg_for_owner(primitive)
    rings=primitive["parameters"]["rings"]
    long_rings=[ring["points"] for ring in rings if len(ring["points"])>=3]
    if not long_rings:return baseline
    d=" ".join(ring_d(points,mode) for points in long_rings)
    count=len(PATH_RE.findall(baseline))
    if count!=1:raise ValueError("unexpected source mask path structure")
    converted,n=PATH_RE.subn(lambda m:m.group(1)+d+m.group(3),baseline)
    if n!=1 or converted==baseline:
        raise ValueError("source owner path wasn't serializable")
    if not all(source["depth"]>=0 and source["role"]==("hole" if source["depth"]%2 else "fill")
               for source in rings):
        raise ValueError("original source ring roles changed")
    return converted

def scene_svg(primitives:list[dict],modes:list[str])->str:
    """Standalone composite of all original owners for full-scene parity.

    Uses the same masks, paint and original back-to-front order. This is a
    diagnostic composite of the Stage8 owners, NOT complete signed Stage04.
    """
    if len(primitives)!=11 or len(modes)!=11:
        raise ValueError("entire original 11-owner scene required")
    defs=[]
    paints=[]
    for i,(p,mode) in enumerate(zip(primitives,modes)):
        owner=owner_svg(p,mode) if mode!="literal" else svg_for_owner(p)
        # Extract mask declaration and leave original singleton/two-point
        # handling inside that source template, with per-owner IDs.
        match=re.search(r'<mask id="r17-owner"[\s\S]*?</mask>',owner)
        if match is None:raise ValueError("original owner mask missing")
        defs.append(match.group(0).replace('id="r17-owner"',f'id="r19-owner-{i}"'))
        paint=_rgb(p["palette_color_rgb"])
        paints.append(f'<rect width="340" height="340" fill="{paint}" mask="url(#r19-owner-{i})"/>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="340" height="340" '
            'viewBox="0 0 340 340" shape-rendering="crispEdges"><defs>'
            + "".join(defs) + '</defs><rect width="340" height="340" fill="#ffffff"/>'
            +"".join(paints)+"</svg>")

def audit(case:str,source:Path,out:Path)->dict:
    if case not in SCENE_SHA256:raise ValueError("unsupported signed source")
    if out.exists():raise FileExistsError("research destination must be fresh")
    raw=source.read_bytes()
    if sha(raw)!=SCENE_SHA256[case]:raise ValueError("immutable Stage8 source SHA mismatch")
    obj=json.loads(raw)
    originals,cap,_,_=input_checks(case,obj)
    before_count=_vertex_budget(originals)["ring_vertices"]
    if len(originals)!=11:raise ValueError("original signed owners missing")
    browser=chrome_driver()
    browser.set_script_timeout(150)
    owner_rows=[];selected=[]
    try:
        chrome=browser.capabilities.get("browserVersion")
        for primitive in originals:
            baseline=svg_for_owner(primitive)
            candidates=[owner_svg(primitive,m) for m in ENCODINGS]
            responses=chrome_candidates(browser,baseline,candidates)
            tested=[{
                "encoding":name,
                "svgBytes":len(svg.encode("utf-8")),
                "nativeChromeDifferentPixels":int(result["d340"]),
                "dpr2ChromeDifferentPixels":int(result["d680"]),
                "accepted":result["d340"]==0 and result["d680"]==0,
            } for name,svg,result in zip(ENCODINGS,candidates,responses)]
            good=[row for row in tested if row["accepted"]]
            best=min(good,key=lambda r:(r["svgBytes"],ENCODINGS.index(r["encoding"]))) if good else None
            original_len=len(baseline.encode("utf-8"))
            if best is not None and best["svgBytes"]<original_len:
                chosen=best["encoding"]
                new_bytes=best["svgBytes"]
            else:
                chosen="literal"
                new_bytes=original_len
            selected.append(chosen)
            owner_rows.append({
              "owner":primitive["source_mask_owner"],
              "rings":len(primitive["parameters"]["rings"]),
              "originalVertices":sum(len(r["points"]) for r in primitive["parameters"]["rings"]),
              "baselineSvgBytes":original_len,
              "selectedEncoding":chosen,
              "selectedSvgBytes":new_bytes,
              "candidateEncodings":tested,
              "vertexCountUnchanged":True,
              "chrome340Exact":True,"chrome680Exact":True,
            })
        baseline_full=scene_svg(originals,["literal"]*11)
        chosen_full=scene_svg(originals,selected)
        native=mismatched_pixels(render_rgba(browser,baseline_full),
                                 render_rgba(browser,chosen_full))
        dpr2=mismatched_pixels(render_2x(browser,baseline_full),
                               render_2x(browser,chosen_full))
        if native or dpr2:raise AssertionError("full Stage8 owner compositing changed Chrome pixels")
        # R19 additionally uses the independent Selenium renderer for exact
        # native and 2x, separate from the JS_MULTI candidate batch path.
        for i,(p,mode) in enumerate(zip(originals,selected)):
            original_svg=svg_for_owner(p)
            candidate_svg=original_svg if mode=="literal" else owner_svg(p,mode)
            if mismatched_pixels(render_rgba(browser,original_svg),render_rgba(browser,candidate_svg)):
                raise AssertionError("Chrome independent native owner mismatch")
            if mismatched_pixels(render_2x(browser,original_svg),render_2x(browser,candidate_svg)):
                raise AssertionError("Chrome independent DPR2 owner mismatch")
    finally:
        browser.quit()

    original_bytes=sum(row["baselineSvgBytes"] for row in owner_rows)
    selected_bytes=sum(row["selectedSvgBytes"] for row in owner_rows)
    if selected_bytes>original_bytes:
        raise AssertionError("lossless SVG representation increased bytes")
    if _vertex_budget(originals)["ring_vertices"]!=before_count:
        raise AssertionError("source Stage8 vertex accounting changed")
    result={
        "version":VERSION,"case":case,"inputFrozenSceneSHA256":sha(raw),
        "signedStage8SourceRingVertices":before_count,
        "historicalStage8VertexCap":cap,
        "sourceOriginalRingVerticesModified":0,
        "sourceHistoricalStage8BudgetPassed":before_count<=cap,
        "ownerCount":len(originals),
        "browser":"real headless Chrome","chromeVersion":chrome,
        "baselineOwnerSvgBytes":original_bytes,
        "selectedOwnerSvgBytes":selected_bytes,
        "savedOwnerSvgBytes":original_bytes-selected_bytes,
        "savedOwnerSvgPercent":round(100*(original_bytes-selected_bytes)/original_bytes,3),
        "selectedSvgMoreCompact":selected_bytes<original_bytes,
        "reencodedOwners":sum(v!="literal" for v in selected),
        "compositeSourceStage8Chrome340DifferentPixels":native,
        "compositeSourceStage8Chrome680DifferentPixels":dpr2,
        "allOriginalOwnersChrome340And680Exact":True,
        "originalSourcePhotoVsStage8ParityApproved":False,
        "sourceSemanticFaceArmsTieStaffApproved":False,
        "humanGoldenApproved":False,
        "iPhoneSafariApproved":False,
        "facetCrossRendererDpr2Approved":False,
        "vertexBudgetImproved":False,
        "productionPromotionAuthorized":False,
        "localMinimalizerTouched":False,
        "status":"SOURCE_GEOMETRY_UNCHANGED_SVG_SERIALIZATION_PASS_RELEASE_HOLD",
        "ownerRows":owner_rows,
    }
    # Candidate contains original source geometry paths, so private only!
    out.mkdir(parents=True)
    private=out/(case+"_r19_PRIVATE_source_equivalent.svg")
    private.write_text(chosen_full,encoding="utf-8")
    result["privateCompositeSvgSHA256"]=sha(private.read_bytes())
    (out/(case+"_r19_coordinate_free_report.json")).write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("R19_REAL_CHROME_SOURCE_ENCODINGS",case,
          "SVG bytes",original_bytes,"->",selected_bytes,
          "saved",original_bytes-selected_bytes,
          "historic vertices",before_count,"cap",cap,"RELEASE_HOLD",flush=True)
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--case",choices=tuple(SCENE_SHA256),required=True)
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    audit(a.case,a.source,a.out)
if __name__=="__main__":main()
