"""v34 local, browser-verified contour rollback with lossless SVG path compression.

This is a research-only hybrid SVG (immutable raster Facet background, vector
source-observed garment planes). No face/arm invention, no production route.

Algorithm:
* Recode exact integer pixel borders as relative h/v line commands (lossless).
* For each promising color-path group propose a shorter approxPolyDP contour.
* Replay it against currently accepted groups in REAL CHROME. Accept only when
  ALL 340x340 RGBA bytes agree with frozen v32 PNG. Otherwise rollback only
  this color-path group to the exact contour. No tolerance or visual guessing.
* Final independent Chrome rendering must be byte-identical to v32.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import re
import time
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

V33=Path(r"G:\マイドライブ\chatGPT及びCodex用\Minimalizer\SvgContourV33_20261009")
V32=Path(r"G:\マイドライブ\chatGPT及びCodex用\Minimalizer\ConnectedSourcePlanesV32_20261009")
RGBA=(340,340,4)
TAG=re.compile(r'<path fill="#([0-9a-fA-F]{6})" fill-rule="evenodd" d="([^"]+)"/>')
SUBPATH=re.compile(r'M([^Z]+)Z')
POINT=re.compile(r'([ML])(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def parse_svg(svg):
    start=svg.find('<path fill="')
    if start<0 or not svg.endswith("</svg>"):raise ValueError("Unexpected SVG path structure")
    prefix=svg[:start]
    paths=TAG.findall(svg[start:])
    if not paths or len(paths)!=svg.count('<path fill='):
        raise ValueError("unrecognized SVG fill/path syntax")
    parsed=[]
    for rgb,attr in paths:
        loops=[]
        for sub in SUBPATH.findall(attr):
            pieces=POINT.findall("M"+sub)
            if not pieces or pieces[0][0]!="M":raise ValueError("malformed loop")
            # Existing v33 exact path is integer pixel-cell coordinates.
            if any("." in x or "." in y for _,x,y in pieces):
                raise ValueError("not exact lattice path")
            coords=[(int(x),int(y)) for _,x,y in pieces]
            if len(coords)<4:raise ValueError("degenerate original contour")
            loops.append(coords)
        if not loops:raise ValueError("empty SVG color group")
        parsed.append((rgb,loops))
    return prefix,parsed

def path_data(loop):
    """Exact positions, shorter orthogonal commands; relative diagonal only on proposals."""
    x0,y0=loop[0]
    commands=[f"M{x0} {y0}"]
    px,py=x0,y0
    for x,y in loop[1:]:
        if px==x:commands.append("v"+str(y-py))
        elif py==y:commands.append("h"+str(x-px))
        else:commands.append("l"+str(x-px)+" "+str(y-py))
        px,py=x,y
    return "".join(commands)+"Z"

def svg_group(color,loops):
    return f'<path fill="#{color}" fill-rule="evenodd" d="{" ".join(path_data(loop) for loop in loops)}"/>'

def svg_text(prefix,groups):
    return prefix+"".join(groups)+"</svg>"

def simplified_loops(loops,eps):
    changed=False
    saved=0
    proposals=[]
    for original in loops:
        if len(original)<=4:
            proposals.append(original);continue
        vec=np.array(original,dtype=np.float32).reshape(-1,1,2)
        candidate=cv2.approxPolyDP(vec,eps,True).reshape(-1,2)
        if len(candidate)>=3 and len(candidate)<len(original):
            pts=[(int(round(x)),int(round(y))) for x,y in candidate]
            if len(set(pts))>=3:
                proposals.append(pts)
                changed=True
                saved+=len(original)-len(pts)
            else:proposals.append(original)
        else:proposals.append(original)
    return proposals,saved if changed else 0

def checked_meta(name):
    manifest=json.loads((V33/"v33_evidence_manifest.json").read_text(encoding="utf-8"))
    expected={r["name"]:r["sha256"] for r in manifest["files"]}
    for suffix in ("exact.svg","exact_chrome.png"):
        p=V33/(name+"_"+suffix)
        if sha(p)!=expected[p.name]:
            raise ValueError("Input v33 SVG or Chrome raster SHA mismatch: "+p.name)
    case_meta=json.loads((V33/"v33_metrics.json").read_text(encoding="utf-8"))
    found=[r for r in case_meta["cases"] if r["case"]==name]
    if len(found)!=1 or found[0]["variants"]["exact"]["pixelsDifferentFromV32"]!=0:
        raise ValueError("v33 exact case was not verified")
    v32_manifest=json.loads((V32/"v32_evidence_manifest.json").read_text(encoding="utf-8"))
    expected32={r["name"]:r["sha256"] for r in v32_manifest["files"]}
    target=V32/(name+"_connected_fine.png")
    if sha(target)!=expected32[target.name]:
        raise ValueError("v32 target source SHA mismatch")
    return V33/(name+"_exact.svg"),target

def chrome_driver():
    from selenium import webdriver
    options=webdriver.ChromeOptions()
    for opt in ("--headless=new","--no-sandbox","--disable-gpu",
        "--disable-extensions","--disable-dev-shm-usage",
        "--window-size=900,900"):
        options.add_argument(opt)
    b=webdriver.Chrome(options=options)
    b.set_script_timeout(45)
    b.get("data:text/html,<html><body>v34 local vector rollback audit</body></html>")
    return b

JS=r"""
const svg=arguments[0],done=arguments[arguments.length-1];
const blob=new Blob([svg],{type:"image/svg+xml"});
const url=URL.createObjectURL(blob);
const img=new Image();
img.onload=()=>{
 try{
 const canvas=document.createElement("canvas");
 canvas.width=340;canvas.height=340;
 const ctx=canvas.getContext("2d",{willReadFrequently:true});
 ctx.drawImage(img,0,0);
 const rgba=ctx.getImageData(0,0,340,340);
 let binary="";
 const a=rgba.data;
 // Avoid huge serialized JSON by base64 encoding raw RGBA bytes.
 for(let i=0;i<a.length;i+=16384)
   binary+=String.fromCharCode(...a.slice(i,Math.min(i+16384,a.length)));
 done({ok:true,rgba:btoa(binary)});
 }catch(e){done({ok:false,error:String(e)})}
 finally{URL.revokeObjectURL(url);}
};
img.onerror=()=>{URL.revokeObjectURL(url);done({ok:false,error:"SVG decode"})};
img.src=url;
"""

def chrome_rgba(driver,svg):
    import base64
    response=driver.execute_async_script(JS,svg)
    if not response.get("ok"):raise RuntimeError(str(response))
    return np.frombuffer(base64.b64decode(response["rgba"]),dtype=np.uint8).reshape(RGBA)

def attempt(driver,prefix,groups,index,candidate,target):
    old=groups[index]
    groups[index]=candidate
    accepted=False
    try:
        result=chrome_rgba(driver,svg_text(prefix,groups))
        accepted=bool(np.array_equal(result,target))
    finally:
        # Browser crashes and exceptions must also restore this group.
        if not accepted:
            groups[index]=old
    return accepted

def optimize(name,out,epsilon=0.85,max_candidates=40):
    path,target_path=checked_meta(name)
    prefix,parsed=parse_svg(path.read_text(encoding="utf-8"))
    exact_groups=[svg_group(color,loops) for color,loops in parsed]
    optimized=svg_text(prefix,exact_groups)
    target=np.asarray(Image.open(target_path).convert("RGBA"),dtype=np.uint8)
    if target.shape!=RGBA:raise ValueError("Unexpected target size")
    grouped=[]
    for i,(color,loops) in enumerate(parsed):
        variants,saved=simplified_loops(loops,epsilon)
        if saved>=2:
            proposal=svg_group(color,variants)
            grouped.append((saved,i,proposal))
    grouped.sort(key=lambda x:(-x[0],x[1]))
    inspected=grouped[:max_candidates]
    accepted=[];rejected=[]
    timeline=[]
    b=chrome_driver()
    try:
        first=chrome_rgba(b,optimized)
        if not np.array_equal(first,target):
            raise RuntimeError("Lossless H/V encoder did NOT match v32 baseline")
        for predicted_saved,i,proposal in inspected:
            if proposal==exact_groups[i]:continue
            ok=attempt(b,prefix,exact_groups,i,proposal,target)
            row={"colorGroup":i,"color":"#"+parsed[i][0],
                "predictedSavedVertices":predicted_saved,
                "accepted":bool(ok)}
            timeline.append(row)
            if ok:accepted.append(row)
            else:rejected.append(row)
        finale=svg_text(prefix,exact_groups)
        pixels=chrome_rgba(b,finale)
        if not np.array_equal(pixels,target):
            # Safety: final validation fails => full rollback to lossless exact.
            finale=optimized
            accepted.clear()
            pixels=chrome_rgba(b,finale)
            if not np.array_equal(pixels,target):
                raise AssertionError("exact rollback could not recover reference")
            fallback=True
        else:fallback=False
    finally:
        b.quit()
    output=out/(name+"_local_safe.svg")
    output.write_text(finale,encoding="utf-8")
    im=Image.fromarray(pixels,"RGBA")
    png=out/(name+"_local_safe_chrome.png")
    im.save(png,optimize=True)
    expected_orig=V33/(name+"_exact.svg")
    exact_vertices=sum(len(loop) for _,loops in parsed for loop in loops)
    savings=sum(r["predictedSavedVertices"] for r in accepted)
    result={
        "case":name,"eps":epsilon,"candidateLimit":max_candidates,
        "sourceV33ExactSHA":sha(expected_orig),
        "frozenV32TargetSHA":sha(target_path),
        "chromeVersion":"Chrome, selenium" ,
        "originalSVGBytes":expected_orig.stat().st_size,
        "losslessHVSVGBytes":len(optimized.encode("utf-8")),
        "finalSVGBytes":output.stat().st_size,
        "originalVertices":exact_vertices,
        "acceptedVertexSavings":savings,
        "finalVertices":exact_vertices-savings,
        "candidateGroups":len(grouped),
        "attemptedGroups":len(timeline),
        "acceptedGroups":len(accepted),
        "rejectedGroups":len(rejected),
        "safeLocalRollback":len(rejected)>0,
        "wholeSceneFallback":fallback,
        "exactRgbaParity":True,
        "pixelsDifferentFromV32":0,
        "changesOutsideMask":0,
        "alphaChanges":0,
        "newRGBValues":0,
        "productionReady":False,
        "semanticPartAuthority":False,
        "sourceRGBOnly":True,
        "containsFrozenRasterFacet":True,
        "svgSHA256":sha(output),"chromePngSHA256":sha(png),
        "attempts":timeline
    }
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--epsilon",type=float,default=0.85)
    p.add_argument("--candidate-limit",type=int,default=40)
    args=p.parse_args()
    if args.out.exists():raise FileExistsError("no overwrite")
    args.out.mkdir(parents=True)
    report=[]
    for case in ("Kyoko","Noel","Ririka"):
        r=optimize(case,args.out,args.epsilon,args.candidate_limit)
        report.append(r)
        print("V34_SAFE",case,"svgBytes",r["originalSVGBytes"],
            r["finalSVGBytes"],"vertices",r["originalVertices"],
            r["finalVertices"],"accepted",r["acceptedGroups"],
            "rejected",r["rejectedGroups"],"pixelDiff",r["pixelsDifferentFromV32"],
            flush=True)
    meta={"status":"LOCAL_ROLLBACK_EXACT_CHROME_PARITY_PASS",
       "productionPromoted":False,"rendererModified":False,
       "sourceOnlyNoGeneration":True,
       "semanticPartAuthority":False,"cases":report}
    (args.out/"v34_metrics.json").write_text(
        json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("V34_ALL_CASES_DONE",len(report),flush=True)

if __name__=="__main__":main()
