#!/usr/bin/env python3
"""Audit actual Chrome 154 Group/Frozen v24 by source RGB, protected details and visual QA."""
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
TIE=(149,211,27)
SLEEVE=(65,66,74)
STAFF=(68,37,36)

def sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def compare(a:Image.Image,b:Image.Image)->dict:
    xs=list(a.getdata())
    ys=list(b.getdata())
    assert a.size==b.size==(340,340)
    d1,d2=Counter(xs),Counter(ys)
    return {
        "changedPixels":sum(x!=y for x,y in zip(xs,ys)),
        "silhouetteChanged":sum((x==(255,255,255))!=(y==(255,255,255)) for x,y in zip(xs,ys)),
        "maxColorMass":max(abs(d1[c]-d2[c]) for c in d1.keys()|d2.keys()),
        "rgbMAE":sum(sum(abs(x[i]-y[i]) for i in range(3)) for x,y in zip(xs,ys))/(len(xs)*3)
    }

def source_error(original:Image.Image,image:Image.Image)->dict:
    a=list(original.getdata())
    b=list(image.getdata())
    return {
        "mae":sum(sum(abs(x[i]-y[i]) for i in range(3)) for x,y in zip(a,b))/(len(a)*3),
        "squared":sum(sum((x[i]-y[i])**2 for i in range(3)) for x,y in zip(a,b))
    }

def audit(folders:dict[str,Path],out:Path,reference_zip:Path):
    out.mkdir(parents=True,exist_ok=True)
    rows=[]
    thumb=340
    label=60
    pad=10
    montage=Image.new("RGB",(4*thumb+5*pad,len(CASES)*(thumb+label+pad)+pad),(248,248,248))
    draw=ImageDraw.Draw(montage)
    fontfile=Path("C:/Windows/Fonts/arial.ttf")
    font=ImageFont.truetype(str(fontfile),17) if fontfile.exists() else ImageFont.load_default()
    with zipfile.ZipFile(reference_zip) as frozen:
        for n,name in enumerate(CASES):
            folder=folders[name]
            info=json.loads((folder/"metrics.json").read_text(encoding="utf-8"))
            assert info["uiVerification"]["profile"]=="group" and info["uiVerification"]["pngPixelAndByteExactToDirectColor"]
            for mode in ("facet","near","color"):
                assert frozen.read(f"{name}/{mode}.png")==(folder/f"{mode}.png").read_bytes(),(name,mode)
            source=Image.open(folder/"source.png").convert("RGB")
            facet=Image.open(folder/"facet.png").convert("RGB")
            group=Image.open(folder/"group.png").convert("RGB")
            color=Image.open(folder/"color.png").convert("RGB")
            delta=compare(facet,group)
            before=source_error(source,facet)
            after=source_error(source,group)
            md=info["group"]["metadata"]
            fm=info["facet"]["metadata"]
            gate=md["groupPlaneQualityGate"]
            assert gate=="pass" or gate.startswith("rejected:"),gate
            assert md["shapeCount"]==fm["shapeCount"]==40
            assert delta["silhouetteChanged"]==0,(name,"silhouette")
            assert delta["maxColorMass"]<=round(340*340*0.012),(name,"mass")
            assert delta["rgbMAE"]<=1.65,(name,"MAE")
            if gate=="pass":
                assert md["groupPlaneMovedPixels"]>=4
                assert md["groupPlaneSourceErrorReduction"]>0
                assert md["groupPlaneRenderChangedPixels"]==delta["changedPixels"]
                assert md["groupPlaneRenderSourceImprovement"]>0
                assert after["squared"]<before["squared"],(name,"render source")
            else:
                assert (folder/"group.png").read_bytes()==(folder/"facet.png").read_bytes()
            if name=="Kyoko":
                # The green tie pixel mass and left-sleeve segment must not drift.
                assert Counter(facet.getdata())[TIE]==Counter(group.getdata())[TIE]==1994,(name,"tie")
                assert facet.getpixel((95,275))==group.getpixel((95,275))==SLEEVE
                assert list(facet.crop((90,263,112,290)).getdata())==list(group.crop((90,263,112,290)).getdata()),(name,"sleeve")
            if name=="Noel":
                assert Counter(facet.getdata())[STAFF]==Counter(group.getdata())[STAFF],(name,"staff")
                assert list(facet.crop((0,100,60,225)).getdata())==list(group.crop((0,100,60,225)).getdata()),(name,"staff ROI")
            row={
                "name":name,"gate":gate,
                "candidates":md["groupPlaneCandidates"],
                "movedPixels":md["groupPlaneMovedPixels"],
                "sourceGain":md["groupPlaneSourceErrorReduction"],
                "renderSourceGain":md["groupPlaneRenderSourceImprovement"],
                "renderChangedPixels":delta["changedPixels"],
                "regions":md["shapeCount"],
                "verticesFacet":fm["vertexCount"],
                "verticesGroup":md["vertexCount"],
                "vertexDelta":md["vertexCount"]-fm["vertexCount"],
                "facetSeconds":info["facet"]["wallSeconds"],
                "groupSeconds":info["group"]["wallSeconds"],
                "sourceMAEFacet":before["mae"],
                "sourceMAEGroup":after["mae"],
                "sourceSquaredFacet":before["squared"],
                "sourceSquaredGroup":after["squared"],
                "minRegionIoU":md["contourMinRegionIoU"],
                "sourceSHA256":sha(folder/"source.png"),
                "facetSHA256":sha(folder/"facet.png"),
                "groupSHA256":sha(folder/"group.png"),
                **delta
            }
            rows.append(row)
            yy=pad+n*(thumb+label+pad)
            draw.text((pad,yy),f"{name} {gate} / {delta['changedPixels']}px changed / group {row['groupSeconds']:.2f}s",
                fill=(20,30,45),font=font)
            draw.text((pad,yy+24),f"Facet {row['verticesFacet']} vertices, Group {row['verticesGroup']} / source MAE {before['mae']:.2f} -> {after['mae']:.2f}",
                fill=(60,60,60),font=font)
            for col,img in enumerate((source,facet,color,group)):
                xx=pad+col*(thumb+pad)
                montage.paste(img,(xx,yy+label))
            print("V25_AUDIT",name,gate,"source moves",row["movedPixels"],"render changed",
                row["renderChangedPixels"],"vertex delta",row["vertexDelta"],
                "source MAE",round(before["mae"],5),round(after["mae"],5),
                "silhouette",row["silhouetteChanged"],flush=True)
    draw.text((12,0),"",fill=(0,0,0))
    montage.save(out/"v25_source_facet_color_group_comparison.png",optimize=True)
    payload={"status":"RESEARCH_HOLD_PENDING_VISUAL_GAIN",
        "exactFrozenV24":True,"appUiGroupByteExact":True,
        "caseCount":len(rows),"cases":rows}
    (out/"v25_metrics.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with (out/"v25_metrics.csv").open("w",newline="",encoding="utf-8-sig") as fp:
        cols=["name","gate","candidates","movedPixels","renderChangedPixels",
            "sourceMAEFacet","sourceMAEGroup","vertexDelta","silhouetteChanged",
            "maxColorMass","rgbMAE","facetSeconds","groupSeconds"]
        w=csv.DictWriter(fp,cols,extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    lines=["# BrowserFallback v25 connected source-color groups","",
        "Status: **RESEARCH HOLD / NOT PRODUCTION**. Original 340x340 source, actual Chrome 154 and app.js group route.",
        "V24 facet, near and color PNGs are individually byte-identical to frozen evidence archive.",
        "This is not semantic arm/garment recognition: source RGB alone supplies only material evidence.",
        "No added colors, no image generation, no eyes, nose or mouth.",
        "",
        "| Case | Gate | Source group moves | Render changed px | Vertices delta | Source MAE Facet to Group | Time Facet/Group |",
        "|---|---|---:|---:|---:|---|---|"]
    for r in rows:
        lines.append(f"| {r['name']} | {r['gate']} | {r['movedPixels']} | {r['renderChangedPixels']} | {r['vertexDelta']:+d} | {r['sourceMAEFacet']:.5f} to {r['sourceMAEGroup']:.5f} | {r['facetSeconds']:.2f}s / {r['groupSeconds']:.2f}s |")
    lines+=["","**Visual promotion remains HOLD** until human source-vs-output visual review demonstrates perceptibly improved garment/arm boundaries. No release is claimed from passing test metrics alone.",""]
    (out/"v25_report.md").write_text("\n".join(lines),encoding="utf-8")
    with zipfile.ZipFile(out/"v25_raw_images_metrics.zip","w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for item in ("v25_metrics.json","v25_metrics.csv","v25_report.md","v25_source_facet_color_group_comparison.png"):
            z.write(out/item,item)
        for name,folder in folders.items():
            for item in ("source.png","facet.png","near.png","color.png","group.png","metrics.json"):
                z.write(folder/item,f"{name}/{item}")
    return payload

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for name in CASES:
        p.add_argument("--"+name.lower(),required=True,type=Path)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--reference-zip",type=Path,required=True)
    x=p.parse_args()
    audit({name:getattr(x,name.lower()) for name in CASES},x.out,x.reference_zip)
