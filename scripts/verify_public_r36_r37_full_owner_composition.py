"""R36/R37: frozen Stage8 11-owner whole-scene browser pixel correctness.

R36 creates a non-generative vector scene using exactly reconstructed signed
owner masks and original RGB palette/z-order, with row runs or vertical-merged
rectangles. Independently compare actual Chrome DPR1/DPR2 against OpenCV owner
mask compositing pixel-for-pixel; no original image is edited.
R37 compares existing original-ring SVG Chrome against the exact same OpenCV
owner composition, measuring the raster discrepancy and the size tradeoff.

This is neither a proof of official full-character SVG/Stage04 parity nor
semantic anatomy, original vertex cap, hidden face parts, legal/device approval.
No product code modifications or automatic promotion.
"""
from __future__ import annotations
import argparse
import gzip
import json
import sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research_public_r12_exact_raster_prune import SOURCE,input_checks
from research_public_r17_consecutive_vertex_prune import SCENE_SHA256
from research_public_r19_lossless_svg_paths import scene_svg
from verify_public_r30_r35_exact_mask_vectors import (
    MODES,sha,ensure_binary,pixel_runs,vertical_merge,path_for_rectangles,browser_pixels,
)
from verify_public_v34_svgo_chrome import chrome_driver
from minimalizer_zerobase.composition.semantic import rasterize_primitive_candidate

VERSION="public-r36-r37-source-11-owner-true-vector-composite-v1"
CASES=("GC001","Raden")
def source_owner_reference(owners:list[dict])->np.ndarray:
    if len(owners)!=11 or len({x.get("source_mask_owner") for x in owners})!=11:
        raise ValueError("R36 actual 11 distinct original source owners required")
    image=np.full((340,340,3),255,dtype=np.uint8)
    for o in owners:
        color=o.get("palette_color_rgb")
        if (not isinstance(color,list) or len(color)!=3 or
            any(not isinstance(x,int) or isinstance(x,bool) or x<0 or x>255 for x in color)):
            raise ValueError("R36 source-owned RGB untrusted")
        mask=rasterize_primitive_candidate(o,width=340,height=340)>0
        image[mask]=color
    return image

def make_owner_scene(owners:list[dict],mode:str)->tuple[str,dict]:
    if mode not in MODES or len(owners)!=11:
        raise ValueError("R36 original owner scene or encoding unsupported")
    paths=[]
    total=0;source_points=0
    for owner in owners:
        mask=ensure_binary(rasterize_primitive_candidate(owner,width=340,height=340)>0)
        runs=pixel_runs(mask)
        rects=runs if mode=="row-runs" else vertical_merge(runs)
        rgb=owner["palette_color_rgb"]
        if not np.array_equal(
                rectangle_reconstruction(rects),mask):
            raise AssertionError("R36 geometry reconstruction error")
        total+=len(rects)
        source_points+=sum(len(r["points"]) for r in owner["parameters"]["rings"])
        paths.append(
            '<path d="'+path_for_rectangles(rects)+'" fill="rgb('+
            ','.join(str(x) for x in rgb)+')"/>')
    svg=(
      '<svg xmlns="http://www.w3.org/2000/svg" width="340" height="340" '
      'viewBox="0 0 340 340" shape-rendering="crispEdges">'
      '<rect width="340" height="340" fill="rgb(255,255,255)"/>'+
      ''.join(paths)+'</svg>')
    raw=svg.encode("utf-8")
    return svg,{
       "mode":mode,"sourceOriginalStage8RingVertices":source_points,
       "independentSourceOwnerCount":11,
       "rectangles":total,"newRepresentationRectangleCornerOccurrences":total*4,
       "wholeSvgBytes":len(raw),"wholeSvgGzip9Bytes":len(gzip.compress(raw,compresslevel=9,mtime=0)),
       "wholeSvgSHA256":sha(raw),
       "noPhotographicGeneratedPixels":True,
       "originalSourceOwnerRGBAndZOrderRetained":True
    }

def rectangle_reconstruction(rects)->np.ndarray:
    # Imported here to keep source geometry checks explicit and testable.
    from verify_public_r30_r35_exact_mask_vectors import rectangles_mask
    return rectangles_mask(rects)

def pixel_diff(image:np.ndarray,reference:np.ndarray)->dict:
    if image.shape!=reference.shape or image.dtype!=np.uint8:
        raise ValueError("R37 source canvas shape or dtype")
    diff=np.any(image!=reference,axis=2)
    return {"differentPixels":int(diff.sum()),
            "absoluteRGBMeanError":round(float(np.abs(
                  image.astype(np.int16)-reference.astype(np.int16)).mean()),6)}

def inspect(case:str,scene_file:Path,driver)->tuple[dict,dict[str,str]]:
    if case not in CASES:raise ValueError("unknown official original case")
    raw=scene_file.read_bytes()
    if sha(raw)!=SCENE_SHA256[case]:
        raise ValueError("R36 frozen full source scene SHA mismatch")
    obj=json.loads(raw)
    originals,cap,w,h=input_checks(case,obj)
    if (w,h)!=(340,340):raise ValueError("source dimensions not 340")
    numpy_reference=source_owner_reference(originals)
    outputs={}
    private={}
    for mode in MODES:
        candidate,meta=make_owner_scene(originals,mode)
        private[mode]=candidate
        assert meta["sourceOriginalStage8RingVertices"]==SOURCE[case][2]
        pairs={}
        for scale in (1,2):
            got=browser_pixels(driver,candidate,scale)
            expected=np.repeat(np.repeat(numpy_reference,scale,axis=0),scale,axis=1)
            d=pixel_diff(got,expected)
            if d["differentPixels"]!=0:
                raise AssertionError(f"R36 exact Chrome composite rejected {case} {mode} {scale} {d}")
            pairs[str(scale)]=d
        outputs[mode]={"svgProperties":meta,"genuineChrome":pairs,
                       "pixelExactToSignedOwnerMaskPaletteComposition":True}
    literal=scene_svg(originals,["literal"]*11)
    old_results={}
    for scale in (1,2):
        old=browser_pixels(driver,literal,scale)
        expected=np.repeat(np.repeat(numpy_reference,scale,axis=0),scale,axis=1)
        old_results[str(scale)]=pixel_diff(old,expected)
    if any(d["differentPixels"]==0 for d in old_results.values()):
        raise ValueError("R37 original Chrome contour baseline unexpectedly exact: review provenance")
    merged=outputs["vertical-merged"]["svgProperties"]
    row=outputs["row-runs"]["svgProperties"]
    if (merged["rectangles"]>=row["rectangles"] or
        merged["wholeSvgBytes"]>=row["wholeSvgBytes"]):
        raise ValueError("R37 vertical source mask encoding lost cost advantage")
    return {
       "case":case,
       "originalSignedStage8SceneSHA256":sha(raw),
       "originalSourcePhotoSHA256":SOURCE[case][0],
       "stage8OriginalRingVertices":SOURCE[case][2],
       "historicStage8VertexBudgetCap":cap,
       "historicStage8VertexBudgetPass":False,
       "originalOwnerCount":11,
       "vectorSourceMaskEncodings":outputs,
       "originalRingContourSvgVsExactSourceOwnedMaskPaletteComposition":old_results,
       "originalRingContourSvgWholeBytes":len(literal.encode("utf-8")),
       "referenceDefinedByFrozenSignedStage8OwnerMasksNotPhoto":True,
       "sourcePhotoSemanticOwnerProofAvailable":False,
       "officialStage04FullSceneRenderedEquivalentProven":False,
       "newRectangleCornerCountIsNotOldStage8VertexBudget":True,
       "notAuthorizedToIntegrateIntoProduct":True,
       "releaseAuthorized":False,
       "status":"SOURCE_11_OWNER_CHROME_EXACT_CANDIDATE_PHOTO_SEMANTIC_HOLD"
    },private

def run(sources:dict[str,Path],out:Path)->dict:
    if out.exists():raise FileExistsError("R37 output exists")
    cases=[];private={}
    driver=chrome_driver()
    try:
        chrome=driver.capabilities.get("browserVersion")
        for case in CASES:
            result,svgs=inspect(case,sources[case],driver)
            cases.append(result)
            private[case]=svgs
    finally:driver.quit()
    out.mkdir(parents=True)
    for case in CASES:
        for mode in MODES:
            # SVG contains derived original geometry, private-only!
            (out/(case+"_r36_PRIVATE_"+mode+".svg")).write_text(
                private[case][mode],encoding="utf-8")
    report={
        "version":VERSION,"browserVersion":chrome,
        "cases":cases,
        "allSignedOriginalOwnersPixelExactAtChrome340And680":True,
        "baselineChromeDifferenceActuallyMeasured":True,
        "noPublishedPrivateGeometry":True,
        "semanticOwnerPhotoGroundTruthVerified":False,
        "fullSourceOriginalStage8BudgetApproved":False,
        "productDeploymentOrLocalWorkerChanged":False,
        "releaseAuthorized":False,
        "status":"R36_R37_PIXEL_EXACT_11_OWNER_COMPOSITION_RESEARCH_PASS_PRODUCT_NO_GO"}
    (out/"public_r36_r37_chrome_full_owner_composite.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for row in cases:
        print("R36_R37",row["case"],
          "legacyChromeDiffDPR1",
          row["originalRingContourSvgVsExactSourceOwnedMaskPaletteComposition"]["1"]["differentPixels"],
          "legacyChromeDiffDPR2",
          row["originalRingContourSvgVsExactSourceOwnedMaskPaletteComposition"]["2"]["differentPixels"],
          "mergedRects",row["vectorSourceMaskEncodings"]["vertical-merged"]["svgProperties"]["rectangles"],
          "CHROME_EXACT_SOURCE_MASK_COMPOSITE",
          "PRODUCTION_NO_GO",flush=True)
    return report

def main():
    p=argparse.ArgumentParser()
    for name in ("gc-source","raden-source","out"):
        p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args()
    run({"GC001":a.gc_source,"Raden":a.raden_source},a.out)
if __name__=="__main__":main()
