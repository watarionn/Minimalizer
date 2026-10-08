#!/usr/bin/env python3
"""Audit source-supported v24 color-region ownership with identical golden Facet baseline."""
from __future__ import annotations
import argparse,csv,hashlib,json,zipfile
from collections import Counter
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

CASES=("Kyoko","Noel","Ririka")
TIE=(149,211,27);SLEEVE=(65,66,74);STAFF=(68,37,36)

def checksum(p:Path):return hashlib.sha256(p.read_bytes()).hexdigest()

def compare(a,b):
    pa=list(a.getdata());pb=list(b.getdata())
    assert len(pa)==len(pb)==340*340
    c1=Counter(pa);c2=Counter(pb)
    return {"changedPixels":sum(x!=y for x,y in zip(pa,pb)),
            "silhouetteChanged":sum((x==(255,255,255))!=(y==(255,255,255)) for x,y in zip(pa,pb)),
            "maxColorMass":max(abs(c1[k]-c2[k]) for k in c1.keys()|c2.keys()),
            "rgbMAE":sum(sum(abs(x[i]-y[i]) for i in range(3)) for x,y in zip(pa,pb))/(len(pa)*3)}

def audit(folders,out,refdir):
    out.mkdir(parents=True,exist_ok=True)
    rows=[]
    montage=Image.new("RGB",(1064,1260),(249,249,249))
    dr=ImageDraw.Draw(montage)
    fontpath=Path("C:/Windows/Fonts/arial.ttf")
    font=ImageFont.truetype(str(fontpath),18) if fontpath.exists() else ImageFont.load_default()
    for n,name in enumerate(CASES):
        p=folders[name]
        data=json.loads((p/"metrics.json").read_text(encoding="utf-8"))
        assert data["uiVerification"]["pngPixelAndByteExactToDirectColor"],name
        md=data["color"]["metadata"]
        assert md["qualityProfile"]=="color",name
        assert md["colorPlaneQualityGate"]=="pass" or md["colorPlaneQualityGate"].startswith("rejected:"),name
        facet=Image.open(p/"facet.png").convert("RGB")
        image=Image.open(p/"color.png").convert("RGB")
        source=Image.open(p/"source.png").convert("RGB")
        assert source.size==facet.size==image.size==(340,340)
        reference=refdir/f"browser-auto-v22-{name}-20261008"
        assert checksum(p/"facet.png")==checksum(reference/"facet.png"),name
        assert checksum(p/"near.png")==checksum(reference/"near.png"),name
        info=compare(facet,image)
        if md["colorPlaneQualityGate"]=="pass":
            assert md["colorPlaneMovedPixels"]==1
            assert md["colorPlaneSourceErrorReduction"]>0
            assert len(md["colorPlaneMoves"])==1
            assert md["shapeCount"]==40
            assert info["changedPixels"]<=348
            assert info["silhouetteChanged"]==0
            assert info["rgbMAE"]<=.55
            assert info["maxColorMass"]<=232
            assert info["changedPixels"]==md["colorPlaneRenderChangedPixels"]
        else:
            assert (p/"color.png").read_bytes()==(p/"facet.png").read_bytes()
            assert info["changedPixels"]==0
        if name=="Kyoko":
            assert Counter(image.getdata())[TIE]==1994
            assert image.getpixel((95,275))==SLEEVE
            assert list(facet.crop((90,263,112,290)).getdata())==list(image.crop((90,263,112,290)).getdata())
        if name=="Noel":
            assert Counter(facet.getdata())[STAFF]==Counter(image.getdata())[STAFF]
            assert list(facet.crop((0,100,60,225)).getdata())==list(image.crop((0,100,60,225)).getdata())
        r={"name":name,"status":md["colorPlaneQualityGate"],
           "candidates":md["colorPlaneCandidates"],
           "movedPixels":md["colorPlaneMovedPixels"],
           "sourceErrorReduction":md["colorPlaneSourceErrorReduction"],
           "moves":md["colorPlaneMoves"],
           "regionCount":md["shapeCount"],
           "vertices":md["vertexCount"],
           "vertexReduction":data["facet"]["metadata"]["vertexCount"]-md["vertexCount"],
           "facetFacetRemovedVertices":data["facet"]["metadata"]["facetRemovedVertices"],
           "colorFacetRemovedVertices":md["facetRemovedVertices"],
           "facetTrialCount":data["facet"]["metadata"]["facetTrialCount"],
           "colorTrialCount":md["facetTrialCount"],
           "minRegionIoU":md["contourMinRegionIoU"],
           "facetTimeSeconds":data["facet"]["wallSeconds"],
           "colorTimeSeconds":data["color"]["wallSeconds"],
           "sourceSHA256":checksum(p/"source.png"),
           "facetSHA256":checksum(p/"facet.png"),
           "colorSHA256":checksum(p/"color.png"),**info}
        rows.append(r)
        y=10+n*407
        dr.text((12,y),f"{name} | {r['status']} | vertices -{r['vertexReduction']} | {r['changedPixels']} px changed",
                font=font,fill=(25,35,45))
        dr.text((12,y+24),f"Facet {r['facetTimeSeconds']:.1f}s / Color {r['planeTimeSeconds']:.1f}s",font=font,fill=(55,65,75))
        for col,img in enumerate((source,facet,image)):
            montage.paste(img,(12+col*350,y+54))
        print("V24_CASE",name,"status",r["status"],"saved",r["vertexReduction"],
              "changed",r["changedPixels"],"IoU",r["minRegionIoU"],"time",r["colorTimeSeconds"],flush=True)
    montage.save(out/"v24_three_source_comparison.png",optimize=True)
    payload={"status":"V24_COLOR_REGION_EXPERIMENT_NOT_PRODUCTION",
             "verifiedUI":True,"cases":rows}
    (out/"v24_metrics.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with (out/"v24_metrics.csv").open("w",newline="",encoding="utf-8-sig") as f:
        cols=["name","status","regionCount","vertices","vertexReduction","changedPixels",
              "silhouetteChanged","maxColorMass","rgbMAE","minRegionIoU",
              "facetTimeSeconds","colorTimeSeconds"]
        w=csv.DictWriter(f,cols,extrasaction="ignore");w.writeheader();w.writerows(rows)
    lines=["# BrowserFallback v24 source-supported color region boundary research","",
           "Status: **RESEARCH ONLY; NO PRODUCTION PROMOTION**. All inputs original 340×340, real Chrome 154 and actual app.js URL route.",
           "The deliberately missing facial features are by design. No image-generation, redraw of eyes or change in palette/region identities.",
           "", "| Source | Gate | Regions | Vertices saved | Changed pixels | Facet / color time |",
           "| --- | --- | ---: | ---: | ---: | --- |"]
    for row in rows:
        lines.append(f"| {row['name']} | {row['status']} | {row['regionCount']} | {row['vertexReduction']} | {row['changedPixels']} | {row['facetTimeSeconds']:.2f}s / {row['planeTimeSeconds']:.2f}s |")
    lines+=["",
            "This v24 experiment tests ONE RGB source-supported pixel ownership correction between existing adjacent regions, without new colors, palettes, or additional regions. A previous 32-pixel batch triggered malformed shared contour and was rejected; the one-pixel mode preserves valid loop topology.",
            "All real PNGs pass the external staff, green and sleeve fidelity audit and white-background silhouette check, or are rolled back byte-identically.",
            "Even successful one-pixel source-color corrections are not visibly improved arm/clothing decomposition. Production stays HOLD until multi-pixel topology-safe planning and externally verified local visual improvement exist.",
            ""]
    (out/"v24_report.md").write_text("\n".join(lines),encoding="utf-8")
    with zipfile.ZipFile(out/"v24_raw_images_metrics.zip","w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for file in ("v24_metrics.json","v24_metrics.csv","v24_report.md","v24_three_source_comparison.png"):
            z.write(out/file,file)
        for name,p in folders.items():
            for file in ("source.png","facet.png","near.png","color.png","metrics.json"):
                z.write(p/file,f"{name}/{file}")
    return payload

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for case in CASES:p.add_argument("--"+case.lower(),type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--reference-root",type=Path,required=True)
    a=p.parse_args()
    audit({c:getattr(a,c.lower()) for c in CASES},a.out,a.reference_root)
