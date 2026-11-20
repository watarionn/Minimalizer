from __future__ import annotations

from tools.research.run_local_l02_model_capability_probe import _capability_report


def test_model_capability_probe_does_not_alias_missing_roles() -> None:
    report = _capability_report(
        {
            0: "background",
            1: "coat_only_torso_region",
            2: "left_sleeve_for_upper",
            3: "right_sleeve_for_upper",
            4: "left_arm",
            5: "right_arm",
        }
    )

    assert report["outerwear"]["status"] == "AVAILABLE"
    assert report["sleeve"]["status"] == "AVAILABLE"
    assert report["arm"]["status"] == "AVAILABLE"
    assert report["underlayer"]["status"] == "MISSING"
    assert report["pairwise_occlusion"]["status"] == "MISSING"
    assert report["person_instance"]["status"] == "MISSING"


def test_model_capability_probe_reports_unknown_roles_without_negative_aliases() -> None:
    report = _capability_report({0: "background", 1: "upper_only_torso_region"})

    assert report["underlayer"]["evidence_labels"] == []
    assert report["pairwise_occlusion"]["evidence_labels"] == []
    assert report["person_instance"]["evidence_labels"] == []
