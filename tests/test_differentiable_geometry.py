import copy
import torch
from minimalizer_zerobase.compose.composer import ComposedPrimitive, VectorScene
from minimalizer_zerobase.refine.backend import TorchSoftRasterBackend
from minimalizer_zerobase.refine.geometry import GeometryProposal, apply_geometry_proposals, finite_difference_step
from minimalizer_zerobase.refine.optimizer import refine_primitive

def _scene(kind="rectangle", parameters=None):
    if parameters is None:
        parameters={"bbox":[8.0,9.0,12.0,10.0]}
    return VectorScene(64,64,(
        ComposedPrimitive("primitive:r1","r1","candidate:r1",kind,parameters,"#ffffff",0,()),
    ),{"producer":"test"})

def test_geometry_proposal_preserves_topology_and_semantics():
    before=_scene()
    after=apply_geometry_proposals(before,(GeometryProposal("primitive:r1",{"bbox":[12.,9.,21.,30.]}),))
    assert len(after.primitives)==len(before.primitives)
    assert after.primitives[0].primitive_id==before.primitives[0].primitive_id
    assert after.primitives[0].fill_ref==before.primitives[0].fill_ref
    assert after.provenance["geometry_refinement"]["topology_changed"] is False

def test_geometry_proposal_rejects_unknown_primitive():
    try: apply_geometry_proposals(_scene(),(GeometryProposal("missing",{"bbox":[0.,0.,1.,1.]}),))
    except ValueError as exc: assert "unknown primitive" in str(exc)
    else: raise AssertionError("expected ValueError")

def test_backend_independent_geometry_step_reduces_synthetic_loss():
    target={"x":15.0,"y":7.0}
    def loss(p): return (p["x"]-target["x"])**2+(p["y"]-target["y"])**2
    before={"x":10.0,"y":10.0}
    after=finite_difference_step(before,loss,learning_rate=0.2)
    assert loss(after)<loss(before)

def test_rectangle_refinement_reduces_loss_without_mutation():
    s=_scene()
    original=copy.deepcopy(s.primitives[0].parameters)
    b=TorchSoftRasterBackend()
    target=b.rectangle(torch.tensor([24.,22.,18.,15.]),64,64).detach()
    result=refine_primitive(s,"primitive:r1",target,steps=80,learning_rate=.35,backend=b)
    assert result.final_loss < result.initial_loss * .25
    assert s.primitives[0].parameters == original
    assert result.scene.primitives[0].parameters != original

def test_ellipse_refinement_reduces_loss():
    s=_scene("ellipse",{"cx":18.0,"cy":17.0,"rx":6.0,"ry":8.0})
    b=TorchSoftRasterBackend()
    target=b.ellipse(torch.tensor([35.,31.,11.,14.]),64,64).detach()
    result=refine_primitive(s,"primitive:r1",target,steps=60,learning_rate=.35,backend=b)
    assert result.final_loss < result.initial_loss * .35
    p=result.scene.primitives[0].parameters
    assert p["rx"] >= 1 and p["ry"] >= 1
