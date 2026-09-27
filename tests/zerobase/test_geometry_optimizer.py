from copy import deepcopy
import pytest
from minimalizer_zerobase.compose import SemanticComposer
from minimalizer_zerobase.core.coordinates import CoordinateSpace
from minimalizer_zerobase.geometry import PrimitiveCandidate, PrimitiveGenerator
from minimalizer_zerobase.optimize import GeometryObjectivePolicy, GeometryOptimizer
from minimalizer_zerobase.palette import MaterialAssignment
from minimalizer_zerobase.scene.models import Region, Scene

SPACE = CoordinateSpace(100, 100)

def scene():
    return Scene(SPACE, "test", "1", regions=(
        Region("body", "coat", geometry={"bbox": [10, 20, 40, 60]}),
        Region("face", "face", geometry={"bbox": [20, 5, 20, 20]}),
        Region("bg", "background", geometry={"bbox": [0, 0, 100, 100]}),
    ))

def materials():
    return (
        MaterialAssignment("bg", "#fff", "#fff", (), True, 1.0, "disposable"),
        MaterialAssignment("body", "#123", "#123", (), True, 1.0, "preserve"),
        MaterialAssignment("face", "#fac", "#fac", (), True, 1.0, "protect"),
    )

def test_selects_deterministically_with_inspectable_costs():
    src = scene()
    candidates = PrimitiveGenerator().generate(src)
    out = GeometryOptimizer().optimize(src, candidates)
    assert set(out.selections) == {"bg", "body", "face"}
    assert out.provenance["selection_authority"] == "GeometryOptimizer"
    for decision in out.decisions:
        assert set(decision.costs) == {
            "coverage", "silhouette", "complexity", "angularity", "semantic", "undercoverage"
        }
    assert out.selections["bg"] == "bg:rectangle"

def test_quality_gate_rejects_low_coverage_even_if_complexity_is_low():
    src = Scene(SPACE, "t", "1", regions=(Region("r", "coat", geometry={"bbox":[0,0,10,10]}),))
    bad = PrimitiveCandidate("bad", "triangle", "r", {}, {
        "coverage": .5, "silhouette": .99, "complexity": 0, "angularity": 1.0})
    good = PrimitiveCandidate("good", "rectangle", "r", {}, {
        "coverage": .9, "silhouette": .9, "complexity": 4, "angularity": 1.0})
    out = GeometryOptimizer().optimize(src, (bad, good))
    assert out.selections == {"r": "good"}
    assert out.decisions[0].rejected_candidate_ids == ("bad",)

def test_all_quality_gate_failures_fail_closed():
    src = Scene(SPACE, "t", "1", regions=(Region("r", "coat", geometry={"bbox":[0,0,10,10]}),))
    bad = PrimitiveCandidate("bad", "triangle", "r", {}, {
        "coverage": .2, "silhouette": .2, "complexity": 1, "angularity": 1.0})
    with pytest.raises(ValueError, match="no candidate passes quality gates"):
        GeometryOptimizer().optimize(src, (bad,))

def test_tie_breaking_replay_and_input_order_are_stable():
    src = Scene(SPACE, "t", "1", regions=(Region("r", "unknown", geometry={"bbox":[0,0,10,10]}),))
    metrics = {"coverage": .9, "silhouette": .9, "complexity": 4, "angularity": .5}
    a = PrimitiveCandidate("a", "rectangle", "r", {}, metrics)
    b = PrimitiveCandidate("b", "rectangle", "r", {}, metrics)
    one = GeometryOptimizer().optimize(src, (b, a))
    two = GeometryOptimizer().optimize(src, (a, b))
    assert one == two
    assert one.selections == {"r": "a"}

def test_source_is_immutable_and_result_feeds_composer():
    src = scene()
    before = deepcopy(src.to_dict())
    candidates = PrimitiveGenerator().generate(src)
    optimized = GeometryOptimizer().optimize(src, candidates)
    vector = SemanticComposer().compose(src, candidates, optimized.selections, materials())
    assert {p.source_region_id: p.selected_candidate_id for p in vector.primitives} == optimized.selections
    assert src.to_dict() == before

def test_missing_metrics_unknown_regions_and_duplicates_fail_closed():
    src = scene()
    candidate = PrimitiveCandidate("x", "rectangle", "body", {}, {"coverage":1.0})
    with pytest.raises(ValueError, match="missing required"):
        GeometryOptimizer().optimize(src, (candidate,))
    unknown = PrimitiveCandidate("u", "rectangle", "nope", {}, {
        "coverage":1.0, "silhouette":1.0, "complexity":4, "angularity":1.0})
    with pytest.raises(ValueError, match="unknown region"):
        GeometryOptimizer().optimize(src, (unknown,))
    valid = PrimitiveGenerator().generate(src)[0]
    with pytest.raises(ValueError, match="duplicate"):
        GeometryOptimizer().optimize(src, (valid, valid))

def test_policy_can_change_tradeoff_without_hiding_dimensions():
    src = Scene(SPACE, "t", "1", regions=(Region("r", "unknown", geometry={"bbox":[0,0,10,10]}),))
    simple = PrimitiveCandidate("simple", "rectangle", "r", {}, {
        "coverage": .8, "silhouette": .8, "complexity": 1, "angularity": .5})
    faithful = PrimitiveCandidate("faithful", "rectangle", "r", {}, {
        "coverage": 1.0, "silhouette": 1.0, "complexity": 8, "angularity": .5})
    default = GeometryOptimizer().optimize(src, (simple, faithful))
    simplicity = GeometryOptimizer(GeometryObjectivePolicy(
        coverage_weight=.1, silhouette_weight=.1, complexity_weight=1.0,
        min_coverage=.7, min_silhouette=.65)).optimize(src, (simple, faithful))
    assert default.selections["r"] == "faithful"
    assert simplicity.selections["r"] == "simple"
