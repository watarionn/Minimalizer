from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np

from .face_identity import FaceIdentitySignals


FEATURES = ("face_base", "primary_eye", "secondary_eye", "mouth", "helper")
OPTIONAL_FEATURES = FEATURES[1:]


@dataclass(slots=True)
class FaceIdentityPlan:
    """A minimal, signal-driven face representation plan.

    Phase 10.5-b decides *which* cues deserve Shape slots but does not change
    rendering yet. Phase 10.5-c consumes this plan in the face primitive
    builder. The face base is the only unconditional cue.
    """

    include_face_base: bool
    include_primary_eye: bool
    include_secondary_eye: bool
    include_mouth: bool
    include_helper: bool
    target_shape_count: int
    max_shape_count: int
    minimality_level: str
    feature_priority: list[str] = field(default_factory=list)
    omitted_features: list[str] = field(default_factory=list)
    reasoning: list[str] = field(default_factory=list)
    utilities: dict[str, float] = field(default_factory=dict)
    thresholds: dict[str, float] = field(default_factory=dict)
    diagnostics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class FaceIdentityBudgetResult:
    """Concrete slot reservation derived from a FaceIdentityPlan."""

    reserved_shapes: dict[str, int]
    omitted_features: list[str]
    total_reserved: int
    available_shapes: int
    released_shapes: int
    plan: FaceIdentityPlan
    diagnostics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        out = asdict(self)
        out["plan"] = self.plan.to_dict()
        return out


def _clamp01(value: float) -> float:
    return float(np.clip(value, 0.0, 1.0))


def _tier_cap(visibility_tier: str) -> int:
    # Includes the face base. These are intentionally small caps because a
    # minimal face should not automatically become a miniature illustration.
    return {
        "micro": 2,
        "small": 2,
        "medium": 3,
        "large": 4,
    }.get(visibility_tier, 2)


def _abstraction_cap_adjustment(level: int) -> int:
    # Level 1 keeps more source detail; level 5 is the most abstract preset.
    if level <= 1:
        return 1
    if level >= 5:
        return -1
    return 0


def _base_feature_threshold(visibility_tier: str, abstraction_level: int) -> float:
    base = {
        "micro": 0.66,
        "small": 0.52,
        "medium": 0.40,
        "large": 0.34,
    }.get(visibility_tier, 0.52)
    # Higher abstraction asks every extra Shape to justify itself more strongly.
    base += (int(abstraction_level) - 3) * 0.035
    return float(np.clip(base, 0.28, 0.78))


def _feature_utilities(signals: FaceIdentitySignals) -> dict[str, float]:
    expression = signals.expression_salience_score
    contour = signals.contour_salience_score

    primary_eye = signals.eye_salience_score
    # A wink/strong asymmetric expression makes the surviving eye more useful.
    if expression >= 0.78 and signals.second_eye_salience_score < primary_eye * 0.55:
        primary_eye = _clamp01(primary_eye + 0.22 * expression)

    secondary_eye = signals.second_eye_salience_score
    # A second eye is useful for symmetry, but should not be forced in a wink or
    # when the source signal is weak.
    if expression >= 0.78 and signals.second_eye_salience_score < 0.25:
        secondary_eye *= 0.55

    mouth = _clamp01(
        signals.mouth_salience_score * (0.86 + 0.18 * expression)
    )

    # Hair is already represented by dedicated Hair Shapes, so a face helper is
    # deliberately discounted. It wins a slot only when fringe/contour relation
    # is one of the strongest identity cues.
    helper = _clamp01(
        signals.fringe_relation_score * 0.62
        + max(0.0, contour - 0.72) * 0.18
    )

    # A distinctive contour can carry identity by itself. Rather than drawing
    # more details to "match" it, slightly raise the cost of optional cues.
    contour_relief = max(0.0, contour - 0.72) * 0.10
    return {
        "primary_eye": _clamp01(primary_eye - contour_relief * 0.35),
        "secondary_eye": _clamp01(secondary_eye - contour_relief * 0.55),
        "mouth": _clamp01(mouth - contour_relief * 0.30),
        "helper": _clamp01(helper - contour_relief * 0.15),
    }


def _feature_thresholds(
    signals: FaceIdentitySignals,
    abstraction_level: int,
) -> dict[str, float]:
    base = _base_feature_threshold(signals.visibility_tier, abstraction_level)
    return {
        # A single eye is the cheapest conventional face cue, so it gets a small
        # preference. The second eye must earn its own slot.
        "primary_eye": max(0.24, base - 0.08),
        "secondary_eye": min(0.86, base + 0.06),
        "mouth": min(0.86, base + 0.01),
        "helper": min(0.90, base + 0.12),
    }


def _minimality_label(target_shape_count: int, max_shape_count: int) -> str:
    if target_shape_count <= 1:
        return "iconic"
    if target_shape_count == 2:
        return "essential"
    if target_shape_count == 3:
        return "balanced"
    if target_shape_count >= max_shape_count:
        return "expressive-minimal"
    return "balanced"


def build_face_identity_plan(
    signals: FaceIdentitySignals,
    *,
    available_shapes: int,
    abstraction_level: int | None = None,
) -> FaceIdentityPlan:
    """Choose the smallest useful set of face cues from Phase 10.5-a signals.

    `available_shapes` is a hard ceiling from the existing Character budget. The
    adaptive plan is allowed to use fewer slots. Released slots are not spent
    automatically; minimality is treated as a feature, not a budget deficit.
    """
    level = int(
        signals.abstraction_level
        if abstraction_level is None
        else abstraction_level
    )
    available = max(0, int(available_shapes))

    if available <= 0:
        return FaceIdentityPlan(
            include_face_base=False,
            include_primary_eye=False,
            include_secondary_eye=False,
            include_mouth=False,
            include_helper=False,
            target_shape_count=0,
            max_shape_count=0,
            minimality_level="none",
            feature_priority=[],
            omitted_features=list(OPTIONAL_FEATURES),
            reasoning=["no face Shape slots are available"],
            utilities={name: 0.0 for name in OPTIONAL_FEATURES},
            thresholds={name: 1.0 for name in OPTIONAL_FEATURES},
            diagnostics={
                "phase": "10.5-b",
                "rendering_changed": False,
                "visibility_tier": signals.visibility_tier,
                "abstraction_level": level,
            },
        )

    visibility_cap = _tier_cap(signals.visibility_tier)
    abstraction_cap = max(1, visibility_cap + _abstraction_cap_adjustment(level))
    max_shapes = min(available, abstraction_cap)

    utilities = _feature_utilities(signals)
    thresholds = _feature_thresholds(signals, level)

    eligible = [
        name
        for name in OPTIONAL_FEATURES
        if utilities[name] >= thresholds[name]
    ]

    # Primary eye is preferred as the first conventional mark when it is close
    # to threshold and expression evidence is strong. This helps one-eye/wink
    # faces survive without forcing a second eye.
    if (
        "primary_eye" not in eligible
        and signals.expression_salience_score >= 0.82
        and utilities["primary_eye"] >= max(0.18, thresholds["primary_eye"] - 0.18)
    ):
        eligible.append("primary_eye")

    ranked = sorted(
        eligible,
        key=lambda name: (
            utilities[name],
            # deterministic tie-break: eye > mouth > second eye > helper
            {"primary_eye": 4, "mouth": 3, "secondary_eye": 2, "helper": 1}[name],
        ),
        reverse=True,
    )

    optional_slots = max(0, max_shapes - 1)
    selected = ranked[:optional_slots]

    # If the second eye survives but the primary eye somehow does not, swap it
    # for the primary cue. A "secondary" eye cannot be the sole eye mark.
    if "secondary_eye" in selected and "primary_eye" not in selected:
        selected[selected.index("secondary_eye")] = "primary_eye"
        selected = list(dict.fromkeys(selected))

    target_count = 1 + len(selected)
    omitted = [name for name in OPTIONAL_FEATURES if name not in selected]

    reasoning = [
        f"{signals.visibility_tier} face cap={visibility_cap}",
        f"abstraction level {level} cap={abstraction_cap}",
        f"existing face budget allows {available} Shape(s)",
    ]
    if selected:
        reasoning.append("kept cues: " + ", ".join(selected))
    else:
        reasoning.append("all optional cues were weaker than their adaptive thresholds")
    if target_count < available:
        reasoning.append(
            f"released {available - target_count} unused face Shape slot(s) to preserve minimality"
        )

    return FaceIdentityPlan(
        include_face_base=True,
        include_primary_eye="primary_eye" in selected,
        include_secondary_eye="secondary_eye" in selected,
        include_mouth="mouth" in selected,
        include_helper="helper" in selected,
        target_shape_count=target_count,
        max_shape_count=max_shapes,
        minimality_level=_minimality_label(target_count, max_shapes),
        feature_priority=ranked,
        omitted_features=omitted,
        reasoning=reasoning,
        utilities={k: float(v) for k, v in utilities.items()},
        thresholds={k: float(v) for k, v in thresholds.items()},
        diagnostics={
            "phase": "10.5-b",
            "rendering_changed": False,
            "visibility_tier": signals.visibility_tier,
            "face_render_scale": float(signals.face_render_scale),
            "feature_density_score": float(signals.feature_density_score),
            "contour_salience_score": float(signals.contour_salience_score),
            "expression_salience_score": float(signals.expression_salience_score),
            "abstraction_level": level,
            "visibility_cap": visibility_cap,
            "abstraction_cap": abstraction_cap,
            "available_shapes": available,
            "selected_features": list(selected),
        },
    )


def reserve_shapes_from_identity_plan(
    plan: FaceIdentityPlan,
) -> dict[str, int]:
    return {
        "face_base": int(plan.include_face_base),
        "primary_eye": int(plan.include_primary_eye),
        "secondary_eye": int(plan.include_secondary_eye),
        "mouth": int(plan.include_mouth),
        "helper": int(plan.include_helper),
    }


def apply_face_identity_budget(
    plan: FaceIdentityPlan,
    *,
    available_shapes: int,
) -> FaceIdentityBudgetResult:
    """Turn a plan into a hard reservation without exceeding available slots."""
    available = max(0, int(available_shapes))
    requested = reserve_shapes_from_identity_plan(plan)

    priority = ["face_base"] + [
        name for name in plan.feature_priority if name in OPTIONAL_FEATURES
    ]
    # Include any selected feature that was not in feature_priority (defensive).
    for name in OPTIONAL_FEATURES:
        if requested[name] and name not in priority:
            priority.append(name)

    reserved = {name: 0 for name in FEATURES}
    left = available
    for name in priority:
        if left <= 0:
            break
        if requested.get(name, 0) <= 0:
            continue
        reserved[name] = 1
        left -= 1

    total = sum(reserved.values())
    omitted = [name for name in OPTIONAL_FEATURES if reserved[name] == 0]
    return FaceIdentityBudgetResult(
        reserved_shapes=reserved,
        omitted_features=omitted,
        total_reserved=total,
        available_shapes=available,
        released_shapes=max(0, available - total),
        plan=plan,
        diagnostics={
            "phase": "10.5-b",
            "rendering_changed": False,
            "priority_order": priority,
            "requested_total": sum(requested.values()),
            "hard_ceiling_respected": total <= available,
        },
    )


def can_render_secondary_eye(
    result: FaceIdentityBudgetResult,
) -> bool:
    return bool(result.reserved_shapes.get("secondary_eye", 0))


def can_render_mouth(
    result: FaceIdentityBudgetResult,
) -> bool:
    return bool(result.reserved_shapes.get("mouth", 0))


def can_render_helper(
    result: FaceIdentityBudgetResult,
) -> bool:
    return bool(result.reserved_shapes.get("helper", 0))
