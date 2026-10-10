"""R26–R29 source-only mask candidates, genuine Chrome observer and gate checks."""
from __future__ import annotations
import copy
import json
import sys
from pathlib import Path
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import verify_public_r26_r29_source_owner_candidates as module
from research_public_r12_exact_raster_prune import SOURCE
from research_public_r17_consecutive_vertex_prune import SCENE_SHA256
from verify_public_v34_svgo_chrome import chrome_driver

def example_masks():
    signed=np.zeros((340,340),dtype=bool)
    signed[90:150,100:160]=True
    connected=np.zeros((340,340),dtype=bool)
    connected[110:115,120:125]=True
    alpha=np.full((340,340),255,dtype=np.uint8)
    alpha[110,120]=128
    return signed,connected,alpha

def test_opaque_exact_bg_candidate_only_subtracts_signed_pixels():
    signed,bg,alpha=example_masks()
    source=signed.copy()
    candidate,removed,row=module.isolate_opaque_exact_border_connected(signed,bg,alpha)
    assert np.array_equal(signed,source)
    assert row["originalRightArmPixels"]==3600
    assert row["candidateRightArmPixels"]==3576
    assert row["originalExactConnectedBorderRGBOverlap"]==25
    assert row["removedPixelsFullyOpaqueExactBorderRGB"]==24
    assert row["partiallyTransparentNotAutoRemoved"]==1
    assert row["addedPixels"]==0
    assert row["sourcePhotoSemanticArmTruthEstablished"] is False
    assert row["sourcePixelDeletionCannotEstablishAnatomicalCorrectness"]
    assert not candidate[111,121]
    assert candidate[110,120]
    assert row["additionalContourVerticesVsSignedMask"]>0

@pytest.mark.parametrize("wrong",("shape","mask_dtype","bg_dtype","alpha_type","all_removed"))
def test_unsafe_source_masks_are_rejected(wrong):
    signed,bg,alpha=example_masks()
    if wrong=="shape":signed=signed[:180]
    elif wrong=="mask_dtype":signed=signed.astype(np.uint8)
    elif wrong=="bg_dtype":bg=bg.astype(np.uint8)
    elif wrong=="alpha_type":alpha=alpha.astype(float)
    elif wrong=="all_removed":
        bg[:]=True
        alpha[:]=255
    with pytest.raises(ValueError,match="R26"):
        module.isolate_opaque_exact_border_connected(signed,bg,alpha)

def test_mask_svg_uses_real_source_contours_not_embedded_bitmap():
    signed,bg,alpha=example_masks()
    svg,info=module.owner_mask_svg(signed)
    assert '<mask id="r2629-right"' in svg
    assert "<path " in svg
    assert "data:image" not in svg
    assert "base64" not in svg
    assert info["source_ring_vertices"]>=4

def test_actual_chrome_two_dpr_observer_detects_changes_without_claiming_repair():
    signed,bg,alpha=example_masks()
    proposal,deleted,_=module.isolate_opaque_exact_border_connected(signed,bg,alpha)
    driver=chrome_driver()
    try:
        info,_=module.browser_raster_audit(driver,signed,proposal,deleted)
    finally:
        driver.quit()
    assert set(info["chromeDprRuns"])=={"1","2"}
    assert info["candidateBrowserParityApprovedForProduct"] is False
    assert info["chromeDprRuns"]["1"]["actualChromeBeforeAfterDifferentPixels"]>0
    assert info["chromeDprRuns"]["2"]["actualChromeBeforeAfterDifferentPixels"]>0
    assert info["chromeDprRuns"]["1"]["expectedRemovedOpaqueMaskPixelsScaled"]==24
    assert info["chromeDprRuns"]["2"]["expectedRemovedOpaqueMaskPixelsScaled"]==96
    for scale,row in info["chromeDprRuns"].items():
        assert row["renderedSize"]==340*int(scale)
        assert row["proposedSvgIntroducedNoGeneratedSourceBitmap"] is True
        assert row["chromeChangedPixelsOutsideExpectedDeletedSourceMask"]==(
            row["changedOutsideExactSourceCandidateDeletedPixels"]>0)

def frozen_row(case):
    scan={str(scale):{"renderedSize":340*scale,
                      "originalSignedBinaryExactInChrome":False,
                      "proposedCandidateBinaryExactInChrome":False,
                      "changedOutsideDeletedSignedMaskZero":False}
          for scale in (1,2)}
    return {"case":case,"sourceOriginalSHA256":SOURCE[case][0],
      "signedStage8SceneSHA256":SCENE_SHA256[case],
      "stage8OriginalVertexCount":SOURCE[case][2],
      "historicCap":SOURCE[case][1],
      "R26SourceConnectedOpaqueCandidate":{
        "addedPixels":0,
        "signedLeftAndFaceUnchanged":True,
        "candidateTrustedSemanticCorrection":False,
        "additionalContourVerticesVsSignedMask":4},
      "R27GenuineChrome340And680RasterAudit":{
         "candidateBrowserParityApprovedForProduct":False,
         "chromeDprRuns":scan},
      "R28GeneralizationStatus":"ABSTAIN_SEMANTIC_ANCHOR_MISSING",
      "independentOriginalPhotoSemanticOwnerAnchorPresent":False,
      "releaseAuthorized":False}

def fixture(tmp_path):
    r6=tmp_path/"r6.json"
    r6.write_text(json.dumps({
       "status":"NO_GO","releaseAuthorized":False,
       "blockedGateCount":8,"blockedGates":[{"gate":str(i)} for i in range(8)]}))
    r25={"productionReleaseAuthorized":False,"cases":[{"case":"GC001"},{"case":"Raden"}]}
    return r6,r25

def test_four_phase_release_gate_records_explicit_technical_abstention(tmp_path):
    r6,r25=fixture(tmp_path)
    rows=[frozen_row(c) for c in ("GC001","Raden")]
    gate=module.assert_r29_no_go(rows,r6,r25)
    assert gate["R26"]=="SOURCE_OPAQUE_RGB_CANDIDATE_MEASURED_NOT_ANATOMY"
    assert gate["R27"]=="CANONICAL_340_680_CHROME_MASK_RASTER_DIAGNOSTICS_MEASURED"
    assert gate["R28"]=="TWO_SIGNED_SOURCES_COMPARED_SEMANTIC_ABSTAIN"
    assert gate["R29"]=="EVIDENCE_PACKAGED_AND_PRODUCTION_NO_GO"
    assert gate["originalReleaseBlockedGates"]==8
    assert gate["stage8OriginalBudgetPass"] is False
    assert gate["releaseAuthorized"] is False
    assert gate["productionPromoted"] is False

@pytest.mark.parametrize("path,value",[
    ("stage8OriginalVertexCount",1),
    ("sourceOriginalSHA256","f"*64),
    ("R28GeneralizationStatus","SEMANTIC_PASS"),
    ("independentOriginalPhotoSemanticOwnerAnchorPresent",True),
    ("releaseAuthorized",True),
])
def test_no_forged_source_approval_or_release(tmp_path,path,value):
    r6,r25=fixture(tmp_path)
    rows=[frozen_row(c) for c in ("GC001","Raden")]
    rows[0][path]=value
    with pytest.raises(ValueError,match="R29"):
        module.assert_r29_no_go(rows,r6,r25)

@pytest.mark.parametrize("name,value",[
    ("candidateTrustedSemanticCorrection",True),
    ("signedLeftAndFaceUnchanged",False),
    ("additionalContourVerticesVsSignedMask",0)
])
def test_candidate_cannot_claim_unproven_owner_semantics(tmp_path,name,value):
    r6,r25=fixture(tmp_path)
    rows=[frozen_row(c) for c in ("GC001","Raden")]
    rows[0]["R26SourceConnectedOpaqueCandidate"][name]=value
    with pytest.raises(ValueError,match="R29"):
        module.assert_r29_no_go(rows,r6,r25)

@pytest.mark.parametrize("name,value",[
    ("candidateBrowserParityApprovedForProduct",True),
    ("chromeDprRuns",{"1":{},"2":{}})
])
def test_nonexact_browser_must_remain_no_go(tmp_path,name,value):
    r6,r25=fixture(tmp_path)
    rows=[frozen_row(c) for c in ("GC001","Raden")]
    rows[0]["R27GenuineChrome340And680RasterAudit"][name]=value
    with pytest.raises((ValueError,KeyError),match="R29|renderedSize"):
        module.assert_r29_no_go(rows,r6,r25)

def test_r6_real_release_blockers_may_not_disappear(tmp_path):
    r6,r25=fixture(tmp_path)
    rows=[frozen_row(c) for c in ("GC001","Raden")]
    obj=json.loads(r6.read_text())
    obj["blockedGateCount"]=0
    r6.write_text(json.dumps(obj))
    with pytest.raises(ValueError,match="R29 frozen"):
        module.assert_r29_no_go(rows,r6,r25)

def test_do_not_modify_product_or_hidden_face_specification():
    code=(ROOT/"scripts/verify_public_r26_r29_source_owner_candidates.py").read_text(encoding="utf-8")
    for literal in ('"noGenerativeFill":True','"faceMicrofeaturesEnabled":False',
                    '"releaseAuthorized":False','"gitMainMerged":False'):
        assert literal in code
    for rel in ("web/static/public-route.js","web/static/browser-fallback.js",
                "local_worker/frontend/local-route.js"):
        assert "verify_public_r26_r29_source_owner_candidates" not in (
            ROOT/rel).read_text(encoding="utf-8")
