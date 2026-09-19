import numpy as np
import pytest

from minimalize_engine.v2.analysis_guidance import (
    AnalysisGuidance,
    LineGuide,
    StructuralGuide,
)


def test_structural_guide_requires_well_formed_confidence_maps():
    maps = np.zeros((2, 8, 8), dtype=np.float32)
    guide = StructuralGuide(
        ("torso", "left_upper_arm"), maps, "rtmlib", "wholebody"
    )
    assert guide.source_shape == (8, 8)

    with pytest.raises(ValueError):
        StructuralGuide(("torso", "torso"), maps, "rtmlib", "wholebody")
    with pytest.raises(ValueError):
        StructuralGuide(("torso",), maps, "rtmlib", "wholebody")
    with pytest.raises(ValueError):
        StructuralGuide(
            ("torso", "left_upper_arm"),
            maps.astype(np.float64),
            "rtmlib",
            "wholebody",
        )
    invalid = maps.copy()
    invalid[0, 0, 0] = 1.1
    with pytest.raises(ValueError):
        StructuralGuide(
            ("torso", "left_upper_arm"), invalid, "rtmlib", "wholebody"
        )


def test_line_guide_requires_probability_map_and_normalized_length_gate():
    support = np.zeros((8, 8), dtype=np.float32)
    guide = LineGuide(support, "deeplsd", "deeplsd_md", 0.13)
    assert guide.source_shape == (8, 8)

    with pytest.raises(ValueError):
        LineGuide(support.astype(np.float64), "deeplsd", "deeplsd_md", 0.13)
    with pytest.raises(ValueError):
        LineGuide(support, "deeplsd", "deeplsd_md", 0.0)
    with pytest.raises(ValueError):
        LineGuide(support, "deeplsd", "deeplsd_md", 1.01)
    invalid = support.copy()
    invalid[0, 0] = np.nan
    with pytest.raises(ValueError):
        LineGuide(invalid, "deeplsd", "deeplsd_md", 0.13)


def test_analysis_guidance_requires_all_lanes_to_share_source_resolution():
    structural = StructuralGuide(
        ("torso",),
        np.zeros((1, 8, 8), dtype=np.float32),
        "rtmlib",
        "wholebody",
    )
    line = LineGuide(
        np.zeros((16, 16), dtype=np.float32),
        "deeplsd",
        "deeplsd_md",
        0.13,
    )
    with pytest.raises(ValueError):
        AnalysisGuidance(structural=structural, line=line)


def test_analysis_guidance_validates_structural_and_line_source_shape():
    structural = StructuralGuide(
        ("torso",),
        np.zeros((1, 8, 8), dtype=np.float32),
        "rtmlib",
        "wholebody",
    )
    line = LineGuide(
        np.zeros((8, 8), dtype=np.float32),
        "deeplsd",
        "deeplsd_md",
        0.13,
    )
    guidance = AnalysisGuidance(structural=structural, line=line)
    guidance.validate_source_shape((8, 8))
    with pytest.raises(ValueError):
        guidance.validate_source_shape((16, 16))
