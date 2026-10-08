#!/usr/bin/env python3
"""Evaluate v21 five explicitly targeted pair trials against accepted Facet PNGs."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path

CASES={
 "Kyoko":[(14,17),(18,15),(18,19)],
 "Noel":[(16,24),(34,27)],
 "Ririka":[],
}
EXPECTED={"Kyoko":(340,340),"Noel":(340,340),"Ririka":(340,340)}
COLOR_RGB=(149,211,27)
SLEEVE_RGB=(65,66,74)


def sha(p:Path)->str:
 return hashlib.sha256(p.read_bytes()).hexdigest()


def compare_rgb(baseline,trial):
 a=list(baseline.getdata());b=list(trial.getdata())
 assert len(a)==len(b)
 differences=sum(x!=y for x,y in zip(a,b))
 silhouette=sum((x==(255,255,255))!=(y==(255,255,255)) for x,y in zip(a,b))
 base_counts=Counter(a);trial_counts=Counter(b)
 max_mass_delta=max((abs(base_counts[color]-trial_counts[color])
                     for color in base_counts.keys()|trial_counts.keys()),default=0)
 mae=sum(sum(abs(x[i]-y[i]) for i in range(3)) for x,y in zip(a,b))/(3*len(a))
 return {"differentPixels":differences,"differentPixelFraction":round(differences/len(a),8),
         "silhouetteChangedPixels":silhouette,
         "colorMassMaxDeltaPixels":max_mass_delta,
         "rgbMAE":round(mae,8)}


def evaluate(folders:dict[str,Path],out:Path,baseline:Path):
 from PIL import Image, ImageDraw, ImageFont
 out.mkdir(parents=True,exist_ok=True)
 cases={}
 trials=[]
 width,height=3*340+45,6*400+30
 montage=Image.new("RGB",(width,height),(247,247,247))
 draw=ImageDraw.Draw(montage)
 font_path=Path("C:/Windows/Fonts/arial.ttf")
 font=ImageFont.truetype(str(font_path),16) if font_path.is_file() else ImageFont.load_default()
 rownum=0
 for name,pairs in CASES.items():
  folder=folders[name]
  raw=json.loads((folder/"metrics.json").read_text(encoding="utf-8"))
  assert raw["uiVerification"]["pngPixelAndByteExactToDirectNear"],name
  src=Image.open(folder/"source.png").convert("RGB")
  facet=Image.open(folder/"facet.png").convert("RGB")
  near=Image.open(folder/"near.png").convert("RGB")
  assert src.size==EXPECTED[name]==facet.size==near.size
  assert (folder/"facet.png").read_bytes()==(folder/"near.png").read_bytes(),name
  b=baseline/f"browser-donor-v20-{name}-20261008"
  assert sha(b/"facet.png")==sha(folder/"facet.png"),("Facet drift",name)
  assert sha(b/"near.png")==sha(folder/"near.png"),("Near drift",name)
  assert raw["near"]["metadata"]["selectiveMergeApplied"]==0
  cases[name]={"sourceSHA256":sha(folder/"source.png"),
      "facetSHA256":sha(folder/"facet.png"),
      "facetVertices":raw["facet"]["metadata"]["vertexCount"],
      "facetRegions":raw["facet"]["metadata"]["shapeCount"],
      "nearSHA256":sha(folder/"near.png"),
      "uiNearMatchesEngine":True}
  targets=[(d,r,f"pair_{d}_{r}") for d,r in pairs]
  if not targets:targets=[(999,998,"pair_missing_999_998")]
  for donor,recipient,key in targets:
   record=raw[key]
   meta=record["metadata"]
   image=Image.open(folder/(key+".png")).convert("RGB")
   change=compare_rgb(facet,image)
   merged=meta["selectiveMergeApplied"]
   expected_before=raw["facet"]["metadata"]["vertexCount"]
   accepted=merged==1
   if accepted:
    assert meta["targetedMergeMatched"]
    assert meta["targetedMergeStatus"]=="raster_pass",(name,key,meta["targetedMergeStatus"])
    assert meta["selectiveMergeRenderGate"]=="pass"
    assert meta["vertexCount"]<expected_before
    assert meta["shapeCount"]==39
    assert change["differentPixels"]<=174
    assert change["silhouetteChangedPixels"]==0
    assert change["differentPixels"]==meta["selectiveMergeRenderChangedPixels"],(name,key,change,meta["selectiveMergeRenderChangedPixels"])
   else:
    assert meta["shapeCount"]==40
    assert sha(folder/(key+".png"))==sha(folder/"facet.png"),("Rollback not exact",name,key)
    assert change["differentPixels"]==0
    assert meta["targetedMergeStatus"].startswith("raster_rejected") or meta["targetedMergeStatus"]=="not_found"
   green_count=Counter(image.getdata())[COLOR_RGB]
   sleeve_pixel=list(image.getpixel((95,275))) if name=="Kyoko" else None
   if name=="Kyoko":
    assert green_count==1994,("green tie/representative green mass",name,key,green_count)
    assert sleeve_pixel==list(SLEEVE_RGB),("sleeve",name,key,sleeve_pixel)
   entry={
    "case":name,"donorId":donor,"recipientId":recipient,"record":key,
    "accepted":accepted,"status":meta["targetedMergeStatus"],
    "matched":meta["targetedMergeMatched"],"renderGate":meta["selectiveMergeRenderGate"],
    "regionCount":meta["shapeCount"],"vertexCount":meta["vertexCount"],
    "vertexDeltaFromFacet":meta["vertexCount"]-expected_before,
    "contourMinRegionIoU":meta["contourMinRegionIoU"],
    "sourceGreenRGBPixelCount":green_count if name=="Kyoko" else None,
    "leftSleeveSampleRGB":sleeve_pixel,
    "facetSHA256":sha(folder/"facet.png"),
    "outputSHA256":sha(folder/(key+".png")),
    **change,
   }
   trials.append(entry)
   top=12+rownum*400
   desc=f"{name} / donor {donor} -> recipient {recipient} / {entry['status']}"
   draw.text((12,top),desc,font=font,fill=(25,34,43))
   draw.text((12,top+22),
      f"regions {meta['shapeCount']} | vertex delta {entry['vertexDeltaFromFacet']:+} | changed {change['differentPixels']}px",
      font=font,fill=(45,59,65))
   for col,img in enumerate((src,facet,image)):
    montage.paste(img,(12+col*355,top+50))
   rownum+=1
 assert len(trials)==6 and sum(x["accepted"] for x in trials)==3
 assert sum(not x["accepted"] for x in trials)==3
 assert all(x["differentPixels"]==0 for x in trials if not x["accepted"])
 montage.save(out/"v21_five_pair_comparison.png",optimize=True)
 # Build a change-only inspection panel: changes amplified on top of each approved trial.
 picks=[item for item in trials if item["accepted"]]
 panel=Image.new("RGB",(3*340+36,3*340+115),(247,247,247))
 pd=ImageDraw.Draw(panel)
 for j,item in enumerate(picks):
  case=item["case"];key=item["record"]
  base=Image.open(folders[case]/"facet.png").convert("RGB")
  trial=Image.open(folders[case]/(key+".png")).convert("RGB")
  tinted=trial.copy()
  for pixel,(a,b) in enumerate(zip(base.getdata(),trial.getdata())):
   if a!=b:
    x=pixel%340;y=pixel//340
    for yy in range(max(0,y-2),min(340,y+3)):
     for xx in range(max(0,x-2),min(340,x+3)):
      tinted.putpixel((xx,yy),(238,43,48))
  panel.paste(tinted,(12+j*350,55))
  pd.text((12+j*350,12),f"{case}: {key}",font=font,fill=(31,41,52))
  pd.text((12+j*350,34),f"changed {item['differentPixels']}px",font=font,fill=(31,41,52))
 panel.save(out/"v21_accepted_changes_emphasized.png",optimize=True)
 summary={
   "status":"V21_GUARDED_EXPERIMENTAL_GAINS_NOT_RELEASED",
   "baseline":"verified Facet v15 40-region 340px chrome images",
   "trials":trials,
   "perCase":cases,
   "approvedResearchCount":3,
   "rolledBackExplicitPairCount":2,
   "missingPairNegativeCount":1,
   "acceptedNotProductionClaim":True,
 }
 (out/"v21_metrics.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 with (out/"v21_trial_results.csv").open("w",newline="",encoding="utf-8-sig") as file:
  columns=("case","donorId","recipientId","status","accepted","regionCount",
           "vertexCount","vertexDeltaFromFacet","differentPixels",
           "silhouetteChangedPixels","rgbMAE","contourMinRegionIoU")
  w=csv.DictWriter(file,fieldnames=columns,extrasaction="ignore")
  w.writeheader()
  w.writerows(trials)
 lines=[
  "# BrowserFallback v21: five targeted same-palette merge trials",
  "",
  "Date: 2026-10-08. Chrome 154, original 340x340 Kyoko/Noel/Ririka.",
  "Each donor-recipient pair is explicitly named and processed alone. Max donor area exception 6% applies ONLY to the named same-palette candidate. All other geometry/contrast guards remain. The actual final rendered PNG is compared to the baseline, including protected green, sleeve ROI and silhouette.",
  "",
  "| Sample | Donor -> recipient | Status | Output regions | Vertex delta | Changed pixels |",
  "| --- | --- | --- | ---: | ---: | ---: |",
 ]
 for item in trials:
  lines.append(f"| {item['case']} | {item['donorId']} -> {item['recipientId']} | {item['status']} | {item['regionCount']} | {item['vertexDeltaFromFacet']:+} | {item['differentPixels']} |")
 lines.extend([
 "",
 "## Outcome",
 "- 3/5 measured pairs are real **gated experimental geometry gains** (39 regions; fewer vertices and <=0.15% RGB pixel changes).",
 "- 1/5 is rolled back due to **no vertex reduction**, and 1/5 due to **rendered pixel changes exceeding the tolerance**.",
 "- Ririka has no v20 candidate; a nonexistent pair is correctly ignored with byte-identical baseline.",
 "- Kyoko's dominant green RGB(149,211,27) stays 1,994 pixels, and sleeve (95,275) remains RGB(65,66,74). No white-background silhouette pixel changed in the accepted trials.",
 "- Actual app.js near UI remains bit-for-bit matched to engine (no targeted quality profile in live UI); old Facet and Near images remain byte-identical to v20.",
 "",
 "## Decision",
 "**HOLD_PRODUCTION pending visual review and v24 multi-source golden testing.** Experimental target IDs are image-dependent, not universal rules. The accepted merges affect only 3-161 pixels; they reduce shape counts and vertices but should not be over-described as dramatic visual improvement.",
 "V22 should generalize candidate selection only with full per-candidate rendered and ROI gates, and abandon the same-color merge direction if the artwork still lacks intentional straight geometric partitions.",
 ])
 (out/"v21_report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
 with zipfile.ZipFile(out/"v21_repro_inputs_outputs.zip","w",
                      zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
  for name in ("v21_metrics.json","v21_trial_results.csv","v21_report.md",
               "v21_five_pair_comparison.png","v21_accepted_changes_emphasized.png"):
   archive.write(out/name,name)
  for case,folder in folders.items():
   file_list=["source.png","facet.png","near.png","metrics.json"]
   file_list.extend(f"pair_{d}_{r}.png" for d,r in CASES[case])
   if not CASES[case]:file_list.append("pair_missing_999_998.png")
   for name in file_list:archive.write(folder/name,f"{case}/{name}")
 print("V21_RESULTS",[{"case":r["case"],"pair":r["record"],
                     "status":r["status"],"vertices":r["vertexCount"],
                     "changed":r["differentPixels"]} for r in trials],flush=True)
 print("V21_REPORT_READY",len(trials),"accepted",summary["approvedResearchCount"],flush=True)
 return summary


def main():
 p=argparse.ArgumentParser()
 for key in CASES:p.add_argument("--"+key.lower(),required=True,type=Path)
 p.add_argument("--out",required=True,type=Path)
 p.add_argument("--baseline-root",required=True,type=Path)
 args=p.parse_args()
 evaluate({case:getattr(args,case.lower()) for case in CASES},
          args.out,args.baseline_root)


if __name__=="__main__":
 main()
