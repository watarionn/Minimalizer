"""R42-R43: source-grounded semantic color review packet (NO auto approval)."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from verify_public_r38_r41_readonly_owner_color_review import hold

def packet(measurement):
    if measurement.get("version")!="public-r38-r41-readonly-owner-review-v1" or (
        measurement.get("status")!="RESEARCH_REVIEW_READY_PRODUCT_NO_GO"):
        raise ValueError("R42 signed numeric review lineage required")
    cases=measurement["cases"]
    reviews=[]
    for row in cases:
        tasks=[]
        for item in row["reviewQueue"]:
            if item["experimentalPaletteMutationAuthorized"]:
                raise ValueError("R42 cannot inherit palette approval")
            if item["owner"]=="face":
                action="KEEP_FACE_DETAILS_HIDDEN_NO_REPAINT"
            elif item["owner"]=="unknown":
                action="REQUIRE_INDEPENDENT_OWNER_LABEL"
            else:
                action="COMPARE_ORIGINAL_PHOTO_OWNER_SHAPE_AND_SOURCE_RGB_MANUALLY"
            tasks.append({"owner":item["owner"],"reviewAction":action,
                          "upstreamSourceReferenceRGBMAE":item["sourceVsReferenceRgbMAE"],
                          "rendererReferenceRGBMAE":item["chromeVsReferenceRgbMAE"],
                          "imageFileOrSourcePixelsEmbedded":False,
                          "independentSourceOnlyOwnerReviewSigned":False,
                          "candidatePaletteApproved":False})
        reviews.append({"case":row["case"],"reviewItems":tasks,
                        "originalHistoricStage8BudgetExceeded":True,
                        "sourcePartReviewComplete":False})
    if len(reviews)!=2 or any(len(r["reviewItems"])!=11 for r in reviews):
        raise ValueError("R42 original two-case evidence incomplete")
    return {"version":"public-r42-r43-semantic-color-decision-packet-v1",
            "cases":reviews,
            "sourceOnlyHumanPhotoSemanticAnnotationsAttached":False,
            "externalIndependentObserverLicenseAndProvenanceVerified":False,
            "originalMasksAndPalettesChanged":False,
            "humanGoldenPass":False,
            "sourceSemanticColorApprovalGranted":False,
            "productionReleaseAuthorized":False,
            "status":"R42_REVIEW_PACKET_READY_R43_PRODUCT_NO_GO"}
def verify(packet):
    if packet["status"]!="R42_REVIEW_PACKET_READY_R43_PRODUCT_NO_GO" or (
        packet["sourceOnlyHumanPhotoSemanticAnnotationsAttached"] is not False or
        packet["externalIndependentObserverLicenseAndProvenanceVerified"] is not False or
        packet["sourceSemanticColorApprovalGranted"] is not False or
        packet["productionReleaseAuthorized"] is not False or
        any(i["candidatePaletteApproved"] for row in packet["cases"]
            for i in row["reviewItems"])):
        raise ValueError("R43 human/observer authorization fabricated")
    return True
def run(source,out):
    if out.exists():raise FileExistsError("cannot overwrite R42 signed packet")
    raw=source.read_bytes()
    measured=json.loads(raw)
    report=packet(measured)
    verify(report)
    report["R38EvidenceSHA256"]=hashlib.sha256(raw).hexdigest()
    out.mkdir(parents=True)
    (out/"public_r42_r43_source_semantic_color_review.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("R42_R43",len(report["cases"]),"signed sources",
          "22 owner records review needed; no palette authorization",flush=True)
    return report
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--review",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    run(args.review,args.out)
if __name__=="__main__":main()
