from __future__ import annotations

import numpy as np
import pytest

from minimalizer_zerobase.parts.decomposition import PART_NAMES
from minimalizer_zerobase.semantic_abstraction.evidence_adapter import (
    build_semantic_abstraction_evidence,
)
from minimalizer_zerobase.semantic_abstraction.ir import (
    AbstractionPolicy,
    VisualRole,
)
from minimalizer_zerobase.structure.graph import PartAnchor, PartRelation, StructuralLayoutGraph


def _masks() -> dict[str, np.ndarray]:
    masks = {name: np.zeros((10, 20), dtype=np.uint8) for name in PART_NAMES}
    masks["torso"][2:8, 5:15] = 1
    masks["unknown"][0:2, 0:2] = 1
    return masks


def _graph() -> StructuralLayoutGraph:
    anchors = (
        PartAnchor("torso:c", "torso", "centroid", (10.0, 5.0), (0.5, 0.5), 1.0, ("e",)),
        PartAnchor("head:c", "head", "centroid", (10.0, 1.0), (0.5, 0.1), 1.0, ("e",)),
    )
    relations = (
        PartRelation(
            "r1", "torso", "head", "connected_to", "torso:c", "head:c", 0.9, ("e",)
        ),
    )
    return StructuralLayoutGraph(20, 10, ("head", "torso"), anchors, relations)


def test_adapter_preserves_unknown_instead_of_guessing() -> None:
    plan = build_semantic_abstraction_evidence(part_masks=_masks(), graph=_graph())
    unknown = next(part for part in plan.parts if part.id == "unknown")
    assert unknown.confidence == 0.0
    assert unknown.visual_role is VisualRole.UNKNOWN
    assert unknown.abstraction_policy is AbstractionPolicy.CONDITIONAL


def test_adapter_normalizes_bbox_and_preserves_provenance() -> None:
    plan = build_semantic_abstraction_evidence(part_masks=_masks(), graph=_graph())
    torso = next(part for part in plan.parts if part.id == "torso")
    assert torso.bbox == pytest.approx((0.25, 0.2, 0.75, 0.8))
    assert "phase04:part_masks/torso.png" in torso.evidence_refs
    assert "phase05:structural_layout_graph.json" in torso.evidence_refs


def test_adapter_carries_structural_relation_as_constraint() -> None:
    plan = build_semantic_abstraction_evidence(part_masks=_masks(), graph=_graph())
    torso = next(part for part in plan.parts if part.id == "torso")
    assert [(item.relation, item.target_part_id, item.required) for item in torso.topology_constraints] == [
        ("connected_to", "head", True)
    ]


def test_adapter_fails_closed_when_phase4_contract_is_incomplete() -> None:
    masks = _masks()
    del masks["hair"]
    with pytest.raises(ValueError, match="missing Phase 4"):
        build_semantic_abstraction_evidence(part_masks=masks, graph=_graph())
