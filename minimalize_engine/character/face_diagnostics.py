from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class FaceDiagnosticsReport:
    """Human-readable consolidation of the alpha10 face pipeline.

    Phase 10.6 is diagnostics-only. It summarizes detection, identity budgeting,
    rendering and quality so visual review does not require opening six separate
    JSON files. It never changes the generated Scene or Shape set.
    """

    status: str
    available: bool
    face_gate_accepted: bool | None
    face_gate_confidence: float | None
    visibility_tier: str | None
    minimality_level: str | None
    selected_features: list[str] = field(default_factory=list)
    omitted_features: list[str] = field(default_factory=list)
    rendered_roles: list[str] = field(default_factory=list)
    risky_omissions: list[str] = field(default_factory=list)
    planned_shape_count: int | None = None
    actual_shape_count: int | None = None
    released_shape_slots: int | None = None
    identity_score: float | None = None
    face_geometry_score: float | None = None
    face_boundary_score: float | None = None
    face_retention_score: float | None = None
    rollback_applied: bool = False
    rollback_feature: str | None = None
    warnings: list[str] = field(default_factory=list)
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _selected_from_plan(plan: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for key, label in (
        ("include_face_base", "face_base"),
        ("include_primary_eye", "primary_eye"),
        ("include_secondary_eye", "secondary_eye"),
        ("include_mouth", "mouth"),
        ("include_helper", "helper"),
    ):
        if bool(plan.get(key, False)):
            out.append(label)
    return out


def build_face_diagnostics_report(
    character_details: dict[str, Any] | None,
    character_quality: dict[str, Any] | None = None,
) -> FaceDiagnosticsReport:
    details = character_details or {}
    face = details.get("face") or {}
    quality = character_quality or {}

    if not face or not bool(face.get("enabled", False)):
        return FaceDiagnosticsReport(
            status="unavailable",
            available=False,
            face_gate_accepted=None,
            face_gate_confidence=None,
            visibility_tier=None,
            minimality_level=None,
            warnings=["dedicated face primitives are unavailable"],
            diagnostics={"phase": "10.6", "rendering_changed": False},
        )

    gate = face.get("validation") or {}
    signals = face.get("identity_signals") or {}
    plan = face.get("identity_plan") or {}
    rendering = face.get("identity_rendering") or {}
    validation = face.get("identity_validation") or {}
    validation_diag = validation.get("diagnostics") or {}

    selected = _selected_from_plan(plan)
    if not selected and rendering.get("enabled") is False:
        # Legacy / diagnostic-disabled route. It is useful to show what actually
        # rendered without pretending an adaptive plan existed.
        selected = []

    omitted = list(plan.get("omitted_features") or [])
    risky = list(validation.get("omitted_risky_features") or [])
    rendered_roles = list(rendering.get("rendered_roles") or [])

    identity_score = _float_or_none(
        quality.get("face_identity_score", validation.get("score"))
    )
    geometry_score = _float_or_none(quality.get("face_geometry_score"))
    boundary_score = _float_or_none(quality.get("face_boundary_score"))
    retention_score = _float_or_none(quality.get("face_retention_score"))

    warnings: list[str] = []
    quality_reasons = list(quality.get("retry_reasons") or [])
    face_reasons = [
        reason
        for reason in quality_reasons
        if reason.startswith("face_") or reason == "false_face_generated"
    ]
    warnings.extend(face_reasons)

    if risky:
        warnings.append("strong identity cue omitted: " + ", ".join(risky))
    if rendering and not bool(rendering.get("plan_fulfilled", True)):
        warnings.append("identity plan was not fully rendered")
    if validation and _float_or_none(validation.get("coverage_score")) is not None:
        if float(validation.get("coverage_score", 1.0)) < 0.999:
            warnings.append("identity plan coverage is incomplete")

    rollback_applied = bool(
        rendering.get("adaptive_rollback_applied", False)
        or validation_diag.get("rollback_applied", False)
    )
    rollback_feature = (
        rendering.get("adaptive_rollback_feature")
        or validation_diag.get("rollback_feature")
    )

    # Diagnostics status is intentionally conservative. "healthy" means the
    # pipeline has no current face-specific retry reason and the adaptive plan
    # was fulfilled. "watch" means review-worthy but not necessarily broken.
    if any(reason == "false_face_generated" for reason in face_reasons):
        status = "repair"
    elif face_reasons:
        status = "watch"
    elif warnings:
        status = "watch"
    else:
        status = "healthy"

    return FaceDiagnosticsReport(
        status=status,
        available=True,
        face_gate_accepted=(
            bool(gate.get("accepted")) if "accepted" in gate else None
        ),
        face_gate_confidence=_float_or_none(gate.get("confidence")),
        visibility_tier=signals.get("visibility_tier"),
        minimality_level=plan.get("minimality_level"),
        selected_features=selected,
        omitted_features=omitted,
        rendered_roles=rendered_roles,
        risky_omissions=risky,
        planned_shape_count=(
            int(rendering["planned_shape_count"])
            if rendering.get("planned_shape_count") is not None
            else None
        ),
        actual_shape_count=(
            int(rendering["actual_shape_count"])
            if rendering.get("actual_shape_count") is not None
            else int(face.get("shape_count", 0))
        ),
        released_shape_slots=(
            int(rendering["released_shape_slots"])
            if rendering.get("released_shape_slots") is not None
            else None
        ),
        identity_score=identity_score,
        face_geometry_score=geometry_score,
        face_boundary_score=boundary_score,
        face_retention_score=retention_score,
        rollback_applied=rollback_applied,
        rollback_feature=rollback_feature,
        warnings=warnings,
        diagnostics={
            "phase": "10.6",
            "rendering_changed": False,
            "signal_phase": signals.get("diagnostics", {}).get("phase"),
            "budget_phase": plan.get("diagnostics", {}).get("phase"),
            "render_phase": rendering.get("phase"),
            "validation_phase": validation_diag.get("phase"),
            "primary_eye_side": signals.get("primary_eye_side"),
            "feature_priority": list(plan.get("feature_priority") or []),
            "utilities": dict(plan.get("utilities") or {}),
            "thresholds": dict(plan.get("thresholds") or {}),
            "identity_validation_reasons": list(validation.get("reasons") or []),
            "quality_face_reasons": face_reasons,
        },
    )
