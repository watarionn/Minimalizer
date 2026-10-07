import numpy as np

from minimalizer_zerobase.compose.composer import ComposedPrimitive, VectorScene
from minimalizer_zerobase.refine.constrained_diffvg import run_constrained_diffvg
from minimalizer_zerobase.refine.geometry import GeometryProposal


def _scene():
    p = ComposedPrimitive("arm", "arm", "c", "rectangle", {"bbox": [3, 4, 4, 4]}, "#fff", 1, ())
    torso = ComposedPrimitive("torso", "torso", "t", "rectangle", {"bbox": [2, 2, 8, 10]}, "#aaa", 0, ())
    return VectorScene(20, 20, (torso, p), {})


def _masks(scene):
    out = np.zeros((20, 20), bool)
    arm = np.zeros_like(out)
    torso = np.zeros_like(out)
    x, y, w, h = map(int, scene.primitives[1].parameters["bbox"])
    arm[y:y+h, x:x+w] = True
    x, y, w, h = map(int, scene.primitives[0].parameters["bbox"])
    torso[y:y+h, x:x+w] = True
    return {"left_arm": arm, "torso": torso}


def _rgb(scene):
    image = np.zeros((20, 20, 3), np.uint8)
    image[_masks(scene)["left_arm"]] = 255
    return image


def _run(scene, source, proposal):
    source_rgb = np.zeros((20, 20, 3), np.uint8)
    source_rgb[source["left_arm"]] = 255
    return run_constrained_diffvg(scene, source_masks=source, candidate_masks=_masks,
                                  source_rgb=source_rgb, candidate_rgb=_rgb,
                                  proposals=(proposal,))


def test_unavailable_diffvg_is_explicit_noop(monkeypatch):
    monkeypatch.setattr("minimalizer_zerobase.refine.constrained_diffvg.backend_available", lambda _: False)
    result = _run(_scene(), _masks(_scene()), GeometryProposal("arm", {"bbox": [4, 4, 4, 4]}))
    assert result.backend == "fallback_noop"
    assert not result.optimized and result.proposals[0].reason == "diffvg-unavailable-fallback-noop"


def test_safe_contour_move_is_accepted_when_backend_available(monkeypatch):
    monkeypatch.setattr("minimalizer_zerobase.refine.constrained_diffvg.backend_available", lambda _: True)
    scene = _scene()
    target = _scene()
    target.primitives[1].parameters["bbox"] = [4, 4, 4, 4]
    source = _masks(target)
    # The proposal is the existing primitive moved toward the source contour.
    result = _run(scene, source, GeometryProposal("arm", {"bbox": [4, 4, 4, 4]}))
    assert result.proposals[0].accepted


def test_arm_detaching_proposal_rolls_back(monkeypatch):
    monkeypatch.setattr("minimalizer_zerobase.refine.constrained_diffvg.backend_available", lambda _: True)
    scene = _scene(); source = _masks(scene)
    result = _run(scene, source, GeometryProposal("arm", {"bbox": [15, 15, 2, 2]}))
    assert result.proposals[0].rollback and "hard-gate" in result.proposals[0].reason


def test_face_rounding_topology_break_is_rolled_back(monkeypatch):
    monkeypatch.setattr("minimalizer_zerobase.refine.constrained_diffvg.backend_available", lambda _: True)
    scene = _scene(); source = _masks(scene)
    result = _run(scene, source, GeometryProposal("arm", {"bbox": [0, 0, 20, 20]}))
    assert result.proposals[0].rollback
