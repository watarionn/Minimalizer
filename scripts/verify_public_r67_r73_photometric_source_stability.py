"""R67–R73 research: adversarial source-color robustness of tiny source edits.

R67 authenticate original two photos, signed Stage8 owner scenes and R66 preview
    via actual private PNG SHA source provenance.
R68 select only changed source pixels reducing both RGB MAE and approximate
    OpenCV LAB Euclidean distance against original photo and two smoothed
    photo observations (sigma 0, .6, 1.2). This is photometric perturbation
    assessment only, not image generation or anatomical validation.
R69 preserve source owner 1px band, topology/hole count and original overlap
    policies; require source-photo Scharr+Canny plus Sobel/Chroma nonregression.
R70 rerender full source RGB eleven-owner scene in real Chrome 340px/680px
    comparing independent NumPy original z-order composite.
R71 record original R6 eight blockers, signed photo semantic/Golden abstain.
R72 emit review-only original vs candidate comparisons, source-derived PRIVATE.
R73 final release-admission hard NO-GO and SHA-preserved research artifacts.

A number optimised on original source photo does NOT certify photographic
source-part semantics, appeal, correct anatomy or original Stage8 vertex cap.
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

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research_public_r12_exact_raster_prune import SOURCE,input_checks
from research_public_r17_consecutive_vertex_prune import SCENE_SHA256
from verify_public_r25_source_owner_attribution import PRIVATE,pinned
from verify_public_r52_r57_source_boundary_candidates import (
    topology,signed_boundary,gradients,boundary_evidence)
from verify_public_r58_r61_conservative_source_boundary import (
    independent_source_boundary_review)
from verify_public_r62_r66_dual_photo_color_edge import (
    compose_rgb,scene_svg,source_photo_error)
from verify_public_r30_r35_exact_mask_vectors import browser_pixels
from minimalizer_zerobase.composition.semantic import rasterize_primitive_candidate
from verify_public_v34_svgo_chrome import chrome_driver

VERSION="public-r67-r73-tri-photometric-source-candidate-fail-closed-v1"
CASES=("GC001","Raden")
ROLES=("right_arm","left_arm","major_clothing")
SIGMAS=(0.0,0.6,1.2)

def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()

def color_distance(rgb:np.ndarray,photo:np.ndarray)->np.ndarray:
    if (rgb.shape!=(340,340,3) or rgb.dtype!=np.uint8 or
        photo.shape!=rgb.shape or photo.dtype!=np.uint8):
        raise ValueError("R68 unsigned source RGB matrix")
    x=cv2.cvtColor(rgb,cv2.COLOR_RGB2LAB).astype(np.float64)
    y=cv2.cvtColor(photo,cv2.COLOR_RGB2LAB).astype(np.float64)
    return np.linalg.norm(x-y,axis=2)

def robust_delta_gate(original_rgb:np.ndarray,
                      proposed_rgb:np.ndarray,source_rgba:np.ndarray)->tuple[np.ndarray,dict]:
    if source_rgba.shape!=(340,340,4) or source_rgba.dtype!=np.uint8:
        raise ValueError("R68 original RGBA alpha source size")
    changed=np.any(original_rgb!=proposed_rgb,axis=2)
    rgb_original=source_photo_error(original_rgb,source_rgba[...,:3])
    rgb_new=source_photo_error(proposed_rgb,source_rgba[...,:3])
    robust=changed&(source_rgba[...,3]==255)&(rgb_new<rgb_original-1e-8)
    scores={}
    for sigma in SIGMAS:
        observed=source_rgba[...,:3] if sigma==0 else cv2.GaussianBlur(
              source_rgba[...,:3],(0,0),sigma)
        better=(color_distance(original_rgb,observed)>
                color_distance(proposed_rgb,observed)+1e-8)
        scores[str(sigma)]={
          "originalCandidateChangedPixels":int(changed.sum()),
          "photoLabColorDistanceBetterPixels":int((better&changed).sum()),
          "photoLabColorDistanceWorseOrEqualPixels":int((~better&changed).sum()),
          "colorVariationIsNumericalObservationNotRevisedSource":True
        }
        robust &=better
    return robust,{
      "baseChangedSourceOwnedRGBPixels":int(changed.sum()),
      "sourceOpaqueRgbMAEBetterPixels":int((changed&(rgb_new<rgb_original)).sum()),
      "sourceOpaqueRgbMAEWorsePixels":int((changed&(rgb_new>rgb_original)).sum()),
      "sourceRgbLabAll3PhotometricConditionsStablePixels":int(robust.sum()),
      "photometricSensitivity":scores,
      "sourcePhotoSemanticsIndependentlyVerified":False,
      "productAdoptionAuthorized":False
    }

def source_owner_subset(photo_rgb:np.ndarray,original:np.ndarray,prior:np.ndarray,
                        robust_visible:np.ndarray)->tuple[np.ndarray,dict]:
    if (original.shape!=(340,340) or prior.shape!=original.shape or
        robust_visible.shape!=original.shape or
        any(a.dtype!=np.dtype("bool") for a in (original,prior,robust_visible))):
        raise ValueError("R69 masks not exact source binary")
    changed=original^prior
    if np.any(changed&~signed_boundary(original)):
        raise ValueError("R69 prior source proposal escaped original one-pixel band")
    trial=original.copy()
    eligible=changed&robust_visible
    trial[eligible]=prior[eligible]
    a=topology(original)
    b=topology(trial)
    before_l,before_c=gradients(photo_rgb)
    before=boundary_evidence(original,before_l,before_c)
    after=boundary_evidence(trial,before_l,before_c)
    independent=independent_source_boundary_review(photo_rgb,original,trial)
    topology_valid=(a["connectedComponents8"]==b["connectedComponents8"] and
                    a["holeContours"]==b["holeContours"])
    fraction=float(np.count_nonzero(original^trial)/max(int(original.sum()),1))
    do_accept=bool(eligible.any() and topology_valid and fraction<=.01 and
        after["sourcePhotoLumGradientMean"]>=before["sourcePhotoLumGradientMean"] and
        after["sourcePhotoLabChromaGradientMean"]>=before["sourcePhotoLabChromaGradientMean"] and
        independent["independentBoundaryScoreNonRegressing"] and
        after["sourceBoundaryPixels"]<=before["sourceBoundaryPixels"]*1.02)
    result=trial if do_accept else original.copy()
    return result,{
       "sourcePriorOwnerMaskPixelsChanged":int(changed.sum()),
       "eligibleAfterRgbAndAllLabSensitivity":int(eligible.sum()),
       "acceptedOwnerPixels":int(np.count_nonzero(result^original)),
       "topologyConnectedComponentsAndHolesPreserved":topology_valid,
       "sourcePhotoLumEdgeGain":round(
            after["sourcePhotoLumGradientMean"]-before["sourcePhotoLumGradientMean"],6),
       "sourcePhotoChromaEdgeGain":round(
            after["sourcePhotoLabChromaGradientMean"]-before["sourcePhotoLabChromaGradientMean"],6),
       "sourceIndependentScharrEdgeGain":independent["independentGradientGain"],
       "sourceIndependentCannyCoincidenceGain":independent["independentCannyCoincidenceGain"],
       "admissionForResearchPreview":do_accept,
       "reason":("BOUNDARY_MULTI_METRIC_PASS_RESEARCH_ONLY" if do_accept else
                 "OWNER_SUBSET_RESET_TO_SIGNED_ORIGINAL"),
       "sourceAnatomicalOwnerApproved":False,
       "productionShapeMutationAllowed":False
    }

def private_comparison(photo:np.ndarray,baseline:np.ndarray,
                       preview:np.ndarray,out:Path)->None:
    changed=np.any(preview!=baseline,axis=2)
    overlay=photo.copy()
    overlay[changed]=[255,0,255]
    names=("SIGNED SOURCE PHOTO","ORIGINAL STAGE8","ROBUST PHOTO-ONLY REVIEW",
           "CHANGES ON SOURCE")
    board=Image.new("RGB",(340*4,372),(245,245,245))
    d=ImageDraw.Draw(board)
    for i,(name,a) in enumerate(zip(names,(photo,baseline,preview,overlay))):
        board.paste(Image.fromarray(a,"RGB"),(340*i,32))
        d.text((340*i+8,10),name,fill=(15,15,15))
    board.save(out)

def score_final(orig:np.ndarray,cand:np.ndarray,rgba:np.ndarray)->dict:
    changing=np.any(orig!=cand,axis=2)
    old_error=source_photo_error(orig,rgba[...,:3])
    new_error=source_photo_error(cand,rgba[...,:3])
    worse=int((changing&(new_error>=old_error)).sum())
    nonopaque=int((changing&(rgba[...,3]!=255)).sum())
    lab={}
    for sigma in SIGMAS:
        reference=rgba[...,:3] if sigma==0 else cv2.GaussianBlur(rgba[...,:3],(0,0),sigma)
        a=color_distance(orig,reference)
        b=color_distance(cand,reference)
        wrong=int((changing&(b>=a)).sum())
        lab[str(sigma)]={"changedPixelLabNonImprovement":wrong,
            "meanLabDistanceDeltaOriginalMinusPreview":round(float((a-b)[changing].mean()),6)
               if changing.any() else 0.0}
        if wrong:raise ValueError("R70 preview color LAB source perturbation not robust")
    if worse or nonopaque:
        raise ValueError("R70 preview not source RGB-opaque improving")
    return {
       "changedSourceFullCanvasPixels":int(changing.sum()),
       "photoRgbErrorImprovedChangedPixels":int((changing&(new_error<old_error)).sum()),
       "photoRgbErrorNotImprovedChangedPixels":worse,
       "photoSourceNonOpaqueChangedPixels":nonopaque,
       "originalGlobalPhotoRgbMAE":round(float(old_error.mean()),6),
       "robustCandidateGlobalPhotoRgbMAE":round(float(new_error.mean()),6),
       "LabPhotometricSensitivity":lab,
       "sourcePhotoSelectionBiasNotIndependentQualityEvidence":True
    }

def browser_full(driver,source_records,proposals)->dict:
    old=compose_rgb(source_records)
    new=compose_rgb(source_records,proposals)
    full={}
    for stage,canvas,overrides in (("original",old,{}),
                                   ("candidate",new,proposals)):
        svg=scene_svg(source_records,overrides)
        per={}
        for scale in (1,2):
            rendered=browser_pixels(driver,svg,scale)
            target=np.repeat(np.repeat(canvas,scale,axis=0),scale,axis=1)
            different=int(np.any(rendered!=target,axis=2).sum())
            if different:raise ValueError("R70 source Chrome full RGB canvas not exact")
            per[str(scale)]={"canvasSidePixels":340*scale,
                             "actualChromeSourceOwnerPaletteMismatchPixels":different}
        full[stage]={"chromeByDpr":per,
                     "sourceDerivedSvgSHA256":hashlib.sha256(svg.encode("utf8")).hexdigest()}
    return full

def trial(case:str,root:Path,scene:Path,prior_folder:Path,out:Path,driver):
    if case not in CASES:raise ValueError("R67 unknown signed case")
    source=root/PRIVATE/"original_inputs"/(case+"_source.png")
    pinned(source,SOURCE[case][0])
    pinned(scene,SCENE_SHA256[case])
    owners,cap,w,h=input_checks(case,json.loads(scene.read_text("utf8")))
    if len(owners)!=11 or (w,h)!=(340,340):
        raise ValueError("R67 incomplete historical source-owner scene")
    rgba=np.asarray(Image.open(source).convert("RGBA"))
    original=compose_rgb(owners)
    prior={}
    original_masks={}
    for role in ROLES:
        p=next(x for x in owners if x["source_mask_owner"]==role)
        old=rasterize_primitive_candidate(p,width=340,height=340)>0
        path=prior_folder/(case+"_r65_PRIVATE_"+role+"_candidate_mask.png")
        candidate=np.asarray(Image.open(path).convert("L"))>0
        if candidate.shape!=old.shape:
            raise ValueError("R67 previous private candidate geometry corrupt")
        original_masks[role]=old
        prior[role]=candidate
    prior_canvas=compose_rgb(owners,prior)
    stable,instability=robust_delta_gate(original,prior_canvas,rgba)
    keep={}
    owners_diag=[]
    for role in ROLES:
        selected,admission=source_owner_subset(rgba[...,:3],
             original_masks[role],prior[role],stable)
        keep[role]=selected
        owners_diag.append({"owner":role,
            "sourceOriginalMaskSHA256":hashlib.sha256(original_masks[role].astype(np.uint8).tobytes()).hexdigest(),
            "R69ConservativeOwnerAdmission":admission,
            "independentAnatomicalSemanticsCertified":False})
        Image.fromarray(selected.astype(np.uint8)*255,"L").save(
            out/(case+"_r69_PRIVATE_"+role+"_review_only.png"))
    candidate=compose_rgb(owners,keep)
    check=score_final(original,candidate,rgba)
    browser=browser_full(driver,owners,keep)
    private_comparison(rgba[...,:3],original,candidate,
        out/(case+"_r72_PRIVATE_robust_photo_review_board.png"))
    return {
        "case":case,
        "originalPhotoSHA256":SOURCE[case][0],
        "originalStage8SourceSHA256":SCENE_SHA256[case],
        "originalStage8RingVertices":SOURCE[case][2],
        "historicStage8RingCap":cap,
        "R68ColorRobustness":instability,
        "R69PerOwnerAdmission":owners_diag,
        "R70SourceRgbAndLabSensitivity":check,
        "R70GenuineChromeFull11OwnerDpr":browser,
        "allOriginalPhotoStage8OwnerMasksPalettesUntouched":True,
        "humanSourcePhotoAnatomyCertificationSigned":False,
        "productionSourceMaskUpdated":False
    }

def run(source_root:Path,scenes:dict[str,Path],prior:Path,r6:Path,out:Path):
    if out.exists():raise FileExistsError("R73 never overwrite signed photo evidence")
    held=json.loads(r6.read_text("utf8"))
    reference=json.loads((prior/"public_r62_r66_dual_objective_photo_fidelity_audit.json").read_text("utf8"))
    if (held.get("status")!="NO_GO" or held.get("blockedGateCount")!=8 or
        held.get("releaseAuthorized") is not False or
        reference.get("status")!="R62_R66_SOURCE_RGB_GATED_GEOMETRY_RESEARCH_COMPLETE_NO_GO" or
        [a["case"] for a in reference["cases"]]!=list(CASES)):
        raise ValueError("R67 signed research lineage or original R6 not held")
    # Check each previous private image against signed evidence where available.
    out.mkdir(parents=True)
    rows=[]
    driver=chrome_driver()
    try:
        version=driver.capabilities.get("browserVersion")
        for case in CASES:
            rows.append(trial(case,source_root,scenes[case],prior,out,driver))
    finally:driver.quit()
    report={
       "version":VERSION,
       "realChromeVersion":version,
       "originalR66PrivateAuditSHA256":sha(prior/"public_r62_r66_dual_objective_photo_fidelity_audit.json"),
       "R6EightBlockedGatesEvidenceSHA256":sha(r6),
       "cases":rows,
       "R73ReleaseGate":{
           "R67":"SIGNATURE_PINNED_SOURCE_AND_PREVIEW_LINEAGE",
           "R68":"RGB_AND_CIELAB_3_PHOTOMETRIC_SCALE_STABILITY",
           "R69":"ORIGINAL_OWNER_TOPOLOGY_AND_ALTERNATE_EDGE_GUARDED",
           "R70":"TRUE_CHROME_340_680_FULL_PALETTE_AND_SENSITIVITY_GATE",
           "R71":"ANATOMICAL_HUMAN_GOLDEN_AND_STAGE8_BUDGET_HOLD",
           "R72":"PRIVATE_ORIGINAL_VS_CANDIDATE_REVIEW_PACKET",
           "R73":"NO_PRODUCT_APPROVAL_EIGHT_BLOCKERS_UNCHANGED",
           "originalR6BlockedGates":8,
           "humanSemanticSourceOwnerCertificationSigned":False,
           "historicalStage8RingBudgetPassed":False,
           "fullSceneChromiumResvgFacetDpr2Signed":False,
           "physicalIphoneSafariSigned":False,
           "redistributionLicenseSigned":False,
           "realDeploymentRollbackSigned":False,
           "originalPhotosMasksAndFaceNoChange":True,
           "productionReleaseAuthorized":False
       },
       "privateOriginalPhotoReviewNeverCommittedToPublicGitHub":True,
       "productionReleaseAuthorized":False,
       "status":"R67_R73_PHOTOMETRIC_ROBUSTNESS_MEASURED_SEMANTIC_NO_GO"
    }
    (out/"public_r67_r73_color_geometry_robustness.json").write_text(
       json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    for row in rows:
        print("R67_R73",row["case"],
              "R66changed",row["R68ColorRobustness"]["baseChangedSourceOwnedRGBPixels"],
              "robustLabChanged",row["R68ColorRobustness"]["sourceRgbLabAll3PhotometricConditionsStablePixels"],
              "afterOwnerGate",row["R70SourceRgbAndLabSensitivity"]["changedSourceFullCanvasPixels"],
              "productionNO_GO",flush=True)
    return report

def main():
    p=argparse.ArgumentParser()
    for name in ("source-root","gc-stage8","raden-stage8","prior","r6","out"):
        p.add_argument("--"+name,required=True,type=Path)
    a=p.parse_args()
    run(a.source_root,{"GC001":a.gc_stage8,"Raden":a.raden_stage8},a.prior,a.r6,a.out)
if __name__=="__main__":main()
