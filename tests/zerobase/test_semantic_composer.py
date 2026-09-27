from copy import deepcopy
import pytest
from minimalizer_zerobase.compose import SemanticComposer
from minimalizer_zerobase.core.coordinates import CoordinateSpace
from minimalizer_zerobase.geometry import PrimitiveGenerator
from minimalizer_zerobase.palette import MaterialAssignment
from minimalizer_zerobase.scene.models import Region, Relation, Scene

SPACE = CoordinateSpace(100, 100)

def source_scene(relations=()):
    return Scene(SPACE, "test", "1", regions=(
        Region("body", "coat", geometry={"bbox": [20, 20, 50, 70]}),
        Region("face", "face", geometry={"bbox": [35, 5, 20, 20]}),
        Region("bg", "background", geometry={"bbox": [0, 0, 100, 100]}),
    ), relations=relations)

def materials():
    return (
        MaterialAssignment("bg", "#ffffff", "#ffffff", (), True, 1.0, "disposable"),
        MaterialAssignment("body", "#112233", "#112233", (), True, 1.0, "preserve"),
        MaterialAssignment("face", "#f0c0a0", "#f0c0a0", (), True, 1.0, "protect"),
    )

def selections(candidates):
    first = {}
    for candidate in candidates:
        first.setdefault(candidate.source_region_id, candidate.candidate_id)
    return first

def test_composes_explicit_selections_without_choosing_winners():
    scene = source_scene()
    candidates = PrimitiveGenerator().generate(scene)
    chosen = selections(candidates)
    out = SemanticComposer().compose(scene, candidates, chosen, materials())
    assert {p.source_region_id: p.selected_candidate_id for p in out.primitives} == chosen
    assert out.provenance["selection_authority"] == "external"
    assert out.primitives[0].source_region_id == "bg"
    assert [p.z_order for p in out.primitives] == list(range(3))

def test_in_front_of_and_behind_normalize_to_occlusion_order():
    scene = source_scene((
        Relation("face", "body", "in_front_of"),
        Relation("bg", "body", "behind"),
    ))
    candidates = PrimitiveGenerator().generate(scene)
    out = SemanticComposer().compose(scene, candidates, selections(candidates), materials())
    z = {p.source_region_id: p.z_order for p in out.primitives}
    assert z["bg"] < z["body"] < z["face"]
    body = next(p for p in out.primitives if p.source_region_id == "body")
    assert body.occluded_by == ("face",)

def test_missing_and_mismatched_references_fail_closed():
    scene = source_scene()
    candidates = PrimitiveGenerator().generate(scene)
    chosen = selections(candidates)
    with pytest.raises(ValueError, match="missing candidate"):
        SemanticComposer().compose(scene, candidates, {**chosen, "face": "missing"}, materials())
    body_candidate = next(c for c in candidates if c.source_region_id == "body")
    with pytest.raises(ValueError, match="wrong region"):
        SemanticComposer().compose(scene, candidates, {**chosen, "face": body_candidate.candidate_id}, materials())
    with pytest.raises(ValueError, match="missing material"):
        SemanticComposer().compose(scene, candidates, chosen, materials()[:-1])

def test_occlusion_cycle_fails_closed():
    scene = source_scene((
        Relation("face", "body", "in_front_of"),
        Relation("body", "face", "in_front_of"),
    ))
    candidates = PrimitiveGenerator().generate(scene)
    with pytest.raises(ValueError, match="cycle"):
        SemanticComposer().compose(scene, candidates, selections(candidates), materials())

def test_replay_input_order_and_source_are_stable():
    scene = source_scene((Relation("face", "body", "in_front_of"),))
    before = deepcopy(scene.to_dict())
    candidates = PrimitiveGenerator().generate(scene)
    chosen = selections(candidates)
    a = SemanticComposer().compose(scene, candidates, chosen, materials())
    reversed_scene = Scene(scene.coordinate_space, scene.producer, scene.producer_version,
        regions=tuple(reversed(scene.regions)), relations=tuple(reversed(scene.relations)))
    b = SemanticComposer().compose(reversed_scene, tuple(reversed(candidates)), chosen,
                                   tuple(reversed(materials())))
    assert a == b
    assert scene.to_dict() == before
