from __future__ import annotations

import numpy as np

from minimalizer_zerobase.parts.decomposition import PART_NAMES
from minimalizer_zerobase.semantic_abstraction.semantic_render_guard import (
    build_semantic_render_guard,
)
from minimalizer_zerobase.structure.graph import (
    PartAnchor,
    PartRelation,
    StructuralLayoutGraph,
)


def _masks() -> dict[str, np.ndarray]:
    masks = {name: np.zeros((80, 80), dtype=np.uint8) for name in PART_NAMES}
    masks["head"][8:28, 28:52] = 1
    masks["face"][12:26, 32:48] = 1
    masks["torso"][28:60, 24:56] = 1
    masks["left_arm"][30:62, 14:25] = 1
    masks["right_arm"][30:62, 55:66] = 1
    masks["lower_body"][58:76, 28:52] = 1
    return masks


def _graph() -> StructuralLayoutGraph:
    parts = ("head", "face", "torso", "left_arm", "right_arm", "lower_body")
    anchors = tuple(
        PartAnchor(
            f"{part}:c",
            part,
            "centroid",
            (40.0, 40.0),
            (0.5, 0.5),
            1.0,
            ("synthetic",),
        )
        for part in parts
    )
    relations = (
        PartRelation("lh", "left_arm", "torso", "attached_to", "left_arm:c", "torso:c", 1.0, ("synthetic",)),
        PartRelation("rh", "right_arm", "torso", "attached_to", "right_arm:c", "torso:c", 1.0, ("synthetic",)),
        PartRelation("lb", "lower_body", "torso", "attached_to", "lower_body:c", "torso:c", 1.0, ("synthetic",)),
        PartRelation("fh", "face", "head", "inside", "face:c", "head:c", 1.0, ("synthetic",)),
    )
    return StructuralLayoutGraph(80, 80, parts, anchors, relations)


def test_guard_restores_anatomy_allocation_that_would_disappear() -> None:
    rgb = np.full((80, 80, 3), 180, dtype=np.uint8)
    allocations = {
        "head": 1,
        "torso": 1,
        "left_arm": 0,
        "right_arm": 1,
        "lower_body": 1,
    }
    result = build_semantic_render_guard(rgb, _masks(), _graph(), allocations)
    assert result.anatomy_before_restore.passed is False
    assert result.safe_allocations["left_arm"] == 1
    assert result.anatomy_after_restore.passed is True
    assert result.passed is True


def test_guard_does_not_invent_absent_face() -> None:
    masks = _masks()
    masks["face"][:] = 0
    rgb = np.full((80, 80, 3), 180, dtype=np.uint8)
    result = build_semantic_render_guard(
        rgb,
        masks,
        _graph(),
        {"head": 1, "torso": 1, "left_arm": 1, "right_arm": 1, "lower_body": 1},
    )
    assert result.face_gate["pass"] is True
    assert result.face_gate["applicable"] is False
    assert result.face_evidence.parts == ()
