from __future__ import annotations

import numpy as np
import pytest

from minimalizer_zerobase.evaluation.actual_emission_support import (
    measure_actual_emission_support,
)
from minimalizer_zerobase.evaluation.source_authority_evidence import (
    build_source_authority_evidence,
)
from minimalizer_zerobase.evaluation.structural_hard_evidence import (
    evaluate_structural_hard_evidence,
)
from minimalizer_zerobase.parts.decomposition import PART_NAMES
from minimalizer_zerobase.semantic_abstraction.macro_geometry_reauthoring import (
    reauthor_macro_geometry_with_budget,
)


def _person_masks() -> dict[str, np.ndarray]:
    shape = (160, 120)
    masks = {name: np.zeros(shape, dtype=bool) for name in PART_NAMES}
    masks["head"][12:58, 38:82] = True
    masks["face"][25:51, 48:72] = True
    masks["hair"][12:29, 38:82] = True
    masks["hair"][29:58, 38:48] = True
    masks["hair"][29:58, 72:82] = True
    masks["neck"][52:68, 54:66] = True
    masks["torso"][68:126, 38:82] = True
    masks["left_arm"][72:124, 82:103] = True
    masks["right_arm"][72:124, 17:38] = True
    masks["lower_body"][126:151, 42:78] = True
    masks["major_clothing"][72:126, 38:45] = True
    masks["accessory_or_held_object"][76:116, 57:63] = True
    return masks


def test_source_authority_requires_hash_and_fresh_provenance():
    sha = "a" * 64
    report = build_source_authority_evidence(
        expected_source_sha256=sha,
        actual_source_sha256=sha,
        provenance_gate_passed=True,
        provenance_artifact_count=86,
    )
    assert report.passed is True

    mismatch = build_source_authority_evidence(
        expected_source_sha256=sha,
        actual_source_sha256="b" * 64,
        provenance_gate_passed=True,
        provenance_artifact_count=86,
    )
    assert mismatch.passed is False

    stale = build_source_authority_evidence(
        expected_source_sha256=sha,
        actual_source_sha256=sha,
        provenance_gate_passed=False,
        provenance_artifact_count=86,
    )
    assert stale.passed is False


def test_structural_hard_evidence_uses_graph_and_anatomy_guards():
    source = _person_masks()
    report = evaluate_structural_hard_evidence(
        source_masks=source,
        candidate_masks={name: mask.copy() for name, mask in source.items()},
        accessory_kind="vivid-accent",
        accessory_confidence=0.8,
    )
    assert report.anatomy_pass is True
    assert report.topology_pass is True
    assert report.to_dict()["phase14_metric_relabeling"] is False


def test_structural_hard_evidence_fails_if_required_arm_disappears():
    source = _person_masks()
    candidate = {name: mask.copy() for name, mask in source.items()}
    candidate["left_arm"][:] = False
    report = evaluate_structural_hard_evidence(
        source_masks=source,
        candidate_masks=candidate,
        accessory_kind="vivid-accent",
        accessory_confidence=0.8,
    )
    assert report.anatomy_pass is False
    assert "left_arm" in report.anatomy.missing_parts
    assert report.topology_pass is False


def test_phase4_unknown_is_observed_unassigned_not_semantic_topology_owner():
    source = _person_masks()
    source["unknown"][4:9, 4:11] = True
    candidate = {name: mask.copy() for name, mask in source.items()}
    candidate["unknown"][:] = False
    report = evaluate_structural_hard_evidence(
        source_masks=source,
        candidate_masks=candidate,
    )
    topology = report.to_dict()["topology"]
    assert topology["source_evidence"]["non_semantic_coverage"]["unknown"] == {
        "coverage_role": "observed-unassigned",
        "pixel_count": 35,
        "excluded_from_semantic_topology": True,
    }
    assert all(not item.startswith("unknown:") for item in topology["mismatches"])
    assert report.topology_pass is True


def test_actual_emission_diagnostic_does_not_reinterpret_sa105():
    hair = np.zeros((120, 120), bool)
    hair[10:90, 10:90] = True
    hair[30:70, 30:70] = False
    clothing = np.zeros((120, 120), bool)
    clothing[95:115, 20:100] = True

    primitives, budget = reauthor_macro_geometry_with_budget(
        hair_mask=hair,
        clothing_mask=clothing,
        global_primitive_budget=5,
    )
    report = measure_actual_emission_support(
        role_masks={"hair": hair, "major_clothing": clothing},
        primitives=primitives,
        budget=budget,
    )
    payload = report.to_dict()
    assert payload["maps_to_sa10_component_survival"] is False
    assert payload["maps_to_sa10_primitive_economy"] is False
    assert report.allocated_primitives == 2
    assert report.emitted_primitives == 1
    assert report.emission_realization_ratio == pytest.approx(0.5)
    assert report.actual_component_representation_ratio == pytest.approx(0.5)
    assert report.actual_primitive_support_ratio == pytest.approx(1.0)
