"""R62–R66: source-photo composite and source-edge double-objective gate.

R62: compare original R37 pixel-EXACT 11-owner canvas and R58 exploratory
     boundary candidate against the authentic original photo RGB, not merely
     an edge-only metric. The first R58 candidates usually WORSEN photo fit.
R63: only retain source-visible edits that reduce original-photo RGB error,
     with original Stage8 owner geometry frozen and no new pixel synthesis.
R64: preserve source-mask topology/<=1% change and require an independently
     computed Scharr+Canny non-regression; decline any failing owner's trial.
R65: reconstruct exact 11-owner composited source-color SVG and verify genuine
     Chrome 340 and 680 against independently computed NumPy RGB/z-order.
R66: release NO-GO despite tiny photo-fit gains: no independent anatomical
     owner model, human Golden or historical Stage8 budget pass.

The source photo *itself* is used for selection: numerical photo color fit is
by construction, NOT heldout human aesthetic or part correctness evidence.
The masks and original signed palettes are immutable. Keep all derived SVG
and original-photo comparison images PRIVATE on canonical Google Drive.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image,ImageDraw

from verify_public_r52_r57_source_boundary_candidates import (
    PRIVATE, SOURCE, SCENE_SHA256, CASES, ROLES, pinned, input_checks,
    rasterize_primitive_candidate)
from verify_public_r58_r61_conservative_source_boundary import (
    select_topology_preserving_delta, independent_source_boundary_review)
from verify_public_r30_r35_exact_mask_vectors import (
    pixel_runs,vertical_merge,path_for_rectangles,browser_pixels)
from verify_public_v34_svgo_chrome import chrome_driver

VERSION="public-r62-r66-source-photo-dual-objective-color-edge-gate-v1"
WHITE=(255,255,255)

def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()

def compose_rgb(records:list[dict],overrides:dict[str,np.ndarray]|None=None)->np.ndarray:
    """Signed original Stage8 palette/z-order, geometry changed ONLY in preview."""
    if len(records)!=11 or len({r["source_mask_owner"] for r in records})!=11:
        raise ValueError("R62 original eleven source-owner scene required")
    result=np.full((340,340,3),255,dtype=np.uint8)
    overrides=overrides or {}
    if not set(overrides).issubset({r["source_mask_owner"] for r in records}):
        raise ValueError("R63 override changed original owner identity")
    for record in records:
        label=record["source_mask_owner"]
        mask=overrides.get(label)
        if mask is None:
            mask=rasterize_primitive_candidate(record,width=340,height=340)>0
        if mask.shape!=(340,340) or mask.dtype!=np.dtype(bool):
            raise ValueError("R63 unsigned owner source pixel mask")
        rgb=record["palette_color_rgb"]
        if len(rgb)!=3 or any(not isinstance(x,int) or not 0<=x<=255 for x in rgb):
            raise ValueError("R63 original palette unsigned")
        result[mask]=rgb
    return result

def source_photo_error(composite:np.ndarray,photo_rgb:np.ndarray)->np.ndarray:
    if composite.shape!=photo_rgb.shape or composite.shape!=(340,340,3):
        raise ValueError("R62 signed composite and source photo RGB sizes mismatch")
    return np.abs(composite.astype(np.int16)-photo_rgb.astype(np.int16)).mean(axis=2)

def select_photo_favorable_pixels(records:list[dict],original_rgb:np.ndarray,
                                  unapproved_rgb:np.ndarray,
                                  rgba:np.ndarray)->np.ndarray:
    """Only original alpha-opaque pixels with strict RGB-MAE improvement."""
    return (np.any(original_rgb!=unapproved_rgb,axis=2)&
            (rgba[...,3]==255)&
            (source_photo_error(unapproved_rgb,rgba[...,:3])+
             1e-9<source_photo_error(original_rgb,rgba[...,:3])))

def scene_svg(records:list[dict],override:dict[str,np.ndarray])->str:
    if len(records)!=11:raise ValueError("R65 source scene changed")
    paths=[]
    for record in records:
        key=record["source_mask_owner"]
        mask=override.get(key)
        if mask is None:
            mask=rasterize_primitive_candidate(record,width=340,height=340)>0
        if mask.shape!=(340,340) or mask.dtype!=np.dtype(bool):
            raise ValueError("R65 source mask untrusted")
        rects=vertical_merge(pixel_runs(mask))
        path=path_for_rectangles(rects)
        color=record["palette_color_rgb"]
        paths.append(f'<path d="{path}" fill="rgb({color[0]},{color[1]},{color[2]})"/>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="340" height="340" '
            'viewBox="0 0 340 340" shape-rendering="crispEdges">'
            '<rect width="340" height="340" fill="rgb(255,255,255)"/>'+
            "".join(paths)+'</svg>')

def gate_source_and_edges(old_rgb:np.ndarray,preview_rgb:np.ndarray,
                          final_rgb:np.ndarray,rgba:np.ndarray)->dict:
    old_error=source_photo_error(old_rgb,rgba[...,:3])
    preview_error=source_photo_error(preview_rgb,rgba[...,:3])
    final_error=source_photo_error(final_rgb,rgba[...,:3])
    old_changed=np.any(old_rgb!=preview_rgb,axis=2)
    changed=np.any(old_rgb!=final_rgb,axis=2)
    improved=int(np.count_nonzero((final_error<old_error)&changed))
    worsened=int(np.count_nonzero((final_error>old_error)&changed))
    neutral=int(np.count_nonzero((final_error==old_error)&changed))
    outsideopaque=int(np.count_nonzero(changed&(rgba[...,3]!=255)))
    if worsened or neutral or outsideopaque:
        raise ValueError("R64 claimed dual-objective candidate worsens original RGB in changed ROI")
    return {
      "originalUnconstrainedR58CompositePixelsChanged":int(old_changed.sum()),
      "originalR58ExperimentalPixelsPhotoFitBetter":int(np.count_nonzero(old_changed&(preview_error<old_error))),
      "originalR58ExperimentalPixelsPhotoFitWorse":int(np.count_nonzero(old_changed&(preview_error>old_error))),
      "conservativePhotoAndEdgeCandidateCompositePixelsChanged":int(changed.sum()),
      "originalPhotoRgbImprovedChangedPixels":improved,
      "originalPhotoRgbWorsenedChangedPixels":worsened,
      "photoUnchangedAtOtherOriginalPixels":int(np.count_nonzero(changed&~old_changed))==0,
      "candidateChangesOutsideOpaqueOriginalSource":outsideopaque,
      "originalPhotoGlobalMeanRGBError":round(float(old_error.mean()),6),
      "R58ExperimentalGlobalMeanRGBError":round(float(preview_error.mean()),6),
      "dualCandidateGlobalMeanRGBError":round(float(final_error.mean()),6),
      "finalOriginalPhotoRGBImprovementIsAnOptimizationTargetNotSemantics":True,
      "independentSourceOwnerSemanticCertification":False,
      "productionPaletteOrShapeApproved":False
    }

def review_private_board(photo:np.ndarray,baseline:np.ndarray,
                         r58:np.ndarray,final:np.ndarray,
                         filename:Path)->None:
    changed=np.any(baseline!=final,axis=2)
    heat=photo.copy()
    heat[changed]=(255,0,255)
    names=("SIGNED ORIGINAL PHOTO","OLD STAGE8 MASK PALETTE",
           "EARLIER EDGE-ONLY PREVIEW","DUAL-OBJECTIVE PRIVATE PREVIEW",
           "SOURCE-PIXEL CHANGES")
    images=(photo,baseline,r58,final,heat)
    board=Image.new("RGB",(340*len(names),375),(245,245,244))
    writer=ImageDraw.Draw(board)
    for i,(name,img) in enumerate(zip(names,images)):
        board.paste(Image.fromarray(img,"RGB"),(i*340,35))
        writer.text((i*340+4,9),name,fill=(20,20,20))
    board.save(filename)

def case_trial(case:str,photo_root:Path,scene_file:Path,
               r58_dir:Path,driver,out:Path)->tuple[dict,dict]:
    signed=photo_root/PRIVATE/"original_inputs"/(case+"_source.png")
    pinned(signed,SOURCE[case][0])
    pinned(scene_file,SCENE_SHA256[case])
    rgba=np.asarray(Image.open(signed).convert("RGBA"))
    owners,cap,w,h=input_checks(case,json.loads(scene_file.read_text(encoding="utf8")))
    if len(owners)!=11 or (w,h)!=(340,340):
        raise ValueError("R62 original signed photo/owner scene unavailable")
    original_masks={
        p["source_mask_owner"]:rasterize_primitive_candidate(
          p,width=340,height=340)>0 for p in owners}
    unconstrained={}
    for role in ROLES:
        candidate_path=r58_dir/(case+"_"+role+"_r58_PRIVATE_conservative_candidate.png")
        image=np.asarray(Image.open(candidate_path).convert("L"))>0
        if image.shape!=(340,340):raise ValueError("R63 untrusted prior source-pixel candidate")
        unconstrained[role]=image
    baseline=compose_rgb(owners)
    unconstrained_rgb=compose_rgb(owners,unconstrained)
    favorable=select_photo_favorable_pixels(owners,baseline,unconstrained_rgb,rgba)
    selected={}
    individual=[]
    for role in ROLES:
        original=original_masks[role]
        previous=unconstrained[role]
        tentative=original.copy()
        changed=original^previous
        tentative[changed&favorable]=previous[changed&favorable]
        proposed,record=select_topology_preserving_delta(rgba[...,:3],original,tentative)
        independent=independent_source_boundary_review(rgba[...,:3],original,proposed)
        if record["limitedChangedPixels"] and not independent["independentBoundaryScoreNonRegressing"]:
            # Fail-closed: undo the entire owner if the alternate observer degrades.
            proposed=original.copy()
            record["ownerResetBecauseIndependentEdgeDegraded"]=True
        else:
            record["ownerResetBecauseIndependentEdgeDegraded"]=False
        selected[role]=proposed
        individual.append({"owner":role,"restrictedByOriginalPhotoRgbPixelImprovement":True,
            "R63TopologyConstrainedSubset":record,
            "R64IndependentEdgeObserver":independent,
            "humanSourceOwnerSemanticPass":False,
            "candidateOriginalPaletteAndStage8SourceChanged":False})
    final=compose_rgb(owners,selected)
    photo_audit=gate_source_and_edges(baseline,unconstrained_rgb,final,rgba)
    svg={"baseline":scene_svg(owners,{}),"candidate":scene_svg(owners,selected)}
    composite={} 
    for method,bytestring in svg.items():
        expect=baseline if method=="baseline" else final
        result={}
        for scale in (1,2):
            output=browser_pixels(driver,bytestring,scale)
            exact=np.repeat(np.repeat(expect,scale,axis=0),scale,axis=1)
            mismatch=int(np.any(output!=exact,axis=2).sum())
            if mismatch:raise AssertionError("R65 exact Chrome composite differs from immutable source-owned numpy")
            result[str(scale)]={"realChromePixelDifferenceFromExactSourcePalette":mismatch,
                                "canvasSize":340*scale,
                                "signedMaskRgbCompositingPixelExact":True}
        composite[method]={"rendering":result,
                           "privateSvgSHA256":hashlib.sha256(bytestring.encode("utf8")).hexdigest()}
    # Save research-only images and SVG; no public source-derived geometry.
    prefix=case+"_r65_PRIVATE_"
    review_private_board(rgba[...,:3],baseline,unconstrained_rgb,final,
                         out/(prefix+"photo_palette_comparison.png"))
    for method,payload in svg.items():
        (out/(prefix+method+".svg")).write_text(payload,encoding="utf8")
    for role,mask in selected.items():
        Image.fromarray(mask.astype(np.uint8)*255,"L").save(
             out/(prefix+role+"_candidate_mask.png"))
    return {"case":case,"originalPhotoSHA256":SOURCE[case][0],
            "originalStage8SHA256":SCENE_SHA256[case],
            "originalStage8Vertices":SOURCE[case][2],
            "originalHistoricalStage8Cap":cap,
            "sourcePhotoAndSignedStage8NeverEdited":True,
            "originalPaletteOwnerCount":11,
            "R62PhotoRGBComparisonAndR64StrictGate":photo_audit,
            "R63_R64OwnerCandidateDecisions":individual,
            "R65GenuineChromeWholeOwnerCanvas":composite,
            "humanPhotoSemanticOwnerApproved":False,
            "sourcePhotoAestheticsGoldenSigned":False,
            "productSvgPromotionAuthorized":False},svg

def run(root:Path,scenes:dict[str,Path],r58:Path,r6:Path,out:Path)->dict:
    if out.exists():raise FileExistsError("R66 cannot overwrite previous signed research")
    held=json.loads(r6.read_text(encoding="utf8"))
    origin=json.loads((r58/"public_r58_r61_source_boundary_evidence.json").read_text("utf8"))
    if held.get("status")!="NO_GO" or held.get("blockedGateCount")!=8 or (
       held.get("releaseAuthorized") is not False or
       origin.get("status")!="R58_R61_CONSTRAINED_BOUNDARY_RESEARCH_COMPLETE_RELEASE_NO_GO"):
        raise ValueError("R66 source boundary history or release gate invalid")
    out.mkdir(parents=True)
    records=[]
    driver=chrome_driver()
    try:
        browser=driver.capabilities.get("browserVersion","unknown")
        for case in CASES:
            row,_=case_trial(case,root,scenes[case],r58,driver,out)
            records.append(row)
    finally:driver.quit()
    release={"R62":"FULL_11_OWNER_SOURCE_PHOTO_RGB_FIDELITY_AUDIT",
             "R63":"ONLY_SIGNED_RGB_PHOTO_BETTER_DELTA_ELIGIBLE",
             "R64":"TOPOLOGY_AND_ALTERNATE_EDGE_NOT_WORSE",
             "R65":"TRUE_CHROME_WHOLE_RGB_CANVAS_340_AND_680_EXACT",
             "R66":"ANATOMY_GOLDEN_BUDGET_R6_EIGHT_HOLD",
             "r6OriginalBlockedGates":8,
             "originalStage8VertexBudgetPassed":False,
             "signedHumanSemanticSourceOwnerReview":False,
             "originalSourcePhotoOrPaletteEdited":False,
             "newFaceFeaturesGenerated":False,
             "productionReleaseAuthorized":False}
    report={"version":VERSION,"realChromeVersion":browser,
            "cases":records,"R66ReleaseGate":release,
            "originalR6EvidenceSHA256":hashlib.sha256(r6.read_bytes()).hexdigest(),
            "originalR58EvidenceSHA256":sha(r58/"public_r58_r61_source_boundary_evidence.json"),
            "sourcePhotoColorWasOptimizationEvidenceNotIndependentGroundTruth":True,
            "allSourceDerivedGeometryAndPhotosPrivate":True,
            "productionReleaseAuthorized":False,
            "status":"R62_R66_SOURCE_RGB_GATED_GEOMETRY_RESEARCH_COMPLETE_NO_GO"}
    (out/"public_r62_r66_dual_objective_photo_fidelity_audit.json").write_text(
         json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    for c in records:
        values=c["R62PhotoRGBComparisonAndR64StrictGate"]
        print("R62_R66",c["case"],"old_r58_pixels",
              values["originalUnconstrainedR58CompositePixelsChanged"],
              "photoFIT_better",values["originalR58ExperimentalPixelsPhotoFitBetter"],
              "photoFIT_worse",values["originalR58ExperimentalPixelsPhotoFitWorse"],
              "dual_pixel_changes",values["conservativePhotoAndEdgeCandidateCompositePixelsChanged"],
              "deltaMeanMAE",round(values["dualCandidateGlobalMeanRGBError"]-
                                      values["originalPhotoGlobalMeanRGBError"],6),
              "RELEASE_NO_GO",flush=True)
    return report

def main():
    p=argparse.ArgumentParser()
    for name in ("root","gc","raden","r58","r6","out"):
        p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args()
    run(a.root,{"GC001":a.gc,"Raden":a.raden},a.r58,a.r6,a.out)
if __name__=="__main__":main()
