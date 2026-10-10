"""R50/R51 human owner review worksheet requires original frozen source identity."""
import sys,hashlib,copy
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from research_public_r12_exact_raster_prune import SOURCE
from research_public_r17_consecutive_vertex_prune import SCENE_SHA256
import verify_public_r50_r51_human_review_worksheet as review

def inputs(tmp_path):
    cases=[]
    signed=[]
    for case in review.CASES:
        board=tmp_path/(case+"_r44_PRIVATE_owner_comparison_board.png")
        board.write_bytes(("fake-artifact-"+case).encode())
        cases.append({"case":case,
          "sourceSHA256":SOURCE[case][0],
          "sourceStage8SHA256":SCENE_SHA256[case],
          "boardSha256":hashlib.sha256(board.read_bytes()).hexdigest(),
          "reviewItems":[{"owner":name,"ownerMaskPixels":200,
               "visibleUnoccludedMaskPixels":170,
               "stage8VsIndependentSignedStage04MaskXorPixels":2}
               for name in review.OWNERS]})
        signed.append({"case":case,"reviewItems":[{}]*11})
    return {"cases":cases,"productionReleaseAuthorized":False},{"cases":signed,"productionReleaseAuthorized":False}
def test_private_annotation_packet_initially_all_pending(tmp_path):
    a,b=inputs(tmp_path)
    rows=review.construct(a,b,tmp_path)
    assert len(rows)==10
    state=review.validate(rows,rows)
    assert state["pendingItems"]==10
    assert state["submittedReviewClaims"]==0
    assert not state["productionReleaseAuthorized"]
def test_missing_review_item_rejected(tmp_path):
    a,b=inputs(tmp_path);rows=review.construct(a,b,tmp_path)
    with pytest.raises(ValueError,match="R51"):
        review.validate(rows,rows[:-1])
def test_forged_mask_identity_rejected(tmp_path):
    a,b=inputs(tmp_path);rows=review.construct(a,b,tmp_path)
    altered=copy.deepcopy(rows)
    altered[0]["source_original_sha256"]="0"*64
    with pytest.raises(ValueError,match="R51"):
        review.validate(rows,altered)
def test_fake_human_approval_has_no_cryptographic_authority(tmp_path):
    a,b=inputs(tmp_path);rows=review.construct(a,b,tmp_path)
    altered=copy.deepcopy(rows)
    altered[0].update({"human_review_decision":"ACCEPT_MASK",
                       "human_reviewer":"claimed",
                       "reviewed_date":"2026-10-10",
                       "source_evidence_notes":"unverified example"})
    result=review.validate(rows,altered)
    assert result["submittedReviewClaims"]==1
    assert not result["reviewerIdentityCryptographicallyVerified"]
    assert not result["productSemanticOwnerApproved"]
    assert not result["productionReleaseAuthorized"]
def test_claimed_accept_with_empty_reviewer_rejected(tmp_path):
    a,b=inputs(tmp_path);rows=review.construct(a,b,tmp_path)
    altered=copy.deepcopy(rows);altered[0]["human_review_decision"]="ACCEPT_MASK"
    with pytest.raises(ValueError,match="R51"):
        review.validate(rows,altered)
def test_corrupted_source_photo_preview_rejected(tmp_path):
    a,b=inputs(tmp_path)
    board=tmp_path/"GC001_r44_PRIVATE_owner_comparison_board.png"
    board.write_bytes(b"replaced")
    with pytest.raises(ValueError,match="R50"):
        review.construct(a,b,tmp_path)
def test_review_code_not_in_product_routes():
    name="verify_public_r50_r51_human_review_worksheet"
    for path in ("web/static/public-route.js","local_worker/frontend/local-route.js"):
        assert name not in (ROOT/path).read_text(encoding="utf8")
