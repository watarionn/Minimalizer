"""R38-R41: read-only signed color-error review. No photo access or edits."""
import argparse,hashlib,json
from pathlib import Path

SHA={
 "r25":"5f7bb72c101c3254a8e2f9beb0c60063d2bb484518dcced12f96726fcd8bd9aa",
 "r30":"45f1f57096b65298cd41063b741fd1f4858d36e9121968285d825f3d18f2a672",
 "r36":"339ba5ce62d0e125975849eaf023d53e5ba998713ed854c7980091d5a1510619"}
PRIORITY=("right_arm","left_arm","accessory_or_held_object","major_clothing",
 "torso","hair","lower_body","head","neck","face","unknown")
def frozen(path,key):
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=SHA[key]:
        raise ValueError("signed source-free RGB evidence SHA mismatch")
    return json.loads(path.read_text(encoding="utf8"))
def evaluate(r25,r30,r36):
    cases=[]
    for a,b,c in zip(r25["cases"],r30["cases"],r36["cases"]):
        if a["case"]!=b["case"] or a["case"]!=c["case"]:
            raise ValueError("original cases mismatch")
        if b["ownerMaskCount"]!=14 or len(a["stage8SourceOwnedRegions"])!=11:
            raise ValueError("original owner count missing")
        if not b["runAndMergedSignedMaskChromeAllExact"]:
            raise ValueError("signed browser mask proof missing")
        if a["signedStage8OriginalVertices"]!=b["frozenStage8Vertices"]:
            raise ValueError("historic source budget changed")
        owners=a["stage8SourceOwnedRegions"]
        if set(owners)!=set(PRIORITY):raise ValueError("owner labels inconsistent")
        queue=[]
        for part in PRIORITY:
            m=owners[part]["regions"]
            inner=m["interiorEroded2"];edge=m["boundaryComplement"];total=m["all"]
            if inner["maskPixels"]+edge["maskPixels"]!=total["maskPixels"]:
                raise ValueError("nonpartitioned owner metric")
            queue.append({
             "owner":part,
             "sourceVsReferenceRgbMAE":total["sourceVsFrozenReferenceMAE"],
             "chromeVsReferenceRgbMAE":total["chromeVsFrozenReferenceMAE"],
             "chromeInteriorDifferencePixels":inner["chromeVsFrozenReferenceChangedPixels"],
             "chromeBoundaryDifferencePixels":edge["chromeVsFrozenReferenceChangedPixels"],
             "originalSourceBorderRGBOverlap":owners[part]["sourceBorderConnectedExactRGBOverlap"],
             "sourcePhotoSemanticOwnerApproved":False,
             "experimentalPaletteMutationAuthorized":False})
        cases.append({"case":a["case"],"reviewQueue":queue,
         "sourceOriginalStage8Vertices":b["frozenStage8Vertices"],
         "sourceHistoricalCap":b["historicOriginalStage8Cap"],
         "stage8BudgetPassed":False,"faceDetailsRendered":False})
    if len(cases)!=2 or [x["case"] for x in cases]!=["GC001","Raden"]:
        raise ValueError("both genuine source cases required")
    return cases
def hold(cases,r6):
    if r6.get("blockedGateCount")!=8 or r6.get("status")!="NO_GO" or r6.get("releaseAuthorized") is not False:
        raise ValueError("R41 release admission unsigned")
    if any(x["sourceOriginalStage8Vertices"]<=x["sourceHistoricalCap"] for x in cases):
        raise ValueError("R41 historical Stage8 budget was forged")
    return {"R38":"SIGNED_NUMERIC_EVIDENCE_VERIFIED",
     "R39":"SOURCE_RGB_ERROR_SEPARATED_FROM_CHROME_ERROR",
     "R40":"PHOTO_SEMANTIC_OWNER_REVIEW_REQUIRED",
     "R41":"STAGE8_AND_R6_RELEASE_HOLD",
     "productionReleaseAuthorized":False}
def run(files,out):
    if out.exists():raise FileExistsError("no evidence overwrite")
    a,b,c=(frozen(files[k],k) for k in ("r25","r30","r36"))
    cases=evaluate(a,b,c)
    state=hold(cases,json.loads(files["r6"].read_text(encoding="utf8")))
    record={"version":"public-r38-r41-readonly-owner-review-v1",
      "signedInputSha256":SHA,"cases":cases,
      "releaseGate":state,"originalPhotosAccessed":False,
      "signedMasksOrColorsModified":False,
      "status":"RESEARCH_REVIEW_READY_PRODUCT_NO_GO"}
    out.mkdir(parents=True)
    (out/"public_r38_r41_source_color_review.json").write_text(
       json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    return record
def main():
    p=argparse.ArgumentParser()
    for x in ("r25","r30","r36","r6","out"):
        p.add_argument("--"+x,type=Path,required=True)
    a=p.parse_args()
    result=run({x:getattr(a,x) for x in ("r25","r30","r36","r6")},a.out)
    for v in result["cases"]:
        print("R38_R41",v["case"],"source_color_critical",
          [(q["owner"],q["sourceVsReferenceRgbMAE"]) for q in v["reviewQueue"][:4]],
          "RELEASE_HOLD")
if __name__=="__main__":main()
