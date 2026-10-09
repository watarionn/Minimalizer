"""v27 independent real-browser part observation audit, strict authority abstention."""
from __future__ import annotations
import argparse,csv,hashlib,json,zipfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

CASES=("Kyoko","Noel","Ririka")
PALETTE={(0,0,0),(244,165,43),(240,189,156),(244,214,170),
         (30,187,125),(112,119,138)}
def digest(path:Path):return hashlib.sha256(path.read_bytes()).hexdigest()

def audit(root:Path,out:Path,frozen:Path):
    out.mkdir(parents=True,exist_ok=True)
    picture=Image.new("RGB",(4*340+5*12,3*(340+60)+8),(248,248,248))
    draw=ImageDraw.Draw(picture)
    font=Path("C:/Windows/Fonts/arial.ttf")
    font=ImageFont.truetype(str(font),17) if font.exists() else ImageFont.load_default()
    rows=[]
    with zipfile.ZipFile(frozen) as z:
        for n,case in enumerate(CASES):
            directory=root/case
            report=json.loads((directory/"metrics.json").read_text(encoding="utf-8"))
            stage=json.loads((directory/"stage.json").read_text(encoding="utf-8"))
            summary=report["summary"]
            assert report["decision"]=="research_part_observations_only"
            assert report["provenance"]["visibleOutputAuthority"] is False
            assert report["provenance"]["partOwnershipAuthority"] is False
            assert report["provenance"]["domainCalibratedForAnime"] is False
            assert summary["finalSemanticBoundSegments"]==0
            assert summary["animeValidatedPartSegments"]==0
            assert summary["garmentsWithIndependentPartCorroboration"]==0
            assert summary["unbound"]==summary["sourceEdges"]==len(report["segments"])
            assert all(seg["semanticPart"]=="unbound"
              and seg["bindingConfidence"]==0
              and all(not c["authority"] and not c["domainCalibrated"]
                 for c in seg["roleCandidates"])
                 for seg in report["segments"])
            assert (directory/"source.png").read_bytes()==z.read(case+"/source.png")
            assert (directory/"facet.png").read_bytes()==z.read(case+"/facet.png")
            assert stage["source_sha256"]==digest(directory/"source.png")
            assert stage["facet_sha256"]==digest(directory/"facet.png")
            assert stage["preview_sha256"]==digest(directory/"preview.png")
            assert stage["part_mask_preview_sha256"]==digest(directory/"part_classes.png")
            assert stage["metrics_sha256"]==digest(directory/"metrics.json")
            assert stage["visible_output_changed"] is False
            assert stage["semantic_part_authority"] is False
            imgs=[Image.open(directory/f).convert("RGB") for f in
               ("source.png","facet.png","part_classes.png","preview.png")]
            assert all(im.size==(340,340) for im in imgs)
            assert set(imgs[2].getdata())<=PALETTE
            # An unmarked fully-opaque original pixel cannot be replaced
            # by the observer. PNG alpha premultiply drift on nonopaque
            # border pixels is a diagnostic-only known limitation.
            original=list(Image.open(directory/"source.png").convert("RGBA").getdata())
            overlay=list(Image.open(directory/"preview.png").convert("RGBA").getdata())
            changed=[i for i,(a,b) in enumerate(zip(original,overlay)) if a[:3]!=b[:3]]
            unexpected=[i for i in changed if overlay[i][:3] not in
              ((20,236,122),(250,204,28),(30,217,228),(241,74,214))]
            assert all(original[i][3]<255 and original[i][3]==overlay[i][3]
              for i in unexpected),(case,"unmarked opaque drift")
            row={
              "case":case,
              "sourceEdges":summary["sourceEdges"],
              "multiclassStatus":summary["multiclassStatus"],
              "poseStatus":summary["poseStatus"],
              "garmentCueSegments":summary["garmentCueSegments"],
              "leftArmCueSegments":summary["leftArmCueSegments"],
              "rightArmCueSegments":summary["rightArmCueSegments"],
              "acceptedClassPixels":summary["acceptedClassPixels"],
              "unboundSegments":summary["unbound"],
              "finalSemanticBoundSegments":0,
              "knownVisualFalsePositive":case!="Kyoko",
              "frozenFacetByteIdentical":True,
              "sourceSHA256":digest(directory/"source.png"),
              "facetSHA256":digest(directory/"facet.png"),
              "previewSHA256":digest(directory/"preview.png"),
              "classMapSHA256":digest(directory/"part_classes.png"),
            }
            rows.append(row)
            y=8+n*400
            draw.text((12,y),f"{case} | class {row['multiclassStatus']} | pose {row['poseStatus']}",
                      fill=(24,34,44),font=font)
            draw.text((12,y+26),
              f"Source-bound edges: {row['sourceEdges']} | garment cues {row['garmentCueSegments']} | left/right arms {row['leftArmCueSegments']}/{row['rightArmCueSegments']} | UNBOUND",
              fill=(54,64,74),font=font)
            for col,image in enumerate(imgs):
                picture.paste(image,(12+col*352,y+56))
            print("V27_AUDIT_PASS",case,"clothes",
              row["garmentCueSegments"],"left",row["leftArmCueSegments"],
              "right",row["rightArmCueSegments"],"unbound",
              row["unboundSegments"],flush=True)
    picture.save(out/"v27_source_facet_classes_cues.png",optimize=True)
    payload={
      "status":"MODEL_EXECUTION_PASS_SEMANTIC_VISUAL_HOLD",
      "visualReview":"FAIL_PHOTO_MULTICLASS_MISLABELS_ANIME_HAIR",
      "reason":"Noel hair and Ririka hair/face false-positive garment cues; no reliable arm landmarks",
      "modelClassificationNotSemanticTruth":True,
      "visibleOutputChanged":False,
      "frozenFacetByteExact":True,
      "cases":rows}
    (out/"v27_metrics.json").write_text(
      json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    with (out/"v27_metrics.csv").open("w",newline="",encoding="utf-8-sig") as f:
        columns=["case","sourceEdges","multiclassStatus","poseStatus",
          "garmentCueSegments","leftArmCueSegments","rightArmCueSegments",
          "unboundSegments","finalSemanticBoundSegments","knownVisualFalsePositive"]
        writer=csv.DictWriter(f,fieldnames=columns,extrasaction="ignore")
        writer.writeheader();writer.writerows(rows)
    lines=[
      "# BrowserFallback v27 part evidence benchmark",
      "",
      "**Research model inference succeeds, semantic use is HOLD.**",
      "Original 340x340 sources in Chrome 154. SHA-pinned MediaPipe 6-class ONNX",
      "and MediaPipe Pose Lite running inside the browser without Local Worker.",
      "The photographic selfie multiclass classifier is not calibrated for these anime cases:",
      "Noel's grey hair is partially classified as clothes; Ririka's hair/face",
      "are also incorrectly classified as clothes. All Pose Lite detections unavailable.",
      "Thus even where clothing observations exist, their semantic owners remain UNBOUND.",
      "No visible Minimalizer pixel, silhouette, tie, sleeve or staff has been modified.",
      "",
      "| Case | Edges | Clothes cues | Left arm | Right arm | Pose |",
      "| --- | ---: | ---: | ---: | ---: | --- |"]
    for r in rows:
        lines.append(f"| {r['case']} | {r['sourceEdges']} | {r['garmentCueSegments']} | {r['leftArmCueSegments']} | {r['rightArmCueSegments']} | {r['poseStatus']} |")
    lines+=["","Next: browser-compatible anime-native semantic observer or",
      "source-verified manual-independent part benchmark. No threshold relaxation",
      "or geometric repair until arm/garment visual false positives are resolved.",""]
    (out/"v27_report.md").write_text("\n".join(lines),encoding="utf-8")
    with zipfile.ZipFile(out/"v27_stages_metrics.zip","w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name in ("v27_metrics.json","v27_metrics.csv","v27_report.md",
                     "v27_source_facet_classes_cues.png"):
            z.write(out/name,name)
        for case in CASES:
            for name in ("source.png","facet.png","part_classes.png","preview.png",
                         "metrics.json","stage.json"):
                z.write(root/case/name,f"{case}/{name}")
    return payload

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--reference-zip",type=Path,required=True)
    x=p.parse_args();audit(x.root,x.out,x.reference_zip)
