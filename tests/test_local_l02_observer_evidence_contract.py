from __future__ import annotations

import hashlib

import numpy as np
import pytest

from tools.research.local_l02_observer_evidence_contract import (
    ObserverEvidenceHold,
    PairwiseRelationObservation,
    RoleObservation,
    ScalarObservation,
    assess_observer_evidence,
)


def _sha(array: np.ndarray) -> str:
    return hashlib.sha256(array.tobytes(order="C")).hexdigest()


def _bundle():
    alpha = np.ones((5, 6), dtype=bool)
    masks = []
    for index, role in enumerate(("outerwear", "underlayer", "sleeve", "arm")):
        mask = np.zeros_like(alpha)
        mask[index // 2 : index // 2 + 2, index : index + 2] = True
        masks.append(RoleObservation(role, mask, _sha(mask), f"observer-{role}"))
    relation = np.zeros_like(alpha, dtype=np.int8)
    relation[1:3, 1:3] = 1
    grouping = np.zeros_like(alpha, dtype=np.uint32)
    grouping[1:3, 1:3] = 1
    relations = tuple(
        PairwiseRelationObservation(
            role_a,
            role_b,
            relation,
            _sha(relation),
            f"depth-{role_a}-{role_b}",
        )
        for role_a, role_b in (
            ("outerwear", "underlayer"),
            ("sleeve", "arm"),
            ("garment", "body"),
        )
    )
    return alpha, tuple(masks), relations, grouping


def test_complete_source_only_bundle_is_admitted_for_research_probe():
    alpha, roles, relations, grouping = _bundle()
    result = assess_observer_evidence(
        source_alpha=alpha,
        role_observations=roles,
        occlusion_relation=relations,
        instance_grouping=ScalarObservation(
            "instance_grouping", grouping, _sha(grouping), "instance-observer"
        ),
    )
    assert result.status == "CAPABILITY_PASS_RESEARCH_ONLY"
    assert result.formal_probe_allowed is True
    assert result.unknown_not_treated_as_negative is True


def test_missing_underlayer_is_a_hold_not_an_inference_default():
    alpha, roles, relations, grouping = _bundle()
    roles = tuple(role for role in roles if role.role != "underlayer")
    result = assess_observer_evidence(
        source_alpha=alpha,
        role_observations=roles,
        occlusion_relation=relations,
        instance_grouping=ScalarObservation(
            "instance_grouping", grouping, _sha(grouping), "instance-observer"
        ),
    )
    assert result.status == "CAPABILITY_HOLD"
    assert result.formal_probe_allowed is False
    assert "underlayer" in result.missing_capabilities


def test_role_hash_drift_fails_closed():
    alpha, roles, relations, grouping = _bundle()
    bad = (*roles[:-1], RoleObservation("arm", roles[-1].mask, "0" * 64, "observer-arm"))
    with pytest.raises(ObserverEvidenceHold, match="ROLE_MASK_SHA_MISMATCH"):
        assess_observer_evidence(
            source_alpha=alpha,
            role_observations=bad,
            occlusion_relation=relations,
            instance_grouping=ScalarObservation(
                "instance_grouping", grouping, _sha(grouping), "instance-observer"
            ),
        )


def test_human_labels_and_frozen_owners_are_never_admitted():
    alpha, roles, relations, grouping = _bundle()
    with pytest.raises(ObserverEvidenceHold, match="HUMAN_LABELS_IN_INFERENCE"):
        assess_observer_evidence(
            source_alpha=alpha,
            role_observations=roles,
            occlusion_relation=relations,
            instance_grouping=ScalarObservation(
                "instance_grouping", grouping, _sha(grouping), "instance-observer"
            ),
            human_labels_used=True,
        )
