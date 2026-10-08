#!/usr/bin/env python3
"""Audit v23 plane-safe three-source Chrome results with unchanged Facet references."""
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
        assert data["uiVerification"]["pngPixelAndByteExactToDirectPlane"],name
        md=data["plane"]["metadata"]
        assert md["qualityProfile"]=="plane",name
        assert md["planeQualityGate"]=="pass" or md["planeQualityGate"].startswith("rejected:"),name
        facet=Image.open(p/"facet.png").convert("RGB")
        image=Image.open(p/"plane.png").convert("RGB")
        source=Image.open(p/"source.png").convert("RGB")
        assert source.size==facet.size==image.size==(340,340)
        reference=refdir/f"browser-auto-v22-{name}-20261008"
        assert checksum(p/"facet.png")==checksum(reference/"facet.png"),name
        assert checksum(p/"near.png")==checksum(reference/"near.png"),name
        info=compare(facet,image)
        if md["planeQualityGate"]=="pass":
            assert md["planeVertexReduction"]>0
            assert md["vertexCount"]<data["facet"]["metadata"]["vertexCount"]
            assert md["shapeCount"]==40
            assert info["changedPixels"]<=925
            assert info["silhouetteChanged"]==0
            assert info["rgbMAE"]<=.85
            assert info["maxColorMass"]<=463
            assert info["changedPixels"]==md["planeQualityChangedPixels"]
        else:
            assert (p/"plane.png").read_bytes()==(p/"facet.png").read_bytes()
            assert md["planeVertexReduction"]==0
            assert info["changedPixels"]==0
        if name=="Kyoko":
            assert Counter(image.getdata())[TIE]==1994
            assert image.getpixel((95,275))==SLEEVE
            assert list(facet.crop((90,263,112,290)).getdata())==list(image.crop((90,263,112,290)).getdata())
        if name=="Noel":
            assert Counter(facet.getdata())[STAFF]==Counter(image.getdata())[STAFF]
            assert list(facet.crop((0,100,60,225)).getdata())==list(image.crop((0,100,60,225)).getdata())
        r={"name":name,"status":md["planeQualityGate"],"regionCount":md["shapeCount"],
           "vertices":md["vertexCount"],
           "vertexReduction":data["facet"]["metadata"]["vertexCount"]-md["vertexCount"],
           "facetFacetRemovedVertices":data["facet"]["metadata"]["facetRemovedVertices"],
           "planeFacetRemovedVertices":md["facetRemovedVertices"],
           "facetTrialCount":data["facet"]["metadata"]["facetTrialCount"],
           "planeTrialCount":md["facetTrialCount"],
           "minRegionIoU":md["contourMinRegionIoU"],
           "facetTimeSeconds":data["facet"]["wallSeconds"],
           "planeTimeSeconds":data["plane"]["wallSeconds"],
           "sourceSHA256":checksum(p/"source.png"),
           "facetSHA256":checksum(p/"facet.png"),
           "planeSHA256":checksum(p/"plane.png"),**info}
        rows.append(r)
        y=10+n*407
        dr.text((12,y),f"{name} | {r['status']} | vertices -{r['vertexReduction']} | {r['changedPixels']} px changed",
                font=font,fill=(25,35,45))
        dr.text((12,y+24),f"Facet {r['facetTimeSeconds']:.1f}s / Plane {r['planeTimeSeconds']:.1f}s",font=font,fill=(55,65,75))
        for col,img in enumerate((source,facet,image)):
            montage.paste(img,(12+col*350,y+54))
        print("V23_CASE",name,"status",r["status"],"saved",r["vertexReduction"],
              "changed",r["changedPixels"],"IoU",r["minRegionIoU"],"time",r["planeTimeSeconds"],flush=True)
    montage.save(out/"v23_three_source_comparison.png",optimize=True)
    payload={"status":"V23_MAJOR_PLANE_EXPERIMENT_NOT_PRODUCTION",
             "verifiedUI":True,"cases":rows}
    (out/"v23_metrics.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with (out/"v23_metrics.csv").open("w",newline="",encoding="utf-8-sig") as f:
        cols=["name","status","regionCount","vertices","vertexReduction","changedPixels",
              "silhouetteChanged","maxColorMass","rgbMAE","minRegionIoU",
              "facetTimeSeconds","planeTimeSeconds"]
        w=csv.DictWriter(f,cols,extrasaction="ignore");w.writeheader();w.writerows(rows)
    lines=["# BrowserFallback v23 major color-plane boundary geometry","",
           "Status: **RESEARCH ONLY; NO PRODUCTION PROMOTION**. All inputs original 340×340, real Chrome 154 and actual app.js URL route.",
           "The deliberately missing facial features are by design. No image-generation, redraw of eyes or change in palette/region identities.",
           "", "| Source | Gate | Regions | Vertices saved | Changed pixels | Facet / plane time |",
           "| --- | --- | ---: | ---: | ---: | --- |"]
    for row in rows:
        lines.append(f"| {row['name']} | {row['status']} | {row['regionCount']} | {row['vertexReduction']} | {row['changedPixels']} | {row['facetTimeSeconds']:.2f}s / {row['planeTimeSeconds']:.2f}s |")
    lines+=["",
            "The major-plane experiment retains Facet segmentation/palette and preserves cross-region chain topology. It changes only the geometric boundary fitting trials on boundaries adjacent to major source regions.",
            "All real PNGs pass the external staff, green and sleeve fidelity audit and white-background silhouette check, or are rolled back byte-identically.",
            "An objective acceptance criterion for v24 must demand a visibly improved major clothing/hair boundary and runtime efficiency. A few fewer vertices alone is not such evidence.",
            ""]
    (out/"v23_report.md").write_text("\n".join(lines),encoding="utf-8")
    with zipfile.ZipFile(out/"v23_raw_images_metrics.zip","w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for file in ("v23_metrics.json","v23_metrics.csv","v23_report.md","v23_three_source_comparison.png"):
            z.write(out/file,file)
        for name,p in folders.items():
            for file in ("source.png","facet.png","near.png","plane.png","metrics.json"):
                z.write(p/file,f"{name}/{file}")
    return payload

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for case in CASES:p.add_argument("--"+case.lower(),type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--reference-root",type=Path,required=True)
    a=p.parse_args()
    audit({c:getattr(a,c.lower()) for c in CASES},a.out,a.reference_root)
