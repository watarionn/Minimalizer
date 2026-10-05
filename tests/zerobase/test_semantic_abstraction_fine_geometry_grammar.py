import numpy as np
from minimalizer_zerobase.parts.decomposition import PART_NAMES
from minimalizer_zerobase.structure.graph import build_structural_layout_graph
from minimalizer_zerobase.semantic_abstraction.fine_geometry_grammar import (
    build_fine_geometry_primitives,reserve_fine_part_budget,
)


def _fixture():
    rgb=np.full((120,100,3),220,np.uint8)
    m={n:np.zeros((120,100),bool) for n in PART_NAMES}
    for n,b in {"head":(20,5,80,65),"hair":(15,3,85,70),"face":(32,30,68,62),"major_clothing":(18,65,82,115),"accessory_or_held_object":(75,72,92,88),"torso":(20,65,80,110)}.items():
        x0,y0,x1,y1=b;m[n][y0:y1,x0:x1]=1
    rgb[24:34,24:76]=(35,45,55)
    rgb[68:83,44:56]=(80,210,45)
    return rgb,m


def test_budget_reserves_eyewear_before_lower_priority_parts():
    got=reserve_fine_part_budget(("hair_front","eyewear","collar"),2)
    assert got=={"eyewear":2}


def test_budget_is_bounded_and_deterministic():
    cats=("major_accessory","eyewear","hair_front","collar")
    a=reserve_fine_part_budget(cats,5);b=reserve_fine_part_budget(tuple(reversed(cats)),5)
    assert a==b and sum(a.values())<=5


def test_eyewear_grammar_uses_multiple_bounded_primitives():
    rgb,m=_fixture();g=build_structural_layout_graph(m)
    rows=build_fine_geometry_primitives(rgb,m,g,primitive_budget=10)
    eye=[x for x in rows if x.semantic_part=="eyewear"]
    assert len(eye)>=2
    assert len(eye)<=3
    assert all(x.family in ("ellipse","convex_polygon") for x in eye)
    assert all(int(x.mask.sum())>0 for x in eye)


def test_face_is_never_a_fine_geometry_primitive():
    rgb,m=_fixture();g=build_structural_layout_graph(m)
    rows=build_fine_geometry_primitives(rgb,m,g,primitive_budget=10)
    assert all(x.semantic_part!="face" for x in rows)


def test_zero_budget_emits_no_fine_geometry():
    rgb,m=_fixture();g=build_structural_layout_graph(m)
    assert build_fine_geometry_primitives(rgb,m,g,primitive_budget=0)==()
