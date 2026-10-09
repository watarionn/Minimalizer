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
            negative=after.replace("</svg>",
                '<rect x="0" y="0" width="340" height="340" fill="#000"/></svg>')
            negative_diff=mismatched_pixels(render_rgba(driver,negative),v32_rgba)
            complete=(audit["totalColorGroups"]==audit["visitedGroups"]==
                      audit["fullOwnerMasksChecked"] and
                      audit["clippingRingsVisited"]>0)
            exact=(base_diff==replay_diff==native_diff==two_x_diff==0 and
                   negative_diff>0 and complete)
            row={"case":name,"totalColorGroups":audit["totalColorGroups"],
                 "visitedColorGroups":audit["visitedGroups"],
                 "ownerMasksChecked":audit["fullOwnerMasksChecked"],
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
                 "negativeControlPixels":negative_diff,
                 "sourceSHA256":sha(original_path),"candidateSHA256":sha(candidate_path),
                 "wholeColorGroupAuditComplete":complete,
                 "goldenExact":exact,
                 "geometryProductionAuthorized":False}
            report["cases"].append(row)
            print(name,json.dumps({k:row[k] for k in
                ("totalColorGroups","ownerMasksChecked","candidateGroupsProposedMaskExact",
                 "candidateSavedVerticesProposed","candidateVsV32NativePixelDiff",
                 "candidateVsOriginal2xPixelDiff","goldenExact")}),flush=True)
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
