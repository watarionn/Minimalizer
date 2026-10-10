"""R19 source-geometric SVG encoding and real Chrome dual-DPR gates."""
from __future__ import annotations
import copy
import sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from research_public_r19_lossless_svg_paths import (
    ring_d,owner_svg,scene_svg,finite_lattice,ENCODINGS,VERSION)
from verify_public_r17_chrome_owner import svg_for_owner
from verify_public_r18_dual_renderer_prune import chrome_candidates
from verify_public_v34_svgo_chrome import chrome_driver

OWNERS=("hair","lower_body","right_arm","face","torso","major_clothing",
        "unknown","left_arm","neck","head","accessory_or_held_object")

def primitive(i):
    x=8+i*28
    rings=[
        {"depth":0,"role":"fill","points":[[x,10],[x+17,10],
                                             [x+17,29],[x,29]]},
        {"depth":1,"role":"hole","points":[[x+5,16],[x+11,16],
                                             [x+11,23],[x+5,23]]},
        {"depth":0,"role":"fill","points":[[x+18,12]]},
        {"depth":0,"role":"fill","points":[[x+20,16],[x+22,17]]},
    ]
    return {"primitive_id":str(i),"source_mask_owner":OWNERS[i],
            "primitive_type":"polygon","source_mask_replay":True,
            "palette_color_rgb":[31+i,120+i,80],
            "parameters":{"rings":rings}}

def test_compact_lossless_svg_retains_source_coordinates_and_path_commands():
    square=[[12,13],[13,13],[23,13],[23,25],[12,25]]
    a=ring_d(square,"implicit-absolute")
    b=ring_d(square,"axis-relative")
    assert a=="M12.5,13.5 13.5,13.5 23.5,13.5 23.5,25.5 12.5,25.5Z"
    assert b=="M12.5,13.5h1h10v12h-11Z"
    assert len(b)<len(a)
    for candidate in (a,b):
        assert candidate[0]=="M" and candidate[-1]=="Z"

def test_never_round_or_invent_fractional_vertices():
    for bad in (0.25,12.3,float("nan"),float("inf"),True,"3"):
        with pytest.raises((ValueError,OverflowError,TypeError)):
            finite_lattice(bad)
    with pytest.raises(ValueError,match="unknown"):
        ring_d([[1,1],[2,2],[3,3]],"curves")
    with pytest.raises(ValueError,match="degenerate"):
        ring_d([[1,1],[2,2]],"axis-relative")

def test_micro_contours_holes_and_original_source_owners_retained():
    p=primitive(0)
    initial=copy.deepcopy(p)
    old=svg_for_owner(p)
    for mode in ENCODINGS:
        version=owner_svg(p,mode)
        assert version.count("<mask ")==1
        assert version.count("<path ")==1
        assert version.count("<line ")==1
        assert version.count("<rect ")>=2
        assert 'fill-rule="evenodd"' in version
        assert 'mask-type="luminance"' in version
        assert 'fill="#1f7850"' in version
        assert len(version)<len(old)
        assert p==initial

def test_only_singleton_and_tiny_rings_need_no_path_rewrite():
    p=primitive(0)
    p["parameters"]["rings"]=p["parameters"]["rings"][2:]
    assert owner_svg(p,"axis-relative")==svg_for_owner(p)
    assert owner_svg(p,"implicit-absolute")==svg_for_owner(p)

def test_exact_real_chrome_native_and_dpr2_for_alternate_path_formats():
    p=primitive(0)
    baseline=svg_for_owner(p)
    candidates=[owner_svg(p,encoding) for encoding in ENCODINGS]
    driver=chrome_driver()
    try:
        data=chrome_candidates(driver,baseline,candidates)
        assert all(row["d340"]==row["d680"]==0 for row in data)
        composite=[primitive(i) for i in range(11)]
        a=scene_svg(composite,["literal"]*11)
        b=scene_svg(composite,["axis-relative"]*11)
        checks=chrome_candidates(driver,a,[b])
        assert checks==[{"d340":0,"d680":0}]
        # Geometry-altering negative control must always be detected.
        changed=copy.deepcopy(p)
        changed["parameters"]["rings"][0]["points"][1][0]+=8
        altered=owner_svg(changed,"axis-relative")
        negative=chrome_candidates(driver,baseline,[altered])[0]
        assert negative["d340"]>0 and negative["d680"]>0
    finally:
        driver.quit()

def test_composite_must_preserve_all_original_owner_count():
    with pytest.raises(ValueError,match="11-owner"):
        scene_svg([primitive(0)],["axis-relative"])
    with pytest.raises(ValueError,match="11-owner"):
        scene_svg([primitive(i) for i in range(11)],["axis-relative"])

def test_research_only_and_no_local_or_public_runtime_writes():
    text=(ROOT/"scripts/research_public_r19_lossless_svg_paths.py").read_text(encoding="utf-8")
    assert '"productionPromotionAuthorized":False' in text
    assert '"sourceOriginalRingVerticesModified":0' in text
    assert '"sourceSemanticFaceArmsTieStaffApproved":False' in text
    for relative in ("web/static/public-route.js",
                     "web/static/browser-fallback.js",
                     "local_worker/frontend/local-route.js"):
        assert "research_public_r19_lossless_svg_paths" not in (
            ROOT/relative).read_text(encoding="utf-8")
