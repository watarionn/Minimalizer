from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np

from ..models import Shape
from .face_identity import FaceIdentitySignals
from .face_identity_budget import FaceIdentityPlan


@dataclass(slots=True)
class FaceIdentityValidationReport:
    """Validate whether an adaptive face plan became *too* minimal.

    Phase 10.5-d is intentionally conservative. It never restores the complete
    legacy face. When an omitted cue still carries substantial identity value,
    at most one Shape is proposed for rollback.
    """

    score: float
    coverage_score: float
    omission_risk_score: float
    minimality_efficiency_score: float
    rendered_feature_count: int
    planned_feature_count: int
    omitted_risky_features: list[str] = field(default_factory=list)
    rollback_recommended: bool = False
    rollback_feature: str | None = None
    reasons: list[str] = field(default_factory=list)
    diagnostics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def _clamp01(value: float) -> float:
    return float(np.clip(value, 0.0, 1.0))


def _rendered_features(shapes: list[Shape], primary_eye_side: str) -> set[str]:
    features: set[str] = set()
    eye_sides = [
        s.side_hint
        for s in shapes
        if s.source_role == "character_eye"
    ]
    if any(s.source_role == "character_face_base" for s in shapes):
        features.add("face_base")
    if eye_sides:
        if primary_eye_side in eye_sides:
            features.add("primary_eye")
            if len(eye_sides) >= 2:
                features.add("secondary_eye")
        else:
            # Defensive fallback when side information is missing or detector
            # ordering changed. One rendered eye still fulfills the primary cue.
            features.add("primary_eye")
            if len(eye_sides) >= 2:
                features.add("secondary_eye")
    if any(s.source_role == "character_mouth" for s in shapes):
        features.add("mouth")
    if any(s.source_role == "character_face_helper" for s in shapes):
        features.add("helper")
    return features


def _selected_features(plan: FaceIdentityPlan) -> set[str]:
    selected = {"face_base"} if plan.include_face_base else set()
    for name, enabled in (
        ("primary_eye", plan.include_primary_eye),
        ("secondary_eye", plan.include_secondary_eye),
        ("mouth", plan.include_mouth),
        ("helper", plan.include_helper),
    ):
        if enabled:
            selected.add(name)
    return selected


def _omission_pressure(plan: FaceIdentityPlan, name: str) -> float:
    utility = float(plan.utilities.get(name, 0.0))
    threshold = float(plan.thresholds.get(name, 1.0))
    if threshold >= 0.999:
        return 0.0
    # Below-threshold cues still receive a small pressure close to the cutoff;
    # above-threshold cues omitted only because of the cap get much stronger risk.
    relative = utility / max(threshold, 1e-6)
    if relative <= 0.72:
        return 0.0
    if relative <= 1.0:
        return _clamp01((relative - 0.72) / 0.28 * 0.28)
    return _clamp01(0.28 + (relative - 1.0) * 0.95)


def validate_face_identity_loss(
    signals: FaceIdentitySignals,
    plan: FaceIdentityPlan,
    rendered_shapes: list[Shape],
    *,
    min_score: float = 0.72,
    primary_eye_side: str | None = None,
) -> FaceIdentityValidationReport:
    primary_side = primary_eye_side or signals.primary_eye_side
    selected = _selected_features(plan)
    rendered = _rendered_features(rendered_shapes, primary_side)

    # Plan fulfillment measures renderer correctness, not whether the plan itself
    # was wise. Face base has extra weight because its absence destroys readability.
    selected_optional = selected - {"face_base"}
    optional_total = max(1, len(selected_optional))
    optional_rendered = len(selected_optional & rendered)
    base_ok = ("face_base" not in selected) or ("face_base" in rendered)
    coverage = _clamp01((0.56 if base_ok else 0.0) + 0.44 * optional_rendered / optional_total)
    if not selected_optional and base_ok:
        coverage = 1.0

    pressures: dict[str, float] = {}
    for name in ("primary_eye", "secondary_eye", "mouth", "helper"):
        if name in selected:
            continue
        pressure = _omission_pressure(plan, name)
        # The second eye is usually redundant with the first, except when both
        # source eye signals are strong and the expression is not strongly asymmetric.
        if name == "secondary_eye" and "primary_eye" in selected:
            if signals.expression_salience_score >= 0.78:
                pressure *= 0.45
            else:
                pressure *= 0.72
        # Hair already owns most fringe identity. A helper must be exceptionally
        # strong to justify rollback.
        if name == "helper":
            pressure *= 0.55
        pressures[name] = float(pressure)

    omitted_risky = [name for name, value in pressures.items() if value >= 0.30]
    omission_risk = max(pressures.values(), default=0.0)

    # Large/high-density faces can become semantically empty if reduced to base
    # only. This is a weak contextual risk, not an automatic detail mandate.
    contextual_risk = 0.0
    if plan.target_shape_count <= 1:
        contextual_risk = _clamp01(
            max(0.0, signals.feature_density_score - 0.52) * 0.75
            + max(0.0, signals.face_size_score - 0.72) * 0.28
        )
    omission_risk = max(omission_risk, contextual_risk)

    # Reward saving slots, but never enough to hide a broken plan.
    efficiency = 1.0
    if plan.max_shape_count > 0:
        efficiency = _clamp01(1.0 - max(0, plan.target_shape_count - 1) / max(plan.max_shape_count, 1) * 0.30)

    score = _clamp01(coverage * 0.62 + (1.0 - omission_risk) * 0.30 + efficiency * 0.08)

    rollback_feature = None
    if score < min_score and pressures:
        candidates = [
            (value, name)
            for name, value in pressures.items()
            if value >= 0.30
        ]
        if candidates:
            candidates.sort(reverse=True)
            rollback_feature = candidates[0][1]

    reasons: list[str] = []
    if coverage < 0.999:
        reasons.append("identity_plan_not_fulfilled")
    if omission_risk >= 0.30:
        reasons.append("omitted_identity_signal_is_strong")
    if contextual_risk >= 0.30:
        reasons.append("face_became_too_iconic_for_source_density")
    if score < min_score:
        reasons.append("face_identity_loss_low")

    return FaceIdentityValidationReport(
        score=score,
        coverage_score=coverage,
        omission_risk_score=float(omission_risk),
        minimality_efficiency_score=efficiency,
        rendered_feature_count=len(rendered),
        planned_feature_count=len(selected),
        omitted_risky_features=omitted_risky,
        rollback_recommended=rollback_feature is not None,
        rollback_feature=rollback_feature,
        reasons=reasons,
        diagnostics={
            "phase": "10.5-d",
            "primary_eye_side": primary_side,
            "selected_features": sorted(selected),
            "rendered_features": sorted(rendered),
            "omission_pressures": pressures,
            "contextual_risk": contextual_risk,
            "min_score": float(min_score),
            "rollback_limit": 1,
        },
    )


def apply_single_feature_rollback(
    reservation: dict[str, int],
    report: FaceIdentityValidationReport,
    *,
    available_shapes: int,
) -> tuple[dict[str, int], str | None]:
    """Restore at most one omitted identity cue, never exceeding face budget."""
    out = {k: int(bool(v)) for k, v in reservation.items()}
    feature = report.rollback_feature
    if not report.rollback_recommended or feature is None:
        return out, None
    if sum(out.values()) >= max(0, int(available_shapes)):
        return out, None
    if feature not in out:
        return out, None
    out[feature] = 1
    return out, feature
