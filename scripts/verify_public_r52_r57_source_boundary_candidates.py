"""R52-R57: signed-source 1px contour hypotheses, Chrome-accurate and NO-GO.

R52 freeze source photo SHA, original signed Stage8 owner masks/palette/ordering.
R53 use source-photo-only OpenCV GrabCut observation, restrained to one-pixel
    boundary around selected source owners, original two-pixel erosion frozen.
R54 independently measure original-image RGB/LAB luminance boundary evidence.
R55 decline topology changes, excessive changes and false owner encroachment.
R56 render original and candidate as exact pixel-run vector masks in true
    Chrome native 340 and 680; verify changed pixels are within signed delta.
R57 retain R6 eight original blockers, Stage8 vertex caps and human Golden HOLD.

A photo gradient is NOT source-part anatomy. Candidate PNGs and evidence are
private-only. No img2img, Generative Fill, new face details or product mutation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT))
from research_public_r12_exact_raster_prune import SOURCE,input_checks
from research_public_r17_consecutive_vertex_prune import SCENE_SHA256
from verify_public_r25_source_owner_attribution import PRIVATE,pinned
from verify_public_r30_r35_exact_mask_vectors import (
    exact_svg,browser_pixels,rectangles_mask,pixel_runs,vertical_merge)
from verify_public_v34_svgo_chrome import chrome_driver
from minimalizer_zerobase.composition.semantic import rasterize_primitive_candidate

VERSION="public-r52-r57-locked-source-photo-boundary-observer-v1"
CASES=("GC001","Raden")
ROLES=("right_arm","left_arm","major_clothing")
CRITICAL=("face","left_arm","right_arm")
MAX_CHANGE_FRACTION=0.05
MIN_EDGE_GAIN=4.0
SIZE=340
K3=np.ones((3,3),dtype=np.uint8)
K5=np.ones((5,5),dtype=np.uint8)
K11=np.ones((11,11),dtype=np.uint8)
K17=np.ones((17,17),dtype=np.uint8)

def sha_bytes(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def topology(mask:np.ndarray)->dict:
    source=mask.astype(np.uint8)
    components=int(cv2.connectedComponents(source,connectivity=8)[0]-1)
    contours,h=cv2.findContours(source,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    holes=0
    if h is not None:
        for i in range(len(contours)):
            depth=0
            parent=int(h[0][i][3])
            while parent>=0:
                depth+=1
                parent=int(h[0][parent][3])
            holes+=int(depth%2==1)
    return {"connectedComponents8":components,"holeContours":holes,
            "contourCount":len(contours),"maskPixels":int(mask.sum())}

def signed_boundary(mask:np.ndarray)->np.ndarray:
    original=mask.astype(np.uint8)
    return ((cv2.dilate(original,K3)>0)&~(cv2.erode(original,K3)>0))

def gradients(photo:np.ndarray)->tuple[np.ndarray,np.ndarray]:
    if photo.shape!=(SIZE,SIZE,3) or photo.dtype!=np.uint8:
        raise ValueError("R52 unsigned RGB original")
    gray=cv2.cvtColor(photo,cv2.COLOR_RGB2GRAY)
    lab=cv2.cvtColor(photo,cv2.COLOR_RGB2LAB)
    def norm_edge(m):
        a=cv2.Sobel(m,cv2.CV_32F,1,0,ksize=3)
        b=cv2.Sobel(m,cv2.CV_32F,0,1,ksize=3)
        return cv2.magnitude(a,b)
    luminance=norm_edge(gray)
    # Different color-space evidence from a source photo, not another mask model.
    chroma=norm_edge(lab[:,:,1])+norm_edge(lab[:,:,2])
    return luminance,chroma

def boundary_evidence(mask:np.ndarray,lum:np.ndarray,chroma:np.ndarray)->dict:
    border=signed_boundary(mask)
    if not border.any():raise ValueError("R54 missing original mask boundary")
    coords=np.where(border)
    return {"sourcePhotoLumGradientMean":round(float(lum[coords].mean()),6),
            "sourcePhotoLabChromaGradientMean":round(float(chroma[coords].mean()),6),
            "sourceBoundaryPixels":int(border.sum())}

def graphcut_trust_region(photo:np.ndarray, original:np.ndarray,
                          protected:np.ndarray)->tuple[np.ndarray,dict]:
    if any(x.shape!=(SIZE,SIZE) for x in (original,protected)) or (
        original.dtype!=np.dtype("bool") or protected.dtype!=np.dtype("bool")):
        raise ValueError("R53 original mask/protected semantics invalid")
    if not original.any():raise ValueError("R53 original owner empty")
    init=np.full((SIZE,SIZE),cv2.GC_PR_BGD,dtype=np.uint8)
    init[cv2.dilate(original.astype(np.uint8),K17)==0]=cv2.GC_BGD
    init[original]=cv2.GC_PR_FGD
    core=cv2.erode(original.astype(np.uint8),K11)>0
    init[core]=cv2.GC_FGD
    if not core.any():
        distances=cv2.distanceTransform(original.astype(np.uint8),cv2.DIST_L2,3)
        y,x=np.unravel_index(int(distances.argmax()),distances.shape)
        core[y,x]=True
    bg=np.zeros((1,65),dtype=np.float64)
    fg=np.zeros((1,65),dtype=np.float64)
    result,_,_=cv2.grabCut(np.ascontiguousarray(photo[:,:,::-1]),
                           init,None,bg,fg,5,cv2.GC_INIT_WITH_MASK)
    suggested=(result==cv2.GC_FGD)|(result==cv2.GC_PR_FGD)
    boundary=signed_boundary(original)
    interior=cv2.erode(original.astype(np.uint8),K5)>0
    # Frozen original two-pixel core and other signed protected original owners.
    allowed=boundary&~protected
    candidate=np.where(allowed,suggested,original)
    candidate[interior]=True
    if np.any((candidate!=original)&~allowed):
        raise AssertionError("R53 candidate escaped 1px source boundary")
    if np.any(candidate[protected]!=original[protected]):
        raise AssertionError("R53 candidate changed protected owner")
    changed=candidate^original
    return candidate,{
       "allowedOnePixelBoundaryPixels":int(allowed.sum()),
       "changedMaskPixels":int(changed.sum()),
       "addedPixels":int(np.count_nonzero(candidate&~original)),
       "removedPixels":int(np.count_nonzero(original&~candidate)),
       "changedOutsideSignedOnePixelBoundary":int((changed&~boundary).sum()),
       "changedProtectedOtherOwnerPixels":int((changed&protected).sum()),
       "originalTwoPixelInteriorFrozen":bool(np.all(candidate[interior])),
       "sourceMaskAreaRatioChanged":round(float(changed.sum()/original.sum()),6),
       "sourcePhotoSemanticOwnerVerified":False
    }

def guard(original:np.ndarray,candidate:np.ndarray,measure:dict,
          before:dict,after:dict)->dict:
    original_top=topology(original)
    proposed_top=topology(candidate)
    delta_l=after["sourcePhotoLumGradientMean"]-before["sourcePhotoLumGradientMean"]
    delta_c=after["sourcePhotoLabChromaGradientMean"]-before["sourcePhotoLabChromaGradientMean"]
    reasons=[]
    if not measure["changedMaskPixels"]:reasons.append("NO_SOURCE_BOUNDARY_CHANGE")
    if measure["sourceMaskAreaRatioChanged"]>MAX_CHANGE_FRACTION:
        reasons.append("BOUNDARY_CHANGE_TOO_LARGE")
    if (original_top["connectedComponents8"]!=proposed_top["connectedComponents8"]
        or original_top["holeContours"]!=proposed_top["holeContours"]):
        reasons.append("SOURCE_MASK_TOPOLOGY_CHANGED")
    if measure["changedOutsideSignedOnePixelBoundary"] or measure["changedProtectedOtherOwnerPixels"]:
        reasons.append("SOURCE_MASK_TRUST_REGION_VIOLATED")
    if delta_l<MIN_EDGE_GAIN:reasons.append("NO_SIGNIFICANT_LUMINANCE_EDGE_SUPPORT")
    if delta_c<0:reasons.append("CHROMA_EDGE_EVIDENCE_WORSENED")
    return {"passForResearchPreviewOnly":not reasons,
            "rejectionReasons":reasons,
            "sourceLuminanceBoundaryEvidenceGain":round(delta_l,6),
            "sourceChromaBoundaryEvidenceGain":round(delta_c,6),
            "originalTopology":original_top,
            "experimentalTopology":proposed_top,
            "humanPhotoSemanticOwnerApproval":False,
            "sourcePhotoBoundaryEvidenceIsNotAnatomicalTruth":True,
            "productGeometryAdoptionAuthorized":False}

def chrome_compare(driver,original:np.ndarray,candidate:np.ndarray)->dict:
    delta=original^candidate
    outputs={}
    for encoding in ("row-runs","vertical-merged"):
        before,_=exact_svg(original,encoding)
        after,_=exact_svg(candidate,encoding)
        details={}
        for scale in (1,2):
            old_rgb=browser_pixels(driver,before,scale)
            new_rgb=browser_pixels(driver,after,scale)
            oldmask=np.repeat(np.repeat(original,scale,axis=0),scale,axis=1)
            newmask=np.repeat(np.repeat(candidate,scale,axis=0),scale,axis=1)
            expected_old=np.where(oldmask[...,None],255,0).astype(np.uint8)
            expected_new=np.where(newmask[...,None],255,0).astype(np.uint8)
            different=np.any(old_rgb!=new_rgb,axis=2)
            signed_change=np.repeat(np.repeat(delta,scale,axis=0),scale,axis=1)
            wrong_old=int(np.any(old_rgb!=expected_old,axis=2).sum())
            wrong_new=int(np.any(new_rgb!=expected_new,axis=2).sum())
            extras=int((different&~signed_change).sum())
            missed=int((signed_change&~different).sum())
            if wrong_old or wrong_new or extras or missed:
                raise AssertionError("R56 Chrome made extra/inexact source candidate pixels")
            details[str(scale)]={"rasterSize":SIZE*scale,
                "pixelChanges":int(different.sum()),
                "signedSourceMaskPixelChangesExpected":int(delta.sum())*scale*scale,
                "changedOutsideOriginalSignedDifferencePixels":extras,
                "browserMaskAgainstSignedPixelsChanged":wrong_old+wrong_new,
                "byteExactOriginalAndCandidateChrome":True}
        outputs[encoding]=details
    return outputs

def run(source_root:Path,scenes:dict[str,Path],r6:Path,out:Path)->dict:
    if out.exists():raise FileExistsError("R57 evidence must not overwrite")
    original_r6=json.loads(r6.read_text(encoding="utf8"))
    if (original_r6.get("status")!="NO_GO" or original_r6.get("blockedGateCount")!=8 or
        original_r6.get("releaseAuthorized") is not False or
        len(original_r6.get("blockedGates",[]))!=8):
        raise ValueError("R57 original release eight blockers absent")
    records=[];private={}
    driver=chrome_driver()
    try:
        browser_version=driver.capabilities.get("browserVersion","unknown")
        for case in CASES:
            photo=source_root/PRIVATE/"original_inputs"/(case+"_source.png")
            pinned(photo,SOURCE[case][0])
            src=Image.open(photo)
            rgb=np.asarray(src.convert("RGB"))
            rgba=np.asarray(src.convert("RGBA"))
            stage=scenes[case]
            pinned(stage,SCENE_SHA256[case])
            owners,cap,w,h=input_checks(case,json.loads(stage.read_text(encoding="utf8")))
            if len(owners)!=11 or (w,h)!=(SIZE,SIZE):
                raise ValueError("R52 original 11 source owner scenes not signed")
            baseline_masks={x["source_mask_owner"]:(
                rasterize_primitive_candidate(x,width=SIZE,height=SIZE)>0)
                for x in owners}
            lum,chroma=gradients(rgb)
            entries=[]
            for role in ROLES:
                original=baseline_masks[role]
                protected=np.zeros((SIZE,SIZE),dtype=bool)
                for k in CRITICAL:
                    if k!=role:protected|=baseline_masks[k]
                candidate,quant=graphcut_trust_region(rgb,original,protected)
                before=boundary_evidence(original,lum,chroma)
                after=boundary_evidence(candidate,lum,chroma)
                admission=guard(original,candidate,quant,before,after)
                # Observe all candidates. The gate NEVER assigns semantic PASS.
                browser=chrome_compare(driver,original,candidate)
                outkey=case+"_"+role+"_r53_PRIVATE_photo_edge_candidate_mask.png"
                private[outkey]=candidate.copy()
                entries.append({"owner":role,"oldSourceMaskPixels":int(original.sum()),
                    "originalSourceMaskSourceSHA256":SCENE_SHA256[case],
                    "sourcePhotoRGBAlphaUnchanged":True,
                    "sourcePhotoRgbGradientMethod":"Sobel luminance and LAB chroma",
                    "sourceBoundaryChange":quant,
                    "boundaryEvidenceBefore":before,
                    "boundaryEvidenceAfter":after,
                    "R55ConservativeCandidateDecision":admission,
                    "R56GenuineChromeExactSourceMask":browser,
                    "privateCandidateFile":outkey,
                    "originalSourceMaskReplaced":False,
                    "productIntegrationApproved":False})
            records.append({"case":case,"sourcePhotoSHA256":SOURCE[case][0],
                "sourceStage8SceneSHA256":SCENE_SHA256[case],
                "originalStage8VertexCount":SOURCE[case][2],
                "originalStage8VertexCap":cap,
                "sourceOriginalOwnerCount":len(owners),
                "sourceMasksUnmodified":True,"candidateStudies":entries,
                "independentSourcePhotoHumanSemanticsSigned":False})
    finally:
        driver.quit()
    result={"version":VERSION,"realChromeVersion":browser_version,
        "cases":records,
        "R57ReleaseGate":{
          "R52":"SIGNED_PHOTO_AND_11_SOURCE_MASK_AUTHENTICATED",
          "R53":"GRABCUT_ONLY_SOURCE_1PX_BOUNDARY_TRUST_REGION",
          "R54":"PHOTO_LUMINANCE_CHROMA_EDGE_OBSERVER_NOT_SEMANTICS",
          "R55":"TOPOLOGY_AREA_AND_PROTECTED_OWNER_GATE",
          "R56":"TRUE_CHROME_340_AND_680_BITEXACT_RASTER",
          "R57":"ORIGINAL_EIGHT_BLOCKERS_AND_SEMANTIC_NO_GO",
          "originalReleaseBlockedGates":8,
          "originalStage8BudgetPass":False,
          "independentHumanPhotoSemanticOwnerSigned":False,
          "sourcePhotoOrStage8OwnerEdited":False,
          "existingFaceMicrofeaturesRendered":False,
          "productionReleaseAuthorized":False
        },
        "originalSourceRgbOrMasksChanged":False,
        "sourcePhotoBoundaryCorrelationIsNotAnatomyProof":True,
        "privateSourceDerivedCandidateMasksNotInGitHub":True,
        "productionReleaseAuthorized":False,
        "status":"R52_R57_SOURCE_BOUNDARY_RESEARCH_DONE_PRODUCT_NO_GO"}
    out.mkdir(parents=True)
    for name,mask in private.items():
        Image.fromarray((mask*255).astype(np.uint8),"L").save(out/name)
    (out/"public_r52_r57_source_boundary_audit.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    for row in records:
        for case in row["candidateStudies"]:
            r=case["R55ConservativeCandidateDecision"]
            print("R52_R57",row["case"],case["owner"],
                "changed",case["sourceBoundaryChange"]["changedMaskPixels"],
                "edgeGain",r["sourceLuminanceBoundaryEvidenceGain"],
                "chromaGain",r["sourceChromaBoundaryEvidenceGain"],
                "researchPreviewOnly",r["passForResearchPreviewOnly"],
                "rejections",r["rejectionReasons"],flush=True)
    return result

def main():
    p=argparse.ArgumentParser()
    for name in ("source-root","gc-stage8","raden-stage8","r6","out"):
        p.add_argument("--"+name,required=True,type=Path)
    a=p.parse_args()
    run(a.source_root,{"GC001":a.gc_stage8,"Raden":a.raden_stage8},a.r6,a.out)
if __name__=="__main__":main()
