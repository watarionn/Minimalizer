"""R58-R61 signed-source conservative photo-edge boundary search.

Only reselect a tiny *subset* of pre-existing R52 private source-derived
GraphCut pixels. No new photo pixels/texture, no original Stage8 mutation,
no eye/mouth or owner re-labels, no automatic product release.

R58: local greedy changes on signed one-pixel trust band with topology/perimeter
     and <=1% changed pixel restriction, LAB chroma and luminance evidence.
R59: independently assess SCHARR source-photo gradient/Canny edge alignment.
R60: real Chrome source mask original-vs-candidate at 340 and 680 exact delta.
R61: signed 2-source research evidence with original R6 eight-blocker NO-GO.
Optimization-target source score is *not* independent semantic ground truth.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from verify_public_r52_r57_source_boundary_candidates import (
    PRIVATE,SOURCE,SCENE_SHA256,CASES,ROLES,MAX_CHANGE_FRACTION,MIN_EDGE_GAIN,
    boundary_evidence,gradients,topology,chrome_compare,signed_boundary,pinned,
    input_checks,rasterize_primitive_candidate)
from verify_public_v34_svgo_chrome import chrome_driver

VERSION="public-r58-r61-conservative-source-boundary-selection-v1"
MAX_RESEARCH_CHANGE_FRACTION=.01
MAX_BOUNDARY_GROWTH_FRACTION=.02
MIN_PIXEL_GRADIENT_PRIORITY=45
EDGE_GAIN_TOLERANCE_L=.01
EDGE_GAIN_TOLERANCE_C=.005

def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()

def select_topology_preserving_delta(photo:np.ndarray,orig:np.ndarray,
                                     r52_candidate:np.ndarray)->tuple[np.ndarray,dict]:
    if (orig.shape!=(340,340) or orig.dtype!=np.dtype("bool") or
        r52_candidate.shape!=orig.shape or r52_candidate.dtype!=np.dtype("bool")):
        raise ValueError("R58 source candidates must be signed 340px binary")
    intended=orig^r52_candidate
    if np.any(intended&~signed_boundary(orig)):
        raise ValueError("R58 prior GraphCut proposal escaped frozen 1px source band")
    lum,chroma=gradients(photo)
    before=boundary_evidence(orig,lum,chroma)
    initial_topology=topology(orig)
    candidate=orig.copy()
    positions=np.column_stack(np.where(intended))
    priority=lum[positions[:,0],positions[:,1]]+chroma[positions[:,0],positions[:,1]]*.7
    order=np.argsort(-priority,kind="stable")
    cap=min(100,max(1,int(orig.sum()*MAX_RESEARCH_CHANGE_FRACTION)))
    prev_l=before["sourcePhotoLumGradientMean"]
    prev_c=before["sourcePhotoLabChromaGradientMean"]
    n=0
    for idx in order:
        if priority[idx]<MIN_PIXEL_GRADIENT_PRIORITY:
            break
        y,x=positions[idx]
        candidate[y,x]=r52_candidate[y,x]
        topo=topology(candidate)
        if (topo["connectedComponents8"]!=initial_topology["connectedComponents8"] or
            topo["holeContours"]!=initial_topology["holeContours"]):
            candidate[y,x]=orig[y,x]
            continue
        stats=boundary_evidence(candidate,lum,chroma)
        if (stats["sourcePhotoLumGradientMean"]<prev_l+EDGE_GAIN_TOLERANCE_L or
            stats["sourcePhotoLabChromaGradientMean"]<prev_c+EDGE_GAIN_TOLERANCE_C or
            stats["sourceBoundaryPixels"]>
               before["sourceBoundaryPixels"]*(1+MAX_BOUNDARY_GROWTH_FRACTION)):
            candidate[y,x]=orig[y,x]
            continue
        n+=1
        prev_l=stats["sourcePhotoLumGradientMean"]
        prev_c=stats["sourcePhotoLabChromaGradientMean"]
        if n>=cap:
            break
    after=boundary_evidence(candidate,lum,chroma)
    changed=orig^candidate
    if np.any(changed&~intended) or (
        topology(candidate)["connectedComponents8"]!=initial_topology["connectedComponents8"] or
        topology(candidate)["holeContours"]!=initial_topology["holeContours"] or
        changed.sum()>cap):
        raise AssertionError("R58 source owner exact mask topology or delta corruption")
    return candidate,{
       "originalR52ExperimentalChangedPixels":int(intended.sum()),
       "limitedChangedPixels":int(changed.sum()),
       "originalSourceOwnerMaskPixels":int(orig.sum()),
       "sourceOwnerChangedFraction":round(float(changed.sum()/orig.sum()),6),
       "originalTopology":initial_topology,
       "newTopology":topology(candidate),
       "selectedPixelsOnlyFromPriorR52SignedSourceBand":True,
       "originalSourcePaletteAndOwnerGeometryUnchanged":True,
       "luminanceMeanEdgeGainOptimizationTarget":round(
          after["sourcePhotoLumGradientMean"]-before["sourcePhotoLumGradientMean"],6),
       "chromaMeanEdgeGainOptimizationTarget":round(
          after["sourcePhotoLabChromaGradientMean"]-before["sourcePhotoLabChromaGradientMean"],6),
       "originalBoundaryPixels":before["sourceBoundaryPixels"],
       "candidateBoundaryPixels":after["sourceBoundaryPixels"],
       "sourceAnatomyGroundTruthSigned":False,
       "productCandidateApproved":False
    }

def independent_source_boundary_review(photo:np.ndarray,
                                       original:np.ndarray,candidate:np.ndarray)->dict:
    lab=cv2.cvtColor(photo,cv2.COLOR_RGB2LAB)
    h=cv2.cvtColor(photo,cv2.COLOR_RGB2HSV)
    # SCHARR, independently of the SOBEL edge used to select candidates.
    def magnitude(channel:np.ndarray)->np.ndarray:
        x=cv2.Scharr(channel,cv2.CV_32F,1,0)
        y=cv2.Scharr(channel,cv2.CV_32F,0,1)
        return cv2.magnitude(x,y)
    independent=magnitude(lab[:,:,0])+magnitude(h[:,:,1])
    canny=cv2.Canny(photo,75,170)
    def scores(mask):
        edge=signed_boundary(mask)
        return {
          "sourcePhotoIndependentScharrLabHsvGradientMean":round(float(independent[edge].mean()),6),
          "sourcePhotoCannyBoundaryCoincidenceRate":round(float((canny[edge]>0).mean()),6)
        }
    old=scores(original)
    new=scores(candidate)
    diff_g=new["sourcePhotoIndependentScharrLabHsvGradientMean"]-old["sourcePhotoIndependentScharrLabHsvGradientMean"]
    diff_c=new["sourcePhotoCannyBoundaryCoincidenceRate"]-old["sourcePhotoCannyBoundaryCoincidenceRate"]
    return {"original":old,"candidate":new,
            "independentGradientGain":round(diff_g,6),
            "independentCannyCoincidenceGain":round(diff_c,6),
            "notAnIndependentAnatomicalSegmentation":True,
            "independentBoundaryScoreNonRegressing":diff_g>=0 and diff_c>=0,
            "productPhotoSemanticApproval":False}

def run(source_root:Path,scenes:dict[str,Path],
        original_r52:Path,r6:Path,out:Path)->dict:
    if out.exists():raise FileExistsError("R61 never overwrites signed candidate packet")
    legacy=json.loads(original_r52.read_text(encoding="utf8"))
    held=json.loads(r6.read_text(encoding="utf8"))
    if (legacy.get("status")!="R52_R57_SOURCE_BOUNDARY_RESEARCH_DONE_PRODUCT_NO_GO" or
        [v.get("case") for v in legacy.get("cases",[])]!=list(CASES) or
        held.get("blockedGateCount")!=8 or held.get("status")!="NO_GO" or
        held.get("releaseAuthorized") is not False):
        raise ValueError("R61 requires frozen R52 source evidence and eight original blockers")
    results=[];private={}
    driver=chrome_driver()
    try:
        browser=driver.capabilities.get("browserVersion","unknown")
        for case,row in zip(CASES,legacy["cases"]):
            photo=source_root/PRIVATE/"original_inputs"/(case+"_source.png")
            pinned(photo,SOURCE[case][0])
            signed=scenes[case]
            pinned(signed,SCENE_SHA256[case])
            data=json.loads(signed.read_text(encoding="utf8"))
            owners,cap,w,h=input_checks(case,data)
            if len(owners)!=11 or (w,h)!=(340,340):
                raise ValueError("R58 source original 11-owner scene unavailable")
            rgba=np.asarray(Image.open(photo).convert("RGBA"))
            source_rgb=rgba[...,:3]
            by={o["source_mask_owner"]:o for o in owners}
            reviews=[]
            for record in row["candidateStudies"]:
                role=record["owner"]
                mask=rasterize_primitive_candidate(by[role],width=340,height=340)>0
                private_source=original_r52.parent/record["privateCandidateFile"]
                candidate=np.asarray(Image.open(private_source).convert("L"))>0
                constrained,measure=select_topology_preserving_delta(source_rgb,mask,candidate)
                independently=independent_source_boundary_review(source_rgb,mask,constrained)
                chromed=chrome_compare(driver,mask,constrained)
                name=case+"_"+role+"_r58_PRIVATE_conservative_candidate.png"
                private[name]=constrained.copy()
                reviews.append({"owner":role,
                    "frozenSourcePhotoSHA256":SOURCE[case][0],
                    "sourceStage8SceneSHA256":SCENE_SHA256[case],
                    "conservativeSelection":measure,
                    "R59AlternateSourceEdgeObserver":independently,
                    "R60ActualChromeSourcePixelEquality":chromed,
                    "candidateSafeForHumanResearchReviewOnly":bool(
                       measure["limitedChangedPixels"]>0 and
                       independently["independentBoundaryScoreNonRegressing"]),
                    "sourceSemanticsHumanApproved":False,
                    "productSourceMaskChanged":False,
                    "productionAdoptionAuthorized":False,
                    "privateCandidateMask":name})
            results.append({"case":case,
                "originalSourcePhotoSHA256":SOURCE[case][0],
                "originalStage8SceneSHA256":SCENE_SHA256[case],
                "originalStage8VertexBudget":cap,
                "originalSourceStage8Vertices":SOURCE[case][2],
                "candidateItems":reviews,
                "independentHumanSemanticSourcePartApproval":False})
    finally:driver.quit()
    packet={"version":VERSION,"realChromeVersion":browser,
        "R52OriginalEvidenceSHA256":sha(original_r52),
        "originalR6EvidenceSHA256":sha(r6),
        "cases":results,
        "R61ReleaseGate":{
          "R58":"TOPOLOGY_PRESERVING_ONE_PERCENT_SIGNED_EDGE_RESELECTION",
          "R59":"INDEPENDENT_SCHARR_CANNY_SOURCE_EDGE_QUALITY_REVIEW",
          "R60":"REAL_CHROME_340_AND_680_SOURCE_MASK_EXACT_BOTH_ENCODINGS",
          "R61":"ORIGINAL_R6_8_BLOCKERS_AND_SEMANTIC_NO_GO",
          "originalReleaseBlockedGates":8,
          "sourcePhotoHumanAnatomicalApproval":False,
          "originalStage8RingBudgetPassed":False,
          "verifiedDeviceSafari":False,"humanGoldenPass":False,
          "faceDetailPixelsGenerated":False,
          "githubMainMerged":False,
          "productionReleaseAuthorized":False
        },
        "signedSourcePhotoAndStage8NeverMutated":True,
        "pixelCandidatesPrivateNotUploadedToPublicGitHub":True,
        "productionReleaseAuthorized":False,
        "status":"R58_R61_CONSTRAINED_BOUNDARY_RESEARCH_COMPLETE_RELEASE_NO_GO"}
    out.mkdir(parents=True)
    for name,mask in private.items():
        Image.fromarray(mask.astype(np.uint8)*255,"L").save(out/name)
    (out/"public_r58_r61_source_boundary_evidence.json").write_text(
        json.dumps(packet,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    for case in results:
        for e in case["candidateItems"]:
            m=e["conservativeSelection"];s=e["R59AlternateSourceEdgeObserver"]
            print("R58_R61",case["case"],e["owner"],
                  "selected",m["limitedChangedPixels"],"sourceMeanGains",
                  m["luminanceMeanEdgeGainOptimizationTarget"],
                  m["chromaMeanEdgeGainOptimizationTarget"],
                  "independentScharr",s["independentGradientGain"],
                  "canny",s["independentCannyCoincidenceGain"],
                  "previewOnly",e["candidateSafeForHumanResearchReviewOnly"],
                  "PRODUCT_NO_GO",flush=True)
    return packet

def main():
    p=argparse.ArgumentParser()
    for n in ("source-root","gc-stage8","raden-stage8","r52","r6","out"):
        p.add_argument("--"+n,required=True,type=Path)
    a=p.parse_args()
    run(a.source_root,{"GC001":a.gc_stage8,"Raden":a.raden_stage8},
        a.r52,a.r6,a.out)
if __name__=="__main__":main()
