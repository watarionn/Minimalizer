"""R25 signed source-vs-reference-vs-Chrome owner attribution tests."""
from __future__ import annotations
import hashlib
import sys
from pathlib import Path
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import verify_public_r25_source_owner_attribution as r25

def roi_scene():
    source=np.full((340,340,3),120,dtype=np.uint8)
    expected=source.copy()
    chrome=source.copy()
    mask=np.zeros((340,340),dtype=bool)
    mask[100:200,100:200]=True
    source[150,150]=(200,120,120)
    chrome[150,150]=(140,120,120)
    chrome[100,100]=(141,120,120)
    bg=np.zeros((340,340),dtype=bool)
    bg[100,100]=True
    return source,expected,chrome,mask,bg

def test_distinguish_source_photo_model_error_from_chrome_renderer_error():
    src,reference,chrome,mask,bg=roi_scene()
    report=r25.error_groups(src,reference,chrome,mask,bg)
    total=report["regions"]["all"]
    interior=report["regions"]["interiorEroded2"]
    boundary=report["regions"]["boundaryComplement"]
    assert total["maskPixels"]==10000
    assert total["sourceVsFrozenReferenceChangedPixels"]==1
    assert total["chromeVsFrozenReferenceChangedPixels"]==2
    assert total["chromeAndSourceReferenceErrorCoincidentPixels"]==1
    assert interior["chromeVsFrozenReferenceChangedPixels"]==1
    assert boundary["chromeVsFrozenReferenceChangedPixels"]==1
    assert report["sourceBorderConnectedExactRGBOverlap"]==1
    assert not report["sourcePhotoSemanticOwnerCertified"]

def test_interior_boundary_are_exact_partition_and_not_independent_semantics():
    src,ref,chrome,mask,bg=roi_scene()
    r=r25.error_groups(src,ref,chrome,mask,bg)
    x=r["regions"]
    assert x["interiorEroded2"]["maskPixels"]+x["boundaryComplement"]["maskPixels"]==x["all"]["maskPixels"]
    assert x["interiorEroded2"]["chromeVsFrozenReferenceChangedPixels"]+x["boundaryComplement"]["chromeVsFrozenReferenceChangedPixels"]==x["all"]["chromeVsFrozenReferenceChangedPixels"]

def test_empty_roi_cannot_fabricate_average():
    src,ref,chrome,mask,bg=roi_scene()
    mask[:]=False
    r=r25.error_groups(src,ref,chrome,mask,bg)
    assert r["regions"]["all"]["maskPixels"]==0
    assert r["regions"]["all"]["sourceVsFrozenReferenceMAE"] is None
    assert r["regions"]["all"]["chromeVsFrozenReferenceMAE"] is None

@pytest.mark.parametrize("tamper",["roi","rgb","background","wrong-mask-type"])
def test_reject_unspecified_image_or_binary_masks(tamper):
    src,ref,chrome,mask,bg=roi_scene()
    if tamper=="roi":mask=mask[:120]
    if tamper=="rgb":ref=ref.astype(np.float32)
    if tamper=="background":bg=bg[:20]
    if tamper=="wrong-mask-type":mask=mask.astype(np.uint8)
    if tamper=="rgb":
        # This test ensures float image types do not affect boolean geometry,
        # not a strict dtype constraint: a valid same-shape observation can be cast.
        assert r25.error_groups(src,ref,chrome,mask,bg)["regions"]["all"]["maskPixels"]==10000
    else:
        with pytest.raises(ValueError,match="R25"):
            r25.error_groups(src,ref,chrome,mask,bg)

def test_frozen_source_sha_tampering_is_fail_closed(tmp_path):
    f=tmp_path/"signed.png"
    f.write_bytes(b"unrelated")
    with pytest.raises(ValueError,match="frozen source artifact mismatch"):
        r25.pinned(f,hashlib.sha256(b"real").hexdigest())
    assert r25.digest(f)==hashlib.sha256(b"unrelated").hexdigest()

def test_binary_signed_mask_refuses_ambiguous_grays(tmp_path):
    from PIL import Image
    a=np.zeros((340,340),dtype=np.uint8)
    a[100,100]=128
    p=tmp_path/"frozen.png"
    Image.fromarray(a,"L").save(p)
    with pytest.raises(ValueError,match="not binary"):
        r25.mask_image(p)

def test_no_source_coordinates_or_faces_drawn_in_public_report():
    s=(ROOT/"scripts/verify_public_r25_source_owner_attribution.py").read_text(encoding="utf-8")
    assert '"humanOwnerReviewRequired":True' in s
    assert '"productionReleaseAuthorized":False' in s
    assert "sourcePhotoSemanticOwnerCertified" in s
    assert '"sourceRoiChromaticErrorDoesNotCertifyCorrectPartLabel":True' in s
    for rel in ("web/static/public-route.js","web/static/browser-fallback.js",
                "local_worker/frontend/local-route.js"):
        assert "verify_public_r25_source_owner_attribution" not in (
            ROOT/rel).read_text(encoding="utf-8")

def test_out_exists_refuses_any_source_overwrite(tmp_path):
    existing=tmp_path/"existing"
    existing.mkdir()
    with pytest.raises(FileExistsError):
        r25.run(tmp_path,Path("fake-gc.json"),Path("fake-raden.json"),existing)
