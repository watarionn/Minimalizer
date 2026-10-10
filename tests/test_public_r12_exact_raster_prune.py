"""R12 bounded exact-OpenCV-output vertex reduction research tests."""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import research_public_r12_exact_raster_prune as module
from minimalizer_zerobase.composition.semantic import rasterize_primitive_candidate

OWNERS=("hair","unknown","major_clothing","torso","left_arm","neck","face",
        "right_arm","lower_body","accessory_or_held_object","head")
def fixture(tmp_path,monkeypatch):
    primitives=[]
    for i,owner in enumerate(OWNERS):
        x=5+i*20
        ring=[[float(x),5.0],[float(x+1),5.0],
              [float(x+2),5.0],[float(x+2),7.0],[float(x),7.0]]
        primitives.append({
           "source_mask_owner":owner,
           "source_mask_replay":True,
           "primitive_type":"polygon",
           "primitive_id":"a"+str(i),
           "parameters":{"rings":[{"depth":0,"role":"fill","points":ring}],
                         "components":[ring],"holes":[]},
           "palette_color_rgb":[10,20,30]
        })
    d={"schema":"sa10.34-adaptive-contour-scene-v1",
       "original_source_sha256":"f"*64,"research_only":True,
       "production_authorized":False,"no_new_primitive":True,
       "no_new_material_or_owner":True,
       "coordinate_space":{"pixel_width":340,"pixel_height":340},
       "primitives_back_to_front":primitives}
    path=tmp_path/"private_source.json"
    path.write_text(json.dumps(d),encoding="utf-8")
    monkeypatch.setitem(module.SOURCE,"GC001",("f"*64,44,55))
    return path

def test_source_bound_exact_raster_simplification_positive(tmp_path,monkeypatch):
    src=fixture(tmp_path,monkeypatch)
    output=tmp_path/"private_candidate"
    record=module.evaluate("GC001",src,output)
    assert record["candidateAgainstFrozenAdaptiveOwnerRasterExact"]
    assert record["originalOwnersAndPalettesRetained"]
    assert record["adaptiveStage8InputVertices"]==55
    assert record["candidateVertices"]<55
    assert record["reducedVertices"]>0
    assert record["releaseAuthorized"] is False
    assert record["originalSourceTopologicalAndSemanticParityProven"] is False
    old=json.loads(src.read_text())["primitives_back_to_front"]
    new=json.loads((output/"GC001_r12_private_raster_exact_scene.json").read_text())["primitives_back_to_front"]
    for a,b in zip(old,new):
        assert a["source_mask_owner"]==b["source_mask_owner"]
        assert a["palette_color_rgb"]==b["palette_color_rgb"]
        assert (rasterize_primitive_candidate(a,width=340,height=340)==
                rasterize_primitive_candidate(b,width=340,height=340)).all()

def test_reject_forged_source_hash_and_protected_owner(tmp_path,monkeypatch):
    src=fixture(tmp_path,monkeypatch)
    contents=json.loads(src.read_text())
    contents["original_source_sha256"]="0"*64
    src.write_text(json.dumps(contents))
    with pytest.raises(ValueError,match="frozen private source authority"):
        module.evaluate("GC001",src,tmp_path/"reject")
    contents["original_source_sha256"]="f"*64
    contents["primitives_back_to_front"][0]["source_mask_owner"]="face"
    src.write_text(json.dumps(contents))
    with pytest.raises(ValueError,match="protected owner missing"):
        module.evaluate("GC001",src,tmp_path/"reject")

def test_refuse_overwriting_and_no_local_or_production_modification(tmp_path,monkeypatch):
    src=fixture(tmp_path,monkeypatch)
    folder=tmp_path/"exists";folder.mkdir()
    with pytest.raises(FileExistsError):
        module.evaluate("GC001",src,folder)
    code=(ROOT/"scripts/research_public_r12_exact_raster_prune.py").read_text(encoding="utf-8")
    assert '"productionPromoted":False' in code
    assert '"releaseAuthorized":False' in code
    for name in ("web/static/public-route.js","local_worker/frontend/local-route.js"):
        assert "research_public_r12_exact_raster_prune" not in (ROOT/name).read_text(encoding="utf-8")
