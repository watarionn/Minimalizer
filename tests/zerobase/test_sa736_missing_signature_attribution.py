import numpy as np
import pytest

from minimalizer_zerobase.evaluation.missing_signature_attribution import (
    attribute_missing_signature,
)
from minimalizer_zerobase.production.feature_survival_gate import FeatureSignature


def test_attributes_connected_source_component_to_semantic_role():
    source = np.full((40, 40, 3), [240, 220, 200], dtype=np.uint8)
    subject = np.zeros((40, 40), dtype=bool)
    subject[5:35, 5:35] = True

    source[22:30, 7:15] = [20, 50, 50]
    arm = np.zeros((40, 40), dtype=bool)
    arm[22:30, 7:15] = True
    torso = np.zeros((40, 40), dtype=bool)
    torso[10:30, 17:30] = True

    sig = FeatureSignature((16, 48, 48), .04, 10 / 39, 25 / 39)
    result = attribute_missing_signature(
        missing_signature=sig,
        source_rgb=source,
        subject_mask=subject,
        semantic_masks={"right_arm": arm, "torso": torso},
    )
    assert result.primary_role == "right_arm"
    assert result.primary_overlap_ratio == 1.0
    assert result.source_component_area == 64


def test_reports_overlapping_semantic_authority_without_forcing_exclusive_role():
    source = np.full((30, 30, 3), [220, 200, 180], dtype=np.uint8)
    subject = np.ones((30, 30), dtype=bool)
    source[12:18, 12:18] = [10, 10, 10]

    torso = np.zeros((30, 30), dtype=bool)
    torso[12:18, 12:18] = True
    clothing = np.zeros((30, 30), dtype=bool)
    clothing[12:18, 12:15] = True

    sig = FeatureSignature((16, 16, 16), .04, 14.5 / 29, 14.5 / 29)
    result = attribute_missing_signature(
        missing_signature=sig,
        source_rgb=source,
        subject_mask=subject,
        semantic_masks={"torso": torso, "major_clothing": clothing},
    )
    assert result.primary_role == "torso"
    ratios = {row.role: row.ratio for row in result.role_overlaps}
    assert ratios["torso"] == 1.0
    assert ratios["major_clothing"] == 0.5


def test_rejects_signature_without_source_support():
    source = np.full((24, 24, 3), [200, 200, 200], dtype=np.uint8)
    subject = np.ones((24, 24), dtype=bool)
    sig = FeatureSignature((16, 16, 16), .1, .5, .5)
    with pytest.raises(ValueError, match="not source-supported"):
        attribute_missing_signature(
            missing_signature=sig,
            source_rgb=source,
            subject_mask=subject,
            semantic_masks={"torso": subject},
            match_threshold=.05,
        )
