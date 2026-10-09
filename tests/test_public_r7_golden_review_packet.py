"""R7 non-invasive frozen-source Golden packet tests."""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path
from PIL import Image
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from build_public_r7_golden_review import CASES, PANEL, REVIEW_FIELDS, execute, review_canvas

def digest(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def fixture(root:Path):
    v32=root/"v32";v34=root/"v34";r4=root/"r4"
    for p in (v32,v34,r4):
        p.mkdir()
    items32=[];items34=[]
    for i,name in enumerate(CASES):
        rgb=(30+i*30,60,180)
        for suffix,color in (
            ("source",(245,230,10,255)),
            ("anime_seg_mask",(255,255,255,255)),
            ("facet",(10,20,30,255)),
            ("connected_fine",(*rgb,255)),
        ):
            p=v32/f"{name}_{suffix}.png"
            Image.new("RGBA",(340,340),color).save(p)
            items32.append({"name":p.name,"sha256":digest(p.read_bytes())})
        orig=(v32/f"{name}_connected_fine.png").read_bytes()
        chrome=v34/f"{name}_local_safe_chrome.png"
        chrome.write_bytes(orig)
        svg=v34/f"{name}_local_safe.svg"
        svg.write_text("<svg></svg>",encoding="utf-8")
        items34 += [{"name":f.name,"sha256":digest(f.read_bytes())} for f in (chrome,svg)]
        (r4/f"{name}_chrome_340.png").write_bytes(orig)
    (v32/"v32_evidence_manifest.json").write_text(json.dumps({"files":items32}))
    (v34/"v34_evidence_manifest.json").write_text(json.dumps({"files":items34}))
    r6=root/"public_r6_release_no_go.json"
    r6.write_text(json.dumps({
        "version":"public-r6-conservative-release-admission-v1",
        "status":"NO_GO","releaseAuthorized":False,"blockedGateCount":8
    }))
    return (v32,v34,r4,r6)

def test_complete_source_contact_sheet_and_unsigned_verdict(tmp_path):
    a=fixture(tmp_path)
    result=execute(*a,tmp_path/"r7")
    assert result["allThreeSourceOriginalsIncluded"]
    assert result["allFrozenCrossVersionsPixelExact"]
    assert result["status"]=="PENDING_HUMAN_REVIEW_NO_GO"
    assert result["releaseAuthorized"] is False
    for case in result["cases"]:
        assert case["reviewStatus"]=="PENDING"
        assert len(case["humanPartReview"])==len(REVIEW_FIELDS)
        assert all(x is None for x in case["humanPartReview"].values())
        assert case["partROIAutomaticallyInvented"] is False
        assert case["frozenV32VsV34PixelDiff"]==0
        assert case["independentR4ChromeVsV34PixelDiff"]==0
        img=Image.open(tmp_path/"r7"/case["reviewGalleryFile"])
        assert img.size[0]>=340*3
        assert img.size[1]>=340*2
    review=(tmp_path/"r7"/"GOLDEN_HUMAN_REVIEW_PENDING.md").read_text(encoding="utf-8")
    assert review.count("Human Golden decision: **PENDING**")==3
    assert review.count("overallQualityHumanGolden")==3

def test_modified_frozen_source_aborts_before_creating_artifacts(tmp_path):
    a=fixture(tmp_path)
    path=a[0]/"Kyoko_source.png"
    Image.new("RGBA",(340,340),(1,2,3,255)).save(path)
    output=tmp_path/"r7"
    with pytest.raises(ValueError,match="SHA mismatch"):
        execute(*a,output)
    assert not output.exists()

def test_forged_r6_release_pass_aborts(tmp_path):
    a=fixture(tmp_path)
    a[3].write_text(json.dumps({
        "version":"public-r6-conservative-release-admission-v1",
        "status":"GO","releaseAuthorized":True,"blockedGateCount":0}))
    with pytest.raises(ValueError,match="NO_GO"):
        execute(*a,tmp_path/"r7")
    assert not (tmp_path/"r7").exists()

def test_changed_v34_or_r4_artifact_aborts(tmp_path):
    a=fixture(tmp_path)
    Image.new("RGBA",(340,340),(50,50,50,255)).save(
        a[2]/"Noel_chrome_340.png")
    with pytest.raises(ValueError,match="do not agree"):
        execute(*a,tmp_path/"r7")
    assert not (tmp_path/"r7").exists()

def test_output_overwrite_and_production_route_isolation(tmp_path):
    a=fixture(tmp_path)
    dest=tmp_path/"r7";dest.mkdir()
    with pytest.raises(FileExistsError):
        execute(*a,dest)
    script=(ROOT/"scripts/build_public_r7_golden_review.py").read_text(encoding="utf-8")
    assert '"releaseAuthorized":False' in script
    assert 'sourceSegmentationSemanticAuthority' in script
    for file in ("web/static/public-route.js",
                 "web/static/browser-fallback.js",
                 "local_worker/frontend/local-route.js"):
        code=(ROOT/file).read_text(encoding="utf-8")
        assert "build_public_r7_golden_review" not in code
