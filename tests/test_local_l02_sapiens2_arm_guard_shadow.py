"""Source-free Sapiens2 arm-guard regression tests."""
import hashlib
import io

import numpy as np
import pytest
from PIL import Image

from tools.research.local_l02_class32_topology_palette_shadow import SourceOnlyAbstentionHold
from tools.research.local_l02_sapiens2_arm_guard_shadow import (
    remove_sapiens2_arm_owner,
    veto_sapiens2_arm_evidence,
)


def sample():
    rgba = np.zeros((24, 24, 4), dtype=np.uint8)
    rgba[3:21, 3:21] = [120, 140, 160, 255]
    stream = io.BytesIO()
    Image.fromarray(rgba).save(stream, format="PNG")
    owner = np.zeros((24, 24), dtype=np.uint8)
    owner[5:18, 5:15] = 1
    owner[9:12, 15:18] = 1
    sapiens = np.zeros_like(owner)
    sapiens[9:12, 15:18] = 7
    return stream.getvalue(), owner, sapiens


def test_explicit_arm_removal_is_source_only_and_topology_safe():
    source, owner, sapiens = sample()
    digest = hashlib.sha256(source).hexdigest()
    observer_digest = hashlib.sha256(sapiens.tobytes(order="C")).hexdigest()
    result, receipt = remove_sapiens2_arm_owner(
        source_bytes=source, expected_source_sha256=digest,
        sapiens_classes=sapiens, expected_sapiens_sha256=observer_digest,
        frozen_owner=owner, candidate_owner=owner)
    assert receipt["human_labels_used"] is False
    assert receipt["unknown_not_treated_as_negative"] is True
    assert receipt["Phase4"] == "FAIL"
    assert np.count_nonzero(result != owner) > 0
    assert np.all(result <= owner)


def test_garment_class_is_never_removed():
    source, owner, sapiens = sample()
    sapiens[sapiens == 7] = 23
    digest = hashlib.sha256(source).hexdigest()
    observer_digest = hashlib.sha256(sapiens.tobytes(order="C")).hexdigest()
    result, receipt = remove_sapiens2_arm_owner(
        source_bytes=source, expected_source_sha256=digest,
        sapiens_classes=sapiens, expected_sapiens_sha256=observer_digest,
        frozen_owner=owner, candidate_owner=owner)
    np.testing.assert_array_equal(result, owner)
    assert receipt["removed_explicit_arm_px"] == 0


def test_wrong_observer_sha_fails_closed():
    source, owner, sapiens = sample()
    with pytest.raises(SourceOnlyAbstentionHold, match="SAPIENS2_CLASS_ARRAY_SHA_MISMATCH"):
        remove_sapiens2_arm_owner(
            source_bytes=source,
            expected_source_sha256=hashlib.sha256(source).hexdigest(),
            sapiens_classes=sapiens, expected_sapiens_sha256="0" * 64,
            frozen_owner=owner, candidate_owner=owner)


def test_arm_veto_does_not_treat_absence_as_negative():
    _, _, sapiens = sample()
    evidence = np.zeros_like(sapiens, dtype=bool)
    evidence[6:8, 6:8] = True
    evidence[9:12, 15:18] = True
    digest = hashlib.sha256(sapiens.tobytes(order="C")).hexdigest()
    result, receipt = veto_sapiens2_arm_evidence(
        positive_evidence=evidence, sapiens_classes=sapiens,
        expected_sapiens_sha256=digest)
    assert int(result.sum()) == 4
    assert receipt["explicit_arm_veto_px"] == 9
    assert receipt["human_labels_used"] is False
