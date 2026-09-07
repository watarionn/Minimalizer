from __future__ import annotations

from dataclasses import dataclass, asdict
import numpy as np


@dataclass
class CharacterWideIdentityReport:
    score: float
    silhouette_score: float
    geometry_score: float | None
    face_score: float | None
    outfit_score: float | None
    prop_score: float | None
    hand_score: float | None
    layout_score: float | None
    minimality_score: float
    retry_reasons: list[str]
    diagnostics: dict

    def to_dict(self) -> dict:
        return asdict(self)


def evaluate_character_wide_identity(
    *,
    generic_quality: dict,
    character_quality: dict,
    outfit_quality: dict | None = None,
    prop_quality: dict | None = None,
    min_score: float = 0.72,
) -> CharacterWideIdentityReport:
    silhouette = float(generic_quality.get("silhouette_similarity", generic_quality.get("identity_score", 0.0)))
    minimality = float(generic_quality.get("minimality_score", 1.0))
    geometry = character_quality.get("geometry_fidelity_score")
    face = character_quality.get("face_identity_score")
    hand = character_quality.get("hand_quality_score")
    layout = character_quality.get("layout_score")
    outfit = (outfit_quality or {}).get("score")
    prop = (prop_quality or {}).get("score")

    weighted: list[tuple[float, float]] = [(silhouette, 0.25)]
    for value, weight in [
        (geometry, 0.20),
        (face, 0.16),
        (outfit, 0.13),
        (prop, 0.08),
        (hand, 0.07),
        (layout, 0.11),
    ]:
        if isinstance(value, (int, float)):
            weighted.append((float(value), weight))
    total_w = sum(w for _, w in weighted)
    structural = sum(v * w for v, w in weighted) / max(total_w, 1e-9)
    # Minimality is not identity by itself, but excessive clutter damages the
    # intended design. Keep it as a gentle multiplier, not a hard part count.
    score = float(np.clip(structural * (0.92 + 0.08 * np.clip(minimality, 0.0, 1.0)), 0.0, 1.0))
    reasons = ["character_wide_identity_low"] if score < min_score else []
    return CharacterWideIdentityReport(
        score=score,
        silhouette_score=silhouette,
        geometry_score=float(geometry) if isinstance(geometry, (int, float)) else None,
        face_score=float(face) if isinstance(face, (int, float)) else None,
        outfit_score=float(outfit) if isinstance(outfit, (int, float)) else None,
        prop_score=float(prop) if isinstance(prop, (int, float)) else None,
        hand_score=float(hand) if isinstance(hand, (int, float)) else None,
        layout_score=float(layout) if isinstance(layout, (int, float)) else None,
        minimality_score=minimality,
        retry_reasons=reasons,
        diagnostics={"structural_score": float(structural), "component_count": len(weighted)},
    )
