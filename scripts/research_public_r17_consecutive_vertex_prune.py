"""R17 source-locked Stage8 multi-vertex span pruning research, NON-PROMOTING.

Unlike R12's all-or-nothing approxPolyDP this tests consecutive existing points
(one through twelve) in isolation and accepts an edit only if the ENTIRE owner's
official OpenCV raster is pixel-identical to the immutable baseline. The image,
color, role, primitive list, original immutable Stage8 reports remain unchanged.
PRIVATE candidate geometry must never be committed to public GitHub.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from minimalizer_zerobase.composition.semantic import rasterize_primitive_candidate
from minimalizer_zerobase.reviewed_sa10.source_exact_vector_replay import _vertex_budget
from research_public_r12_exact_raster_prune import SOURCE, input_checks, sync

VERSION="public-r17-private-source-bound-consecutive-vertex-reduction-v1"
SCENE_SHA256={
  "GC001":"7eed624b31c9a117b6d7e6e5fe9788067f00b3fc3e8889fd250c14adaaac8f08",
  "Raden":"be6001f3607466617a4c2db92cdc92ad81296a403cdeeef009ac0628dc149b5f",
}
SPANS=tuple(range(1,13))
MODES=("forward","reverse")

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def mask_bytes(mask:np.ndarray)->bytes:
    return np.asarray(mask,dtype=np.uint8).tobytes()

def masks(owners:list[dict],width:int,height:int)->dict[str,bytes]:
    return {p["source_mask_owner"]:mask_bytes(
        rasterize_primitive_candidate(p,width=width,height=height)) for p in owners}

def prune_one(original:dict,reference:dict[str,bytes],width:int,height:int,
              direction:str,max_passes:int=4)->tuple[dict,dict]:
    if direction not in MODES or not (1<=max_passes<=6):
        raise ValueError("unrecognized deterministic pruning strategy")
    item=copy.deepcopy(original)
    prims=item["primitives_back_to_front"]
    tested=0
    accepted={str(n):0 for n in SPANS}
    iterations=0
    for _ in range(max_passes):
        iterations+=1
        removed=0
        for span in SPANS:
            for primitive in prims:
                expected=reference[primitive["source_mask_owner"]]
                for ring in primitive["parameters"]["rings"]:
                    points=ring["points"]
                    if len(points)<span+3:continue
                    cursor=0 if direction=="forward" else len(points)-span
                    while (cursor+span<=len(points) if direction=="forward"
                           else cursor>=0) and len(points)>=span+3:
                        proposed=points[:cursor]+points[cursor+span:]
                        ring["points"]=proposed
                        tested+=1
                        observed=mask_bytes(
                            rasterize_primitive_candidate(primitive,width=width,height=height))
                        if observed==expected:
                            points=proposed
                            accepted[str(span)]+=span
                            removed+=span
                            if direction=="reverse":
                                cursor=min(cursor-1,len(points)-span)
                        else:
                            ring["points"]=points
                            cursor=cursor+1 if direction=="forward" else cursor-1
                    ring["points"]=points
        if removed==0:break
    for primitive in prims:sync(primitive)
    after=masks(prims,width,height)
    if after!=reference:
        raise AssertionError("R17 pixel/owner protection invariant failed")
    return item,{"direction":direction,"passes":iterations,"trialEdits":tested,
                 "verticesRemovedPerSpan":accepted,
                 "finalRingVertices":_vertex_budget(prims)["ring_vertices"],
                 "ownerRasterByteExact":True}

def run(case:str,scene:Path,out:Path)->dict:
    if case not in SOURCE:raise ValueError("R17 source identity absent")
    if out.exists():raise FileExistsError("no overwrite of private candidate")
    raw=scene.read_bytes()
    if sha(raw)!=SCENE_SHA256[case]:
        raise ValueError("R17 exact frozen scene SHA-256 mismatch")
    payload=json.loads(raw)
    original,cap,width,height=input_checks(case,payload)
    original_count=_vertex_budget(original)["ring_vertices"]
    baseline=masks(original,width,height)
    if len(baseline)!=11:raise ValueError("source owners collapsed")
    trials=[]
    results=[]
    for direction in MODES:
        new,details=prune_one(payload,baseline,width,height,direction)
        trials.append(details)
        results.append(new)
    best_index=min(range(len(trials)),key=lambda i:
                   (trials[i]["finalRingVertices"],i))
    chosen=results[best_index]
    selected=trials[best_index]
    unchanged=(masks(chosen["primitives_back_to_front"],width,height)==baseline)
    if not unchanged:raise AssertionError("owner mask changed after best-selection")
    if len(chosen["primitives_back_to_front"])!=11:raise AssertionError("owner count changed")
    for orig,new in zip(original,chosen["primitives_back_to_front"]):
        for key in ("primitive_id","source_mask_owner","composition_part",
                    "palette_color_rgb","structural_support_only","primitive_type"):
            if orig.get(key)!=new.get(key):
                raise AssertionError("source owner, paint, pose or face changed")
        if len(orig["parameters"]["rings"])!=len(new["parameters"]["rings"]):
            raise AssertionError("source contour rings created or removed")
        for a,b in zip(orig["parameters"]["rings"],new["parameters"]["rings"]):
            if a["depth"]!=b["depth"] or a["role"]!=b["role"]:
                raise AssertionError("hole/outer contour semantics changed")
            # Every retained point must be an original forward subsequence.
            index=0
            for point in b["points"]:
                while index<len(a["points"]) and a["points"][index]!=point:
                    index+=1
                if index==len(a["points"]):raise AssertionError("new invented vertex")
                index+=1
    compact=_vertex_budget(chosen["primitives_back_to_front"])["ring_vertices"]
    if compact>original_count or compact!=selected["finalRingVertices"]:
        raise AssertionError("unreconciled original Stage8 vertex budget")
    chosen["research_only"]=True
    chosen["production_authorized"]=False
    out.mkdir(parents=True)
    private=out/(case+"_r17_PRIVATE_candidate_scene.json")
    private.write_text(json.dumps(chosen,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    report={
        "version":VERSION,"case":case,
        "frozenSourceSceneSHA256":sha(raw),
        "signedOriginalImageSHA256":SOURCE[case][0],
        "baselineOwnerMaskSHA256":{k:sha(v) for k,v in sorted(baseline.items())},
        "original11SourceOwnerRasterPreservedByteExact":unchanged,
        "sourcePaletteAndProvenanceLabelsUnchanged":True,
        "unchangedOriginalContourRingCountsAndRoles":True,
        "onlyRetainedPreviouslyExistingVertices":True,
        "sourceOriginalStage8RingVerticesHistoric":original_count,
        "frozenSourceOriginalStage8BudgetCap":cap,
        "historicalStage8InputWithinCap":original_count<=cap,
        "bestExperimentalRingVertices":compact,
        "safeVertexReduction":original_count-compact,
        "researchCandidateWithinOriginalNumericCap":compact<=cap,
        "candidateBudgetGap":max(0,compact-cap),
        "strategySelected":selected["direction"],
        "independentSearchStrategies":trials,
        "isolatedOpenCvRasterComparedToFrozenAdaptiveCandidate":True,
        "chromiumSvgRasterParityApproved":False,
        "sourcePhotoSemanticOwnershipUserApproved":False,
        "humanArtisticGoldenApproved":False,
        "faceDetailsEnabled":False,
        "newColorsCreated":False,"newPrimitiveCreated":False,
        "policyExceptionRequested":False,
        "productionReleaseAuthorized":False,"mainMerged":False,
        "status":"RASTER_EXACT_VERTEX_REDUCTION_VERIFIED_RELEASE_HOLD",
        "privateCandidateSHA256":sha(private.read_bytes()),
    }
    (out/(case+"_r17_coordinate_free_audit.json")).write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--case",choices=tuple(SOURCE),required=True)
    p.add_argument("--input-scene",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    r=run(args.case,args.input_scene,args.out)
    print("R17_REAL_STAGE8_CONSECUTIVE_VERTICES",r["case"],
          r["sourceOriginalStage8RingVerticesHistoric"],"->",
          r["bestExperimentalRingVertices"],"saved",r["safeVertexReduction"],
          "ownerMaskExact",r["original11SourceOwnerRasterPreservedByteExact"],
          "originalBudgetGap",r["candidateBudgetGap"],"RELEASE_HOLD",flush=True)

if __name__=="__main__":main()
