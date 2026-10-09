"""BrowserFallback v29: real frozen Noel/Ririka sparse hair/clothes QA.

Small manually reviewed source-visible anchors are *spot checks*, never
full-image ground truth or evidence for generating invisible anatomy.
Every input and derived output has exact SHA256 provenance; no inference.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,zipfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

EXPECTED_ZIP="91b9f3851622feb55169bbf301b9dbb52d81036c260ea7e8f88fd7814423bd39"
EXPECTED_SOURCES={
"Noel":"f0dceadc5af23eaa914d3fece271186aca428ce176d76bd91c05686b1f44ef26",
"Ririka":"6da229380c2673611b57bada10b77d03b9b831770070d594137f2062ca302914",
}
EXPECTED_FACETS={
"Noel":"d369aea0c89fc50918efaa0221a3445a642091e748ad7f86ab873edc6854e6a5",
"Ririka":"badb7de356d1672d98399df3ea3800c6d42c10a34d6eca5ab76375773413ea45",
}
CLASSES={
(0,0,0):"unclassified_or_background",
(244,165,43):"hair",
(240,189,156):"body_skin",
(244,214,170):"face_skin",
(30,187,125):"clothes",
(112,119,138):"accessories",
}
# Coordinates are individual inspectable source-visible pixels, not polygons,
# inferred region boundaries or automatic manual masks.
# The case source + source PNG itself is included in the evidence ZIP.
SPARSE_ANCHORS={
"Noel":[
("N-H1",165,35,"hair"),("N-H2",135,47,"hair"),
("N-H3",220,128,"hair"),("N-H4",198,62,"hair"),
("N-H5",114,104,"hair"),
("N-C1",148,236,"clothes"),("N-C2",260,222,"clothes"),
("N-C3",146,292,"clothes"),("N-C4",291,288,"clothes"),
("N-C5",100,232,"clothes")],
"Ririka":[
("R-H1",120,76,"hair"),("R-H2",106,105,"hair"),
("R-H3",202,139,"hair"),("R-H4",99,75,"hair"),
("R-H5",148,43,"hair"),
("R-C1",285,142,"clothes"),("R-C2",290,255,"clothes"),
("R-C3",60,297,"clothes"),("R-C4",172,242,"clothes"),
("R-C5",147,295,"clothes")],
}
def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def audit(reference:Path,out:Path)->dict:
    if sha(reference.read_bytes())!=EXPECTED_ZIP:
        raise ValueError("v27 frozen reference SHA differs: abort")
    if out.exists():raise FileExistsError("No overwriting benchmark output")
    out.mkdir(parents=True)
    results=[]
    rows=[]
    with zipfile.ZipFile(reference) as z:
        for case in ("Noel","Ririka"):
            src=z.read(f"{case}/source.png")
            facet=z.read(f"{case}/facet.png")
            mask=z.read(f"{case}/part_classes.png")
            metadata=json.loads(z.read(f"{case}/metrics.json"))
            if sha(src)!=EXPECTED_SOURCES[case] or sha(facet)!=EXPECTED_FACETS[case]:
                raise ValueError(f"{case}: source/facet mismatch")
            if metadata["version"]!="browser-part-evidence-v27":
                raise ValueError(f"{case}: unexpected observer")
            if metadata["summary"]["finalSemanticBoundSegments"]!=0:
                raise ValueError(f"{case}: v27 unexpectedly promoted an uncertain part")
            source=Image.open(io.BytesIO(src)).convert("RGBA")
            classes=Image.open(io.BytesIO(mask)).convert("RGB")
            image_facet=Image.open(io.BytesIO(facet)).convert("RGB")
            if source.size!=classes.size or classes.size!=image_facet.size or source.size!=(340,340):
                raise ValueError(f"{case}: image shape mismatch")
            overlay=source.convert("RGB").copy()
            mask_overlay=classes.copy()
            annotation=[]
            for id_,x,y,expected in SPARSE_ANCHORS[case]:
                if not(0<=x<340 and 0<=y<340):raise ValueError("bad coordinates")
                if source.getpixel((x,y))[3]!=255:
                    raise ValueError(f"nonopaque annotation point {id_}")
                observed=CLASSES.get(classes.getpixel((x,y)))
                if observed is None:raise ValueError(f"unknown v27 palette {id_}")
                status=("matched" if observed==expected else
                        "abstained" if observed=="unclassified_or_background" else
                        "misclassified")
                annotation.append({"id":id_,"x":x,"y":y,"visibleReference":expected,
                    "v27Observed":observed,"result":status,
                    "annotationAuthority":"sparse_manual_source_spot_check_only",
                    "segmentationAuthority":False})
                rows.append({"case":case,**annotation[-1]})
            label_stats={
              category:{k:sum(a["result"]==k for a in annotation if a["visibleReference"]==category)
                        for k in ("matched","abstained","misclassified")}
              for category in ("hair","clothes")}
            all_stats={k:sum(a["result"]==k for a in annotation)
                        for k in ("matched","abstained","misclassified")}
            # Be explicit that these 10 selected source pixels are not an IoU
            # estimate and must not be extrapolated as a model-wide accuracy.
            report={"case":case,"sourceSHA":sha(src),"facetSHA":sha(facet),
                "photoClassMapSHA":sha(mask),
                "photoModelCueGroups":metadata["summary"]["garmentCueSegments"],
                "validatedPoseTracks":metadata["summary"]["usablePoseTracks"],
                "poseStatus":metadata["summary"]["poseStatus"],
                "pointCount":len(annotation),"counts":all_stats,
                "perExpectedCategory":label_stats,"anchorRows":annotation,
                "unboundSemanticParts":metadata["summary"]["unbound"],
                "semanticBindingAuthority":False,"fullImageAccuracyMeasured":False,
                "animeMaskAvailable":False,"newInferencePerformed":False}
            results.append(report)
            # Yellow rings on Hair and cyan on Clothes are review markers,
            # *not* output changes. Keep labels outside mark pixels.
            for (rid,x,y,expected) in SPARSE_ANCHORS[case]:
                color=(248,222,35) if expected=="hair" else (31,240,242)
                for im in (overlay,mask_overlay):
                    d=ImageDraw.Draw(im)
                    d.ellipse((x-4,y-4,x+4,y+4),outline=color,width=2)
            for name,data in (("source.png",src),("facet.png",facet),
                              ("part_classes.png",mask)):
                (out/f"{case}_{name}").write_bytes(data)
            overlay.save(out/f"{case}_anchor_review.png",optimize=True)
            mask_overlay.save(out/f"{case}_v27_class_anchor_review.png",optimize=True)
            print("V29_SOURCE_ANCHORS",case,json.dumps(all_stats,sort_keys=True),
                  "garment cues",report["photoModelCueGroups"],flush=True)
    summary={"status":"SPARSE_SOURCE_QA_PASS_SEMANTIC_GLOBAL_HOLD",
      "frozenV27ZipSHA":EXPECTED_ZIP,
      "sourceCases":["Noel","Ririka"],
      "anchorCount":len(rows),
      "notGroundTruth":"Sparse selected visible source points are not full-image segmentation labels",
      "allArmPartEvidenceUnbound":True,
      "animeSegNoelRirika":"NOT_RUN",
      "productionAuthority":False,"renderChanged":False,
      "newInference":False,
      "cases":results}
    (out/"v29_metrics.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    with (out/"v29_sparse_anchor_results.csv").open("w",newline="",encoding="utf-8-sig") as f:
        fields=("case","id","x","y","visibleReference","v27Observed","result",
                "annotationAuthority","segmentationAuthority")
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    # 2 cases x 4 evidence columns, no original pixels modified by observer.
    gallery=Image.new("RGB",(4*340+5*12,2*(340+58)+12),(246,246,246))
    gd=ImageDraw.Draw(gallery)
    labels=("Original","v27 Class Map","Source sparse QA","Class sparse QA")
    for k,case in enumerate(("Noel","Ririka")):
        for n,file in enumerate((f"{case}_source.png",f"{case}_part_classes.png",
            f"{case}_anchor_review.png",f"{case}_v27_class_anchor_review.png")):
            xx=12+n*(340+12);yy=12+k*(340+58)
            gd.text((xx,yy),case+" | "+labels[n],fill=(25,30,40))
            img=Image.open(out/file).convert("RGB")
            gallery.paste(img,(xx,yy+30))
    gallery.save(out/"v29_noel_ririka_sparse_qa.png",optimize=True)
    report_md=[
      "# BrowserFallback v29 sparse validation of hair/clothes",
      "",
      "**CORPUS SPOT-CHECK PASS / ANIMESEG & ARM SEMANTIC HOLD**.",
      "This is an exact-source sparse manual visible-pixel review (10 points per case).",
      "It is NOT a full-image ground-truth mask and does not support global accuracy claims.",
      "Source and Facet PNGs exactly match frozen v27 ZIP and preserve all output pixels.",
      "",
      "| Case | Hair points classified clothes | Hair abstentions | Clothes matches | Clothes abstentions |",
      "|---|---:|---:|---:|---:|",
    ]
    for c in results:
        hair=c["perExpectedCategory"]["hair"];cloth=c["perExpectedCategory"]["clothes"]
        report_md.append(f"| {c['case']} | {hair['misclassified']} | {hair['abstained']} | {cloth['matched']} | {cloth['abstained']} |")
    report_md+=["",
       "Noel and Ririka have no verified AnimeSeg source-aligned v3 output under current",
       "memory budget. Pose model did not provide validated left/right arms.",
       "All observed role candidates remain UNBOUND, no painting, no facial detail synthesis.",
       "Visible source-point selection is for deterministic falsification of raw classifier hints.",
       "When future anime-model masks exist, evaluate *these same frozen source anchors*",
       "before considering large-plane geometry changes. Do not relax the current output HOLD.",""]
    (out/"v29_report.md").write_text("\n".join(report_md),encoding="utf-8")
    return summary

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--v27-zip",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    audit(a.v27_zip,a.out)
