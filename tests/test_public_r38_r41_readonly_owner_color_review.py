"""R38 signed source-free evidence review safety tests."""
import sys,json,copy
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import verify_public_r38_r41_readonly_owner_color_review as audit
OWNERS=audit.PRIORITY
def fixtures():
    def region():
        full={"maskPixels":10,"sourceVsFrozenReferenceMAE":12.5,"chromeVsFrozenReferenceMAE":1.4}
        inside={"maskPixels":7,"chromeVsFrozenReferenceChangedPixels":2}
        edge={"maskPixels":3,"chromeVsFrozenReferenceChangedPixels":1}
        return {"regions":{"all":full,"interiorEroded2":inside,"boundaryComplement":edge},
                "sourceBorderConnectedExactRGBOverlap":0}
    a={"cases":[{"case":c,"signedStage8OriginalVertices":cnt,
       "stage8SourceOwnedRegions":{name:region() for name in OWNERS}}
       for c,cnt in (("GC001",3604),("Raden",2370))]}
    b={"cases":[{"case":c,"ownerMaskCount":14,"frozenStage8Vertices":cnt,
       "historicOriginalStage8Cap":cap,"runAndMergedSignedMaskChromeAllExact":True}
       for c,cnt,cap in (("GC001",3604,1887),("Raden",2370,1412))]}
    c={"cases":[{"case":"GC001"},{"case":"Raden"}]}
    return a,b,c
def test_strict_source_and_chrome_error_separate():
    a,b,c=fixtures()
    r=audit.evaluate(a,b,c)
    assert len(r)==2
    assert r[0]["reviewQueue"][0]["owner"]=="right_arm"
    assert r[0]["reviewQueue"][0]["sourceVsReferenceRgbMAE"]==12.5
    assert r[0]["reviewQueue"][0]["chromeVsReferenceRgbMAE"]==1.4
    assert all(x["experimentalPaletteMutationAuthorized"] is False
               for y in r for x in y["reviewQueue"])
def test_existing_release_blocks_auto_palette():
    a,b,c=fixtures()
    rows=audit.evaluate(a,b,c)
    accepted=audit.hold(rows,{"blockedGateCount":8,"status":"NO_GO","releaseAuthorized":False})
    assert accepted["productionReleaseAuthorized"] is False
    with pytest.raises(ValueError):
        audit.hold(rows,{"blockedGateCount":0,"status":"GO","releaseAuthorized":True})
def test_forged_stage8_fails():
    a,b,c=fixtures()
    b["cases"][0]["frozenStage8Vertices"]=10
    with pytest.raises(ValueError):
        audit.evaluate(a,b,c)
def test_incomplete_owner_fails():
    a,b,c=fixtures()
    a["cases"][0]["stage8SourceOwnedRegions"].pop("right_arm")
    with pytest.raises(ValueError):
        audit.evaluate(a,b,c)
def test_source_file_mutation_rejected(tmp_path):
    f=tmp_path/"audit.json"
    f.write_text("{}",encoding="utf8")
    with pytest.raises(ValueError,match="SHA"):
        audit.frozen(f,"r25")
def test_original_product_files_unchanged():
    source=(ROOT/"scripts/verify_public_r38_r41_readonly_owner_color_review.py").read_text()
    assert '"signedMasksOrColorsModified":False' in source
    assert '"originalPhotosAccessed":False' in source
    for path in ("web/static/public-route.js","local_worker/frontend/local-route.js"):
        assert "verify_public_r38_r41_readonly_owner_color_review" not in (ROOT/path).read_text()
