"""R67–R73: photometric signed source masks and release no-go tests."""
import sys
from pathlib import Path
import numpy as np
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import verify_public_r67_r73_photometric_source_stability as r

def photos():
    old=np.full((340,340,3),255,dtype=np.uint8)
    cand=old.copy();cand[25:30,25:30]=[0,0,0]
    source=np.dstack((old,np.full((340,340),255,dtype=np.uint8)))
    source[25:30,25:30,:3]=[0,0,0]
    return old,cand,source

def test_rgb_source_and_lab_sensitivity_is_unsigned():
    old,cand,source=photos()
    snapshot=source.copy()
    mask,diag=r.robust_delta_gate(old,cand,source)
    assert np.array_equal(snapshot,source)
    assert diag["baseChangedSourceOwnedRGBPixels"]==25
    assert diag["sourceOpaqueRgbMAEBetterPixels"]==25
    assert diag["sourcePhotoSemanticsIndependentlyVerified"] is False
    assert diag["productAdoptionAuthorized"] is False

def test_alpha_transparent_cannot_be_changed():
    old,cand,source=photos()
    source[25:30,25:30,3]=100
    mask,diag=r.robust_delta_gate(old,cand,source)
    assert not mask.any()

def test_wrong_photo_shape_rejected():
    old,cand,source=photos()
    with pytest.raises(ValueError,match="R68"):
        r.color_distance(old[:300],source[:300,:,:3])

def test_outside_original_source_one_pixel_band_rejected():
    old=np.zeros((340,340),dtype=bool)
    old[70:150,80:140]=True
    trial=old.copy();trial[200,200]=True
    valid=np.ones((340,340),dtype=bool)
    with pytest.raises(ValueError,match="R69"):
        r.source_owner_subset(np.zeros((340,340,3),dtype=np.uint8),old,trial,valid)

def test_empty_photo_evidence_restores_original_mask():
    old=np.zeros((340,340),dtype=bool)
    old[70:150,80:140]=True
    approved=np.zeros_like(old)
    result,report=r.source_owner_subset(np.full((340,340,3),80,dtype=np.uint8),
                                        old,old.copy(),approved)
    assert np.array_equal(result,old)
    assert report["acceptedOwnerPixels"]==0
    assert report["productionShapeMutationAllowed"] is False

def test_photo_fit_wrong_direction_rejected():
    old,cand,source=photos()
    with pytest.raises(ValueError,match="R70"):
        r.score_final(cand,old,source)

def test_r73_no_semantic_or_product_signoff():
    text=(ROOT/"scripts/verify_public_r67_r73_photometric_source_stability.py").read_text(encoding="utf8")
    assert '"productionReleaseAuthorized":False' in text
    assert '"humanSemanticSourceOwnerCertificationSigned":False' in text
    assert '"historicalStage8RingBudgetPassed":False' in text
    for path in ("web/static/public-route.js","local_worker/frontend/local-route.js"):
        assert "verify_public_r67_r73_photometric_source_stability" not in (ROOT/path).read_text(encoding="utf8")

def test_prior_archive_requires_all_nine_sha_pinned_source_inputs(tmp_path):
    import json
    folder=tmp_path/"private"
    folder.mkdir()
    index=tmp_path/"manifest.json"
    index.write_text(json.dumps({"artifactCount":28,
                                 "productionReleaseAuthorized":False,
                                 "files":[]}),encoding="utf8")
    with pytest.raises(ValueError,match="R67"):
        r.verify_archive(index,folder)
