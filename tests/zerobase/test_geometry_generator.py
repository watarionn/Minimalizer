from copy import deepcopy
import pytest
from minimalizer_zerobase.core.coordinates import CoordinateSpace
from minimalizer_zerobase.geometry import PrimitiveFamilyPolicy, PrimitiveGenerator
from minimalizer_zerobase.scene.models import Region, Scene

SPACE=CoordinateSpace(100,100)

def scene():
    return Scene(SPACE,"test","1",regions=(
        Region("body","coat",geometry={"bbox":[10,20,40,60]}),
        Region("face","face",geometry={"bbox":[20,5,20,20]}),
        Region("bg","background",geometry={"bbox":[0,0,100,100]}),
    ))

def test_generates_multiple_candidates_without_selecting_winner():
    out=PrimitiveGenerator().generate(scene())
    body=[x for x in out if x.source_region_id=="body"]
    assert {x.primitive_type for x in body}=={"rectangle","trapezoid","convex_polygon"}
    assert all({"coverage","silhouette","complexity","angularity"} <= x.metrics.keys() for x in body)
    assert len({x.candidate_id for x in out})==len(out)

def test_semantic_family_policy_is_explicit():
    out=PrimitiveGenerator().generate(scene())
    assert [x.primitive_type for x in out if x.source_region_id=="bg"]==["rectangle"]
    assert {x.primitive_type for x in out if x.source_region_id=="face"}=={"ellipse","convex_polygon","rectangle"}
def test_replay_and_input_order_are_stable_and_source_immutable():
    src=scene(); before=deepcopy(src.to_dict())
    a=PrimitiveGenerator().generate(src)
    rev=Scene(src.coordinate_space,src.producer,src.producer_version,
              regions=tuple(reversed(src.regions)))
    b=PrimitiveGenerator().generate(rev)
    assert a==b
    assert src.to_dict()==before

def test_metrics_expose_complexity_tradeoff():
    out=PrimitiveGenerator().generate(scene())
    body={x.primitive_type:x for x in out if x.source_region_id=="body"}
    assert body["rectangle"].metrics["coverage"] > body["convex_polygon"].metrics["coverage"]
    assert body["rectangle"].metrics["complexity"] < body["convex_polygon"].metrics["complexity"]

def test_invalid_or_tiny_geometry_is_fail_closed_or_skipped():
    bad=Scene(SPACE,"t","1",regions=(Region("x","coat",geometry={"bbox":[0,0,-1,2]}),))
    with pytest.raises(ValueError):
        PrimitiveGenerator().generate(bad)
    tiny=Scene(SPACE,"t","1",regions=(Region("x","coat",geometry={"bbox":[0,0,.5,.5]}),))
    assert PrimitiveGenerator(PrimitiveFamilyPolicy(min_area=1)).generate(tiny)==()
