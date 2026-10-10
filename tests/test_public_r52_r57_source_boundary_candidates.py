"""R52–R57 immutable source-photo boundary research and browser exactness."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import verify_public_r52_r57_source_boundary_candidates as r57
from verify_public_v34_svgo_chrome import chrome_driver

def sample_mask():
    mask=np.zeros((340,340),dtype=bool)
    mask[95:180,75:140]=True
    return mask

def test_signed_boundary_is_strict_one_pixel_outer_and_inner():
    mask=sample_mask()
    b=r57.signed_boundary(mask)
    assert b[95,75] and b[94,75] and b[180,75]
    assert not b[93,75] and not b[98,80]
    assert int(b.sum())>0

def test_source_topology_observes_real_holes_and_components():
    mask=sample_mask()
    x=r57.topology(mask)
    assert x["connectedComponents8"]==1
    assert x["holeContours"]==0
    mask[120:125,100:105]=False
    assert r57.topology(mask)["holeContours"]==1
    mask[200:210,240:250]=True
    assert r57.topology(mask)["connectedComponents8"]==2

def test_photo_gradient_has_two_independent_color_spaces():
    array=np.zeros((340,340,3),dtype=np.uint8)
    array[:,:170]=(30,90,120)
    array[:,170:]=(150,90,120)
    lum,chroma=r57.gradients(array)
    assert lum.shape==chroma.shape==(340,340)
    assert float(lum[:,170].mean())>0
    assert float(chroma[:,170].mean())>0
    with pytest.raises(ValueError,match="R52"):
        r57.gradients(array[:300])

def test_r55_rejects_connected_component_split_despite_better_source_gradient():
    before=sample_mask()
    after=before.copy()
    after[110:180,108]=False
    vals={"changedMaskPixels":70,"sourceMaskAreaRatioChanged":0.01,
          "changedOutsideSignedOnePixelBoundary":0,
          "changedProtectedOtherOwnerPixels":0}
    old={"sourcePhotoLumGradientMean":20,"sourcePhotoLabChromaGradientMean":20}
    new={"sourcePhotoLumGradientMean":34,"sourcePhotoLabChromaGradientMean":24}
    decision=r57.guard(before,after,vals,old,new)
    assert not decision["passForResearchPreviewOnly"]
    assert "SOURCE_MASK_TOPOLOGY_CHANGED" in decision["rejectionReasons"] or (
       decision["experimentalTopology"]["holeContours"]!=decision["originalTopology"]["holeContours"])
    assert decision["productGeometryAdoptionAuthorized"] is False

def test_r55_rejects_small_edge_gain_or_negative_chroma():
    before=sample_mask();after=before.copy();after[95,75]=False
    vals={"changedMaskPixels":1,"sourceMaskAreaRatioChanged":0.001,
          "changedOutsideSignedOnePixelBoundary":0,"changedProtectedOtherOwnerPixels":0}
    old={"sourcePhotoLumGradientMean":20,"sourcePhotoLabChromaGradientMean":20}
    new={"sourcePhotoLumGradientMean":21,"sourcePhotoLabChromaGradientMean":18}
    decision=r57.guard(before,after,vals,old,new)
    assert "NO_SIGNIFICANT_LUMINANCE_EDGE_SUPPORT" in decision["rejectionReasons"]
    assert "CHROMA_EDGE_EVIDENCE_WORSENED" in decision["rejectionReasons"]

def test_r55_rejects_threshold_or_source_owner_escape():
    before=sample_mask();after=before.copy();after[95,75]=False
    vals={"changedMaskPixels":1,"sourceMaskAreaRatioChanged":0.051,
          "changedOutsideSignedOnePixelBoundary":1,"changedProtectedOtherOwnerPixels":1}
    old={"sourcePhotoLumGradientMean":20,"sourcePhotoLabChromaGradientMean":20}
    new={"sourcePhotoLumGradientMean":26,"sourcePhotoLabChromaGradientMean":21}
    decision=r57.guard(before,after,vals,old,new)
    assert "BOUNDARY_CHANGE_TOO_LARGE" in decision["rejectionReasons"]
    assert "SOURCE_MASK_TRUST_REGION_VIOLATED" in decision["rejectionReasons"]

def test_real_chrome_source_one_pixel_delta_bitexact_on_both_dpr():
    before=sample_mask();after=before.copy();after[95,75]=False
    driver=chrome_driver()
    try:
        data=r57.chrome_compare(driver,before,after)
    finally:
        driver.quit()
    for encoding in ("row-runs","vertical-merged"):
        for scale in ("1","2"):
            audit=data[encoding][scale]
            assert audit["byteExactOriginalAndCandidateChrome"]
            assert audit["changedOutsideOriginalSignedDifferencePixels"]==0
            assert audit["pixelChanges"]==int(scale)**2

def test_research_only_no_source_photo_or_runtime_modification():
    source=(ROOT/"scripts/verify_public_r52_r57_source_boundary_candidates.py").read_text(encoding="utf8")
    for snippet in ('"productionReleaseAuthorized":False',
                    '"existingFaceMicrofeaturesRendered":False',
                    '"originalStage8BudgetPass":False'):
        assert snippet in source
    for runtime in ("web/static/public-route.js","web/static/browser-fallback.js",
                    "local_worker/frontend/local-route.js"):
        assert "verify_public_r52_r57_source_boundary_candidates" not in (
           ROOT/runtime).read_text(encoding="utf8")
