"""R18 guarded source-mask AND actual Chrome SVG 340/DPR2 candidate selection.

Research only. Opens frozen private Stage8 inputs, never imports generated imagery,
never approves a production release. R17 large pixel-exact OpenCV improvements
are used solely as proposed deleted source vertices; no new geometry.
Every accepted owner edit needs byte-exact official OpenCV owner raster AND
exact SVG Chrome raster at 340px and 680px. All unapproved edits roll back.
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
from research_public_r12_exact_raster_prune import SOURCE,input_checks,sync
from research_public_r17_consecutive_vertex_prune import SCENE_SHA256,masks,sha
from verify_public_r17_chrome_owner import svg_for_owner
from verify_public_v34_svgo_chrome import chrome_driver,render_rgba
from verify_public_r2_chrome import render_2x
from minimalizer_zerobase.reviewed_sa10.source_exact_vector_replay import _vertex_budget

VERSION="public-r18-source-opencv-chrome340-chrome680-exact-owner-gate-v1"

JS_MULTI=r"""
const baseline=arguments[0],candidates=arguments[1],
      done=arguments[arguments.length-1];
async function pixels(svg,scale) {
  const blob=new Blob([svg],{type:'image/svg+xml'});
  const url=URL.createObjectURL(blob);
  try {
    const image=new Image();
    await new Promise((yes,no)=>{
      image.onload=yes;image.onerror=()=>no(new Error('svg decode failed'));
      image.src=url;});
    const w=340*scale;
    const canvas=document.createElement('canvas');
    canvas.width=w;canvas.height=w;
    const ctx=canvas.getContext('2d',{willReadFrequently:true});
    if (!ctx)throw Error('no canvas');
    ctx.drawImage(image,0,0,w,w);
    return ctx.getImageData(0,0,w,w).data;
  } finally {URL.revokeObjectURL(url);}
}
function diff(a,b) {
 if(a.length!==b.length)throw Error('size mismatch');
 let count=0;
 for(let i=0;i<a.length;i+=4)
   if(a[i]!=b[i]||a[i+1]!=b[i+1]||a[i+2]!=b[i+2]||a[i+3]!=b[i+3])
     count++;
 return count;
}
(async()=>{
 try {
 const base340=await pixels(baseline,1),base680=await pixels(baseline,2);
 const rows=[];
 for(const svg of candidates){
   rows.push({d340:diff(base340,await pixels(svg,1)),
              d680:diff(base680,await pixels(svg,2))});
 }
 done({ok:true,rows});
 } catch(e){done({ok:false,error:String(e)});}
})();
"""

def chrome_candidates(driver,baseline:str,candidates:list[str])->list[dict]:
    if not candidates:return []
    result=driver.execute_async_script(JS_MULTI,baseline,candidates)
    if not result.get("ok") or len(result.get("rows",[]))!=len(candidates):
        raise RuntimeError("R18 actual Chrome dual-DPR gate failed: "+str(result))
    return result["rows"]

def retained_source_subsequence(old:list,new:list)->bool:
    idx=0
    for point in new:
        while idx<len(old) and old[idx]!=point:
            idx+=1
        if idx>=len(old):return False
        idx+=1
    return True

def confirm_source_and_r17(case:str,source:Path,proposed:Path,audit:Path):
    raw=source.read_bytes()
    if sha(raw)!=SCENE_SHA256[case]:raise ValueError("R18 immutable signed source SHA mismatch")
    old=json.loads(raw)
    original,cap,w,h=input_checks(case,old)
    variant=json.loads(proposed.read_text(encoding="utf-8"))
    summary=json.loads(audit.read_text(encoding="utf-8"))
    if summary.get("case")!=case or summary.get("privateCandidateSHA256")!=sha(proposed.read_bytes()) or (
        summary.get("original11SourceOwnerRasterPreservedByteExact") is not True or
        summary.get("productionReleaseAuthorized") is not False):
        raise ValueError("R18 refuses unsigned or unauthorized R17 input")
    current=variant["primitives_back_to_front"]
    if len(current)!=11:raise ValueError("missing authentic owner")
    for a,b in zip(original,current):
        if a["source_mask_owner"]!=b["source_mask_owner"] or (
            a["palette_color_rgb"]!=b["palette_color_rgb"]):
            raise ValueError("source owner color changed")
        ra=a["parameters"]["rings"];rb=b["parameters"]["rings"]
        if len(ra)!=len(rb):raise ValueError("ring count changed")
        for x,y in zip(ra,rb):
            if (x["depth"],x["role"])!=(y["depth"],y["role"]) or (
                not retained_source_subsequence(x["points"],y["points"])):
                raise ValueError("R17 invented coordinates or changed topology")
    ref=masks(original,w,h)
    if masks(current,w,h)!=ref:raise ValueError("R17 changed original OpenCV owner raster")
    return old,variant,ref,cap,w,h


def missing_original_indices(before:list,after:list)->list[int]:
    """R17 accepted points must be an ordered subsequence."""
    missing=[]
    k=0
    for i,point in enumerate(before):
        if k<len(after) and point==after[k]:
            k+=1
        else:
            missing.append(i)
    if k!=len(after):raise ValueError("unmatched R17 source point")
    return missing

def micro_candidates(part:dict,baseline:dict,r17_variant:dict,
                     reference_mask:bytes,w:int,h:int,
                     limit:int=360)->list[tuple[int,int,dict]]:
    """One-point deletions suggested by R17; OpenCV-filter then Chrome."""
    proposed=[]
    for index,(old,short) in enumerate(zip(baseline["parameters"]["rings"],
                                           r17_variant["parameters"]["rings"])):
        if old["points"]==short["points"]:continue
        missing=missing_original_indices(old["points"],short["points"])
        current=part["parameters"]["rings"][index]["points"]
        for original_index in missing:
            point=old["points"][original_index]
            if len(current)<=3:break
            try:
                j=current.index(point)
            except ValueError:
                continue
            attempt=copy.deepcopy(part)
            attempt["parameters"]["rings"][index]["points"]=current[:j]+current[j+1:]
            sync(attempt)
            if masks([attempt],w,h)[part["source_mask_owner"]]==reference_mask:
                proposed.append((index,original_index,attempt))
            if len(proposed)>=limit:return proposed
    return proposed

def evaluate(case:str,source:Path,proposed:Path,audit:Path,out:Path)->dict:
    if out.exists():raise FileExistsError("R18 refuses overwriting private research")
    original,proposed_obj,reference,cap,w,h=confirm_source_and_r17(
        case,source,proposed,audit)
    adopted=copy.deepcopy(original)
    current=adopted["primitives_back_to_front"]
    original_parts=original["primitives_back_to_front"]
    R17_parts=proposed_obj["primitives_back_to_front"]
    all_rows=[]
    browser=chrome_driver()
    browser.set_script_timeout(240)
    try:
        version=browser.capabilities.get("browserVersion")
        for src,variant,part in zip(original_parts,R17_parts,current):
            owner=src["source_mask_owner"]
            baseline=svg_for_owner(src)
            # Every changed ring is evaluated individually in Chrome.
            # Greedy addition remains rejected unless cumulative scene is exact.
            proposed_rings=[]
            for ring_idx,(old,new) in enumerate(zip(src["parameters"]["rings"],variant["parameters"]["rings"])):
                removed=len(old["points"])-len(new["points"])
                if removed<=0:continue
                trial=copy.deepcopy(part)
                trial["parameters"]["rings"][ring_idx]["points"]=copy.deepcopy(new["points"])
                sync(trial)
                proposed_rings.append((ring_idx,removed,trial))
            candidates=[svg_for_owner(item[2]) for item in proposed_rings]
            rows=chrome_candidates(browser,baseline,candidates)
            owner_summary={"owner":owner,
                           "candidateChangedRings":len(proposed_rings),
                           "acceptedRingChanges":0,
                           "acceptedRemovedVertices":0,
                           "rejectedChromeChangedRings":0,
                           "singleVertexOpenCvExactProposals":0,
                           "singleVertexChromeExactProposals":0,
                           "singleVertexCumulativeAccepted":0,
                           "testedNativeAndDpr2":True}
            # Check all proposed rings independently; then check cumulatively.
            for (ring_idx,removed,trial),result in zip(proposed_rings,rows):
                if result["d340"] or result["d680"]:
                    owner_summary["rejectedChromeChangedRings"]+=1
                    continue
                # Must still compare cumulative owner raster with frozen OpenCV.
                before=part["parameters"]["rings"][ring_idx]["points"]
                part["parameters"]["rings"][ring_idx]["points"]=copy.deepcopy(
                    trial["parameters"]["rings"][ring_idx]["points"])
                sync(part)
                if masks([part],w,h)[owner]!=reference[owner]:
                    part["parameters"]["rings"][ring_idx]["points"]=before
                    sync(part)
                    raise AssertionError("R18 Chrome candidate silently changed OpenCV owner")
                cumulative=chrome_candidates(browser,baseline,[svg_for_owner(part)])[0]
                if cumulative["d340"] or cumulative["d680"]:
                    part["parameters"]["rings"][ring_idx]["points"]=before
                    sync(part)
                    continue
                owner_summary["acceptedRingChanges"]+=1
                owner_summary["acceptedRemovedVertices"]+=removed

            # Second pass: independently probe R17-proposed single original vertices.
            # A whole-ring Chrome failure does not justify rejecting each point.
            singles=micro_candidates(part,src,variant,reference[owner],w,h)
            owner_summary["singleVertexOpenCvExactProposals"]=len(singles)
            checks=chrome_candidates(browser,baseline,
                                    [svg_for_owner(item[2]) for item in singles])
            for (ri,source_idx,trial),diff in zip(singles,checks):
                if diff["d340"] or diff["d680"]:
                    continue
                owner_summary["singleVertexChromeExactProposals"]+=1
                old_points=part["parameters"]["rings"][ri]["points"]
                candidate_points=trial["parameters"]["rings"][ri]["points"]
                # Never blindly apply stale coordinates after another edit.
                if len(old_points)!=len(candidate_points)+1 or (
                    not retained_source_subsequence(old_points,candidate_points)):
                    continue
                part["parameters"]["rings"][ri]["points"]=copy.deepcopy(candidate_points)
                sync(part)
                if masks([part],w,h)[owner]!=reference[owner]:
                    part["parameters"]["rings"][ri]["points"]=old_points
                    sync(part)
                    continue
                combined=chrome_candidates(browser,baseline,[svg_for_owner(part)])[0]
                if combined["d340"] or combined["d680"]:
                    part["parameters"]["rings"][ri]["points"]=old_points
                    sync(part)
                    continue
                owner_summary["singleVertexCumulativeAccepted"]+=1
                owner_summary["acceptedRemovedVertices"]+=1
            # Final owner validation is compulsory even if no candidate survived.
            final=chrome_candidates(browser,baseline,[svg_for_owner(part)])[0]
            if final["d340"]!=0 or final["d680"]!=0 or masks([part],w,h)[owner]!=reference[owner]:
                raise AssertionError("Chrome or OpenCV was modified in final owner")
            all_rows.append(owner_summary)
    finally:
        browser.quit()
    if masks(current,w,h)!=reference:
        raise AssertionError("final all 11 source masks differ")
    old_count=_vertex_budget(original_parts)["ring_vertices"]
    new_count=_vertex_budget(current)["ring_vertices"]
    accepted=sum(r["acceptedRemovedVertices"] for r in all_rows)
    if new_count!=old_count-accepted:
        raise AssertionError("accepted ring-count reduction bookkeeping broken")
    if any(r["testedNativeAndDpr2"] is not True for r in all_rows):
        raise AssertionError("owner not actually browser tested")
    candidate_output=out/(case+"_r18_PRIVATE_dual_exact_scene.json")
    adopted["production_authorized"]=False
    adopted["research_only"]=True
    out.mkdir(parents=True)
    candidate_output.write_text(
        json.dumps(adopted,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    record={
      "version":VERSION,"case":case,
      "sourcePrivateSceneSHA256":sha(source.read_bytes()),
      "r17RejectedCandidateSHA256":sha(proposed.read_bytes()),
      "r17ProposalNotAdoptedWithoutIndependentChrome":True,
      "actualChromeVersion":version,
      "independentSourceOwnerCount":len(all_rows),
      "sourceOriginalStage8RingVertices":old_count,
      "sourceHistoricalRingBudgetCap":cap,
      "r17ProposedRingVertices":_vertex_budget(R17_parts)["ring_vertices"],
      "dualRendererAcceptedRingVertices":new_count,
      "dualRendererRemovedVertices":old_count-new_count,
      "allElevenOriginalOpenCvOwnerRastersByteExact":True,
      "allElevenOriginalChromeOwnerSvgAt340Exact":True,
      "allElevenOriginalChromeOwnerSvgAt680Exact":True,
      "originalVertexBudgetPassed":False,
      "provisionalCandidateUnderHistoricCap":new_count<=cap,
      "humanSemanticSourceOwnershipSigned":False,
      "fullSceneGoldenApproved":False,
      "trueStage8OriginalRasterVsOfficialStage04Approved":False,
      "faceDetailsEnabled":False,
      "modifiedOriginal":False,"localMinimalizerTouched":False,
      "productionReleaseAuthorized":False,"githubMainMerged":False,
      "status":"DUAL_RENDERER_OWNER_EXACT_RESEARCH_HOLD",
      "ownerChecks":all_rows,
      "privateCandidateSHA256":sha(candidate_output.read_bytes())
    }
    (out/(case+"_r18_dual_renderer_gate.json")).write_text(
        json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return record

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--case",choices=tuple(SOURCE),required=True)
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--r17-candidate",type=Path,required=True)
    p.add_argument("--r17-audit",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    r=evaluate(a.case,a.source,a.r17_candidate,a.r17_audit,a.out)
    print("R18_GENUINE_CHROME_340_680_OWNER_EXACT",a.case,
          r["sourceOriginalStage8RingVertices"],"->",r["dualRendererAcceptedRingVertices"],
          "saved",r["dualRendererRemovedVertices"],
          "historical cap",r["sourceHistoricalRingBudgetCap"],
          "RELEASE_HOLD",flush=True)

if __name__=="__main__":main()
