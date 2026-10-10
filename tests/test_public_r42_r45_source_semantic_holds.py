"""R42 and R45 keep source color proposals unsigned."""
import sys
from pathlib import Path
import numpy as np
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import verify_public_r42_r43_semantic_review_packet as r42
import verify_public_r45_visible_source_palette as r45

def packet_source():
    roles=("right_arm","left_arm","accessory_or_held_object","major_clothing",
           "torso","hair","lower_body","head","neck","face","unknown")
    return {"version":"public-r38-r41-readonly-owner-review-v1",
            "status":"RESEARCH_REVIEW_READY_PRODUCT_NO_GO",
            "cases":[{"case":case,"reviewQueue":[{
               "owner":r,"sourceVsReferenceRgbMAE":10.,
               "chromeVsReferenceRgbMAE":2.,
               "experimentalPaletteMutationAuthorized":False} for r in roles]}
               for case in ("GC001","Raden")]}

def test_r42_all_22_source_review_items_unapproved():
    result=r42.packet(packet_source())
    assert r42.verify(result)
    assert sum(len(x["reviewItems"]) for x in result["cases"])==22
    assert not result["productionReleaseAuthorized"]
def test_r42_face_hidden():
    result=r42.packet(packet_source())
    assert all(next(x for x in c["reviewItems"] if x["owner"]=="face")["reviewAction"]==
               "KEEP_FACE_DETAILS_HIDDEN_NO_REPAINT" for c in result["cases"])
def test_r43_forged_owner_signoff_rejected():
    result=r42.packet(packet_source())
    result["cases"][0]["reviewItems"][0]["candidatePaletteApproved"]=True
    with pytest.raises(ValueError,match="R43"):r42.verify(result)
def test_r43_forged_human_signoff_rejected():
    result=r42.packet(packet_source())
    result["sourceSemanticColorApprovalGranted"]=True
    with pytest.raises(ValueError,match="R43"):r42.verify(result)
def test_r45_medoid_color_must_exist_in_source():
    pixels=np.array([[4,8,12],[20,24,28],[30,34,38]],dtype=np.uint8)
    assert r45.observed_medoid(pixels) in pixels.tolist()
def test_r45_empty_visible_owner_has_no_color_proposal():
    assert r45.mae(np.zeros((0,3),dtype=np.uint8),[10,10,10]) is None
    with pytest.raises(ValueError):r45.observed_medoid(np.zeros((0,3),dtype=np.uint8))
def test_r45_only_readonly_private_source_no_product_route():
    for script in ("verify_public_r42_r43_semantic_review_packet",
                   "verify_public_r45_visible_source_palette"):
        for f in ("web/static/public-route.js","local_worker/frontend/local-route.js"):
            assert script not in (ROOT/f).read_text(encoding="utf8")
