"""R4 whole-scene native Chrome vs independent pinned resvg-WASM matrix.

SHA-verified frozen v34 SVG + v32 original PNG + archived v34 Chrome PNG.
All output is research-only. A renderer disagreement always yields HOLD.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFont
from verify_public_v34_svgo_chrome import (
    CASES, SIZE, check_sha, chrome_driver, render_rgba, mismatched_pixels, sha)
from verify_public_r2_chrome import render_2x

RESVG = Path(__file__).with_name("public_r4_resvg_full_scene.mjs")

def rgba_image(pixels: bytes, size: int) -> Image.Image:
    if len(pixels) != size*size*4:
        raise ValueError("incorrect RGBA image dimensions")
    return Image.frombytes("RGBA",(size,size),pixels)

def compare_rgba(a: bytes,b: bytes) -> dict:
    if len(a)!=len(b) or len(a)%4:
        raise ValueError("RGBA input size mismatch")
    differing=0
    alpha_differing=0
    max_delta=0
    total_channel_abs_delta=0
    left=len(a)//4
    right=0
    top=len(a)//4
    bottom=0
    size=int((len(a)//4)**0.5)
    for index in range(0,len(a),4):
        parts=[abs(a[index+j]-b[index+j]) for j in range(4)]
        if any(parts):
            differing+=1
            k=index//4
            y,x=divmod(k,size)
            left=min(left,x)
            top=min(top,y)
            right=max(right,x)
            bottom=max(bottom,y)
        if parts[3]:alpha_differing+=1
        max_delta=max(max_delta,*parts)
        total_channel_abs_delta+=sum(parts)
    return {
        "differentPixels":differing,"alphaDifferentPixels":alpha_differing,
        "maxChannelDelta":max_delta,
        "absoluteChannelDelta":total_channel_abs_delta,
        "boundingBox": [left,top,right+1,bottom+1] if differing else None,
        "exact":differing==0
    }

def run_resvg(svg:Path,output:Path,width:int,negative_control:bool=False) -> dict:
    args=["node",str(RESVG),str(svg),str(output),str(width)]
    if negative_control:
        args.extend(["full","--negative-control"])
    p=subprocess.run(args,
                     capture_output=True,text=True,check=True,timeout=90)
    result=json.loads(p.stdout.strip())
    with Image.open(output) as image:
        if image.size!=(width,width):
            raise ValueError("resvg PNG wrong dimensions")
    return result

def gallery_png(reference:Image.Image, chrome:Image.Image,
                resvg:Image.Image, out:Path, label:str) -> None:
    """Read-only imagery, no corrections to sources or renderers."""
    w=340
    if reference.size!=(w,w) or chrome.size!=(w,w) or resvg.size!=(w,w):
        raise ValueError("expected native Golden")
    panes=[reference.convert("RGBA"),chrome.convert("RGBA"),resvg.convert("RGBA")]
    base=Image.new("RGB",(w*4,405),"white")
    names=("Frozen v32","v34 Chrome","v34 resvg","Difference x8")
    for i,src in enumerate(panes):
        flat=Image.new("RGBA",(w,w),"white")
        flat.alpha_composite(src)
        base.paste(flat.convert("RGB"),(i*w,40))
    diff=ImageChops.difference(chrome,resvg).convert("RGBA")
    # Accentuated discrepancy, not a repaired or generated character image.
    diff=diff.point(lambda v:min(255,v*8)).convert("RGBA")
    black=Image.new("RGBA",(w,w),"white")
    black.alpha_composite(diff)
    base.paste(black.convert("RGB"),(3*w,40))
    pen=ImageDraw.Draw(base)
    for i,name in enumerate(names):
        pen.text((w*i+8,12),name,fill="black")
    pen.text((8,385),label+" | research only; no human Golden approval",fill="black")
    base.save(out,"PNG")

def verify(v34:Path,v32:Path,out:Path)->dict:
    if out.exists():
        raise FileExistsError("R4 output already exists: "+str(out))
    for name in CASES:
        check_sha(v34,"v34_evidence_manifest.json",v34/f"{name}_local_safe.svg")
        check_sha(v34,"v34_evidence_manifest.json",v34/f"{name}_local_safe_chrome.png")
        check_sha(v32,"v32_evidence_manifest.json",v32/f"{name}_connected_fine.png")
    out.mkdir(parents=True)
    driver=chrome_driver()
    report={
      "version":"public-r4-native-vs-resvg-full-scene-v1",
      "chromeVersion":driver.capabilities.get("browserVersion","unknown"),
      "resvgVersion":"@resvg/resvg-wasm@2.6.2",
      "cases":[],"semanticPartRegionsAvailable":False,
      "protectedArmTieStaffVisualApproved":False,
      "frozenSourceOwnerRgbVerified":False,
      "stage8OriginalBudgetPass":False,
      "iphoneSafariDprVerified":False,
      "resvgLicenseReleaseApproved":False,
      "humanGoldenApproved":False,
      "localMinimalizerTouched":False,
      "productionPromoted":False
    }
    try:
        for name in CASES:
            source=v34/f"{name}_local_safe.svg"
            svg=source.read_text("utf-8")
            v32_native=Image.open(v32/f"{name}_connected_fine.png").convert("RGBA")
            archived=Image.open(v34/f"{name}_local_safe_chrome.png").convert("RGBA")
            if v32_native.size!=SIZE or archived.size!=SIZE:
                raise ValueError("Golden size failure")
            chrome_native=rgba_image(render_rgba(driver,svg),340)
            chrome_double=rgba_image(render_2x(driver,svg),680)
            chrome_native.save(out/f"{name}_chrome_340.png")
            chrome_double.save(out/f"{name}_chrome_680.png")
            resvg_meta1=run_resvg(source,out/f"{name}_resvg_340.png",340)
            resvg_meta2=run_resvg(source,out/f"{name}_resvg_680.png",680)
            with Image.open(out/f"{name}_resvg_340.png") as im:
                resvg_native=im.convert("RGBA")
            with Image.open(out/f"{name}_resvg_680.png") as im:
                resvg_double=im.convert("RGBA")
            cross1=compare_rgba(chrome_native.tobytes(),resvg_native.tobytes())
            cross2=compare_rgba(chrome_double.tobytes(),resvg_double.tobytes())
            original=compare_rgba(v32_native.tobytes(),chrome_native.tobytes())
            archived_match=compare_rgba(archived.tobytes(),chrome_native.tobytes())
            frozen_vs_resvg=compare_rgba(v32_native.tobytes(),resvg_native.tobytes())
            injected=svg.replace("</svg>",
                 '<rect x="0" y="0" width="340" height="340" fill="#000"/></svg>')
            bad_chrome=render_rgba(driver,injected)
            # A real second renderer negative check, without risking source rewrite:
            bad_svg=out/f"{name}_r4_negative_control.svg"
            bad_svg.write_text(injected,encoding="utf-8")
            run_resvg(bad_svg,out/f"{name}_negative_resvg_340.png",340,negative_control=True)
            with Image.open(out/f"{name}_negative_resvg_340.png") as im:
                bad_resvg=im.convert("RGBA")
            bad1=mismatched_pixels(bad_chrome,v32_native.tobytes())
            bad2=mismatched_pixels(bad_resvg.tobytes(),resvg_native.tobytes())
            if bad1==0 or bad2==0:raise AssertionError("unsourced paint undetected")
            gallery_png(v32_native,chrome_native,resvg_native,
                        out/f"{name}_cross_renderer_gallery.png",name)
            row={
                "case":name,"sourceSHA256":sha(source),
                "frozenV32VsChrome340":original,
                "archivedV34VsChrome340":archived_match,
                "frozenV32VsResvg340":frozen_vs_resvg,
                "chromeVsResvg340":cross1,"chromeVsResvg680":cross2,
                "negativeChromeDifferentPixels":bad1,
                "negativeResvgDifferentPixels":bad2,
                "resvgNativePNGBytes":resvg_meta1["pngBytes"],
                "resvgDpr2PNGBytes":resvg_meta2["pngBytes"],
                "chromeNativePNG_SHA256":sha(out/f"{name}_chrome_340.png"),
                "resvgNativePNG_SHA256":sha(out/f"{name}_resvg_340.png"),
                "gallerySHA256":sha(out/f"{name}_cross_renderer_gallery.png"),
                "chromeFrozenGoldenExact":original["exact"] and archived_match["exact"],
                "fullSceneCrossRendererExact":cross1["exact"] and cross2["exact"],
                "productPartSafetyAuthorized":False,
                "productionPromoted":False
            }
            report["cases"].append(row)
            print(name,json.dumps({
              "chromeVsResvg340":cross1["differentPixels"],
              "chromeVsResvg680":cross2["differentPixels"],
              "alpha340":cross1["alphaDifferentPixels"],
              "frozenVsChrome":original["differentPixels"],
              "crossRendererExact":row["fullSceneCrossRendererExact"]}),flush=True)
    finally:
        driver.quit()
    report["chromeBaselinePass"]=len(report["cases"])==3 and all(
        row["chromeFrozenGoldenExact"] for row in report["cases"])
    report["crossRendererExact"]=len(report["cases"])==3 and all(
        row["fullSceneCrossRendererExact"] for row in report["cases"])
    report["negativeControlsPassed"]=len(report["cases"])==3 and all(
        row["negativeChromeDifferentPixels"]>0 and
        row["negativeResvgDifferentPixels"]>0 for row in report["cases"])
    report["researchEvidenceComplete"]=(
        report["chromeBaselinePass"] and report["negativeControlsPassed"] and
        len(report["cases"])==3)
    report["rendererAgreementRequiredForRelease"]=True
    report["releaseGatePass"]=False
    (out/"public_r4_matrix.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return report

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--v34",required=True,type=Path)
    parser.add_argument("--v32",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    a=parser.parse_args()
    result=verify(a.v34,a.v32,a.out)
    if not result["researchEvidenceComplete"]:
        raise SystemExit("R4 RESEARCH INCOMPLETE: source/negative Golden failed")
    if not result["crossRendererExact"]:
        print("R4_FULL_SCENE_DIAGNOSTIC_COMPLETE / CROSS_ENGINE_MISMATCH_HOLD",flush=True)
    else:
        print("R4_FULL_SCENE_DIAGNOSTIC_COMPLETE / CROSS_ENGINE_MATCH / HUMAN_GOLDEN_HOLD",flush=True)

if __name__=="__main__":main()
