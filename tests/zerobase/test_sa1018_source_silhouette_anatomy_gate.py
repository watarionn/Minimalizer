import numpy as np

from minimalizer_zerobase.evaluation.structural_hard_evidence import (
    evaluate_structural_hard_evidence,
)


def _masks():
    shape = (40, 40)
    masks = {"torso": np.zeros(shape, bool), "head": np.zeros(shape, bool), "face": np.zeros(shape, bool), "left_arm": np.zeros(shape, bool), "right_arm": np.zeros(shape, bool)}
    masks["torso"][18:35, 14:26] = 1
    masks["head"][5:18, 14:26] = 1
    masks["face"][8:16, 16:24] = 1
    masks["left_arm"][19:30, 8:14] = 1
    masks["right_arm"][19:30, 26:32] = 1
    return masks


def test_sa1018_source_visible_arm_disappearance_is_hard_fail():
    source = _masks()
    candidate = {key: value.copy() for key, value in source.items()}
    candidate["left_arm"][:] = False
    report = evaluate_structural_hard_evidence(source_masks=source, candidate_masks=candidate)
    assert report.anatomy_pass is False
    assert "left_arm:source-visible-part-disappearance" in report.source_anatomy["failures"]


def test_sa1018_face_expansion_and_outer_silhouette_loss_are_hard_fail():
    source = _masks()
    candidate = {key: value.copy() for key, value in source.items()}
    candidate["face"][:] = False
    candidate["face"][2:25, 4:36] = 1
    candidate["right_arm"][:] = False
    report = evaluate_structural_hard_evidence(source_masks=source, candidate_masks=candidate)
    assert report.anatomy_pass is False
    assert report.source_silhouette["passed"] is False


def test_sa1020_arm_component_split_is_topology_hard_fail():
    source = _masks()
    candidate = {key: value.copy() for key, value in source.items()}
    candidate["left_arm"][24, 8:14] = False
    report = evaluate_structural_hard_evidence(source_masks=source, candidate_masks=candidate)
    assert report.topology_pass is False
    assert any(item.startswith("left_arm:components:") for item in report.topology_mismatches)


def test_sa1020_source_hole_and_euler_change_are_hard_fail():
    source = _masks()
    source["torso"][24:27, 18:22] = False
    candidate = {key: value.copy() for key, value in source.items()}
    candidate["torso"][24:27, 18:22] = True
    report = evaluate_structural_hard_evidence(source_masks=source, candidate_masks=candidate)
    assert report.topology_pass is False
    assert any(item.startswith("torso:holes:") for item in report.topology_mismatches)
    assert report.source_topology["per_part"]["torso"]["euler_characteristic"] != report.candidate_topology["per_part"]["torso"]["euler_characteristic"]
