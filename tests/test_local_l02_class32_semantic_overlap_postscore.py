"""Source-free negative controls for class32 component postscore."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from local_l02_class32_semantic_overlap_postscore import (
    Class32PostscoreHold, audit_class32_component_semantics,
)


def fixture():
    class_ids = np.zeros((5, 6), dtype=np.uint8)
    class_ids[1:4, 1:5] = 32
    alpha = np.full_like(class_ids, 255)
    garment = np.zeros_like(class_ids)
    garment[1:4, 1:3] = 1
    under = np.zeros_like(class_ids)
    under[1:4, 3] = 1
    arm = np.zeros_like(class_ids)
    arm[1:4, 4] = 1
    labelled = garment | under | arm
    return dict(class_ids=class_ids, source_alpha=alpha,
                reviewed_outerwear=garment, reviewed_underlayer=under,
                reviewed_arm_skin=arm, reviewed_labelled=labelled,
                minimum_component_pixels=1)


def test_mixed_component_is_not_safe_to_delete():
    receipt = audit_class32_component_semantics(**fixture())
    c = receipt['components_above_minimum'][0]
    assert c['class32_source_pixels'] == 12
    assert c['reviewed_outerwear_pixels'] == 6
    assert c['reviewed_underlayer_pixels'] == 3
    assert c['reviewed_arm_skin_pixels'] == 3
    assert c['mixed_outerwear_underlayer']
    assert c['mixed_outerwear_arm']
    assert c['whole_component_removal_would_erase_reviewed_outerwear']
    assert receipt['quality'] == 'FAIL'


def test_unknown_not_treated_as_negative():
    args = fixture()
    args['reviewed_labelled'][1, 4] = 0
    args['reviewed_arm_skin'][1, 4] = 0
    c = audit_class32_component_semantics(**args)['components_above_minimum'][0]
    assert c['unreviewed_unknown_pixels'] == 1
    assert c['reviewed_arm_skin_pixels'] == 2


def test_conflicting_or_unlabelled_positive_is_rejected():
    args = fixture()
    args['reviewed_underlayer'][1, 1] = 1
    with pytest.raises(Class32PostscoreHold, match='CONFLICTING'):
        audit_class32_component_semantics(**args)
    args = fixture()
    args['reviewed_labelled'][1, 1] = 0
    with pytest.raises(Class32PostscoreHold, match='CONFLICTING'):
        audit_class32_component_semantics(**args)


def test_nonopaque_label_and_invalid_input_rejected():
    args = fixture()
    args['source_alpha'][1, 1] = 0
    with pytest.raises(Class32PostscoreHold, match='CONFLICTING'):
        audit_class32_component_semantics(**args)
    args = fixture()
    args['connectivity'] = 5
    with pytest.raises(Class32PostscoreHold, match='INVALID'):
        audit_class32_component_semantics(**args)
