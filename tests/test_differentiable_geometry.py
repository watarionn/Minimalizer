from minimalizer_zerobase.compose.composer import ComposedPrimitive, VectorScene
from minimalizer_zerobase.refine.geometry import GeometryProposal, apply_geometry_proposals, finite_difference_step

def _scene():
    return VectorScene(100, 100, (
        ComposedPrimitive("primitive:r1", "r1", "candidate:r1", "rectangle",
                          {"x": 10.0, "y": 10.0, "width": 20.0, "height": 30.0},
                          "#ffffff", 0, ()),
    ), {"producer": "test"})

def test_geometry_proposal_preserves_topology_and_semantics():
    before = _scene()
    after = apply_geometry_proposals(before, (
        GeometryProposal("primitive:r1", {"x": 12.0, "y": 9.0, "width": 21.0, "height": 30.0}),
    ))
    assert len(after.primitives) == len(before.primitives)
    assert after.primitives[0].primitive_id == before.primitives[0].primitive_id
    assert after.primitives[0].fill_ref == before.primitives[0].fill_ref
    assert after.primitives[0].parameters["x"] == 12.0
    assert after.provenance["geometry_refinement"]["topology_changed"] is False

def test_geometry_proposal_rejects_unknown_primitive():
    try:
        apply_geometry_proposals(_scene(), (GeometryProposal("missing", {"x": 0.0}),))
    except ValueError as exc:
        assert "unknown primitive" in str(exc)
    else:
        raise AssertionError("expected ValueError")

def test_backend_independent_geometry_step_reduces_synthetic_loss():
    target = {"x": 15.0, "y": 7.0}
    def loss(p):
        return (p["x"] - target["x"]) ** 2 + (p["y"] - target["y"]) ** 2
    before = {"x": 10.0, "y": 10.0}
    after = finite_difference_step(before, loss, learning_rate=0.2)
    assert loss(after) < loss(before)
