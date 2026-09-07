from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .face_rules import (
    _choose_eye_pair,
    estimate_eye_candidates,
    estimate_mouth_candidate,
)
from .heuristics import bbox_overlap_ratio, mask_bbox, mask_centroid


@dataclass
class FaceValidationResult:
    accepted: bool
    confidence: float
    threshold: float
    candidate_bbox: tuple[int, int, int, int]
    expected_bbox: tuple[int, int, int, int]
    candidate_source: str = "unknown"
    eye_count: int = 0
    left_eye: tuple[float, float, float] | None = None
    right_eye: tuple[float, float, float] | None = None
    mouth: tuple[float, float, float] | None = None
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "accepted": self.accepted,
            "confidence": self.confidence,
            "threshold": self.threshold,
            "candidate_bbox": list(self.candidate_bbox),
            "expected_bbox": list(self.expected_bbox),
            "candidate_source": self.candidate_source,
            "eye_count": self.eye_count,
            "left_eye": list(self.left_eye) if self.left_eye else None,
            "right_eye": list(self.right_eye) if self.right_eye else None,
            "mouth": list(self.mouth) if self.mouth else None,
            "reasons": list(self.reasons),
            "warnings": list(self.warnings),
            "metrics": self.metrics,
        }


def _clamp01(v: float) -> float:
    return float(max(0.0, min(1.0, v)))


def _score_band(value: float, lo: float, hi: float, *, soft_lo: float, soft_hi: float) -> float:
    if lo <= value <= hi:
        return 1.0
    if value < lo:
        if value <= soft_lo:
            return 0.0
        return _clamp01((value - soft_lo) / max(lo - soft_lo, 1e-6))
    if value >= soft_hi:
        return 0.0
    return _clamp01((soft_hi - value) / max(soft_hi - hi, 1e-6))


def validate_face_candidate(
    image_rgb: np.ndarray,
    face_mask: np.ndarray,
    head_mask: np.ndarray,
    head_bbox: tuple[int, int, int, int],
    expected_face_bbox: tuple[int, int, int, int],
    *,
    candidate_source: str = "unknown",
    skin_mask: np.ndarray | None = None,
    threshold: float = 0.52,
) -> FaceValidationResult:
    face_area = int(np.count_nonzero(face_mask > 0))
    head_area = max(1, int(np.count_nonzero(head_mask > 0)))
    if face_area <= 0:
        return FaceValidationResult(
            accepted=False,
            confidence=0.0,
            threshold=threshold,
            candidate_bbox=expected_face_bbox,
            expected_bbox=expected_face_bbox,
            candidate_source=candidate_source,
            reasons=["empty face candidate"],
            metrics={"face_area": 0, "head_area": head_area},
        )

    bbox = mask_bbox(face_mask)
    cx, cy = mask_centroid(face_mask)
    hx, hy, hw, hh = head_bbox
    hcx = hx + hw / 2.0
    hcy = hy + hh * 0.48

    area_ratio = face_area / max(1.0, head_area)
    bbox_fill = face_area / max(1.0, bbox[2] * bbox[3])
    aspect = bbox[2] / max(1.0, bbox[3])
    center_dx = abs(cx - hcx) / max(hw * 0.5, 1.0)
    center_dy = abs(cy - hcy) / max(hh * 0.5, 1.0)
    centrality = _clamp01(1.0 - (0.60 * center_dx + 0.55 * center_dy))
    expected_overlap = bbox_overlap_ratio(bbox, expected_face_bbox)

    eye_candidates = estimate_eye_candidates(image_rgb, bbox, face_mask)
    left_eye, right_eye = _choose_eye_pair(eye_candidates, bbox)
    mouth = estimate_mouth_candidate(image_rgb, bbox, face_mask)

    eye_count = int(left_eye is not None) + int(right_eye is not None)
    eye_conf = 0.0
    if eye_count > 0:
        eye_conf = float(sum(e[2] for e in [left_eye, right_eye] if e is not None) / eye_count)
    mouth_conf = float(mouth[2]) if mouth is not None else 0.0

    skin_ratio = 0.0
    if skin_mask is not None:
        face_bool = face_mask > 0
        skin_ratio = float(np.count_nonzero(face_bool & (skin_mask > 0)) / max(1, np.count_nonzero(face_bool)))

    top_band = np.zeros_like(face_mask, dtype=np.uint8)
    top_end = hy + max(1, int(round(hh * 0.35)))
    top_band[hy:top_end, hx:hx+hw] = 255
    top_heavy_ratio = float(np.count_nonzero((face_mask > 0) & (top_band > 0)) / max(1, face_area))

    source_prior = {
        "skin_component": 1.0,
        "skin_zone": 0.82,
        "face_zone": 0.42,
    }.get(candidate_source, 0.50)

    eye_presence_score = {0: 0.0, 1: 0.55, 2: 1.0}.get(eye_count, 1.0)
    area_score = _score_band(area_ratio, 0.12, 0.58, soft_lo=0.06, soft_hi=0.72)
    aspect_score = _score_band(aspect, 0.48, 1.35, soft_lo=0.28, soft_hi=1.80)
    skin_score = _score_band(skin_ratio, 0.16, 0.70, soft_lo=0.06, soft_hi=0.88)
    fill_score = _score_band(bbox_fill, 0.28, 0.95, soft_lo=0.12, soft_hi=1.00)

    score = (
        0.10 * source_prior
        + 0.16 * centrality
        + 0.12 * expected_overlap
        + 0.10 * area_score
        + 0.08 * aspect_score
        + 0.06 * fill_score
        + 0.16 * skin_score
        + 0.14 * eye_presence_score
        + 0.05 * eye_conf
        + 0.03 * mouth_conf
    )

    warnings: list[str] = []
    reasons: list[str] = []

    if eye_count == 0 and skin_ratio < 0.22:
        reasons.append("no eye evidence and weak skin support")
    elif eye_count == 0:
        warnings.append("no eye evidence")

    if area_ratio < 0.08:
        reasons.append("face candidate too small for head")
    elif area_ratio > 0.66:
        reasons.append("face candidate too large for head")

    if centrality < 0.34:
        reasons.append("face candidate too far from head center")

    if expected_overlap < 0.30:
        reasons.append("face candidate misses expected face zone")

    if top_heavy_ratio > 0.88 and skin_ratio < 0.18:
        reasons.append("top-heavy non-skin patch looks more like hat or hair")
    elif top_heavy_ratio > 0.72 and skin_ratio < 0.25:
        warnings.append("top-heavy face candidate")

    if aspect > 1.75 and eye_count == 0:
        reasons.append("face candidate too flat and featureless")

    accepted = score >= threshold and not reasons

    metrics = {
        "face_area": face_area,
        "head_area": head_area,
        "area_ratio": area_ratio,
        "bbox_fill": bbox_fill,
        "aspect": aspect,
        "centrality": centrality,
        "expected_overlap": expected_overlap,
        "skin_ratio": skin_ratio,
        "top_heavy_ratio": top_heavy_ratio,
        "source_prior": source_prior,
        "eye_confidence": eye_conf,
        "mouth_confidence": mouth_conf,
    }
    return FaceValidationResult(
        accepted=accepted,
        confidence=float(_clamp01(score)),
        threshold=threshold,
        candidate_bbox=bbox,
        expected_bbox=expected_face_bbox,
        candidate_source=candidate_source,
        eye_count=eye_count,
        left_eye=left_eye,
        right_eye=right_eye,
        mouth=mouth,
        reasons=reasons,
        warnings=warnings,
        metrics=metrics,
    )
