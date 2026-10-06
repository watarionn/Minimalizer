import numpy as np
import pytest

from minimalizer_zerobase.analyzers.contracts import Evidence
from minimalizer_zerobase.analyzers.slic_regions import SLICRegionAdapter
from minimalizer_zerobase.analyzers.structured_mask_evidence import (
    EvidenceAuthorityState,
    EvidenceAuthorityTrace,
    build_pb2_structured_evidence,
)
from minimalizer_zerobase.core.coordinates import CoordinateSpace
from minimalizer_zerobase.scene.fusion import EvidenceFusion


SPACE = CoordinateSpace(80, 80)


def _mask(boxes=()):
    out = np.zeros((80, 80), bool)
    for x0, y0, x1, y1 in boxes:
        out[y0:y1, x0:x1] = True
    return out


def _relation_records(expansion):
    return [
        row for row in expansion.evidence
        if row.evidence_type == "layer_relation"
    ]


def _component_records(expansion, role=None):
    rows = [
        row for row in expansion.evidence
        if row.evidence_type == "region_component"
    ]
    if role is not None:
        rows = [row for row in rows if row.semantic_label == role]
    return rows


def _relation(expansion, a, b):
    roles = sorted((a, b))
    return next(
        row for row in _relation_records(expansion)
        if row.geometry["roles"] == roles
    )


def test_disconnected_components_become_stable_observer_evidence():
    expansion = build_pb2_structured_evidence(
        role_masks={
            "hair": _mask(
                (
                    (5, 5, 25, 25),
                    (50, 10, 60, 20),
                )
            )
        },
        coordinate_space=SPACE,
        source_refs={"hair": "phase04:part_masks/hair.png"},
    )

    rows = _component_records(expansion, "hair")
    assert expansion.component_count == 2
    assert [row.evidence_id for row in rows] == [
        "pb2:hair:component:000",
        "pb2:hair:component:001",
    ]
    assert rows[0].geometry["pixel_count"] == 400
    assert rows[1].geometry["pixel_count"] == 100
    assert rows[0].geometry["support_ratio"] == pytest.approx(0.8)
    assert "bbox" not in rows[0].geometry
    assert rows[0].geometry["component_bbox"] == [5, 5, 20, 20]


def test_relation_evidence_distinguishes_overlap_touching_and_disjoint():
    expansion = build_pb2_structured_evidence(
        role_masks={
            "hair": _mask(((5, 5, 30, 30),)),
            "head": _mask(((20, 20, 45, 45),)),
            "torso": _mask(((45, 20, 65, 45),)),
            "lower_body": _mask(((50, 60, 70, 75),)),
        },
        coordinate_space=SPACE,
    )

    assert _relation(expansion, "hair", "head").geometry["relation"] == "OVERLAP"
    assert _relation(expansion, "head", "torso").geometry["relation"] == "TOUCHING"
    assert _relation(expansion, "hair", "lower_body").geometry["relation"] == "DISJOINT"


def test_overlap_does_not_invent_occlusion_direction():
    expansion = build_pb2_structured_evidence(
        role_masks={
            "hair": _mask(((5, 5, 35, 35),)),
            "head": _mask(((20, 20, 50, 50),)),
        },
        coordinate_space=SPACE,
    )

    row = _relation(expansion, "hair", "head")
    assert row.geometry["front_role"] is None
    assert row.geometry["back_role"] is None
    assert row.normalization["direction_source"] == "unavailable"
    assert expansion.z_order_observed is False


def test_existing_z_order_is_observed_without_becoming_authority():
    expansion = build_pb2_structured_evidence(
        role_masks={
            "hair": _mask(((5, 5, 35, 35),)),
            "head": _mask(((20, 20, 50, 50),)),
        },
        coordinate_space=SPACE,
        role_z_order={"hair": 5, "head": 10},
    )

    row = _relation(expansion, "hair", "head")
    assert row.geometry["front_role"] == "head"
    assert row.geometry["back_role"] == "hair"
    assert row.normalization["direction_source"] == "canonical_z_order_observation"
    assert row.normalization["authority"]["production_authority"] is False
    assert expansion.production_output_changed is False


def test_mapping_order_is_fully_deterministic():
    hair = _mask(((5, 5, 30, 30), (50, 5, 60, 15)))
    head = _mask(((20, 20, 50, 50),))
    refs = {
        "hair": "phase04:part_masks/hair.png",
        "head": "phase04:part_masks/head.png",
    }

    a = build_pb2_structured_evidence(
        role_masks={"hair": hair, "head": head},
        coordinate_space=SPACE,
        source_refs=refs,
    )
    b = build_pb2_structured_evidence(
        role_masks={"head": head, "hair": hair},
        coordinate_space=SPACE,
        source_refs={"head": refs["head"], "hair": refs["hair"]},
    )

    assert a.to_dict() == b.to_dict()


def test_pb2_records_preserve_observed_authority_provenance():
    expansion = build_pb2_structured_evidence(
        role_masks={"hair": _mask(((5, 5, 30, 30),))},
        coordinate_space=SPACE,
        source_refs={"hair": "phase04:part_masks/hair.png"},
    )

    row = _component_records(expansion)[0]
    assert isinstance(row, Evidence)
    assert row.provenance.producer == "PB2StructuredMaskEvidenceAdapter"
    authority = row.normalization["authority"]
    assert authority == {
        "state": "observed",
        "source_ref": "phase04:part_masks/hair.png",
        "advisor_source": None,
        "promoted_by": None,
        "production_authority": False,
    }
    assert row.normalization["evidence_scope"] == "observer_only"


def test_authority_trace_distinguishes_observed_advisor_and_promoted():
    observed = EvidenceAuthorityTrace(
        EvidenceAuthorityState.OBSERVED,
        "source:a",
    )
    advisor = EvidenceAuthorityTrace(
        EvidenceAuthorityState.ADVISOR,
        "source:a",
        advisor_source="starvector",
    )
    promoted = EvidenceAuthorityTrace(
        EvidenceAuthorityState.PROMOTED,
        "source:a",
        advisor_source="starvector",
        promoted_by="explicit-deterministic-rule:future-phase",
    )

    assert observed.to_dict()["production_authority"] is False
    assert advisor.to_dict()["production_authority"] is False
    assert promoted.to_dict()["production_authority"] is True
    assert promoted.to_dict()["promoted_by"].startswith("explicit-deterministic-rule")


def test_invalid_authority_transitions_fail_closed():
    with pytest.raises(ValueError, match="observed"):
        EvidenceAuthorityTrace(
            EvidenceAuthorityState.OBSERVED,
            "source:a",
            advisor_source="external",
        )
    with pytest.raises(ValueError, match="advisor_source"):
        EvidenceAuthorityTrace(
            EvidenceAuthorityState.ADVISOR,
            "source:a",
        )
    with pytest.raises(ValueError, match="promoted_by"):
        EvidenceAuthorityTrace(
            EvidenceAuthorityState.PROMOTED,
            "source:a",
        )


def test_pb2_observer_evidence_fails_closed_if_accidentally_sent_to_fusion():
    expansion = build_pb2_structured_evidence(
        role_masks={
            "hair": _mask(((5, 5, 30, 30),)),
            "head": _mask(((20, 20, 50, 50),)),
        },
        coordinate_space=SPACE,
    )

    with pytest.raises(ValueError, match="requires geometry.bbox"):
        EvidenceFusion().fuse(expansion.evidence)


def test_generating_pb2_evidence_does_not_mutate_existing_production_evidence():
    image = np.zeros((80, 80, 3), dtype=np.uint8)
    image[:, 40:] = 255
    base = SLICRegionAdapter(n_segments=8).analyze(image, SPACE)
    before = EvidenceFusion().fuse(base).to_json()
    base_json = [item.to_json() for item in base]

    expansion = build_pb2_structured_evidence(
        role_masks={
            "hair": _mask(((5, 5, 30, 30),)),
            "head": _mask(((20, 20, 50, 50),)),
        },
        coordinate_space=SPACE,
    )

    after = EvidenceFusion().fuse(base).to_json()
    assert before == after
    assert base_json == [item.to_json() for item in base]
    assert expansion.production_output_changed is False


def test_coordinate_mismatch_fails_closed():
    with pytest.raises(ValueError, match="coordinate space"):
        build_pb2_structured_evidence(
            role_masks={"hair": _mask(((5, 5, 30, 30),))},
            coordinate_space=CoordinateSpace(81, 80),
        )
