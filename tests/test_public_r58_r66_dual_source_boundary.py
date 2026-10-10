"""R58-R66 source-photo dual-objective research: exact mask and nonrelease tests."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from verify_public_v34_svgo_chrome import chrome_driver
from verify_public_r30_r35_exact_mask_vectors import browser_pixels
import verify_public_r58_r61_conservative_source_boundary as r61
import verify_public_r62_r66_dual_photo_color_edge as r66

def scene():
    roles=("hair","unknown","major_clothing","torso","left_arm","neck",
           "face","right_arm","lower_body","accessory_or_held_object","head")
    records=[]
    for i,role in enumerate(roles):
        x=9+i*19
        points=[[x,60],[x+23,60],[x+23,89],[x,89]]
        records.append({"primitive_id":f"p{i}","source_mask_owner":role,
           "primitive_type":"polygon","source_mask_replay":True,
           "palette_color_rgb":[30+i,80+i,160-i],
           "parameters":{"rings":[{"depth":0,"role":"fill","points":points}],
                        "components":[points],"holes":[]}})
    return records

def test_r62_complete_11_owner_original_palette_z_order_preserved():
    records=scene()
    image=r66.compose_rgb(records)
    assert image.shape==(340,340,3)
    assert image[1,1].tolist()==[255,255,255]
    assert image[75,220].tolist()==records[-1]["palette_color_rgb"]
    assert image[75,45].tolist()==records[1]["palette_color_rgb"]

def test_r63_photo_favorable_source_pixel_only():
    records=scene()
    old=r66.compose_rgb(records)
    new=old.copy()
    rgba=np.dstack((old,np.full((340,340),255,dtype=np.uint8)))
    y,x=80,35
    rgba[y,x,:3]=0
    new[y,x]=[0,0,0]
    chosen=r66.select_photo_favorable_pixels(records,old,new,rgba)
    assert chosen.sum()==1
    assert chosen[y,x]
    rgba[y,x,3]=0
    assert not r66.select_photo_favorable_pixels(records,old,new,rgba)[y,x]

def test_r64_rejects_photo_color_worsening_source_diff():
    records=scene()
    old=r66.compose_rgb(records)
    rgba=np.dstack((old,np.full((340,340),255,dtype=np.uint8)))
    bad=old.copy()
    bad[75,35]=[0,0,0]
    with pytest.raises(ValueError,match="R64"):
        r66.gate_source_and_edges(old,bad,bad,rgba)

def test_r64_accepts_only_photo_better_and_no_unsigned_promotion():
    records=scene()
    old=r66.compose_rgb(records)
    rgba=np.dstack((old,np.full((340,340),255,dtype=np.uint8)))
    rgba[80,35,:3]=0
    better=old.copy()
    better[80,35]=[0,0,0]
    report=r66.gate_source_and_edges(old,better,better,rgba)
    assert report["conservativePhotoAndEdgeCandidateCompositePixelsChanged"]==1
    assert report["originalPhotoRgbImprovedChangedPixels"]==1
    assert report["originalPhotoRgbWorsenedChangedPixels"]==0
    assert report["productionPaletteOrShapeApproved"] is False

def test_r61_selected_source_delta_never_invents_outside_previous_candidate():
    orig=np.zeros((340,340),dtype=bool)
    orig[60:150,75:130]=True
    attempted=orig.copy()
    attempted[60,75]=False
    photo=np.full((340,340,3),220,dtype=np.uint8)
    photo[60:150,75:130]=(60,50,40)
    trial,metadata=r61.select_topology_preserving_delta(photo,orig,attempted)
    assert metadata["selectedPixelsOnlyFromPriorR52SignedSourceBand"]
    assert metadata["sourceAnatomyGroundTruthSigned"] is False
    assert not np.any((trial^orig)&~(attempted^orig))

def test_r59_independent_source_edge_does_not_certify_photo_anatomy():
    orig=np.zeros((340,340),dtype=bool)
    orig[60:150,75:130]=True
    image=np.full((340,340,3),220,dtype=np.uint8)
    image[60:150,75:130]=(20,70,40)
    report=r61.independent_source_boundary_review(image,orig,orig)
    assert report["independentGradientGain"]==0
    assert report["independentCannyCoincidenceGain"]==0
    assert report["notAnIndependentAnatomicalSegmentation"] is True

def test_r65_genuine_chrome_rgb_zorder_composite_dpr1_and_2():
    records=scene()
    original=r66.compose_rgb(records)
    svg=r66.scene_svg(records,{})
    driver=chrome_driver()
    try:
        for scale in (1,2):
            actual=browser_pixels(driver,svg,scale)
            target=np.repeat(np.repeat(original,scale,axis=0),scale,axis=1)
            assert np.array_equal(actual,target)
    finally:
        driver.quit()

def test_r66_no_face_generated_and_product_release_no_go():
    source=(ROOT/"scripts/verify_public_r62_r66_dual_photo_color_edge.py").read_text(encoding="utf8")
    for expected in ('"productionReleaseAuthorized":False',
                     '"newFaceFeaturesGenerated":False',
                     '"originalStage8VertexBudgetPassed":False'):
        assert expected in source
    for program in ("verify_public_r58_r61_conservative_source_boundary",
                    "verify_public_r62_r66_dual_photo_color_edge"):
        for path in ("web/static/public-route.js","web/static/browser-fallback.js",
                     "local_worker/frontend/local-route.js"):
            assert program not in (ROOT/path).read_text(encoding="utf8")
