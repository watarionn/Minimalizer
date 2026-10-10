"""R22-R24 signed actual-source SVG certification and fail-closed release gate.

R22: cross-check real Chrome original-owner parity from R19 research report.
R23: byte/gzip sizes and descriptive repeat Chrome decode/draw timings on
     the authentic 11-owner composite (NOT a speedup/release gate).
R24: prevent any unsigned source-quality, Stage8 numeric or live hosting
     assertion from being laundered through R22/R23 research PASS.
All source-derived SVGs remain in PRIVATE on-PC/Drive only.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import statistics
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research_public_r12_exact_raster_prune import SOURCE,input_checks
from research_public_r17_consecutive_vertex_prune import SCENE_SHA256
from research_public_r19_lossless_svg_paths import VERSION as R19_VERSION,scene_svg,sha
from verify_public_v34_svgo_chrome import chrome_driver,mismatched_pixels,render_rgba
from verify_public_r2_chrome import render_2x

VERSION="public-r22-r24-genuine-source-serialization-and-held-release-v1"
CASE_NAMES=("GC001","Raden")

JS_BENCH=r"""
const svg=arguments[0],scale=arguments[1],rounds=arguments[2],done=arguments[arguments.length-1];
if(rounds<3||rounds>25||![1,2].includes(scale)){done({ok:false,error:"unsafe experiment"});return;}
(async()=>{
  const timings=[],w=340*scale;
  for(let j=0;j<rounds;j++){
    const start=performance.now();
    const url=URL.createObjectURL(new Blob([svg],{type:"image/svg+xml"}));
    try {
      const img=new Image();
      await new Promise((yes,no)=>{img.onload=yes;img.onerror=()=>no("decode failed");img.src=url;});
      const canvas=document.createElement("canvas");
      canvas.width=w;canvas.height=w;
      const ctx=canvas.getContext("2d",{willReadFrequently:true});
      ctx.drawImage(img,0,0,w,w);
      const pixels=ctx.getImageData(0,0,w,w).data;
      if(pixels.length!==4*w*w)throw new Error("missing RGBA");
      timings.push(performance.now()-start);
    }finally{URL.revokeObjectURL(url);}
  }
  done({ok:true,measuredMs:timings});
})().catch(e=>done({ok:false,error:String(e)}));
"""

def full_case(source:Path, report:Path, private_svg:Path)->tuple[dict,list]:
    case=source.parent.name.replace("_adaptive","")
    if case not in CASE_NAMES:
        raise ValueError("R22 only accepts frozen two-source golden authority")
    raw=source.read_bytes()
    if sha(raw)!=SCENE_SHA256[case]:
        raise ValueError("actual frozen original Stage8 SHA mismatch")
    obj=json.loads(raw)
    owners,cap,w,h=input_checks(case,obj)
    r19=json.loads(report.read_text(encoding="utf-8"))
    if (r19.get("version")!=R19_VERSION or r19.get("case")!=case or
        r19.get("inputFrozenSceneSHA256")!=sha(raw) or
        r19.get("sourceOriginalRingVerticesModified")!=0 or
        r19.get("signedStage8SourceRingVertices")!=SOURCE[case][2] or
        r19.get("historicalStage8VertexCap")!=cap or
        r19.get("ownerCount")!=11 or
        r19.get("compositeSourceStage8Chrome340DifferentPixels")!=0 or
        r19.get("compositeSourceStage8Chrome680DifferentPixels")!=0 or
        r19.get("allOriginalOwnersChrome340And680Exact") is not True or
        r19.get("sourceHistoricalStage8BudgetPassed") is not False or
        r19.get("productionPromotionAuthorized") is not False or
        len(r19.get("ownerRows",[]))!=11):
        raise ValueError("R22 requires authentic actual Chrome owner and composite R19 PASS/HOLD")
    selected=[row["selectedEncoding"] for row in r19["ownerRows"]]
    if selected!=["axis-relative"]*11:
        # A mixed set can be valid but requires independent source-specific
        # reapproval, rather than implicitly trusting a changed experiment.
        raise ValueError("unexpected frozen R19 case encoder selection")
    for primitive,row in zip(owners,r19["ownerRows"]):
        if (primitive["source_mask_owner"]!=row["owner"] or
            row["vertexCountUnchanged"] is not True or
            row["chrome340Exact"] is not True or
            row["chrome680Exact"] is not True):
            raise ValueError("R19 per-owner provenance or DPR gate changed")
    expected=scene_svg(owners,selected)
    if sha(private_svg.read_bytes())!=r19["privateCompositeSvgSHA256"] or (
        private_svg.read_text(encoding="utf-8")!=expected):
        raise ValueError("R22 saved selected full-scene SVG changed since R19 Chrome")
    original=scene_svg(owners,["literal"]*11)
    return r19,[original,expected]

def compression_size(svg:str)->dict:
    raw=svg.encode("utf-8")
    # Deterministic gzip header, no local machine timestamp or file path.
    gz=gzip.compress(raw,compresslevel=9,mtime=0)
    return {"svgBytes":len(raw),"svgSHA256":sha(raw),
            "gzip9Bytes":len(gz),"gzip9SHA256":sha(gz)}

def characterize(case:str,source:Path,r19report:Path,private_svg:Path,
                 samples:int=7)->dict:
    r19,(original,shortened)=full_case(source,r19report,private_svg)
    if samples<3 or samples>25:raise ValueError("sample count bounded")
    driver=chrome_driver()
    driver.set_script_timeout(180)
    try:
        chrome=driver.capabilities.get("browserVersion")
        original_rgba=render_rgba(driver,original)
        chosen_rgba=render_rgba(driver,shortened)
        diff340=mismatched_pixels(original_rgba,chosen_rgba)
        diff680=mismatched_pixels(render_2x(driver,original),
                                  render_2x(driver,shortened))
        if diff340 or diff680:
            raise ValueError("R22 independent real Chrome whole-owner SVG parity failed")
        metrics={}
        for scale in (1,2):
            metrics[str(scale)]={}
            for label,svg in (("literal",original),("relative",shortened)):
                result=driver.execute_async_script(JS_BENCH,svg,scale,samples)
                arr=result.get("measuredMs",[])
                if not result.get("ok") or len(arr)!=samples or not all(
                    isinstance(x,(int,float)) and 0<=x<20000 for x in arr):
                    raise ValueError("real Chrome timing trial incomplete: "+str(result))
                metrics[str(scale)][label]={
                    "sampleCount":samples,
                    "medianMs":round(statistics.median(arr),4),
                    "minMs":round(min(arr),4),
                    "maxMs":round(max(arr),4)}
    finally:
        driver.quit()
    baseline=compression_size(original)
    selected=compression_size(shortened)
    if selected["svgBytes"]>baseline["svgBytes"]:
        raise AssertionError("R23 did not save original whole owner SVG")
    return {
       "case":case,"sourceStage8SHA256":SCENE_SHA256[case],
       "sourceRingVertices":r19["signedStage8SourceRingVertices"],
       "historicVertexCap":r19["historicalStage8VertexCap"],
       "historicalStage8BudgetPass":False,
       "ownersCertified":11,
       "realChromeVersion":chrome,
       "fullOwnerSvgChangedPixels340":diff340,
       "fullOwnerSvgChangedPixels680":diff680,
       "realChromeWholeOwnerDpr1And2Exact":True,
       "vertexCountChanged":False,
       "baselineComposite":baseline,
       "compressedComposite":selected,
       "wholeSvgSavedBytes":baseline["svgBytes"]-selected["svgBytes"],
       "wholeSvgSavedPercent":round(100*(baseline["svgBytes"]-selected["svgBytes"])/baseline["svgBytes"],3),
       "wholeGzipSavedBytes":baseline["gzip9Bytes"]-selected["gzip9Bytes"],
       "wholeGzipSavedPercent":round(100*(baseline["gzip9Bytes"]-selected["gzip9Bytes"])/baseline["gzip9Bytes"],3),
       "descriptiveChromeDecodeDraw":metrics,
       "performanceRegressionOrSpeedupSignoff":False,
       "originalSourcePhotoSemanticParityPass":False,
       "humanGoldenAndIphoneSafariSigned":False,
       "releaseAuthorized":False,
       "status":"ACTUAL_CHROME_340_680_EXACT_SIZE_BENCHMARKED_RELEASE_HOLD"
    }

def gate_final(rows:list[dict],r6path:Path,r11path:Path)->dict:
    if len(rows)!=2 or [r.get("case") for r in rows]!=list(CASE_NAMES):
        raise ValueError("R24 requires two independently authenticated Stage8 original cases")
    for row in rows:
        if (row["sourceStage8SHA256"]!=SCENE_SHA256[row["case"]] or
            row.get("sourceRingVertices")!=SOURCE[row["case"]][2] or
            row.get("historicVertexCap")!=SOURCE[row["case"]][1] or
            row.get("ownersCertified")!=11 or
            row.get("realChromeWholeOwnerDpr1And2Exact") is not True or
            row.get("fullOwnerSvgChangedPixels340")!=0 or
            row.get("fullOwnerSvgChangedPixels680")!=0 or
            row.get("historicalStage8BudgetPass") is not False or
            row.get("performanceRegressionOrSpeedupSignoff") is not False or
            row.get("releaseAuthorized") is not False):
            raise ValueError("R24 forged or incomplete source SVG research evidence")
    r6=json.loads(r6path.read_bytes())
    r11=json.loads(r11path.read_bytes())
    if (r6.get("version")!="public-r6-conservative-release-admission-v1" or
        r6.get("blockedGateCount")!=8 or r6.get("status")!="NO_GO" or
        r6.get("releaseAuthorized") is not False or
        r11.get("status")!="LIVE_HOST_HTTP_AUDIT_PASS_RELEASE_NO_GO" or
        r11.get("releaseAuthorized") is not False or
        r11.get("liveResponseMeasurements",{}).get("css",{}).get("maxAgeSeconds")!=604800):
        raise ValueError("R24 requires authentic held release and real hosting evidence")
    return {
      "stage":"R24",
      "status":"SOURCE_SVG_SERIALIZATION_RESEARCH_PASS_PRODUCTION_NO_GO",
      "R22RealOriginalSource11OwnerChrome340And680Pass":True,
      "R23RealSourceFullSvgAndGzipBenchmarksComplete":True,
      "R24ResearchIntegrationGateComplete":True,
      "cases":list(CASE_NAMES),
      "unresolvedOriginalR6Gates":r6["blockedGates"],
      "blockedGateCount":r6["blockedGateCount"],
      "productionCacheMaxAgeSeconds":604800,
      "onlySerializationByteSizeImproved":True,
      "originalVertexBudgetApproved":False,
      "originalSourceSemanticsApproved":False,
      "crossEngineWholeSceneDpr2Approved":False,
      "physicalIphoneSafariApproved":False,
      "MplDistributionApproved":False,
      "realHostingRollbackApproved":False,
      "humanGoldenSigned":False,
      "productionReleaseAuthorized":False,
      "gitMainMerged":False,
      "localMinimalizerModified":False
    }

def run(inputs:dict[str,tuple[Path,Path,Path]],
        r6:Path,r11:Path,out:Path,samples:int=7)->dict:
    if out.exists():raise FileExistsError("R24 immutable evidence directory exists")
    rows=[]
    for case in CASE_NAMES:
        source,report,svg=inputs[case]
        rows.append(characterize(case,source,report,svg,samples))
    final=gate_final(rows,r6,r11)
    out.mkdir(parents=True)
    record={
      "version":VERSION,
      "r6SHA256":sha(r6.read_bytes()),"r11SHA256":sha(r11.read_bytes()),
      "r19RealBrowserReportsSHA256":{
         c:sha(inputs[c][1].read_bytes()) for c in CASE_NAMES},
      "actualSourceResults":rows,
      "finalGate":final,
      "sourceCoordinatesPublishedInThisReport":False,
      "researchOnly":True,"releaseAuthorized":False,
      "status":"R22_R24_ENGINEERING_RESEARCH_PASS_PRODUCT_NO_GO"}
    (out/"public_r22_r24_live_source_chrome_gzip_gate.json").write_text(
        json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return record

def main():
    p=argparse.ArgumentParser()
    for case in CASE_NAMES:
        for name in ("source","report","private-svg"):
            p.add_argument(f"--{case.lower()}-{name}",type=Path,required=True)
    p.add_argument("--r6",type=Path,required=True)
    p.add_argument("--r11",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--samples",type=int,default=7)
    a=p.parse_args()
    inputs={c:(getattr(a,f"{c.lower()}_source"),
               getattr(a,f"{c.lower()}_report"),
               getattr(a,f"{c.lower()}_private_svg")) for c in CASE_NAMES}
    report=run(inputs,a.r6,a.r11,a.out,a.samples)
    for r in report["actualSourceResults"]:
        print("R22_R23_ACTUAL_BROWSER",r["case"],
              r["baselineComposite"]["svgBytes"],"->",r["compressedComposite"]["svgBytes"],
              "GZIP",r["baselineComposite"]["gzip9Bytes"],"->",r["compressedComposite"]["gzip9Bytes"],
              "CHROME340_680_EXACT",flush=True)
    print("R24_RELEASE",report["finalGate"]["status"],flush=True)
if __name__=="__main__":main()
