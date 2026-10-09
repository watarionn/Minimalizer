"""Independent v26 Chrome read-only evidence auditor and stage-image package."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import zipfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

CASES=("Kyoko","Noel","Ririka")
def sha(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()
def audit(root:Path,out:Path,frozen_zip:Path):
    out.mkdir(parents=True,exist_ok=True)
    width=340;height=340
    pic=Image.new("RGB",(4*width+5*12,len(CASES)*(height+62)+10),(248,248,248))
    draw=ImageDraw.Draw(pic)
    font_file=Path("C:/Windows/Fonts/arial.ttf")
    font=ImageFont.truetype(str(font_file),17) if font_file.exists() else ImageFont.load_default()
    rows=[]
    with zipfile.ZipFile(frozen_zip) as archive:
        for n,case in enumerate(CASES):
            d=root/case
            report=json.loads((d/"metrics.json").read_text(encoding="utf-8"))
            stage=json.loads((d/"stage.json").read_text(encoding="utf-8"))
            s=report["summary"]
            assert stage["decision"]=="EVIDENCE_ONLY_NOT_SEMANTIC",case
            assert stage["visibleOutputUnmodified"] is True
            assert report["provenance"]["visibleOutputAuthority"] is False
            assert report["provenance"]["partAuthority"] is False
            assert s["knownArmSegments"]==0 and s["knownGarmentSegments"]==0
            assert s["retainedSegmentCount"]==s["unboundSegments"]==len(report["segments"])
            assert s["retainedPixels"]==len(report["overlayPixels"])
            assert all(x["semanticPart"]=="unbound" and x["semanticConfidence"]==0
                for x in report["segments"])
            assert len(set(report["overlayPixels"]))==len(report["overlayPixels"])
            assert sorted(report["overlayPixels"])==report["overlayPixels"]
            assert all(0<=x<width*height for x in report["overlayPixels"])
            assert (d/"facet.png").read_bytes()==archive.read(case+"/facet.png")
            assert (d/"source.png").read_bytes()==archive.read(case+"/source.png")
            source=Image.open(d/"source.png").convert("RGB")
            facet=Image.open(d/"facet.png").convert("RGB")
            preview=Image.open(d/"preview.png").convert("RGB")
            subject=Image.open(d/"subject_probability.png").convert("RGB")
            assert source.size==facet.size==preview.size==subject.size==(width,height)
            original_rgba=list(Image.open(d/"source.png").convert("RGBA").getdata())
            preview_rgba=list(Image.open(d/"preview.png").convert("RGBA").getdata())
            touched={i for i,(a,b) in enumerate(zip(original_rgba,preview_rgba))
              if a[:3]!=b[:3]}
            overlay=set(report["overlayPixels"])
            unexpected=touched-overlay
            # Browser canvas premultiply/unpremultiply can change RGB
            # arbitrarily when alpha is very low (and discards RGB at A=0).
            # Only nonopaque source pixels may differ outside v26 marks;
            # their alpha MUST be preserved. Opaque pixels stay byte-exact.
            assert all(original_rgba[i][3]<255 and
              original_rgba[i][3]==preview_rgba[i][3]
              for i in unexpected),(case,"unexpected opaque/alpha drift")
            assert all(preview_rgba[i][:3]==(255,0,220) for i in touched&overlay)
            y_cut=round(height*.45)
            lower=sum((i//width)>=y_cut for i in report["overlayPixels"])
            # Spatial focus is observational only and NEVER a torso/arm classifier.
            row={"case":case,"subjectEvidence":s["eligibleSubjectPixels"],
              "rawLostEdgePixels":s["rawLostBoundaryPixels"],
              "retainedSegments":s["retainedSegmentCount"],
              "retainedEvidencePixels":s["retainedPixels"],
              "lowerFrameEvidencePixels":lower,
              "lowerFrameFraction":round(lower/max(1,s["retainedPixels"]),6),
              "knownArmSegments":0,"knownGarmentSegments":0,
              "unboundSegments":s["unboundSegments"],
              "changedFacetPixels":0,
              "nonopaqueCanvasRgbDriftPixels":len(unexpected),
              "sourceSHA256":sha((d/"source.png").read_bytes()),
              "facetSHA256":sha((d/"facet.png").read_bytes()),
              "previewSHA256":sha((d/"preview.png").read_bytes()),
              "metricsSHA256":sha((d/"metrics.json").read_bytes())}
            rows.append(row)
            yy=n*(height+62)+8
            draw.text((12,yy),f"{case} / foreground {s['eligibleSubjectPixels']} px / lost-edge groups {s['retainedSegmentCount']}",
                fill=(24,34,44),font=font)
            draw.text((12,yy+26),
                f"Source edges retained: {s['retainedPixels']} px / lower-image {lower} px / semantic owner: UNBOUND",
                fill=(54,64,74),font=font)
            for j,image in enumerate((source,facet,subject,preview)):
                pic.paste(image,(12+j*(width+12),yy+58))
            print("V26_EXTERNAL_AUDIT_PASS",case,
                "unbound",s["unboundSegments"],
                "lost",s["rawLostBoundaryPixels"],"lowerFocus",lower,
                "frozenFacet",row["facetSHA256"],flush=True)
    pic.save(out/"v26_original_facet_foreground_lost_edges.png",optimize=True)
    (out/"v26_metrics.json").write_text(json.dumps({
      "status":"BROWSER_STRUCTURAL_EVIDENCE_READ_ONLY_PASS",
      "semanticDecision":"HOLD_NO_BROWSER_PART_AUTHORITY",
      "frozenV25FacetByteExact":True,
      "partMaskAvailable":False,
      "subjectMaskIsNotPartTruth":True,
      "visibleOutputModified":False,
      "cases":rows},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    with (out/"v26_metrics.csv").open("w",newline="",encoding="utf-8-sig") as fp:
        writer=csv.DictWriter(fp,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    lines=[
      "# BrowserFallback v26 — structural lost-boundary observations",
      "",
      "Status: **READ-ONLY OBSERVER PASS / SEMANTIC OWNERSHIP HOLD**.",
      "3 original 340×340 inputs, Chrome 154, real Facet browser request, original browser-U2NetP foreground evidence.",
      "The browser U2NetP provides foreground probability only; no trusted left-arm, right-arm, or garment-part masks are available.",
      "Every structural candidate remains **unbound**, and NONE is authorized to alter Minimalizer's visible output.",
      "High-contrast source edges unresolved in flat Facet polygons can reveal missing clothing/arm details, but also hair and facial internals.",
      "No eyes, nose or mouth are drawn into the Minimalizer. Bright pink overlay is a separate diagnostic image only.",
      "",
      "| Source | High-conf foreground px | Lost-edge px | Connected edge groups | Retained edge px | Lower frame px (spatial ONLY) | Semantic arms/garments |",
      "|---|---:|---:|---:|---:|---:|---|"]
    for r in rows:
        lines.append(f"| {r['case']} | {r['subjectEvidence']} | {r['rawLostEdgePixels']} | {r['retainedSegments']} | {r['retainedEvidencePixels']} | {r['lowerFrameEvidencePixels']} | 0 / 0; all unbound |")
    lines.extend([
      "",
      "**Independent audit** checks source/frozen Facet byte parity, stage invariants, preview overlay support against original RGB, no invented arm/garment IDs and preserved source/raster SHA.",
      "No new dependencies or generation/paint. This v26 stage measures the upstream part-evidence gap; visible quality is not improved yet.",
      "Next: v27 research must add source-verified semantic part evidence (for both arms and garment) with provenance and uncertainty, without requiring a Local Worker, before geometry/large-plane reconstruction.",
      ""])
    (out/"v26_report.md").write_text("\n".join(lines),encoding="utf-8")
    with zipfile.ZipFile(out/"v26_stages_and_metrics.zip","w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for item in ("v26_original_facet_foreground_lost_edges.png","v26_metrics.json",
                     "v26_metrics.csv","v26_report.md"):
            z.write(out/item,item)
        for case in CASES:
            for item in ("source.png","facet.png","preview.png","subject_probability.png",
                         "metrics.json","stage.json"):
                z.write(root/case/item,f"{case}/{item}")
    return rows

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--reference-zip",type=Path,required=True)
    a=p.parse_args()
    audit(a.root,a.out,a.reference_zip)
