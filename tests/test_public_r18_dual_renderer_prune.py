"""R18 Stage8 Chrome DPR1/2 strict acceptance, safety and negative controls."""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from research_public_r12_exact_raster_prune import SOURCE
import research_public_r18_dual_renderer_prune as r18
from research_public_r17_consecutive_vertex_prune import masks
from verify_public_v34_svgo_chrome import chrome_driver
from verify_public_r17_chrome_owner import svg_for_owner

OWNERS=("hair","unknown","major_clothing","torso","left_arm","neck","face",
        "right_arm","lower_body","accessory_or_held_object","head")

def owner_fixture(i=0):
    pts=[[12.,13.],[13.,13.],[23.,13.],[23.,25.],[12.,25.]]
    return {"primitive_id":f"id-{i}","source_mask_owner":OWNERS[i],
            "palette_color_rgb":[20+i,50,80],"source_mask_replay":True,
            "primitive_type":"polygon","composition_part":OWNERS[i],
            "parameters":{"rings":[{"depth":0,"role":"fill","points":pts}],
                          "components":[pts],"holes":[]}}

def synthetic(tmp_path,monkeypatch):
    parts=[owner_fixture(i) for i in range(11)]
    original={"schema":"sa10.34-adaptive-contour-scene-v1",
      "original_source_sha256":"a"*64,"research_only":True,
      "production_authorized":False,"no_new_primitive":True,
      "no_new_material_or_owner":True,
      "coordinate_space":{"pixel_width":340,"pixel_height":340},
      "primitives_back_to_front":parts}
    src=tmp_path/"signed.json"
    raw=json.dumps(original,ensure_ascii=False).encode()
    src.write_bytes(raw)
    monkeypatch.setitem(SOURCE,"GC001",("a"*64,44,55))
    monkeypatch.setitem(r18.SCENE_SHA256,"GC001",hashlib.sha256(raw).hexdigest())
    proposed=json.loads(raw)
    for p in proposed["primitives_back_to_front"]:
        p["parameters"]["rings"][0]["points"].pop(1)
    candidate=tmp_path/"r17-private.json"
    candidate.write_text(json.dumps(proposed),encoding="utf-8")
    record={"case":"GC001",
            "privateCandidateSHA256":r18.sha(candidate.read_bytes()),
            "original11SourceOwnerRasterPreservedByteExact":True,
            "productionReleaseAuthorized":False}
    audit=tmp_path/"r17-audit.json"
    audit.write_text(json.dumps(record),encoding="utf-8")
    return src,candidate,audit

def test_removed_source_vertex_subsequence_and_forged_geometry():
    assert r18.missing_original_indices([[1],[2],[3],[4]],[[1],[3]])==[1,3]
    assert r18.missing_original_indices([[1],[2],[2],[3]],[[1],[2],[3]])==[2]
    with pytest.raises(ValueError,match="unmatched"):
        r18.missing_original_indices([[1],[2]],[[1],[88]])

def test_source_hash_and_candidate_hash_fail_closed(tmp_path,monkeypatch):
    s,c,a=synthetic(tmp_path,monkeypatch)
    obj=json.loads(c.read_text())
    obj["primitives_back_to_front"][0]["parameters"]["rings"][0]["points"][0]=[99.,99.]
    c.write_text(json.dumps(obj),encoding="utf-8")
    with pytest.raises(ValueError,match="unsigned"):
        r18.confirm_source_and_r17("GC001",s,c,a)
    s.write_text(s.read_text()+" ")
    with pytest.raises(ValueError,match="immutable signed source SHA"):
        r18.confirm_source_and_r17("GC001",s,c,a)

def test_opencv_single_candidate_is_not_implicitly_chrome_approved():
    a=owner_fixture()
    b=json.loads(json.dumps(a))
    b["parameters"]["rings"][0]["points"].pop(1)
    expected=masks([a],340,340)["hair"]
    checks=r18.micro_candidates(a,a,b,expected,340,340)
    assert len(checks)>=1
    assert checks[0][2]["parameters"]["rings"][0]["points"]!=a["parameters"]["rings"][0]["points"]
    assert r18.masks([a],340,340)["hair"]==expected

def test_real_chrome_native_and_dpr2_negative_and_positive():
    source=svg_for_owner(owner_fixture())
    same=svg_for_owner(owner_fixture())
    changed=owner_fixture()
    changed["parameters"]["rings"][0]["points"]=[[18.,13.],[23.,13.],
                                                   [23.,25.],[12.,25.]]
    other=svg_for_owner(changed)
    driver=chrome_driver()
    driver.set_script_timeout(120)
    try:
        row=r18.chrome_candidates(driver,source,[same,other])
    finally:
        driver.quit()
    assert row[0]["d340"]==0 and row[0]["d680"]==0
    # A deliberately substantial geometry mutation must register as nonexact.
    assert row[1]["d340"]>0 or row[1]["d680"]>0

def test_missing_or_preexisting_private_output_refused(tmp_path,monkeypatch):
    s,c,a=synthetic(tmp_path,monkeypatch)
    folder=tmp_path/"already"
    folder.mkdir()
    with pytest.raises(FileExistsError):
        r18.evaluate("GC001",s,c,a,folder)

def test_never_false_claims_public_golden_or_local_promotion():
    code=(ROOT/"scripts/verify_public_r18_dual_renderer_prune.py").read_text(encoding="utf-8")
    for required in ('"productionReleaseAuthorized":False',
                     '"humanSemanticSourceOwnershipSigned":False',
                     '"trueStage8OriginalRasterVsOfficialStage04Approved":False'):
        assert required in code
    for path in ("web/static/public-route.js","web/static/browser-fallback.js",
                 "local_worker/frontend/local-route.js"):
        assert "verify_public_r18_dual_renderer_prune" not in (
            ROOT/path).read_text(encoding="utf-8")
