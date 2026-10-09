"""MinimalizerPublic R2: frozen v34 full-group geometry observer and independent Chrome gate.

Research-only, no production promotion. SHA-verified v34 SVG & v32 Golden.
Runs genuine vendored JS geometry libraries, then checks whole-scene Chrome RGBA
at native and double resolution. The original output stays immutable.
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
from pathlib import Path
from PIL import Image
from verify_public_v34_svgo_chrome import (CASES, check_sha, chrome_driver, render_rgba,
                                          mismatched_pixels, sha, SIZE)

NODE = Path(__file__).with_name("public_r2_owner_geometry.cjs")
JS_2X = r"""
const svg=arguments[0],done=arguments[arguments.length-1];
const url=URL.createObjectURL(new Blob([svg],{type:'image/svg+xml'}));
const img=new Image();
img.onload=()=>{try{
 const canvas=document.createElement('canvas');canvas.width=680;canvas.height=680;
 const ctx=canvas.getContext('2d',{willReadFrequently:true});
 if(!ctx)throw Error('missing canvas');ctx.drawImage(img,0,0,680,680);
 const data=ctx.getImageData(0,0,680,680).data;
 let str='';for(let k=0;k<data.length;k+=16384)
   str+=String.fromCharCode(...data.slice(k,Math.min(k+16384,data.length)));
 done({ok:true,rgba:btoa(str)});
 }catch(err){done({ok:false,error:String(err)});}finally{URL.revokeObjectURL(url);}};
img.onerror=()=>{URL.revokeObjectURL(url);done({ok:false,error:'SVG decode failed'});};
img.src=url;
"""
def render_2x(driver, source):
    import base64
    result = driver.execute_async_script(JS_2X, source)
    if not result.get("ok"):
        raise RuntimeError("Chrome 2x decode error: "+str(result))
    rgba=base64.b64decode(result["rgba"],validate=True)
    if len(rgba)!=680*680*4:raise RuntimeError("incorrect Chrome 2x channels")
    return rgba


PATH_RE = re.compile(r'<path fill="#([0-9a-fA-F]{6})" fill-rule="evenodd" d="[^"]+"/>')

def rollback_checked_candidates(original_svg, proposed_svg, groups, reference_native,
                                reference_2x, native_render, double_render):
    """Only commit a color-group trial if both real Chrome grids are exact."""
    original=list(PATH_RE.finditer(original_svg))
    proposed=list(PATH_RE.finditer(proposed_svg))
    if len(original)!=len(proposed) or len(original)!=len(groups):
        raise ValueError("R2 path count altered")
    if not original or not proposed:
        raise ValueError("empty group scene")
    head=original_svg[:original[0].start()]
    tail=original_svg[original[-1].end():]
    if proposed_svg[:proposed[0].start()]!=head or proposed_svg[proposed[-1].end():]!=tail:
        raise ValueError("source-image prefix or SVG tail altered")
    approved=[m.group(0) for m in original]
    proposed_parts=[m.group(0) for m in proposed]
    changed={i for i,(a,b) in enumerate(zip(approved,proposed_parts)) if a!=b}
    declared={i for i,row in enumerate(groups) if row["removedVertices"]>0}
    if changed!=declared or any(a.group(1)!=b.group(1)
        for a,b in zip(original,proposed)):
        raise ValueError("unexpected source group or RGB changed")
    accepted=[]
    rejected=[]
    for i in sorted(declared):
        trial=approved.copy()
        trial[i]=proposed_parts[i]
        trial_svg=head+"".join(trial)+tail
        diff_native=mismatched_pixels(native_render(trial_svg),reference_native)
        diff_2x=mismatched_pixels(double_render(trial_svg),reference_2x)
        result={"groupIndex":i,"removedVertices":groups[i]["removedVertices"],
                "nativeDifferentPixels":diff_native,"twoXDifferentPixels":diff_2x}
        if diff_native==0 and diff_2x==0:
            approved=trial
            accepted.append(result)
        else:
            rejected.append(result)
    safe=head+"".join(approved)+tail
    return safe,accepted,rejected

def run(v34: Path,v32: Path,out: Path):
    if out.exists():raise FileExistsError("no overwrite: "+str(out))
    for name in CASES:
        check_sha(v34,"v34_evidence_manifest.json",v34/f"{name}_local_safe.svg")
        check_sha(v34,"v34_evidence_manifest.json",v34/f"{name}_local_safe_chrome.png")
        check_sha(v32,"v32_evidence_manifest.json",v32/f"{name}_connected_fine.png")
    out.mkdir(parents=True)
    driver=chrome_driver()
    report={"version":"public-r2-full-owner-geometry-v1",
            "chromeVersion":driver.capabilities.get("browserVersion","unknown"),
            "cases":[],"localMinimalizerTouched":False,"productionPromoted":False,
            "semanticOwnerAuthorized":False,"sourceOnly":True}
    try:
        for name in CASES:
            original_path=v34/f"{name}_local_safe.svg"
            candidate_path=out/f"{name}_r2_candidate.svg"
            audit_path=out/f"{name}_r2_owner_audit.json"
            result=subprocess.run(["node",str(NODE),str(original_path),
                                   str(candidate_path),str(audit_path)],
                                  capture_output=True,text=True,check=True,timeout=150)
            audit=json.loads(audit_path.read_text(encoding="utf-8"))
            before=original_path.read_text(encoding="utf-8")
            after=candidate_path.read_text(encoding="utf-8")
            v32_rgba=Image.open(v32/f"{name}_connected_fine.png").convert("RGBA").tobytes()
            prior_rgba=Image.open(v34/f"{name}_local_safe_chrome.png").convert("RGBA").tobytes()
            if len(v32_rgba)!=SIZE[0]*SIZE[1]*4:raise RuntimeError("Golden size mismatch")
            original_rgba=render_rgba(driver,before)
            candidate_rgba=render_rgba(driver,after)
            base_diff=mismatched_pixels(original_rgba,v32_rgba)
            replay_diff=mismatched_pixels(original_rgba,prior_rgba)
            native_diff=mismatched_pixels(candidate_rgba,v32_rgba)
            two_x_diff=mismatched_pixels(render_2x(driver,before),render_2x(driver,after))
            reference_2x=render_2x(driver,before)
            safe_svg,chrome_accepted,chrome_rolled_back=rollback_checked_candidates(
                before,after,audit["groups"],v32_rgba,reference_2x,
                lambda svg:render_rgba(driver,svg),
                lambda svg:render_2x(driver,svg))
            safe_path=out/f"{name}_r2_chrome_safe.svg"
            safe_path.write_text(safe_svg,encoding="utf-8")
            safe_native_diff=mismatched_pixels(render_rgba(driver,safe_svg),v32_rgba)
            safe_2x_diff=mismatched_pixels(render_2x(driver,safe_svg),reference_2x)
            negative=safe_svg.replace("</svg>",
                '<rect x="0" y="0" width="340" height="340" fill="#000"/></svg>')
            negative_diff=mismatched_pixels(render_rgba(driver,negative),v32_rgba)
            complete=(audit["totalColorGroups"]==audit["visitedGroups"]==
                      audit["fullOwnerMasksBuilt"] and
                      audit["clippingRingsVisited"]>0 and
                      audit["candidateCoverageComplete"] and
                      audit["clippingErrors"]==0 and audit["earcutErrors"]==0)
            exact=(base_diff==replay_diff==safe_native_diff==safe_2x_diff==0 and
                   negative_diff>0 and complete)
            row={"case":name,"totalColorGroups":audit["totalColorGroups"],
                 "visitedColorGroups":audit["visitedGroups"],
                 "ownerMasksPrepared":audit["fullOwnerMasksBuilt"],
                 "candidateFullMaskComparisons":audit["candidateFullMaskComparisons"],
                 "candidateGroupsProposedMaskExact":audit["acceptedGroups"],
                 "candidateSavedVerticesProposed":audit["proposedSavedVertices"],
                 "proposalsTested":audit["proposalsTested"],
                 "proposalsRejected":audit["proposalsRejected"],
                 "candidateCoverageComplete":audit["candidateCoverageComplete"],
                 "clippingRingsVisited":audit["clippingRingsVisited"],
                 "clippingErrors":audit["clippingErrors"],
                 "earcutSingleRingDiagnostics":audit["earcutUnambiguousSingleRingGroups"],
                 "earcutErrors":audit["earcutErrors"],
                 "originalVsV32PixelDiff":base_diff,
                 "originalVsArchivedV34PixelDiff":replay_diff,
                 "candidateVsV32NativePixelDiff":native_diff,
                 "candidateVsOriginal2xPixelDiff":two_x_diff,
                 "safeVsV32NativePixelDiff":safe_native_diff,
                 "safeVsOriginal2xPixelDiff":safe_2x_diff,
                 "chromeAcceptedGroups":len(chrome_accepted),
                 "chromeRolledBackGroups":len(chrome_rolled_back),
                 "chromeAcceptedVerticesSaved":sum(v["removedVertices"] for v in chrome_accepted),
                 "chromeRejectedGroupDetails":chrome_rolled_back,
                 "safeSHA256":sha(safe_path),
                 "negativeControlPixels":negative_diff,
                 "sourceSHA256":sha(original_path),"candidateSHA256":sha(candidate_path),
                 "wholeColorGroupAuditComplete":complete,
                 "goldenExact":exact,
                 "geometryProductionAuthorized":False}
            report["cases"].append(row)
            print(name,json.dumps({k:row[k] for k in
                ("totalColorGroups","ownerMasksPrepared","candidateGroupsProposedMaskExact",
                 "candidateSavedVerticesProposed","candidateVsV32NativePixelDiff",
                 "candidateVsOriginal2xPixelDiff","chromeRolledBackGroups",\n                 "safeVsV32NativePixelDiff","safeVsOriginal2xPixelDiff","goldenExact")}),flush=True)
    finally:
        driver.quit()
    report["allGoldensExact"]=len(report["cases"])==len(CASES) and all(
        r["goldenExact"] for r in report["cases"])
    report["allColorGroupsVisited"]=len(report["cases"])==len(CASES) and all(
        r["wholeColorGroupAuditComplete"] for r in report["cases"])
    (out/"public_r2_gate.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",
                                           encoding="utf-8")
    return report

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--v34",type=Path,required=True)
    a.add_argument("--v32",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    args=a.parse_args()
    result=run(args.v34,args.v32,args.out)
    if not result["allGoldensExact"] or not result["allColorGroupsVisited"]:
        raise SystemExit("HOLD: full-color-group and Chrome exact gate failed")
    print("R2_FULL_COLOR_GROUP_CHROME_PASS / SEMANTIC_AND_PRODUCTION_HOLD",flush=True)

if __name__=="__main__":main()
