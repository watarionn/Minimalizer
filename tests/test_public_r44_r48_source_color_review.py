"""R44-R48 source-fidelity gates remain diagnostic, unsigned and private."""
import sys,copy
from pathlib import Path
import numpy as np
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import verify_public_r45_visible_source_palette as r45
import verify_public_r46_r48_color_risk_gate as r46

def sample():
    masks={"right_arm":(900,[25,30,35],[24,30,35],0.2),
           "hair":(300,[255,90,20],[240,240,240],9.0),
           "face":(250,[200,200,200],[210,210,210],2.0),
           "unknown":(0,[150,90,120],None,None),
           "accessory_or_held_object":(44,[30,70,90],[31,71,91],0.01),
           "left_arm":(500,[30,30,30],[30,31,30],0.05),
           "major_clothing":(600,[30,30,30],[30,31,30],0.05),
           "torso":(600,[30,30,30],[30,31,30],0.05),
           "head":(600,[30,30,30],[30,31,30],0.05),
           "neck":(600,[30,30,30],[30,31,30],0.05),
           "lower_body":(600,[30,30,30],[30,31,30],0.05)}
    cases=[]
    review=[]
    packet=[]
    for name in ("GC001","Raden"):
        rows=[{"owner":o,"opaqueVisibleInteriorSourceSamplePixels":v[0],
               "existingPaletteRGB":v[1],"observedSourcePixelCandidateRGB":v[2],
               "measuredMAEGain":v[3]} for o,v in masks.items()]
        cases.append({"case":name,"sourceOwnerCount":11,
                      "semanticCandidateColorApproved":False,"ownerRows":rows})
        review.append({"case":name,"reviewItems":[{"owner":o,"visibleUnoccludedMaskPixels":n[0]}
                            for o,n in masks.items()]})
        packet.append({"case":name,"reviewItems":[{}]*11})
    return {"cases":review},{"cases":cases},{"cases":packet},{"blockedGateCount":8,"releaseAuthorized":False}
def test_original_observed_rgb_medoid_is_actual_pixel():
    a=np.array([[10,20,30],[100,110,120],[14,24,34]],dtype=np.uint8)
    assert r45.observed_medoid(a) in a.tolist()
def test_empty_source_roi_never_yields_invented_rgb():
    with pytest.raises(ValueError):
        r45.observed_medoid(np.zeros((0,3),dtype=np.uint8))
def test_r46_large_source_hair_contrast_requires_semantic_review():
    review,colors,packet,r6=sample()
    rows=r46.evaluate(review,colors,packet,r6)
    assert rows[0]["ownerReview"][1]["status"]=="POTENTIAL_SEMANTIC_OWNER_OR_PALETTE_CONFLICT"
    assert next(r for r in rows[0]["ownerReview"] if r["owner"]=="face")["criticalOwnerProtected"]
    assert next(r for r in rows[0]["ownerReview"] if r["owner"]=="unknown")["status"]=="NO_VISIBLE_SOURCE_SAMPLES"
    assert next(r for r in rows[0]["ownerReview"] if r["owner"]=="accessory_or_held_object")["status"]=="INSUFFICIENT_OPAQUE_INTERIOR_SOURCE"
def test_r48_cannot_grant_palette_release():
    a,b,c,d=sample()
    rows=r46.evaluate(a,b,c,d)
    assert r46.gate(rows,d)["productionReleaseAuthorized"] is False
    rows[0]["ownerReview"][0]["experimentalPalettePromotionAuthorized"]=True
    with pytest.raises(ValueError,match="R48"):
        r46.gate(rows,d)
def test_r48_forged_r6_blockers_rejected():
    a,b,c,d=sample()
    d["blockedGateCount"]=0
    with pytest.raises(ValueError,match="R48"):
        r46.evaluate(a,b,c,d)
def test_source_readonly_and_no_product_route_mutations():
    for source in ("verify_public_r44_source_owner_review_boards",
                   "verify_public_r45_visible_source_palette",
                   "verify_public_r46_r48_color_risk_gate"):
        for path in ("web/static/public-route.js","local_worker/frontend/local-route.js"):
            assert source not in (ROOT/path).read_text(encoding="utf8")
