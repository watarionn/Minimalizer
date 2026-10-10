"""R30–R35 exact signed binary pixel vector tests and release fail-closed."""
from __future__ import annotations
import copy
import json
import sys
from pathlib import Path
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import verify_public_r30_r35_exact_mask_vectors as r35
from verify_public_v34_svgo_chrome import chrome_driver
from research_public_r12_exact_raster_prune import SOURCE

def binary_fixture()->np.ndarray:
    mask=np.zeros((340,340),dtype=bool)
    mask[0:22,0:35]=True
    mask[3:8,5:12]=False
    mask[20:34,10:60]=True
    mask[50:105,100:101]=True
    mask[337:340,338:340]=True
    return mask

def test_true_pixel_rectangle_roundtrip_with_holes_borders_and_thin_shapes():
    expected=binary_fixture()
    row=r35.pixel_runs(expected)
    merged=r35.vertical_merge(row)
    assert len(merged)<len(row)
    assert np.array_equal(r35.rectangles_mask(row),expected)
    assert np.array_equal(r35.rectangles_mask(merged),expected)
    assert min(x for x,_,_,_ in merged)==0
    assert any(x+w==340 and y+h==340 for x,y,w,h in merged)
    assert all(w>0 and h>0 for x,y,w,h in merged)
    assert r35.vertical_merge(row)==r35.vertical_merge(row)

def test_true_stage04_binary_mask_only_and_never_bitmap_embed():
    expected=binary_fixture()
    for mode in r35.MODES:
        svg,meta=r35.exact_svg(expected,mode)
        assert svg.startswith('<svg xmlns="http://www.w3.org/2000/svg"')
        assert "shape-rendering=\"crispEdges\"" in svg
        assert "<path d=\"" in svg
        assert "data:image" not in svg
        assert "base64" not in svg
        assert meta["rasterReconstructionExact"]
        assert meta["maskPixels"]==int(expected.sum())
        assert len(meta["svgSHA256"])==64
    a=r35.exact_svg(expected,"row-runs")[1]
    b=r35.exact_svg(expected,"vertical-merged")[1]
    assert b["encodedRectangles"]<a["encodedRectangles"]
    assert b["rawSvgBytes"]<a["rawSvgBytes"]

@pytest.mark.parametrize("wrong",("size","float","grays","negative","unsupported-mode"))
def test_nonbinary_or_malformed_source_geometry_is_rejected(wrong):
    mask=binary_fixture()
    if wrong=="size":mask=mask[:300]
    elif wrong=="float":mask=mask.astype(np.float32)
    elif wrong=="grays":mask=mask.astype(np.uint8)*128
    if wrong in ("size","float","grays"):
        with pytest.raises(ValueError,match="signed owner"):
            r35.exact_svg(mask,"row-runs")
    elif wrong=="negative":
        with pytest.raises(ValueError,match="rectangle"):
            r35.rectangles_mask([(340,12,2,1)])
    elif wrong=="unsupported-mode":
        with pytest.raises(ValueError,match="unknown"):
            r35.exact_svg(mask,"compressedImage")

def test_overlapping_rectangles_rejected_without_silent_union():
    with pytest.raises(ValueError,match="overlapping"):
        r35.rectangles_mask([(0,0,10,10),(4,4,8,8)])

def test_real_chrome_signed_bitmask_exact_at_both_dpr_and_no_leaked_edit():
    original=binary_fixture()
    changed=original.copy()
    changed[12:15,15:22]=False
    delete=original&~changed
    driver=chrome_driver()
    try:
        for mode in r35.MODES:
            a,_=r35.assert_chrome_exact(driver,original,mode)
            b,_=r35.assert_chrome_exact(driver,changed,mode)
            assert a["ChromeAndSignedMaskBothDprPixelExact"]
            assert b["ChromeAndSignedMaskBothDprPixelExact"]
            assert a["actualChrome340DifferentPixels"]==0
            assert a["actualChrome680DifferentPixels"]==0
            delta=r35.pair_compare(driver,original,changed,delete,mode)
            assert delta["signedMaskRasterDeltaExact"]
            assert all(v["extraChangedPixelsOutsideSourceDeletedMask"]==0 for v in delta["perDpr"].values())
            assert delta["perDpr"]["1"]["realChromeBeforeAfterChangedPixels"]==21
            assert delta["perDpr"]["2"]["realChromeBeforeAfterChangedPixels"]==84
            assert not delta["candidateSemanticallyApproved"]
    finally:driver.quit()

def test_negative_claims_of_unobserved_pixel_deletion_are_rejected():
    original=binary_fixture()
    candidate=original.copy()
    candidate[13,16]=False
    with pytest.raises(ValueError,match="R34"):
        r35.pair_compare(None,original,candidate,np.zeros((340,340),dtype=bool),"row-runs")
    with pytest.raises(ValueError,match="R34"):
        r35.pair_compare(None,original,original,original&~candidate,"row-runs")

def test_semantic_observer_cannot_issue_auto_approval():
    row=r35.classify_semantic_anchors({"approved":False})
    assert row["sourcePixelOwnershipSemanticStatus"]=="ABSTAIN"
    assert row["independentSourceOnlyModelSigned"] is False
    assert row["independentHumanOwnerAnnotationSigned"] is False
    assert row["originalStage04MaskMayBeIncorrect"] is True
    with pytest.raises(ValueError,match="R30"):
        r35.classify_semantic_anchors({"approved":True})

def fake_gate_row(case):
    return {"case":case,"frozenStage8Vertices":SOURCE[case][2],
       "historicOriginalStage8Cap":r35.ORIGINAL_STAGE8_CAP[case],
       "sourceSemantics":r35.classify_semantic_anchors({"approved":False}),
       "runAndMergedSignedMaskChromeAllExact":True,
       "candidateChangeWithoutSvgSpillExact":True,
       "ownerMaskCount":14,"approvedToChangeProduct":False}

def fake_r6():
    return {"status":"NO_GO","blockedGateCount":8,"releaseAuthorized":False,
            "blockedGates":[{"gate":str(i)} for i in range(8)]}

def test_release_holds_even_with_perfect_technical_mask_browser_parity():
    r=r35.release_gate([fake_gate_row(x) for x in r35.CASES],fake_r6())
    assert r["R31"]=="EXACT_SCANLINE_SOURCE_VECTORS"
    assert r["R32"]=="REVERSIBLE_VERTICAL_RECTANGLE_MERGE"
    assert r["R34"]=="SOURCE_PIXEL_DELETION_CHROME_DELTA_EXACT_NOT_SEMANTICS"
    assert r["originalSourcePhotoSemanticOwnerPass"] is False
    assert r["historicStage8VertexBudgetPass"] is False
    assert r["productionReleaseAuthorized"] is False

@pytest.mark.parametrize("path,value",[
    ("frozenStage8Vertices",20),("historicOriginalStage8Cap",6000),
    ("runAndMergedSignedMaskChromeAllExact",False),
    ("candidateChangeWithoutSvgSpillExact",False),
    ("ownerMaskCount",13),("approvedToChangeProduct",True)])
def test_fake_budget_chrome_coverage_or_product_promotion_refused(path,value):
    rows=[fake_gate_row(x) for x in r35.CASES]
    rows[0][path]=value
    with pytest.raises(ValueError,match="R35"):
        r35.release_gate(rows,fake_r6())

def test_unsigned_release_r6_cannot_silently_unlock():
    rows=[fake_gate_row(x) for x in r35.CASES]
    gate=fake_r6();gate["blockedGateCount"]=0
    with pytest.raises(ValueError,match="R35"):
        r35.release_gate(rows,gate)

def test_no_changes_to_original_photo_or_runtime_public_local():
    source=(ROOT/"scripts/verify_public_r30_r35_exact_mask_vectors.py").read_text(encoding="utf-8")
    assert '"productionReleaseAuthorized":False' in source
    assert '"faceMicrofeaturesGenerated":False' in source
    assert '"originalSignedMasksChanged":False' in source
    for name in ("web/static/public-route.js","web/static/browser-fallback.js",
                 "local_worker/frontend/local-route.js"):
        assert "verify_public_r30_r35_exact_mask_vectors" not in (
            ROOT/name).read_text(encoding="utf-8")
