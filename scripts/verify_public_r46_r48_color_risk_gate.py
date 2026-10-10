"""R46-R48: source-observed colors are diagnostics, never automatic repaint."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
CRITICAL={"face","right_arm","left_arm","accessory_or_held_object"}
MIN_SAMPLES=128
MAX_SAFE_PALETTE_L1=96

def evaluate(r44:dict,r45:dict,r42:dict,r6:dict):
    if ([c["case"] for c in r44.get("cases",[])]!=["GC001","Raden"] or
        [c["case"] for c in r45.get("cases",[])]!=["GC001","Raden"] or
        [c["case"] for c in r42.get("cases",[])]!=["GC001","Raden"] or
        r42.get("productionReleaseAuthorized") is not False or
        r6.get("blockedGateCount")!=8 or r6.get("releaseAuthorized") is not False):
        raise ValueError("R48 signed source evidence or R6 release blockers missing")
    results=[]
    for review,color,packet in zip(r44["cases"],r45["cases"],r42["cases"]):
        if (review["case"]!=color["case"] or review["case"]!=packet["case"] or
            color["sourceOwnerCount"]!=11 or color["semanticCandidateColorApproved"] is not False or
            len(packet["reviewItems"])!=11):
            raise ValueError("R46 signed image or owner review provenance mismatch")
        original={i["owner"]:i for i in review["reviewItems"]}
        tasks=[]
        for item in color["ownerRows"]:
            name=item["owner"];source_n=item["opaqueVisibleInteriorSourceSamplePixels"]
            proposal=item["observedSourcePixelCandidateRGB"]
            old=item["existingPaletteRGB"]
            if source_n==0:
                status="NO_VISIBLE_SOURCE_SAMPLES"
                delta=None
            elif source_n<MIN_SAMPLES:
                status="INSUFFICIENT_OPAQUE_INTERIOR_SOURCE"
                delta=sum(abs(a-b) for a,b in zip(old,proposal))
            else:
                delta=sum(abs(a-b) for a,b in zip(old,proposal))
                status=("POTENTIAL_SEMANTIC_OWNER_OR_PALETTE_CONFLICT" if delta>=MAX_SAFE_PALETTE_L1
                        else "OBSERVED_PIXEL_CANDIDATE_UNAPPROVED")
            if (name=="face" and status=="OBSERVED_PIXEL_CANDIDATE_UNAPPROVED"):
                status="FACE_HIDDEN_POLICY_REQUIRES_NO_REPAINT"
            tasks.append({"owner":name,"sourceInteriorSampleCount":source_n,
                          "sourcePaletteRGBDifferenceL1":delta,
                          "observedSourcePixelColorFitGainMAE":item["measuredMAEGain"],
                          "sourceVisibleOwnerMaskPixels":original.get(name,{}).get("visibleUnoccludedMaskPixels"),
                          "status":status,"criticalOwnerProtected":name in CRITICAL,
                          "humanSemanticOwnerApprovalAttached":False,
                          "experimentalPalettePromotionAuthorized":False})
        if len(tasks)!=11 or len(set(x["owner"] for x in tasks))!=11:
            raise ValueError("R46 no complete source owner classification")
        results.append({"case":review["case"],"ownerReview":tasks,
                        "sourceSemanticQualityApproved":False,
                        "originalStage8BudgetExceeded":True})
    return results

def gate(cases,r6):
    if [x["case"] for x in cases]!=["GC001","Raden"] or r6.get("blockedGateCount")!=8:
        raise ValueError("R48 release not grounded")
    if any(row["experimentalPalettePromotionAuthorized"] or row["humanSemanticOwnerApprovalAttached"]
        for case in cases for row in case["ownerReview"]):
        raise ValueError("R48 cannot fabricate product palette or anatomy approval")
    return {"R46":"SOURCE_OBSERVED_RGB_CANDIDATE_RISK_CLASSIFICATION",
            "R47":"SIGNED_PHOTO_MASK_MANUAL_REVIEW_READY",
            "R48":"HUMAN_SEMANTIC_AND_STAGE8_BUDGET_HOLD",
            "originalReleaseR6Blockers":8,
            "unknownOwnerAnatomyApproved":False,
            "faceFeatureRenderApproved":False,
            "originalSourcePaletteOrMasksModified":False,
            "historicalStage8VertexBudgetPass":False,
            "productionReleaseAuthorized":False,
            "status":"OWNER_COLOR_RISK_TRIAGE_PASS_RELEASE_NO_GO"}
def run(r44,r45,r42,r6,out):
    if out.exists():raise FileExistsError("cannot overwrite R48 evidence")
    paths=(r44,r45,r42,r6)
    raw=[p.read_bytes() for p in paths]
    data=[json.loads(x) for x in raw]
    cases=evaluate(*data)
    verdict=gate(cases,data[-1])
    result={"version":"public-r46-r48-owner-color-risk-review-v1",
            "inputEvidenceSHA256":[hashlib.sha256(x).hexdigest() for x in raw],
            "cases":cases,"releaseGate":verdict,
            "sourceImagePixelOrMaskChanged":False,
            "independentSemanticOwnerHumanApprovalSigned":False,
            "productionReleaseAuthorized":False}
    out.mkdir(parents=True)
    (out/"public_r46_r48_owner_color_risk_gate.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    for case in cases:
        print("R46_R48",case["case"],
              [(x["owner"],x["status"],x["sourcePaletteRGBDifferenceL1"])
               for x in case["ownerReview"] if x["status"]!="OBSERVED_PIXEL_CANDIDATE_UNAPPROVED"],
              "NO_GO",flush=True)
    return result
def main():
    parser=argparse.ArgumentParser()
    for name in ("r44","r45","r42","r6","out"):
        parser.add_argument("--"+name,required=True,type=Path)
    a=parser.parse_args()
    run(a.r44,a.r45,a.r42,a.r6,a.out)
if __name__=="__main__":main()
