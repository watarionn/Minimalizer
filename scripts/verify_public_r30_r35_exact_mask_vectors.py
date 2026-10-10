"""R30-R35 source-authenticated exact-run SVG research (NOT production).

R30: reject unsigned semantic-owner anchors and authenticate frozen Stage04/8.
R31: full pixel-row aligned non-generative vector rectangles from signed masks.
R32: merge equal x/width consecutive rows into taller rectangles; exact bytes.
R33: actual Chrome native + DPR2 exactness across 11 Stage8 owner masks and
     signed Stage04 face/left/right arm for GC001 and Raden, both encodings.
R34: independently replay the unapproved R26 right-arm subtraction using
     exact raster vectors and demonstrate zero browser bleed, not semantic truth.
R35: preserve Stage8 vertex budgets and original R6 product release NO-GO.

This cannot certify anatomy, source photo aesthetics, garments/tie/staff,
nor waive original primitive/vertex budgets. Faces are masks only; no features.
Only private Drive receives source-derived raster or SVG previews.
"""
from __future__ import annotations
import argparse
import copy
import gzip
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from verify_public_v34_svgo_chrome import chrome_driver,render_rgba
from verify_public_r2_chrome import render_2x
from research_public_r12_exact_raster_prune import SOURCE,input_checks
from research_public_r17_consecutive_vertex_prune import SCENE_SHA256
from verify_public_r25_source_owner_attribution import FROZEN,PRIVATE,CASES,pinned,mask_image
from minimalizer_zerobase.composition.semantic import rasterize_primitive_candidate

VERSION="public-r30-r35-true-signed-mask-run-rect-chrome-gate-v1"
ROLE_ORDER=("face","left_arm","right_arm")
MODES=("row-runs","vertical-merged")
ORIGINAL_R6_BLOCKED=8
ORIGINAL_STAGE8_CAP={"GC001":1887,"Raden":1412}

def sha(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()

def ensure_binary(mask:np.ndarray)->np.ndarray:
    if (mask.shape!=(340,340) or
        mask.dtype not in (np.dtype("bool"),np.dtype("uint8")) or
        (mask.dtype==np.dtype("uint8") and not np.isin(mask,[0,1]).all())):
        raise ValueError("signed owner source mask must be 340x340 binary")
    return mask.astype(bool)

def pixel_runs(mask:np.ndarray)->list[tuple[int,int,int,int]]:
    """Cover exact signed binary pixels using 1px-high integer aligned rects."""
    binary=ensure_binary(mask)
    out=[]
    for y,row in enumerate(binary):
        edges=np.diff(np.r_[0,row.astype(np.int8),0])
        start=np.flatnonzero(edges==1)
        stop=np.flatnonzero(edges==-1)
        if len(start)!=len(stop):raise AssertionError("unbalanced exact row runs")
        out.extend((int(x),y,int(end-x),1) for x,end in zip(start,stop))
    return out

def vertical_merge(runs:list[tuple[int,int,int,int]])->list[tuple[int,int,int,int]]:
    """Merge only identical x and width in consecutive rows.

    No bbox union, no contour approximation, no source color interpolation.
    """
    by_y={}
    for x,y,width,h in runs:
        if h!=1 or width<=0 or x<0 or y<0 or x+width>340 or y>=340:
            raise ValueError("invalid source exact-row interval")
        by_y.setdefault(y,[]).append((x,width))
    closed=[]
    active={}
    for y in range(340):
        updated={}
        row=by_y.get(y,[])
        if len(set(row))!=len(row):raise ValueError("duplicate pixel interval")
        for x,w in row:
            if (x,w) in active:
                start,height=active[(x,w)]
                updated[(x,w)]=(start,height+1)
            else:updated[(x,w)]=(y,1)
        for (x,w),(start,height) in active.items():
            if (x,w) not in updated:
                closed.append((x,start,w,height))
        active=updated
    closed.extend((x,start,w,height)
                  for (x,w),(start,height) in active.items())
    return sorted(closed,key=lambda q:(q[1],q[0],q[2],q[3]))

def rectangles_mask(rects:list[tuple[int,int,int,int]])->np.ndarray:
    reconstructed=np.zeros((340,340),dtype=bool)
    for x,y,w,h in rects:
        if x<0 or y<0 or x+w>340 or y+h>340 or w<=0 or h<=0:
            raise ValueError("candidate rectangle extends source image")
        if np.any(reconstructed[y:y+h,x:x+w]):
            raise ValueError("overlapping rectangle cover is not a partition")
        reconstructed[y:y+h,x:x+w]=True
    return reconstructed

def path_for_rectangles(rects:list[tuple[int,int,int,int]])->str:
    # Explicit closed axis-aligned integer-coordinate paths. shape-rendering
    # crispEdges is deliberate. Disjoint rectangles never require evenodd.
    return "".join(f"M{x} {y}h{w}v{h}h-{w}Z" for x,y,w,h in rects)

def exact_svg(mask:np.ndarray,mode:str)->tuple[str,dict]:
    if mode not in MODES:raise ValueError("unknown source vector encoding")
    binary=ensure_binary(mask)
    row=pixel_runs(binary)
    rectangles=row if mode=="row-runs" else vertical_merge(row)
    if not np.array_equal(rectangles_mask(rectangles),binary):
        raise AssertionError("reconstructed geometry differs from signed mask")
    path=path_for_rectangles(rectangles)
    svg=('<svg xmlns="http://www.w3.org/2000/svg" width="340" height="340" '
         'viewBox="0 0 340 340" shape-rendering="crispEdges">'
         '<rect width="340" height="340" fill="#000000"/>'
         f'<path d="{path}" fill="#ffffff"/></svg>')
    compressed=gzip.compress(svg.encode("utf-8"),compresslevel=9,mtime=0)
    return svg,{
     "maskPixels":int(binary.sum()),
     "rowRuns":len(row),"encodedRectangles":len(rectangles),
     "nominalRectangleVertexOccurrences":4*len(rectangles),
     "rawSvgBytes":len(svg.encode("utf-8")),
     "gzip9SvgBytes":len(compressed),
     "svgSHA256":sha(svg.encode("utf-8")),
     "rasterReconstructionExact":True
    }

def browser_pixels(driver,svg:str,scale:int)->np.ndarray:
    if scale not in (1,2):raise ValueError("unsupported Chrome size")
    raw=render_rgba(driver,svg) if scale==1 else render_2x(driver,svg)
    w=340*scale
    result=np.frombuffer(raw,dtype=np.uint8).reshape(w,w,4)
    if not np.all(result[...,3]==255):
        raise ValueError("background RGB must be opaque")
    return result[...,:3].copy()

def assert_chrome_exact(driver,mask:np.ndarray,mode:str)->tuple[dict,dict]:
    binary=ensure_binary(mask)
    svg,description=exact_svg(binary,mode)
    mismatches={}
    for scale in (1,2):
        got=browser_pixels(driver,svg,scale)
        expected=np.repeat(np.repeat(binary,scale,axis=0),scale,axis=1)
        rgb=np.where(expected[...,None],255,0).astype(np.uint8)
        changed=int(np.any(got!=rgb,axis=2).sum())
        mismatches[str(scale)]=changed
        if changed:raise AssertionError(
            f"R33 real Chrome source mask not exact: {mode} DPR{scale} {changed}")
    result={"encoding":mode,**description,
            "actualChrome340DifferentPixels":mismatches["1"],
            "actualChrome680DifferentPixels":mismatches["2"],
            "ChromeAndSignedMaskBothDprPixelExact":True}
    return result,{"svg":svg}

def pair_compare(driver,original:np.ndarray,candidate:np.ndarray,
                 deleted:np.ndarray,mode:str)->dict:
    base=ensure_binary(original)
    new=ensure_binary(candidate)
    removed=ensure_binary(deleted)
    if (np.any(new&~base) or
        not np.array_equal(base&~new,removed) or
        int(removed.sum())==0):
        raise ValueError("R34 no original-signature-preserving candidate")
    base_svg,_=exact_svg(base,mode)
    new_svg,_=exact_svg(new,mode)
    per_dpr={}
    for scale in (1,2):
        old_img=browser_pixels(driver,base_svg,scale)
        cand_img=browser_pixels(driver,new_svg,scale)
        got=np.any(old_img!=cand_img,axis=2)
        expected=np.repeat(np.repeat(removed,scale,axis=0),scale,axis=1)
        unapproved=int(np.count_nonzero(got&~expected))
        missed=int(np.count_nonzero(expected&~got))
        per_dpr[str(scale)]={
           "nativePixels":340*scale,
           "realChromeBeforeAfterChangedPixels":int(got.sum()),
           "exactSignedDeletedMaskPixelsScaled":int(expected.sum()),
           "extraChangedPixelsOutsideSourceDeletedMask":unapproved,
           "missedRemovedPixels":missed,
           "bitExactDeltaLimitedToDeletedPixels":unapproved==0 and missed==0
        }
        if unapproved or missed:raise AssertionError("R34 browser edit leaked")
    return {"encoding":mode,"perDpr":per_dpr,
            "signedMaskRasterDeltaExact":True,
            "candidateSemanticallyApproved":False}

def validate_r26(r26:Path,original_case:dict,case:str)->None:
    source=json.loads(r26.read_text(encoding="utf-8"))
    if (source.get("version")!="public-r26-r29-signed-right-arm-bg-candidate-and-chrome-abstain-v1" or
        source.get("releaseAuthorized") is not False or
        [x.get("case") for x in source.get("cases",[])]!=list(CASES) or
        source.get("status")!="R26_R29_OWNER_RESEARCH_EXECUTED_SEMANTIC_HOLD_RELEASE_NO_GO"):
        raise ValueError("R34 R26 source evidence missing/forged")
    row=next(x for x in source["cases"] if x["case"]==case)
    if (row["sourceOriginalSHA256"]!=SOURCE[case][0] or
        row["signedStage8SceneSHA256"]!=SCENE_SHA256[case] or
        row["R28GeneralizationStatus"]!="ABSTAIN_SEMANTIC_ANCHOR_MISSING" or
        row["R26SourceConnectedOpaqueCandidate"]["originalRightArmPixels"]!=int(original_case["right_arm"].sum()) or
        row["R26SourceConnectedOpaqueCandidate"]["candidateTrustedSemanticCorrection"] is not False):
        raise ValueError("R34 inherited R26 candidate evidence not authorized")

def classify_semantic_anchors(observation:dict)->dict:
    """No human/source-only independent anchor exists just because a mask exists."""
    if not isinstance(observation,dict) or observation.get("approved") is not False:
        raise ValueError("R30 requires explicit absence of independent semantic approval")
    return {
       "independentSourceOnlyModelSigned":False,
       "independentHumanOwnerAnnotationSigned":False,
       "photoArmMaskAnatomicalTruthEstablished":False,
       "sourcePixelOwnershipSemanticStatus":"ABSTAIN",
       "originalStage04MaskMayBeIncorrect":True
    }

def release_gate(rows:list[dict],r6:dict)->dict:
    if [x.get("case") for x in rows]!=list(CASES) or (
        r6.get("blockedGateCount")!=ORIGINAL_R6_BLOCKED or
        r6.get("status")!="NO_GO" or
        r6.get("releaseAuthorized") is not False or
        len(r6.get("blockedGates",[]))!=ORIGINAL_R6_BLOCKED):
        raise ValueError("R35 original R6 release admission missing")
    for row in rows:
        case=row["case"]
        if (row.get("frozenStage8Vertices")!=SOURCE[case][2] or
            row.get("historicOriginalStage8Cap")!=ORIGINAL_STAGE8_CAP[case] or
            row.get("sourceSemantics",{}).get("sourcePixelOwnershipSemanticStatus")!="ABSTAIN" or
            row.get("runAndMergedSignedMaskChromeAllExact") is not True or
            row.get("candidateChangeWithoutSvgSpillExact") is not True or
            row.get("ownerMaskCount")!=14 or
            row.get("approvedToChangeProduct") is not False):
            raise ValueError("R35 fabricated quality or Stage8 acceptance")
    return {
      "status":"BROWSER_BINARY_SIGNED_MASK_REPRESENTATION_PASS_PRODUCT_NO_GO",
      "R30":"SEMANTIC_ANCHOR_ABSENT_ABSTAIN",
      "R31":"EXACT_SCANLINE_SOURCE_VECTORS",
      "R32":"REVERSIBLE_VERTICAL_RECTANGLE_MERGE",
      "R33":"ACTUAL_CHROME_340_680_ALL_11_SOURCE_OWNERS_AND_STAGE04",
      "R34":"SOURCE_PIXEL_DELETION_CHROME_DELTA_EXACT_NOT_SEMANTICS",
      "R35":"EVIDENCE_AUTHENTICATED_RELEASE_NO_GO",
      "originalSourcePhotoSemanticOwnerPass":False,
      "historicStage8VertexBudgetPass":False,
      "wholePhotoGoldenHumanPass":False,
      "fullSceneChromeResvgFacetDpr2Pass":False,
      "realIphoneSafariPass":False,
      "MplLegalRedistributionApproved":False,
      "realHostingRollbackPass":False,
      "r6OriginalReleaseBlocked":ORIGINAL_R6_BLOCKED,
      "browserMaskRepresentationMayReplaceOfficialProductionStage8":False,
      "originalSignedMasksChanged":False,
      "faceMicrofeaturesGenerated":False,
      "localMinimalizerModified":False,
      "githubMainMerged":False,
      "productionReleaseAuthorized":False,
    }

def run(source_root:Path,stage8:dict[str,Path],
        r26_path:Path,r6_path:Path,
        private_candidates:dict[str,Path],out:Path)->dict:
    if out.exists():raise FileExistsError("R35 immutable output already exists")
    base=source_root.resolve()/PRIVATE
    frozen_r6=json.loads(r6_path.read_text(encoding="utf-8"))
    rows=[]
    driver=chrome_driver()
    try:
        chrome=driver.capabilities.get("browserVersion")
        for case in CASES:
            source=base/"original_inputs"/(case+"_source.png")
            pinned(source,SOURCE[case][0])
            signed=base/case
            old_masks={}
            for part in ROLE_ORDER:
                p=signed/(f"signed_{part}_stage04_mask.png")
                pinned(p,FROZEN[case]["masks"][part])
                old_masks[part]=mask_image(p)
            scene=stage8[case]
            pinned(scene,SCENE_SHA256[case])
            payload=json.loads(scene.read_text(encoding="utf-8"))
            original,cap,w,h=input_checks(case,payload)
            if len(original)!=11 or w!=340 or h!=340:
                raise ValueError("R33 original owner evidence incomplete")
            validate_r26(r26_path,old_masks,case)
            proposed=private_candidates[case]
            candidate=mask_image(proposed)
            row={"case":case,
                 "originalSourceSHA256":SOURCE[case][0],
                 "sourceStage8SceneSHA256":SCENE_SHA256[case],
                 "frozenStage8Vertices":SOURCE[case][2],
                 "historicOriginalStage8Cap":cap,
                 "sourceSemantics":classify_semantic_anchors({"approved":False}),
                 "ownerMaskCount":0,
                 "stage04Signed":{},
                 "stage8OriginalOwners":[],
                 "unapprovedR26Subtraction":{},
                 "runAndMergedSignedMaskChromeAllExact":False,
                 "candidateChangeWithoutSvgSpillExact":False,
                 "approvedToChangeProduct":False}
            stage04=[]
            for part in ROLE_ORDER:
                mask=old_masks[part]
                encoded=[]
                for mode in MODES:
                    diag,_=assert_chrome_exact(driver,mask,mode)
                    encoded.append(diag)
                stage04.append(part)
                row["stage04Signed"][part]={"originalSignedMaskPixels":int(mask.sum()),
                                            "encodings":encoded,
                                            "ownerSemanticApproved":False}
            for primitive in original:
                owner=primitive["source_mask_owner"]
                mask=rasterize_primitive_candidate(primitive,width=340,height=340)>0
                diag=[]
                for mode in MODES:
                    d,_=assert_chrome_exact(driver,mask,mode)
                    diag.append(d)
                row["stage8OriginalOwners"].append({
                  "owner":owner,"maskPixels":int(mask.sum()),
                  "existingSourceVertices":sum(len(r["points"]) for r in primitive["parameters"]["rings"]),
                  "encodings":diag,
                  "originalSourceSemanticOwnerApproved":False})
            # 3 signed Phase04 independent binary masks + 11 Stage8 owner masks.
            row["ownerMaskCount"]=len(row["stage04Signed"])+len(row["stage8OriginalOwners"])
            original_mask=old_masks["right_arm"]
            deleted=original_mask &~candidate
            for mode in MODES:
                # exact original AND exact candidate at both resolutions
                assert_chrome_exact(driver,candidate,mode)
                row["unapprovedR26Subtraction"][mode]=pair_compare(
                    driver,original_mask,candidate,deleted,mode)
            row["runAndMergedSignedMaskChromeAllExact"]=True
            row["candidateChangeWithoutSvgSpillExact"]=True
            rows.append(row)
    finally:driver.quit()
    gate=release_gate(rows,frozen_r6)
    report={"version":VERSION,
            "originalReleaseR6EvidenceSHA256":sha(r6_path.read_bytes()),
            "originalR26EvidenceSHA256":sha(r26_path.read_bytes()),
            "realChromeVersion":chrome,
            "cases":rows,
            "finalGate":gate,
            "sourceSignedStage04AndStage8Private":True,
            "inputSourcePhotosOrPrivateMasksExportedToPublicGitHub":False,
            "noProductRoutesChanged":True,
            "releaseAuthorized":False,
            "status":"R30_R35_TRUE_SOURCE_MASK_BROWSER_EXACT_SEMANTIC_HOLD"}
    out.mkdir(parents=True)
    dest=out/"public_r30_r35_signed_masks_true_browser_gate.json"
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for row in rows:
        summary=row["unapprovedR26Subtraction"]["vertical-merged"]["perDpr"]
        print("R30_R35",row["case"],
              "frozen_stage8",row["frozenStage8Vertices"],
              "Stage8_caps",row["historicOriginalStage8Cap"],
              "masks",row["ownerMaskCount"],
              "right_arm_changes340",summary["1"]["realChromeBeforeAfterChangedPixels"],
              "right_arm_changes680",summary["2"]["realChromeBeforeAfterChangedPixels"],
              "ZERO_OUTSIDE_DELETION",flush=True)
    print("R35",gate["status"],"SOURCE_SEMANTICS_HOLD",flush=True)
    return report

def main():
    p=argparse.ArgumentParser()
    for flag in ("source-root","gc-stage8","raden-stage8",
                 "gc-candidate","raden-candidate","r26","r6","out"):
        p.add_argument("--"+flag,required=True,type=Path)
    a=p.parse_args()
    scenes={"GC001":a.gc_stage8,"Raden":a.raden_stage8}
    candidates={"GC001":a.gc_candidate,"Raden":a.raden_candidate}
    run(a.source_root,scenes,a.r26,a.r6,candidates,a.out)
if __name__=="__main__":main()
