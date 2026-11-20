from __future__ import annotations

from dataclasses import replace

import pytest

from tools.research.local_l02_observer_adoption_plan import (
    AdoptionPlanHold,
    adoption_plan_summary,
    default_adoption_plan,
    assess_adoption_plan,
)


def test_default_plan_is_concrete_but_cannot_grant_quality_or_production():
    result = adoption_plan_summary()

    assert result["status"] == "ADOPTION_PLAN_PASS_RESEARCH_ONLY"
    assert len(result["target_capabilities"]) == 8
    assert result["required_cases"] == ("H04", "H06", "H08")
    assert result["phase4_before_phase5"] is True
    assert result["production_authority"] is False


@pytest.mark.parametrize(
    "field,value,error",
    [
        ("human_labels_used_for_inference", True, "HUMAN_LABELS_IN_INFERENCE"),
        ("holdout_is_frozen_before_inference", False, "HOLDOUT_NOT_FROZEN_BEFORE_INFERENCE"),
        ("phase4_before_phase5", False, "PHASE5_BEFORE_PHASE4"),
        ("production_authority", True, "PLAN_CANNOT_GRANT_PRODUCTION_AUTHORITY"),
    ],
)
def test_unsafe_plan_is_rejected(field, value, error):
    with pytest.raises(AdoptionPlanHold, match=error):
        assess_adoption_plan(replace(default_adoption_plan(), **{field: value}))
