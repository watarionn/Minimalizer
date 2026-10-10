"""R50/R51: source-pinned human annotation worksheet, NEVER a signed review.

CSV is intentionally editable by a human. Re-imported answers are UNTRUSTED
until separately verified against source-only imagery and reviewer identity.
No "PASS" state in this tool grants product approval.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from research_public_r12_exact_raster_prune import SOURCE
from research_public_r17_consecutive_vertex_prune import SCENE_SHA256
CASES=("GC001","Raden")
OWNERS=("right_arm","left_arm","major_clothing","accessory_or_held_object","unknown")
COLUMNS=("case","owner","source_original_sha256","stage8_owner_scene_sha256",
         "private_review_board_filename","signed_owner_mask_pixels",
         "visible_source_owner_pixels","stage04_mask_xor_pixels",
         "human_review_decision","human_reviewer","reviewed_date","source_evidence_notes")
CHOICES=("PENDING","ACCEPT_MASK","REJECT_MASK","UNCERTAIN")
VERSION="public-r50-r51-human-review-pending-worksheet-v1"
def digest(raw):return hashlib.sha256(raw).hexdigest()
def construct(r44:dict,r42:dict,board_root:Path)->list[dict]:
    if ([x.get("case") for x in r44.get("cases",[])]!=list(CASES) or
        [x.get("case") for x in r42.get("cases",[])]!=list(CASES) or
        r42.get("productionReleaseAuthorized") is not False or
        r44.get("productionReleaseAuthorized") is not False):
        raise ValueError("R50 original photo/mask authority is missing")
    rows=[]
    for origin,review in zip(r44["cases"],r42["cases"]):
        case=origin["case"]
        if (origin["sourceSHA256"]!=SOURCE[case][0] or
            origin["sourceStage8SHA256"]!=SCENE_SHA256[case] or
            len(review["reviewItems"])!=11):
            raise ValueError("R50 source photo or Stage8 signed SHA mismatch")
        board=board_root/(case+"_r44_PRIVATE_owner_comparison_board.png")
        if not board.is_file() or digest(board.read_bytes())!=origin["boardSha256"]:
            raise ValueError("R50 unsigned or changed photo review overlay")
        found={item["owner"]:item for item in origin["reviewItems"]}
        if set(found)!=set(OWNERS):raise ValueError("R50 incomplete priority owner comparison")
        for name in OWNERS:
            item=found[name]
            rows.append(dict(zip(COLUMNS,(
                case,name,SOURCE[case][0],SCENE_SHA256[case],
                board.name,str(item["ownerMaskPixels"]),
                str(item["visibleUnoccludedMaskPixels"]),
                "" if item["stage8VsIndependentSignedStage04MaskXorPixels"] is None
                   else str(item["stage8VsIndependentSignedStage04MaskXorPixels"]),
                "PENDING","","",""))))
    return rows
def validate(rows:list[dict],input_rows:list[dict])->dict:
    if len(rows)!=len(input_rows) or len(rows)!=10:
        raise ValueError("R51 all ten grounded review identities required")
    observed=set()
    pending=0;submitted=0
    for original,item in zip(rows,input_rows):
        if set(item)!=set(COLUMNS):raise ValueError("R51 CSV header cannot change")
        key=(item["case"],item["owner"])
        if key in observed:raise ValueError("R51 repeated review owner")
        observed.add(key)
        for field in COLUMNS[:8]:
            if item[field]!=original[field]:
                raise ValueError("R51 source photo or signed mask identity changed")
        if item["human_review_decision"] not in CHOICES:
            raise ValueError("R51 invalid human review status")
        if item["human_review_decision"]=="PENDING":
            pending+=1
        else:
            submitted+=1
            if not item["human_reviewer"] or not item["reviewed_date"] or not item["source_evidence_notes"]:
                raise ValueError("R51 review fields absent")
    return {"reviewItems":len(rows),"pendingItems":pending,
            "submittedReviewClaims":submitted,
            "reviewerIdentityCryptographicallyVerified":False,
            "independentSourcePartAnnotationValidated":False,
            "sourcePhotoGoldenApproved":False,
            "productSemanticOwnerApproved":False,
            "productionReleaseAuthorized":False,
            "status":"R51_CSV_INTEGRITY_VERIFIED_HUMAN_SOURCE_TRUTH_HOLD"}
def run(r44path:Path,r42path:Path,board_root:Path,out:Path)->dict:
    if out.exists():raise FileExistsError("R50 evidence cannot overwrite")
    source=json.loads(r44path.read_text(encoding="utf8"))
    packet=json.loads(r42path.read_text(encoding="utf8"))
    original=construct(source,packet,board_root)
    stats=validate(original,original)
    out.mkdir(parents=True)
    worksheet=out/"PRIVATE_R50_human_source_owner_review_PENDING.csv"
    with worksheet.open("w",newline="",encoding="utf-8-sig") as f:
        writer=csv.DictWriter(f,fieldnames=COLUMNS)
        writer.writeheader();writer.writerows(original)
    with worksheet.open("r",newline="",encoding="utf-8-sig") as f:
        restored=list(csv.DictReader(f))
    assert validate(original,restored)==stats
    report={"version":VERSION,"sources":{
            "r44AuditSHA256":digest(r44path.read_bytes()),
            "r42HumanReviewPacketSHA256":digest(r42path.read_bytes())},
            "worksheetSha256":digest(worksheet.read_bytes()),
            "caseCount":2,"priorityOwnerCount":10,
            "recordStatus":stats,
            "originalSourcePhotoAndMaskModified":False,
            "userHumanPhotoSemanticApprovalGranted":False,
            "productionReleaseAuthorized":False}
    (out/"public_r50_r51_owner_review_worksheet_audit.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("R50_R51",stats["reviewItems"],"human-review items still pending",
          stats["pendingItems"],"NO_GO",flush=True)
    return report
def main():
    p=argparse.ArgumentParser()
    for n in ("r44","r42","boards","out"):p.add_argument("--"+n,required=True,type=Path)
    a=p.parse_args()
    run(a.r44,a.r42,a.boards,a.out)
if __name__=="__main__":main()
