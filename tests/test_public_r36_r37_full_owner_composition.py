"""R36–R37 exact 11-owner source-color composite and true Chrome regression."""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from verify_public_v34_svgo_chrome import chrome_driver
from verify_public_r30_r35_exact_mask_vectors import browser_pixels
import verify_public_r36_r37_full_owner_composition as r37

OWNERS=("hair","unknown","major_clothing","torso","left_arm","neck",
        "face","right_arm","lower_body","accessory_or_held_object","head")

def fixture():
    records=[]
    for i,name in enumerate(OWNERS):
        x=10+i*18
        points=[[x,40],[x+22,40],[x+22,70],[x,70]]
        records.append({
            "primitive_id":f"p{i}","source_mask_owner":name,
            "primitive_type":"polygon","source_mask_replay":True,
            "palette_color_rgb":[100+i,25+i,180-i],
            "parameters":{"rings":[{"depth":0,"role":"fill","points":points}],
                          "components":[points],"holes":[]}})
    return records

def test_preserve_original_11_source_rgb_palette_z_order_and_shape():
    data=fixture()
    expected=r37.source_owner_reference(data)
    # The last owner is drawn on top in overlap.
    assert expected[50,191].tolist()==data[-1]["palette_color_rgb"]
    assert expected[1,1].tolist()==[255,255,255]
    assert expected.shape==(340,340,3)
    assert expected.dtype==np.dtype("uint8")
    for mode in r37.MODES:
        svg,info=r37.make_owner_scene(data,mode)
        assert info["independentSourceOwnerCount"]==11
        assert info["originalSourceOwnerRGBAndZOrderRetained"]
        assert info["noPhotographicGeneratedPixels"]
        assert info["newRepresentationRectangleCornerOccurrences"]==4*info["rectangles"]
        assert svg.count("<path d=")==11
        assert "base64" not in svg
        assert "data:image" not in svg

def test_true_chrome_composite_equals_original_overlapping_owner_masks_both_dpr():
    owners=fixture()
    source=r37.source_owner_reference(owners)
    driver=chrome_driver()
    try:
        for mode in r37.MODES:
            svg,_=r37.make_owner_scene(owners,mode)
            for scale in (1,2):
                actual=browser_pixels(driver,svg,scale)
                expected=np.repeat(np.repeat(source,scale,axis=0),scale,axis=1)
                assert r37.pixel_diff(actual,expected)["differentPixels"]==0
    finally:driver.quit()

def test_vertical_merge_reduces_original_rectangles_without_owner_invention():
    records=fixture()
    row_svg,row=r37.make_owner_scene(records,"row-runs")
    better_svg,merged=r37.make_owner_scene(records,"vertical-merged")
    assert merged["rectangles"]<row["rectangles"]
    assert merged["wholeSvgBytes"]<row["wholeSvgBytes"]
    assert merged["wholeSvgGzip9Bytes"]>0
    assert len(row["wholeSvgSHA256"])==len(merged["wholeSvgSHA256"])==64

@pytest.mark.parametrize("mutation",("missing","duplicate","wrong_color","negative_color","float_color"))
def test_invalid_source_provenance_palette_and_mask_rejected(mutation):
    records=fixture()
    if mutation=="missing":records.pop()
    if mutation=="duplicate":records[-1]["source_mask_owner"]=records[0]["source_mask_owner"]
    if mutation=="wrong_color":records[0]["palette_color_rgb"]=[999,0,0]
    if mutation=="negative_color":records[0]["palette_color_rgb"]=[-1,0,0]
    if mutation=="float_color":records[0]["palette_color_rgb"]=[1.5,2,3]
    with pytest.raises(ValueError,match="R36"):
        r37.source_owner_reference(records)

def test_new_geometry_cost_must_not_be_mislabeled_historical_stage8_vertices():
    code=(ROOT/"scripts/verify_public_r36_r37_full_owner_composition.py").read_text()
    assert "newRectangleCornerCountIsNotOldStage8VertexBudget" in code
    assert '"originalSourcePhotoSemanticOwnerSHA256"' not in code
    assert '"releaseAuthorized":False' in code
    assert '"sourcePhotoSemanticOwnerProofAvailable":False' in code
    for file in ("web/static/public-route.js","web/static/browser-fallback.js",
                 "local_worker/frontend/local-route.js"):
        assert "verify_public_r36_r37_full_owner_composition" not in (
            ROOT/file).read_text(encoding="utf-8")
