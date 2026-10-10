"""R17 pixel-exact adjacent span reductions: positive and negative source checks."""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import research_public_r17_consecutive_vertex_prune as r17
from research_public_r12_exact_raster_prune import SOURCE
from minimalizer_zerobase.composition.semantic import rasterize_primitive_candidate

OWNERS=("hair","unknown","major_clothing","torso","left_arm","neck",
        "face","right_arm","lower_body","accessory_or_held_object","head")

def scene_fixture(tmp_path,monkeypatch):
    prims=[]
    for i,owner in enumerate(OWNERS):
        x=i*27+5
        pts=[[float(x),5.0],[float(x+1),5.0],[float(x+2),5.0],
             [float(x+2),10.0],[float(x),10.0]]
        prims.append({"source_mask_owner":owner,"source_mask_replay":True,
           "composition_part":owner,"primitive_type":"polygon",
           "primitive_id":f"owner-{i}",
           "palette_color_rgb":[i+5,33,100],
           "parameters":{"rings":[{"depth":0,"role":"fill","points":pts}],
                         "components":[pts],"holes":[]}})
    scene={"schema":"sa10.34-adaptive-contour-scene-v1",
       "original_source_sha256":"f"*64,"research_only":True,
       "production_authorized":False,"no_new_primitive":True,
       "no_new_material_or_owner":True,
       "coordinate_space":{"pixel_width":340,"pixel_height":340},
       "primitives_back_to_front":prims}
    raw=json.dumps(scene,ensure_ascii=False).encode()
    path=tmp_path/"signed_PRIVATE_scene.json"
    path.write_bytes(raw)
    monkeypatch.setitem(SOURCE,"GC001",("f"*64,44,55))
    monkeypatch.setitem(r17.SCENE_SHA256,"GC001",hashlib.sha256(raw).hexdigest())
    return path

def test_multi_span_real_raster_positive_and_private_candidate(tmp_path,monkeypatch):
    private=scene_fixture(tmp_path,monkeypatch)
    frozen=private.read_bytes()
    out=tmp_path/"private_output"
    row=r17.run("GC001",private,out)
    assert row["sourceOriginalStage8RingVerticesHistoric"]==55
    assert row["safeVertexReduction"]>0
    assert row["bestExperimentalRingVertices"]<55
    assert row["original11SourceOwnerRasterPreservedByteExact"]
    assert len(row["independentSearchStrategies"])==2
    assert row["productionReleaseAuthorized"] is False
    assert row["chromiumSvgRasterParityApproved"] is False
    assert row["historicalStage8InputWithinCap"] is False
    assert private.read_bytes()==frozen
    old=json.loads(frozen)["primitives_back_to_front"]
    new=json.loads((out/"GC001_r17_PRIVATE_candidate_scene.json").read_text())["primitives_back_to_front"]
    assert len(old)==len(new)==11
    for before,after in zip(old,new):
        assert before["palette_color_rgb"]==after["palette_color_rgb"]
        assert before["source_mask_owner"]==after["source_mask_owner"]
        assert np.array_equal(rasterize_primitive_candidate(before,width=340,height=340),
                              rasterize_primitive_candidate(after,width=340,height=340))

def test_must_refuse_tampered_signed_stage8_private_scene(tmp_path,monkeypatch):
    private=scene_fixture(tmp_path,monkeypatch)
    obj=json.loads(private.read_text())
    obj["primitives_back_to_front"][0]["source_mask_owner"]="face"
    private.write_text(json.dumps(obj),encoding="utf-8")
    with pytest.raises(ValueError,match="exact frozen scene SHA"):
        r17.run("GC001",private,tmp_path/"wrong")

def test_fake_reference_raster_bit_is_detected(tmp_path,monkeypatch):
    private=scene_fixture(tmp_path,monkeypatch)
    obj=json.loads(private.read_text())
    refs=r17.masks(obj["primitives_back_to_front"],340,340)
    refs["left_arm"]=bytes(len(refs["left_arm"]))
    with pytest.raises(AssertionError,match="protection invariant"):
        r17.prune_one(obj,refs,340,340,"forward",max_passes=1)

def test_refuse_overwriting_existing_private_candidate(tmp_path,monkeypatch):
    src=scene_fixture(tmp_path,monkeypatch)
    folder=tmp_path/"old";folder.mkdir()
    with pytest.raises(FileExistsError):
        r17.run("GC001",src,folder)

def test_research_cannot_modify_live_or_local_routes():
    script=(ROOT/"scripts/research_public_r17_consecutive_vertex_prune.py").read_text(encoding="utf-8")
    assert '"productionReleaseAuthorized":False' in script
    assert '"sourcePhotoSemanticOwnershipUserApproved":False' in script
    for rel in ("web/static/public-route.js","local_worker/frontend/local-route.js"):
        assert "research_public_r17_consecutive_vertex_prune" not in (ROOT/rel).read_text(encoding="utf-8")
