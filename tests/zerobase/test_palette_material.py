from copy import deepcopy
import pytest
from minimalizer_zerobase.core.coordinates import CoordinateSpace
from minimalizer_zerobase.importance import ImportanceEngine
from minimalizer_zerobase.palette import MaterialEvidence, PaletteMaterialEngine, PalettePolicy
from minimalizer_zerobase.scene.models import Region, Scene, Subject

SPACE = CoordinateSpace(100, 100)

def scene():
    regions = (Region("coat", "coat", confidence=.9, geometry={"bbox":[0,0,60,60]}),
               Region("trim", "identity_accent", confidence=.9, geometry={"bbox":[0,0,5,5]}),
               Region("bg", "background", confidence=.8, geometry={"bbox":[0,0,100,100]}))
    return ImportanceEngine().apply(Scene(SPACE, "test", "1", regions=regions,
        subjects=(Subject("s", "person", ("coat","trim")),)))

def test_material_evidence_separates_base_from_illumination():
    e = MaterialEvidence("coat", (100, 80, 60), ((70, 60, 50), (140, 120, 100)), .8)
    assert e.base_color == (100,80,60)
    assert len(e.illumination_colors) == 2
    with pytest.raises(ValueError):
        MaterialEvidence("x", (999,0,0))

def test_assignment_is_replay_stable_and_illumination_is_not_palette():
    src = scene()
    evidence = [MaterialEvidence("coat",(100,80,60),((50,40,30),)),
                MaterialEvidence("trim",(220,30,40)),
                MaterialEvidence("bg",(105,84,64))]
    engine = PaletteMaterialEngine()
    a = engine.assign(src, evidence)
    b = engine.assign(src, reversed(evidence))
    assert a == b
    assert "#32281e" not in {x.palette_color for x in a}
    assert next(x for x in a if x.region_id=="coat").illumination_disposable

def test_importance_tier_controls_merge_aggressiveness():
    src = scene()
    evidence = [MaterialEvidence("trim",(200,20,20)), MaterialEvidence("coat",(220,20,20)),
                MaterialEvidence("bg",(225,20,20))]
    out = PaletteMaterialEngine(PalettePolicy(merge_distance=40, preserve_merge_distance=25,
        protect_merge_distance=10)).assign(src, evidence)
    by_id = {x.region_id:x for x in out}
    assert by_id["trim"].palette_color == by_id["trim"].base_color
    assert by_id["coat"].palette_color == by_id["trim"].palette_color
    assert by_id["bg"].palette_color in {by_id["trim"].palette_color, by_id["coat"].palette_color}

def test_apply_is_immutable_and_persists_inspectable_assignments():
    src = scene()
    before = deepcopy(src.to_dict())
    out = PaletteMaterialEngine().apply(src, [MaterialEvidence("coat",(10,20,30)),
        MaterialEvidence("trim",(200,30,40)), MaterialEvidence("bg",(12,22,32))])
    assert src.to_dict() == before
    assert out.palette
    assert out.provenance["importance"] == src.provenance["importance"]
    assert out.provenance["palette_material"]["assignments"]

def test_unknown_and_duplicate_region_evidence_fail_closed():
    engine = PaletteMaterialEngine()
    with pytest.raises(ValueError):
        engine.assign(scene(), [MaterialEvidence("missing",(1,2,3))])
    with pytest.raises(ValueError):
        engine.assign(scene(), [MaterialEvidence("coat",(1,2,3)), MaterialEvidence("coat",(2,3,4))])
