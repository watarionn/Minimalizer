import json
from minimalizer_zerobase.core.coordinates import CoordinateSpace
from minimalizer_zerobase.analyzers.contracts import Evidence, Provenance
from minimalizer_zerobase.scene.models import Scene, Subject, Region, Relation
from minimalizer_zerobase.geometry.models import PrimitiveCandidate, Primitive


def test_coordinate_normalization_invariant():
    px = CoordinateSpace(200, 100, "pixel")
    assert px.normalize_point(50, 25) == (0.25, 0.25)
    norm = CoordinateSpace(200, 100, "normalized")
    assert norm.denormalize_point(0.25, 0.25) == (50.0, 25.0)


def test_canonical_schema_json_round_trip_and_version():
    cs = CoordinateSpace(640, 480)
    ev = Evidence("e1", "contour", cs, Provenance("test", "1"), 0.8, "person", {"bbox":[1,2,3,4]}, {"method":"identity"})
    scene = Scene(cs, "test", "1", (Subject("s1","person",("r1",),1,0.9),), (Region("r1","body",("e1",),1,0.9),), (Relation("s1","r1","inside",1),))
    candidate = PrimitiveCandidate("c1","rectangle","r1",{"xywh":[1,2,3,4]},{"coverage":0.9})
    primitive = Primitive("p1","c1","r1","skin",1,{"source":"test"},{"coverage":0.9})
    for obj in (ev, scene, candidate, primitive):
        payload = obj.to_json()
        assert json.loads(payload) == obj.to_dict()
        assert json.loads(payload)["schema_version"] == "1.0"


def test_serialization_is_deterministic():
    cs = CoordinateSpace(10, 10)
    a = Evidence("e","x",cs,Provenance("p","1"),geometry={"z":1,"a":2})
    assert a.to_json() == a.to_json()
    assert a.to_json().index('"a"') < a.to_json().index('"z"')
