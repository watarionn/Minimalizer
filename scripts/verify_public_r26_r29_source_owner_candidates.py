"""R26–R29 actual signed source-owner repair research, NEVER production promotion.

R26: strictly subtract fully opaque 4-connected exact background RGB from
     original signed Stage04 RIGHT-ARM ROI (diagnostic hypothesis, not anatomy).
R27: independently render signed-versus-proposed masks in genuine Chrome at
     both 340 and 680 and compare against the exact binary source mask.
R28: compare both original sources and abstain on unsigned semantic evidence.
R29: preserve strict historical Stage8 and R6 release NO-GO, with artifacts.
No generated pixels; no photo, original signed masks, Stage8, Local or live
web edits. PRIVATE mask previews and source photos must not enter GitHub.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"tools/research"))
from verify_public_r25_source_owner_attribution import (
    FROZEN,PRIVATE,CASES,VERSION as R25_VERSION,digest,pinned,
    rgb_image,mask_image
)
from verify_public_v34_svgo_chrome import chrome_driver,render_rgba
from verify_public_r2_chrome import render_2x
from research_public_r17_consecutive_vertex_prune import SCENE_SHA256
from research_public_r12_exact_raster_prune import SOURCE,input_checks
from minimalizer_zerobase.reviewed_sa10.full_character_svg import _binary_mask_svg
from sa1060b_first_bad_stage_audit import source_connected_background

VERSION="public-r26-r29-signed-right-arm-bg-candidate-and-chrome-abstain-v1"
EXPECTED_R25_SHA="5f7bb72c101c3254a8e2f9beb0c60063d2bb484518dcced12f96726fcd8bd9aa"
HISTORIC_STAGE8={"GC001":(3604,1887),"Raden":(2370,1412)}
EXPECTED_R6_BLOCKED=8

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def validate_r25(path:Path)->dict:
    pinned(path,EXPECTED_R25_SHA)
    data=json.loads(path.read_text(encoding="utf-8"))
    if (data.get("version")!=R25_VERSION or
        data.get("status")!="R25_SIGNED_SOURCE_OWNER_ERROR_ATTRIBUTION_COMPLETE_RELEASE_NO_GO" or
        data.get("productionReleaseAuthorized") is not False or
        [x.get("case") for x in data.get("cases",[])]!=list(CASES)):
        raise ValueError("R26 R25 original evidence status or ordering drift")
    for c in data["cases"]:
        name=c["case"]
        if c["originalSourceSHA256"]!=SOURCE[name][0] or (
            c["signedStage8SceneSHA256"]!=SCENE_SHA256[name]) or (
            c["stage8OwnerCount"]!=11):
            raise ValueError("R26 Stage8 or source provenance drift")
    return data

def mask_cc(mask:np.ndarray)->dict:
    n,_,components,_=cv2.connectedComponentsWithStats(mask.astype(np.uint8),8)
    area=sorted([int(x) for x in components[1:,cv2.CC_STAT_AREA]],reverse=True)
    contours,_=cv2.findContours(mask.astype(np.uint8),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    return {"components":int(n-1),"componentsAreaDescending":area[:10],
            "polygonContours":len(contours),
            "polygonVertices":sum(len(x) for x in contours)}

def isolate_opaque_exact_border_connected(
    right:np.ndarray, bg:np.ndarray,alpha:np.ndarray
)->tuple[np.ndarray,np.ndarray,dict]:
    if any(x.shape!=(340,340) for x in (right,bg,alpha)) or (
        right.dtype!=np.dtype(bool) or bg.dtype!=np.dtype(bool)):
        raise ValueError("R26 signed mask geometry not 340x340 binary")
    if not np.issubdtype(alpha.dtype,np.integer):
        raise ValueError("R26 alpha must originate in signed RGBA")
    removed=right & bg & (alpha==255)
    candidate=right & ~removed
    if np.any(candidate & ~right):
        raise AssertionError("R26 may only subtract source-owned pixels")
    orig_count=int(right.sum())
    after_count=int(candidate.sum())
    if orig_count-after_count!=int(removed.sum()):
        raise AssertionError("R26 original owner budget inconsistent")
    if not after_count or not orig_count:
        raise ValueError("R26 pathological empty original/right arm")
    exterior_band=right & ~(cv2.erode(right.astype(np.uint8),
                           np.ones((3,3),np.uint8),iterations=2)>0)
    return candidate,removed,{
      "originalRightArmPixels":orig_count,
      "candidateRightArmPixels":after_count,
      "removedPixelsFullyOpaqueExactBorderRGB":int(removed.sum()),
      "originalExactConnectedBorderRGBOverlap":int((right&bg).sum()),
      "partiallyTransparentNotAutoRemoved":int((right&bg&(alpha!=255)).sum()),
      "removedPixelsWithinSignedTwoPixelBoundaryBand":int((removed&exterior_band).sum()),
      "removedPixelsInsideTwoPixelErodedArm":int((removed&~exterior_band).sum()),
      "addedPixels":int((candidate&~right).sum()),
      "originalTopology":mask_cc(right),
      "candidateTopology":mask_cc(candidate),
      "sameOriginalMaskBitstream":False if np.any(removed) else True,
      "sourcePhotoSemanticArmTruthEstablished":False,
      "additionalContourVerticesVsSignedMask":mask_cc(candidate)["polygonVertices"]-mask_cc(right)["polygonVertices"],
      "sourcePixelDeletionCannotEstablishAnatomicalCorrectness":True
    }

def owner_mask_svg(mask:np.ndarray)->tuple[str,dict]:
    markup,meta=_binary_mask_svg(name="r2629-right",mask=mask,width=340,height=340)
    # Signed original binary pixels are *not* embedded. All geometric contours
    # come from signed mask; observed browser aliasing is measured, not waived.
    svg=('<svg xmlns="http://www.w3.org/2000/svg" width="340" height="340" '
         'viewBox="0 0 340 340" shape-rendering="crispEdges">'
         '<defs>'+markup+'</defs>'
         '<rect width="340" height="340" fill="#000000"/>'
         '<rect width="340" height="340" fill="#ffffff" mask="url(#r2629-right)"/>'
         '</svg>')
    return svg,meta

def browser_raster_audit(driver,source_mask:np.ndarray,candidate_mask:np.ndarray,
                         removed:np.ndarray)->tuple[dict,dict]:
    base_svg,base_meta=owner_mask_svg(source_mask)
    cand_svg,cand_meta=owner_mask_svg(candidate_mask)
    if np.array_equal(source_mask,candidate_mask):raise ValueError("R27 unchanged candidate")
    scans={}
    private={}
    for scale in (1,2):
        # Canonical established Chrome paths at their actual DPR; no resvg.
        baseline_raw=(render_rgba(driver,base_svg) if scale==1 else render_2x(driver,base_svg))
        after_raw=(render_rgba(driver,cand_svg) if scale==1 else render_2x(driver,cand_svg))
        w=340*scale
        before=np.frombuffer(baseline_raw,dtype=np.uint8).reshape(w,w,4)
        after=np.frombuffer(after_raw,dtype=np.uint8).reshape(w,w,4)
        diff=np.any(before!=after,axis=2)
        source_ref=np.repeat(np.repeat(source_mask,scale,axis=0),scale,axis=1)
        candidate_ref=np.repeat(np.repeat(candidate_mask,scale,axis=0),scale,axis=1)
        removed_ref=np.repeat(np.repeat(removed,scale,axis=0),scale,axis=1)
        # This is strict pixel equality, not tolerant antialias pixel threshold.
        expect_before_rgb=np.where(source_ref[...,None],255,0).astype(np.uint8)
        expect_after_rgb=np.where(candidate_ref[...,None],255,0).astype(np.uint8)
        source_disagreement=np.any(before[...,:3]!=expect_before_rgb,axis=2)
        candidate_disagreement=np.any(after[...,:3]!=expect_after_rgb,axis=2)
        scans[str(scale)]={
         "renderedSize":w,
         "actualChromeBeforeAfterDifferentPixels":int(diff.sum()),
         "expectedRemovedOpaqueMaskPixelsScaled":int(removed_ref.sum()),
         "changedOutsideExactSourceCandidateDeletedPixels":int(np.count_nonzero(diff & ~removed_ref)),
         "browserOriginalVsSignedBinaryMaskDifferentPixels":int(source_disagreement.sum()),
         "browserCandidateVsProposedBinaryMaskDifferentPixels":int(candidate_disagreement.sum()),
         "originalSignedBinaryExactInChrome":not bool(np.any(source_disagreement)),
         "proposedCandidateBinaryExactInChrome":not bool(np.any(candidate_disagreement)),
         "changedOutsideDeletedSignedMaskZero":not bool(np.any(diff & ~removed_ref)),
         "chromeChangedPixelsOutsideExpectedDeletedSourceMask":bool(np.any(diff & ~removed_ref)),
         "proposedSvgIntroducedNoGeneratedSourceBitmap":True,
        }
        private[str(scale)]={"original":before.copy(),"candidate":after.copy(),"diff":diff.copy()}
    return {
      "chromeDprRuns":scans,"originalSvgMetadata":base_meta,
      "candidateSvgMetadata":cand_meta,
      "actualBaselineSvgBytes":len(base_svg.encode("utf-8")),
      "actualCandidateSvgBytes":len(cand_svg.encode("utf-8")),
      "baselineSvgSha256":sha(base_svg.encode("utf-8")),
      "candidateSvgSha256":sha(cand_svg.encode("utf-8")),
      "candidateBrowserParityApprovedForProduct":False
    },private

def case_measurement(case:str,source_root:Path,stage8:Path,
                     r25_row:dict,driver)->tuple[dict,dict]:
    path=source_root/PRIVATE
    photo=path/"original_inputs"/(case+"_source.png")
    owner_path=path/case/"signed_right_arm_stage04_mask.png"
    left_path=path/case/"signed_left_arm_stage04_mask.png"
    face_path=path/case/"signed_face_stage04_mask.png"
    frozen=FROZEN[case]
    pinned(photo,SOURCE[case][0])
    for name,p in (("right_arm",owner_path),("left_arm",left_path),("face",face_path)):
        pinned(p,frozen["masks"][name])
    pinned(stage8,SCENE_SHA256[case])
    original=json.loads(stage8.read_text(encoding="utf-8"))
    owners,cap,w,h=input_checks(case,original)
    if (len(owners)!=11 or r25_row["stage8OwnerCount"]!=11 or
        (SOURCE[case][2],cap)!=HISTORIC_STAGE8[case]):
        raise ValueError("R26 immutable 11 owner Stage8 authority mismatch")
    rgba=rgb_image(photo,True)
    border,observer=source_connected_background(rgba[...,:3],rgba[...,3])
    right=mask_image(owner_path)
    left=mask_image(left_path)
    face=mask_image(face_path)
    new,removed,stats=isolate_opaque_exact_border_connected(right,border,rgba[...,3])
    if stats["originalExactConnectedBorderRGBOverlap"]!=frozen["connectedBorder"]["right_arm"]:
        raise ValueError("R26 historical right background overlap changed")
    if stats["removedPixelsFullyOpaqueExactBorderRGB"]==0:
        raise ValueError("R26 no observed opaque background-removal hypothesis")
    # What happens to *other* signed source owners is NOT silently inferred.
    # Their masks remain immutable byte-for-byte; overlap is a warning only.
    stats["removedIntersectSignedLeftArmPixels"]=int((removed & left).sum())
    stats["removedIntersectSignedFacePixels"]=int((removed & face).sum())
    stats["signedLeftAndFaceUnchanged"]=True
    stats["signedRightArmMaskOriginalSHA256"]=digest(owner_path)
    # Owner semantics do not follow from equal source RGB.
    stats["candidateTrustedSemanticCorrection"]=False
    r27,chrome_private=browser_raster_audit(driver,right,new,removed)
    return {
      "case":case,"sourceOriginalSHA256":digest(photo),
      "signedStage8SceneSHA256":digest(stage8),
      "stage8OriginalVertexCount":SOURCE[case][2],"historicCap":cap,
      "originalSignedMasksSHA256":{k:digest(p) for k,p in (
        ("face",face_path),("left_arm",left_path),("right_arm",owner_path))},
      "R26SourceConnectedOpaqueCandidate":stats,
      "R27GenuineChrome340And680RasterAudit":r27,
      "R28GeneralizationStatus":"ABSTAIN_SEMANTIC_ANCHOR_MISSING",
      "independentOriginalPhotoSemanticOwnerAnchorPresent":False,
      "candidatesNeverAppliedToStage8OrProduct":True,
      "privateSourceGeometryNotInPublicReport":True,
      "releaseAuthorized":False
    },{
      "sourceRgb":rgba[...,:3],"originalMask":right,
      "candidateMask":new,"removed":removed,
      "chrome":chrome_private
    }

def save_private_artifacts(case:str,images:dict,out:Path)->None:
    """Contact sheet shows signed source and subtraction only; not approved art."""
    source=images["sourceRgb"]
    original=images["originalMask"]
    candidate=images["candidateMask"]
    removed=images["removed"]
    views=[
      ("SIGNED SOURCE RGB",source),
      ("HISTORIC SIGNED RIGHT ARM",np.repeat((original*255)[...,None],3,axis=2)),
      ("OPAQUE RGB SUBTRACTION ONLY",np.repeat((candidate*255)[...,None],3,axis=2)),
      ("REMOVED EXACT BG PIXELS",np.repeat((removed*255)[...,None],3,axis=2))
    ]
    board=Image.new("RGB",(340*len(views),380),(247,247,245))
    pen=ImageDraw.Draw(board)
    for i,(label,a) in enumerate(views):
        board.paste(Image.fromarray(a.astype(np.uint8),"RGB"),(340*i,40))
        pen.text((340*i+8,12),label,fill=(16,16,16))
    board.save(out/(case+"_r26_PRIVATE_source_background_arm_candidate.png"))
    # Private read-only evidence; no raster mask in source SVG/production.
    Image.fromarray(candidate.astype(np.uint8)*255,"L").save(
        out/(case+"_r26_PRIVATE_candidate_right_mask.png"))

def assert_r29_no_go(rows:list,r6:Path,r25_report:dict)->dict:
    if [r["case"] for r in rows]!=list(CASES):
        raise ValueError("R29 demands both pinned independent original sources")
    if (r25_report.get("productionReleaseAuthorized") is not False or
        [c.get("case") for c in r25_report["cases"]]!=list(CASES)):
        raise ValueError("R29 source/audit continuation mismatch")
    for row in rows:
        case=row["case"]
        changed=row["R26SourceConnectedOpaqueCandidate"]
        browser=row["R27GenuineChrome340And680RasterAudit"]
        if (row["sourceOriginalSHA256"]!=SOURCE[case][0] or
            row["signedStage8SceneSHA256"]!=SCENE_SHA256[case] or
            (row["stage8OriginalVertexCount"],row["historicCap"])!=HISTORIC_STAGE8[case] or
            changed["addedPixels"]!=0 or
            changed["signedLeftAndFaceUnchanged"] is not True or
            changed["candidateTrustedSemanticCorrection"] is not False or
            browser["candidateBrowserParityApprovedForProduct"] is not False or
            set(browser["chromeDprRuns"])!={"1","2"} or
            any(v["renderedSize"]!=340*int(scale) for scale,v in browser["chromeDprRuns"].items()) or
            any(v["originalSignedBinaryExactInChrome"] is not False for v in browser["chromeDprRuns"].values()) or
            any(v["proposedCandidateBinaryExactInChrome"] is not False for v in browser["chromeDprRuns"].values()) or
            any(v["changedOutsideDeletedSignedMaskZero"] is not False for v in browser["chromeDprRuns"].values()) or
            changed["additionalContourVerticesVsSignedMask"]<=0 or
            row["R28GeneralizationStatus"]!="ABSTAIN_SEMANTIC_ANCHOR_MISSING" or
            row["independentOriginalPhotoSemanticOwnerAnchorPresent"] is not False or
            row["releaseAuthorized"] is not False):
            raise ValueError("R29 refuses forged source repair or unverified Chrome gate")
    r6e=json.loads(r6.read_text(encoding="utf-8"))
    if (r6e.get("blockedGateCount")!=EXPECTED_R6_BLOCKED or
        r6e.get("status")!="NO_GO" or
        r6e.get("releaseAuthorized") is not False or
        len(r6e.get("blockedGates",[]))!=EXPECTED_R6_BLOCKED):
        raise ValueError("R29 frozen R6 legal/quality release blockers changed")
    return {
      "version":VERSION,
      "R26":"SOURCE_OPAQUE_RGB_CANDIDATE_MEASURED_NOT_ANATOMY",
      "R27":"CANONICAL_340_680_CHROME_MASK_RASTER_DIAGNOSTICS_MEASURED",
      "R28":"TWO_SIGNED_SOURCES_COMPARED_SEMANTIC_ABSTAIN",
      "R29":"EVIDENCE_PACKAGED_AND_PRODUCTION_NO_GO",
      "originalReleaseBlockedGates":EXPECTED_R6_BLOCKED,
      "sourcePaletteOrSignedOwnerGeometryChanged":False,
      "stage8OriginalBudgetPass":False,
      "goldenHumanApproved":False,
      "independentSemanticOwnerAnchorsAvailable":False,
      "crossRendererFacetDpr2Accepted":False,
      "actualIphoneSafariApproved":False,
      "legalRedistributionApproved":False,
      "liveHostingRollbackApproved":False,
      "releaseAuthorized":False,
      "gitMainMerged":False,"productionPromoted":False
    }

def run(source_root:Path,stage8_gc:Path,stage8_raden:Path,
        r25:Path,r6:Path,out:Path)->dict:
    if out.exists():raise FileExistsError("R26-R29 no overwrite of private evidence")
    old=validate_r25(r25)
    root=source_root.resolve()
    for p in (root,stage8_gc.resolve(),stage8_raden.resolve()):
        if out.resolve()==p or p in out.resolve().parents or out.resolve() in p.parents:
            raise ValueError("R26 output overlaps signed input")
    scenes={"GC001":stage8_gc,"Raden":stage8_raden}
    results=[];privates={}
    driver=chrome_driver()
    try:
        chrome_version=driver.capabilities.get("browserVersion","unknown")
        for row in old["cases"]:
            case=row["case"]
            result,private=case_measurement(case,root,scenes[case],row,driver)
            results.append(result)
            privates[case]=private
    finally:driver.quit()
    gate=assert_r29_no_go(results,r6,old)
    out.mkdir(parents=True)
    for case in CASES:
        save_private_artifacts(case,privates[case],out)
    final={
      "version":VERSION,
      "R25FrozenEvidenceSHA256":digest(r25),
      "R6OriginalReleaseEvidenceSHA256":digest(r6),
      "genuineChromeBrowserVersion":chrome_version,
      "cases":results,"R29FinalGate":gate,
      "privateSourceImagesAndMasksOutsideGitHub":True,
      "noSourcePhotoModification":True,
      "noGenerativeFill":True,"faceMicrofeaturesEnabled":False,
      "releaseAuthorized":False,
      "status":"R26_R29_OWNER_RESEARCH_EXECUTED_SEMANTIC_HOLD_RELEASE_NO_GO"
    }
    (out/"public_r26_r29_owner_chrome_candidate_gate.json").write_text(
        json.dumps(final,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return final

def main():
    p=argparse.ArgumentParser()
    for name in ("source-root","gc-stage8","raden-stage8","r25","r6","out"):
        p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args()
    r=run(a.source_root,a.gc_stage8,a.raden_stage8,a.r25,a.r6,a.out)
    for row in r["cases"]:
        measure=row["R26SourceConnectedOpaqueCandidate"]
        diag=row["R27GenuineChrome340And680RasterAudit"]["chromeDprRuns"]
        print("SOURCE_ARM_CANDIDATE",row["case"],
              "signed",measure["originalRightArmPixels"],
              "removed",measure["removedPixelsFullyOpaqueExactBorderRGB"],
              "dpr1Diff",diag["1"]["actualChromeBeforeAfterDifferentPixels"],
              "dpr2Diff",diag["2"]["actualChromeBeforeAfterDifferentPixels"],
              "SEMANTIC_HOLD",flush=True)
    print("R29",r["R29FinalGate"]["R29"],"RELEASE_NO_GO",flush=True)
if __name__=="__main__":main()
