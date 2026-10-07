from __future__ import annotations

import pytest

from minimalizer_zerobase.geometrization.part_aware import (
    PART_FAMILIES as CURRENT_PART_FAMILIES,
    PartAwareGeometrizationPolicy as CurrentPhase10Policy,
)
from minimalizer_zerobase.production.profile import (
    CURRENT_PROFILE,
    REVIEWED_SA10_PROFILE,
    reviewed_sa10_enabled,
    semantic_profile,
)
from minimalizer_zerobase.reviewed_sa10.geometrization_part_aware import (
    PART_FAMILIES as REVIEWED_PART_FAMILIES,
    PartAwareGeometrizationPolicy as ReviewedPhase10Policy,
)


def test_semantic_profile_defaults_to_current(monkeypatch):
    monkeypatch.delenv("MINIMALIZER_SEMANTIC_PROFILE", raising=False)
    assert semantic_profile() == CURRENT_PROFILE
    assert reviewed_sa10_enabled() is False


def test_semantic_profile_selects_reviewed_sa10(monkeypatch):
    monkeypatch.setenv("MINIMALIZER_SEMANTIC_PROFILE", REVIEWED_SA10_PROFILE)
    assert semantic_profile() == REVIEWED_SA10_PROFILE
    assert reviewed_sa10_enabled() is True


def test_semantic_profile_rejects_unknown_value(monkeypatch):
    monkeypatch.setenv("MINIMALIZER_SEMANTIC_PROFILE", "unknown")
    with pytest.raises(ValueError, match="unsupported Minimalizer semantic profile"):
        semantic_profile()


def test_reviewed_sa10_phase10_contract_is_frozen_separately_from_current():
    reviewed = ReviewedPhase10Policy().to_dict()
    current = CurrentPhase10Policy().to_dict()

    assert "polygon" not in REVIEWED_PART_FAMILIES["left_arm"]
    assert "polygon" not in REVIEWED_PART_FAMILIES["right_arm"]
    assert "arm_family_policy" not in reviewed

    assert "polygon" in CURRENT_PART_FAMILIES["left_arm"]
    assert "polygon" in CURRENT_PART_FAMILIES["right_arm"]
    assert "arm_family_policy" in current
