#!/usr/bin/env python3
"""Verify BrowserFallback v22 Auto vs accepted v15 baseline and v21 visual guard."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

CASES=("Kyoko","Noel","Ririka")
STAFF_BROWN=(68,37,36)
TIE_GREEN=(149,211,27)
LEFT_SLEEVE=(65,66,74)

def sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def paired_metrics(facet:Image.Image,auto:Image.Image):
    a=list(facet.getdata());b=list(auto.getdata())
    assert len(a)==len(b)==340*340
    countsA=Counter(a);countsB=Counter(b)
    changed=sum(v!=u for v,u in zip(a,b))
    silhouette=sum((u==(255,255,255))!=(v==(255,255,255)) for u,v in zip(a,b))
    mass=max((abs(countsA[c]-countsB[c]) for c in countsA.keys()|countsB.keys()),default=0)
    mae=sum(sum(abs(u[k]-v[k]) for k in range(3)) for u,v in zip(a,b))/(len(a)*3)
    return {"changedPixels":changed,"changedRatio":changed/len(a),
            "silhouetteChanged":silhouette,"maxColorMassDelta":mass,"meanRGBError":mae}

def audit(folderMap:dict[str,Path],out:Path,referenceRoot:Path):
    out.mkdir(parents=True,exist_ok=True)
    rows=[]
    w,h=3*340+32,3*(340+68)+32
    canvas=Image.new("RGB",(w,h),(247,247,247))
    painter=ImageDraw.Draw(canvas)
    fontfile=Path("C:/Windows/Fonts/arial.ttf")
    font=ImageFont.truetype(str(fontfile),18) if fontfile.exists() else ImageFont.load_default()
    for i,name in enumerate(CASES):
        p=folderMap[name]
        m=json.loads((p/"metrics.json").read_text(encoding="utf-8"))
        assert m["uiVerification"]["pngPixelAndByteExactToDirectAuto"]
        assert m["uiVerification"]["profile"]=="auto"
        facet=Image.open(p/"facet.png").convert("RGB")
        auto=Image.open(p/"auto.png").convert("RGB")
        source=Image.open(p/"source.png").convert("RGB")
        reference=referenceRoot/f"browser-targeted-v21-final-{name}-20261008"
        assert sha(p/"facet.png")==sha(reference/"facet.png"),name
        assert sha(p/"near.png")==sha(reference/"near.png"),name
        md=m["auto"]["metadata"]
        assert md["qualityProfile"]=="auto"
        assert md["autoMergeStatus"] in ("accepted","fallback")
        assert 0<=md["autoMergeCandidates"]<=4
        attempts=md["autoMergeAttempts"]
        assert len(attempts)<=4
        assert all(t["donorPixels"]>0 and t["contactFraction"]>0 for t in attempts)
        assert len({(t["donorId"],t["recipientId"]) for t in attempts})==len(attempts)
        metrics=paired_metrics(facet,auto)
        if md["autoMergeStatus"]=="accepted":
            assert md["selectiveMergeApplied"]==1
            assert md["shapeCount"]==39
            assert md["vertexCount"]<m["facet"]["metadata"]["vertexCount"]
            assert md["autoMergeSelected"] is not None
            assert attempts[-1]["accepted"] is True
            assert metrics["changedPixels"]<=174
            assert metrics["silhouetteChanged"]==0
            assert metrics["maxColorMassDelta"]<=174
            assert metrics["meanRGBError"]<=.30
        else:
            assert md["selectiveMergeApplied"]==0
            assert md["shapeCount"]==40
            assert (p/"auto.png").read_bytes()==(p/"facet.png").read_bytes()
            assert md["autoMergeSelected"] is None
            assert metrics["changedPixels"]==0
        if name=="Kyoko":
            assert Counter(auto.getdata())[TIE_GREEN]==1994
            assert auto.getpixel((95,275))==LEFT_SLEEVE
            rect=(90,263,112,290)
            assert list(facet.crop(rect).getdata())==list(auto.crop(rect).getdata())
        if name=="Noel":
            rect=(0,100,60,225)
            assert list(facet.crop(rect).getdata())==list(auto.crop(rect).getdata()),"Staff changed in Auto"
            assert Counter(facet.getdata())[STAFF_BROWN]==Counter(auto.getdata())[STAFF_BROWN],"Staff brown changed in Auto"
        item={
            "case":name,
            "autoStatus":md["autoMergeStatus"],
            "regions":md["shapeCount"],
            "vertices":md["vertexCount"],
            "vertexReduction":m["facet"]["metadata"]["vertexCount"]-md["vertexCount"],
            "candidatePairs":md["autoMergeCandidates"],
            "trialCount":len(attempts),
            "selectedPair":md["autoMergeSelected"],
            "trialTrace":attempts,
            "browserRuntimeSec":m["auto"]["wallSeconds"],
            "facetRuntimeSec":m["facet"]["wallSeconds"],
            "uiMatchesDirectAuto":True,
            "sourceSHA256":sha(p/"source.png"),
            "facetSHA256":sha(p/"facet.png"),
            "autoSHA256":sha(p/"auto.png"),
            **metrics,
        }
        rows.append(item)
        y=16+i*(340+68)
        painter.text((16,y),f"{name} | {md['autoMergeStatus']} | {len(attempts)} trials | {item['vertexReduction']} fewer vertices",font=font,fill=(24,30,35))
        painter.text((16,y+23),f"changed pixels {metrics['changedPixels']} | Chrome auto {item['browserRuntimeSec']}s",font=font,fill=(49,64,75))
        for j,im in enumerate((source,facet,auto)):
            canvas.paste(im,(16+j*351,y+56))
    canvas.save(out/"v22_three_golden_comparison.png",optimize=True)
    data={"status":"EXPERIMENTAL_AUTO_RESEARCH_PRODUCTION_HOLD",
          "source":"Chrome 154 real UI route against v15 baseline",
          "notProductionReady":True,
          "cases":rows}
    (out/"v22_metrics.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with (out/"v22_metrics.csv").open("w",encoding="utf-8-sig",newline="") as f:
        cols=["case","autoStatus","regions","vertices","vertexReduction",
              "candidatePairs","trialCount","changedPixels",
              "silhouetteChanged","maxColorMassDelta","meanRGBError",
              "browserRuntimeSec","facetRuntimeSec"]
        writer=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    lines=[
        "# v22 automated geometry candidate selection: three-golden actual Chrome audit",
        "", "Status: **RESEARCH, HOLD PRODUCTION**",
        "No hardcoded donor/recipient IDs in v22 Auto selection or protection.",
        "Only one accepted same-palette merge is allowed per final output, after per-candidate raster, silhouette, exact-color-blob-thin-feature, and vertex-count gates.",
        "", "| Input | Candidate pairs | Trials | Result | Regions | Vertices saved | Changed pixels | Auto time |",
        "| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for t in rows:
        lines.append(f"| {t['case']} | {t['candidatePairs']} | {t['trialCount']} | {t['autoStatus']} | {t['regions']} | {t['vertexReduction']} | {t['changedPixels']} | {t['browserRuntimeSec']:.2f}s |")
    lines+=["",
        "The guard independently checks Kyoko representative green RGB(149,211,27), gray left-sleeve ROI, Noel's staff rectangle and exact staff brown RGB(68,37,36); Ririka is an automatic no-candidate fallback.",
        "These golden ROI checks are evidence-only and do not substitute for a general unseen-image fidelity guarantee.",
        "Original Facet and Near outputs on all golden inputs exactly match v21 SHA256.",
        "The Auto route's actual app.js response is byte-identical to direct engine invocation for each source.",
        "If shape reduction does not yield appreciable artistic geometric improvement, do not promote a faster/smaller polygon graph as a quality upgrade.",
    ]
    (out/"v22_report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    with zipfile.ZipFile(out/"v22_raw_images_and_metrics.zip","w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for filename in ("v22_metrics.json","v22_metrics.csv","v22_report.md","v22_three_golden_comparison.png"):
            z.write(out/filename,filename)
        for name,p in folderMap.items():
            for filename in ("source.png","facet.png","near.png","auto.png","metrics.json"):
                z.write(p/filename,f"{name}/{filename}")
    for row in rows:
        print("V22_GOLDEN_RESULT",row["case"],
              row["autoStatus"],"selected",row["selectedPair"],
              "candidateCount",row["candidatePairs"],
              "trials",row["trialTrace"],
              "verticesSaved",row["vertexReduction"],
              "changed",row["changedPixels"],
              "time",row["browserRuntimeSec"],flush=True)
    return data

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for c in CASES:p.add_argument("--"+c.lower(),type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--reference-root",type=Path,required=True)
    a=p.parse_args()
    audit({c:getattr(a,c.lower()) for c in CASES},a.out,a.reference_root)
