from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence

import cv2
import numpy as np


PRIMITIVE_ADVISOR_VERSION = "sa7.46-v1"
SUPPORTED_ADVISOR_FAMILIES = (
    "polygon",
    "rectangle",
    "ellipse",
    "line",
    "ribbon",
)
CURRENT_RENDERER_FAMILIES = (
    "polygon",
    "rectangle",
    "ellipse",
)


class PrimitiveAdvisorStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class PrimitiveGeometryEvidence:
    role: str
    source_area: int
    bbox_aspect_ratio: float
    extent: float
    solidity: float
    contour_vertices: int
    ellipse_iou: float
    deterministic_family: str

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "source_area": self.source_area,
            "bbox_aspect_ratio": round(float(self.bbox_aspect_ratio), 6),
            "extent": round(float(self.extent), 6),
            "solidity": round(float(self.solidity), 6),
            "contour_vertices": self.contour_vertices,
            "ellipse_iou": round(float(self.ellipse_iou), 6),
            "deterministic_family": self.deterministic_family,
        }


@dataclass(frozen=True)
class PrimitiveTypeSuggestion:
    role: str
    primitive_family: str
    confidence: float
    source: str
    rationale: str = ""
    authoritative: bool = False

    def __post_init__(self) -> None:
        if self.primitive_family not in SUPPORTED_ADVISOR_FAMILIES:
            raise ValueError(
                f"unsupported advisor primitive family: {self.primitive_family}"
            )
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("advisor confidence must be within [0, 1]")
        if self.authoritative:
            raise ValueError("primitive advisor suggestions must be non-authoritative")

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "primitive_family": self.primitive_family,
            "confidence": float(self.confidence),
            "source": self.source,
            "rationale": self.rationale,
            "authoritative": False,
        }


@dataclass(frozen=True)
class PrimitiveAdvisorAudit:
    role: str
    suggestion: PrimitiveTypeSuggestion
    geometry: PrimitiveGeometryEvidence
    family_agreement: bool
    renderer_supported: bool
    production_eligible: bool
    reasons: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "suggestion": self.suggestion.to_dict(),
            "geometry": self.geometry.to_dict(),
            "family_agreement": self.family_agreement,
            "renderer_supported": self.renderer_supported,
            "production_eligible": self.production_eligible,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class PrimitiveAdvisorReport:
    status: PrimitiveAdvisorStatus
    geometry_evidence: Mapping[str, PrimitiveGeometryEvidence]
    audits: tuple[PrimitiveAdvisorAudit, ...]
    authoritative: bool = False
    production_output_changed: bool = False
    version: str = PRIMITIVE_ADVISOR_VERSION

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "status": self.status.value,
            "geometry_evidence": {
                role: evidence.to_dict()
                for role, evidence in sorted(self.geometry_evidence.items())
            },
            "audits": [audit.to_dict() for audit in self.audits],
            "authoritative": False,
            "production_output_changed": False,
        }


def _largest_contour(mask: np.ndarray):
    contours, _ = cv2.findContours(
        np.asarray(mask).astype(np.uint8),
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    return max(contours, key=cv2.contourArea) if contours else None


def _ellipse_iou(mask: np.ndarray, contour) -> float:
    if contour is None or len(contour) < 5:
        return 0.0
    try:
        ellipse = cv2.fitEllipse(contour)
    except cv2.error:
        return 0.0
    rendered = np.zeros(mask.shape, np.uint8)
    cv2.ellipse(rendered, ellipse, 1, -1)
    src = np.asarray(mask).astype(bool)
    out = rendered.astype(bool)
    union = int((src | out).sum())
    return 0.0 if union == 0 else int((src & out).sum()) / union


def analyze_primitive_geometry(
    role: str,
    mask: np.ndarray,
) -> PrimitiveGeometryEvidence:
    src = np.asarray(mask).astype(bool)
    area = int(src.sum())
    if area <= 0:
        raise ValueError(f"{role}: source mask is empty")

    ys, xs = np.where(src)
    width = int(xs.max() - xs.min() + 1)
    height = int(ys.max() - ys.min() + 1)
    aspect = max(width / max(1, height), height / max(1, width))
    extent = area / max(1, width * height)

    contour = _largest_contour(src)
    contour_vertices = 0
    solidity = 0.0
    if contour is not None:
        perimeter = cv2.arcLength(contour, True)
        polygon = cv2.approxPolyDP(
            contour,
            max(1.0, 0.01 * perimeter),
            True,
        )
        contour_vertices = int(len(polygon))
        hull = cv2.convexHull(contour)
        hull_area = float(cv2.contourArea(hull))
        contour_area = float(cv2.contourArea(contour))
        solidity = 0.0 if hull_area <= 0 else contour_area / hull_area

    ellipse_iou = _ellipse_iou(src, contour)

    # This is evidence, not a new renderer selector. It provides an explicit,
    # deterministic comparison point for external StarVector-style advice.
    if aspect >= 5.0 and extent <= 0.45:
        family = "line"
    elif aspect >= 3.0 and extent <= 0.75:
        family = "ribbon"
    elif ellipse_iou >= 0.88 and solidity >= 0.90:
        family = "ellipse"
    elif extent >= 0.90 and solidity >= 0.95 and contour_vertices <= 8:
        family = "rectangle"
    else:
        family = "polygon"

    return PrimitiveGeometryEvidence(
        role=role,
        source_area=area,
        bbox_aspect_ratio=aspect,
        extent=extent,
        solidity=solidity,
        contour_vertices=contour_vertices,
        ellipse_iou=ellipse_iou,
        deterministic_family=family,
    )


def audit_primitive_type_advice(
    role_masks: Mapping[str, np.ndarray],
    suggestions: Sequence[PrimitiveTypeSuggestion] | None,
) -> PrimitiveAdvisorReport:
    geometry = {
        role: analyze_primitive_geometry(role, mask)
        for role, mask in sorted(role_masks.items())
    }

    if suggestions is None:
        return PrimitiveAdvisorReport(
            status=PrimitiveAdvisorStatus.UNAVAILABLE,
            geometry_evidence=geometry,
            audits=(),
        )

    audits: list[PrimitiveAdvisorAudit] = []
    seen_roles: set[str] = set()
    for suggestion in suggestions:
        if suggestion.role in seen_roles:
            raise ValueError(f"duplicate primitive advisor role: {suggestion.role}")
        seen_roles.add(suggestion.role)
        if suggestion.role not in geometry:
            raise ValueError(
                f"advisor suggestion references unknown role: {suggestion.role}"
            )

        evidence = geometry[suggestion.role]
        agreement = (
            suggestion.primitive_family == evidence.deterministic_family
        )
        renderer_supported = (
            suggestion.primitive_family in CURRENT_RENDERER_FAMILIES
        )
        reasons: list[str] = []
        if not agreement:
            reasons.append(
                "advisor_family_disagrees_with_source_geometry_evidence"
            )
        if not renderer_supported:
            reasons.append("advisor_family_not_currently_renderer_supported")
        reasons.append("advisor_output_is_research_only")

        # SA7.46 deliberately promotes nothing. A later deterministic rule
        # change requires explicit tests and a separate production decision.
        audits.append(
            PrimitiveAdvisorAudit(
                role=suggestion.role,
                suggestion=suggestion,
                geometry=evidence,
                family_agreement=agreement,
                renderer_supported=renderer_supported,
                production_eligible=False,
                reasons=tuple(reasons),
            )
        )

    return PrimitiveAdvisorReport(
        status=PrimitiveAdvisorStatus.AVAILABLE,
        geometry_evidence=geometry,
        audits=tuple(sorted(audits, key=lambda row: row.role)),
    )
