from __future__ import annotations

from dataclasses import dataclass, asdict
import numpy as np

from ..models import Scene


@dataclass(slots=True)
class HandQualityReport:
    score: float
    retention_score: float
    geometry_score: float
    connection_score: float
    direction_score: float
    holding_contact_score: float | None
    expected_count: int
    rendered_count: int
    applicable: bool
    retry_reasons: list[str]
    diagnostics: dict

    def to_dict(self) -> dict:
        return asdict(self)


def _details(scene: Scene) -> dict:
    return (
        scene.metadata.get("character", {})
        .get("details", {})
        .get("hands", {})
        or {}
    )


def evaluate_hand_quality(
    scene: Scene,
    *,
    min_score: float = 0.72,
    min_retention: float = 0.72,
    min_geometry: float = 0.72,
    min_holding_contact: float = 0.45,
) -> HandQualityReport:
    """Evaluate whether validated hand intent survived as readable minimal masses.

    This is intentionally not a finger-count metric.  It checks only that hand
    candidates considered worth keeping were rendered, connected to the arm,
    aligned with the gesture, and touching a prop when the intent is holding.
    """
    hands = _details(scene)
    if not hands or not hands.get("enabled", False):
        return HandQualityReport(
            score=1.0,
            retention_score=1.0,
            geometry_score=1.0,
            connection_score=1.0,
            direction_score=1.0,
            holding_contact_score=None,
            expected_count=0,
            rendered_count=0,
            applicable=False,
            retry_reasons=[],
            diagnostics={"reason": "hand analysis unavailable or disabled"},
        )

    validation = hands.get("candidate_validation") or {}
    analysis = hands.get("analysis") or {}
    rendering = hands.get("rendering") or {}
    geometry = hands.get("geometry_validation") or {}

    expected = int(
        validation.get("accepted_count", analysis.get("diagnostics", {}).get("detected_hand_count", 0))
        or 0
    )
    rendered = int(hands.get("shape_count", 0) or 0)
    if expected <= 0:
        retention = 1.0
    else:
        retention = float(np.clip(rendered / expected, 0.0, 1.0))

    geom_items = list(geometry.get("hands") or [])
    geometry_score = float(geometry.get("score", 1.0) or 0.0) if geom_items else 1.0
    connection = float(np.mean([x.get("connection_score", 0.0) for x in geom_items])) if geom_items else 1.0
    direction = float(np.mean([x.get("direction_score", 0.0) for x in geom_items])) if geom_items else 1.0
    holding = [float(x.get("prop_contact_score", 0.0)) for x in geom_items if x.get("intent") == "holding"]
    holding_score = float(np.mean(holding)) if holding else None

    weighted = [(retention, 0.38), (geometry_score, 0.26), (connection, 0.18), (direction, 0.18)]
    if holding_score is not None:
        weighted = [(retention, 0.32), (geometry_score, 0.22), (connection, 0.17), (direction, 0.14), (holding_score, 0.15)]
    score = float(sum(v * w for v, w in weighted) / sum(w for _, w in weighted))

    reasons: list[str] = []
    if retention < min_retention:
        reasons.append("hand_retention_low")
    if geometry_score < min_geometry or connection < min_geometry * 0.90 or direction < min_geometry * 0.78:
        reasons.append("hand_geometry_low")
    if holding_score is not None and holding_score < min_holding_contact:
        reasons.append("hand_holding_contact_low")
    if score < min_score:
        reasons.append("hand_quality_low")

    return HandQualityReport(
        score=float(np.clip(score, 0.0, 1.0)),
        retention_score=retention,
        geometry_score=geometry_score,
        connection_score=connection,
        direction_score=direction,
        holding_contact_score=holding_score,
        expected_count=expected,
        rendered_count=rendered,
        applicable=bool(expected > 0 or rendered > 0),
        retry_reasons=reasons,
        diagnostics={
            "phase": "11.5",
            "principle": "preserve hand intent, not finger detail",
            "validation": validation,
            "rendering": rendering,
            "geometry": geometry,
            "thresholds": {
                "score": min_score,
                "retention": min_retention,
                "geometry": min_geometry,
                "holding_contact": min_holding_contact,
            },
        },
    )
