from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any, Mapping

import cv2
import numpy as np


FAMILY_ORDER = (
    "polygon",
    "rounded_polygon",
    "ellipse",
    "capsule",
    "oriented_rectangle",
    "tapered_strip",
    "polyline_ribbon",
)

PART_FAMILIES: dict[str, tuple[str, ...]] = {
    "face": ("ellipse", "rounded_polygon", "polygon"),
    "hair": ("polygon", "rounded_polygon", "polyline_ribbon"),
    "head": ("ellipse", "rounded_polygon", "polygon"),
    "neck": ("capsule", "tapered_strip", "rounded_polygon", "polygon"),
    "torso": (
        "rounded_polygon",
        "polygon",
        "tapered_strip",
        "oriented_rectangle",
    ),
    "left_arm": (
        "capsule",
        "tapered_strip",
        "polyline_ribbon",
        "rounded_polygon",
        "polygon",
    ),
    "right_arm": (
        "capsule",
        "tapered_strip",
        "polyline_ribbon",
        "rounded_polygon",
        "polygon",
    ),
    "lower_body": (
        "polygon",
        "rounded_polygon",
        "tapered_strip",
        "oriented_rectangle",
    ),
    "major_clothing": (
        "rounded_polygon",
        "polygon",
        "tapered_strip",
        "oriented_rectangle",
    ),
    "accessory_or_held_object": (
        "polyline_ribbon",
        "tapered_strip",
        "polygon",
        "ellipse",
    ),
}

ARM_PARTS = frozenset(("left_arm", "right_arm"))
ARM_LOW_ELONGATION_MAX = 2.25
ARM_LARGE_MASS_MIN_SUBJECT_RATIO = 0.02
ARM_SLENDER_FAMILIES = (
    "capsule",
    "tapered_strip",
    "polyline_ribbon",
    "rounded_polygon",
)
ARM_BROAD_FAMILIES = (
    "polygon",
    "rounded_polygon",
    "tapered_strip",
    "polyline_ribbon",
)

PART_VERTEX_BUDGETS: dict[str, int] = {
    "face": 10,
    "hair": 16,
    "head": 12,
    "neck": 8,
    "torso": 12,
    "left_arm": 10,
    "right_arm": 10,
    "lower_body": 12,
    "major_clothing": 14,
    "accessory_or_held_object": 14,
}

FAMILY_PRIORS: dict[str, dict[str, float]] = {
    "face": {"ellipse": -0.08, "rounded_polygon": -0.03},
    "hair": {"polygon": -0.06, "rounded_polygon": -0.03},
    "head": {"ellipse": -0.05, "rounded_polygon": -0.03},
    "torso": {"rounded_polygon": -0.04, "tapered_strip": -0.02},
    "lower_body": {"polygon": -0.04, "tapered_strip": -0.02},
    "major_clothing": {"rounded_polygon": -0.04, "polygon": -0.03},
    "accessory_or_held_object": {
        "polyline_ribbon": -0.08,
        "tapered_strip": -0.05,
    },
}


def _rounded(value: float) -> float:
    return round(float(value), 6)


def _points_payload(points: np.ndarray) -> list[list[float]]:
    return [
        [_rounded(point[0]), _rounded(point[1])]
        for point in np.asarray(points, dtype=np.float64).reshape(-1, 2)
    ]


@dataclass(frozen=True)
class PartAwareGeometrizationPolicy:
    coverage_weight: float = 0.45
    spill_weight: float = 0.25
    silhouette_weight: float = 0.20
    complexity_weight: float = 0.10
    unbound_families: tuple[str, ...] = ("polygon", "rounded_polygon")
    max_candidates_per_mass: int = 4
    unbound_vertex_budget: int = 12
    minimum_candidates_per_active_mass: int = 2
    allow_axis_aligned_rectangle: bool = False
    allow_cross_mass_candidate: bool = False
    allow_prune_resurrection: bool = False

    def __post_init__(self) -> None:
        weights = (
            self.coverage_weight,
            self.spill_weight,
            self.silhouette_weight,
            self.complexity_weight,
        )
        if any(value < 0 for value in weights) or sum(weights) <= 0:
            raise ValueError("Phase 10 cost weights must be non-negative")
        if self.max_candidates_per_mass < 2:
            raise ValueError("Phase 10 requires multiple candidates per mass")
        if not 2 <= self.minimum_candidates_per_active_mass <= self.max_candidates_per_mass:
            raise ValueError("invalid Phase 10 candidate-count bounds")
        if self.unbound_vertex_budget < 3:
            raise ValueError("unbound vertex budget must be at least 3")
        if self.allow_axis_aligned_rectangle:
            raise ValueError("Phase 10 forbids generic axis-aligned rectangles")
        if self.allow_cross_mass_candidate:
            raise ValueError("Phase 10 forbids cross-mass candidates")
        if self.allow_prune_resurrection:
            raise ValueError("Phase 10 forbids Phase 8 prune resurrection")
        if len(set(PART_FAMILIES.values())) < 4:
            raise ValueError("Phase 10 requires genuinely part-specific families")
        known = set(FAMILY_ORDER)
        configured = {
            family
            for families in (*PART_FAMILIES.values(), self.unbound_families)
            for family in families
        }
        if not configured <= known:
            raise ValueError("Phase 10 policy contains an unsupported family")

    def families_for(self, part_id: str | None) -> tuple[str, ...]:
        families = (
            self.unbound_families
            if part_id is None
            else PART_FAMILIES.get(part_id, ("polygon", "rounded_polygon"))
        )
        return tuple(families[: self.max_candidates_per_mass])

    def families_for_mass(
        self,
        part_id: str | None,
        *,
        elongation: float,
    ) -> tuple[str, ...]:
        if part_id in ARM_PARTS:
            families = (
                ARM_BROAD_FAMILIES
                if elongation <= ARM_LOW_ELONGATION_MAX
                else ARM_SLENDER_FAMILIES
            )
            return tuple(families[: self.max_candidates_per_mass])
        return self.families_for(part_id)

    def vertex_budget_for(self, part_id: str | None) -> int:
        if part_id is None:
            return self.unbound_vertex_budget
        return PART_VERTEX_BUDGETS.get(part_id, self.unbound_vertex_budget)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cost_weights": {
                "complexity": self.complexity_weight,
                "coverage": self.coverage_weight,
                "silhouette": self.silhouette_weight,
                "spill": self.spill_weight,
            },
            "family_order": list(FAMILY_ORDER),
            "part_families": {
                key: list(value) for key, value in sorted(PART_FAMILIES.items())
            },
            "unbound_families": list(self.unbound_families),
            "part_vertex_budgets": {
                key: value for key, value in sorted(PART_VERTEX_BUDGETS.items())
            },
            "unbound_vertex_budget": self.unbound_vertex_budget,
            "max_candidates_per_mass": self.max_candidates_per_mass,
            "minimum_candidates_per_active_mass": self.minimum_candidates_per_active_mass,
            "allow_axis_aligned_rectangle": False,
            "allow_cross_mass_candidate": False,
            "allow_prune_resurrection": False,
            "arm_family_policy": {
                "broad_families": list(ARM_BROAD_FAMILIES),
                "large_mass_min_subject_ratio": ARM_LARGE_MASS_MIN_SUBJECT_RATIO,
                "low_elongation_max": ARM_LOW_ELONGATION_MAX,
                "slender_families": list(ARM_SLENDER_FAMILIES),
                "large_low_elongation_winner_forbidden": [
                    "capsule",
                    "oriented_rectangle",
                ],
            },
            "selection": "minimum-total-cost-then-family-order",
        }


@dataclass(frozen=True)
class PrimitiveCandidate:
    candidate_id: str
    mass_id: str
    semantic_part_id: str | None
    binding_status: str
    action: str
    primitive_type: str
    parameters: dict[str, Any]
    source_pixel_count: int
    candidate_pixel_count: int
    complexity_units: int
    complexity_budget: int
    cost_breakdown: dict[str, float]
    total_cost: float
    palette_id: str
    evidence_refs: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "mass_id": self.mass_id,
            "semantic_part_id": self.semantic_part_id,
            "binding_status": self.binding_status,
            "action": self.action,
            "primitive_type": self.primitive_type,
            "parameters": self.parameters,
            "source_pixel_count": self.source_pixel_count,
            "candidate_pixel_count": self.candidate_pixel_count,
            "complexity_units": self.complexity_units,
            "complexity_budget": self.complexity_budget,
            "cost_breakdown": self.cost_breakdown,
            "total_cost": _rounded(self.total_cost),
            "palette_id": self.palette_id,
            "binding": {
                "source_mass": f"phase07:{self.mass_id}",
                "semantic_part": self.semantic_part_id,
            },
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True)
class SelectedPrimitive:
    primitive_id: str
    candidate_id: str
    mass_id: str
    semantic_part_id: str | None
    binding_status: str
    primitive_type: str
    palette_id: str
    palette_color_rgb: tuple[int, int, int]
    total_cost: float
    selection_rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "primitive_id": self.primitive_id,
            "candidate_id": self.candidate_id,
            "mass_id": self.mass_id,
            "semantic_part_id": self.semantic_part_id,
            "binding_status": self.binding_status,
            "primitive_type": self.primitive_type,
            "palette_id": self.palette_id,
            "palette_color_rgb": list(self.palette_color_rgb),
            "total_cost": _rounded(self.total_cost),
            "selection_rationale": self.selection_rationale,
        }


@dataclass(frozen=True)
class PartAwareGeometrizationResult:
    width: int
    height: int
    candidates: tuple[PrimitiveCandidate, ...]
    selected: tuple[SelectedPrimitive, ...]
    omitted_mass_ids: tuple[str, ...]
    validation: dict[str, Any]
    policy: PartAwareGeometrizationPolicy
    candidate_masks: dict[str, np.ndarray]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "coordinate_space": {
                "pixel_width": self.width,
                "pixel_height": self.height,
                "normalized_origin": "top-left",
                "normalized_range": [0.0, 1.0],
            },
            "geometrization_policy": self.policy.to_dict(),
            "primitive_candidates": [item.to_dict() for item in self.candidates],
            "candidate_costs": [
                {
                    "candidate_id": item.candidate_id,
                    "mass_id": item.mass_id,
                    "semantic_part_id": item.semantic_part_id,
                    "primitive_type": item.primitive_type,
                    "cost_breakdown": item.cost_breakdown,
                    "total_cost": _rounded(item.total_cost),
                }
                for item in self.candidates
            ],
            "selected_primitives": [item.to_dict() for item in self.selected],
            "omitted_mass_ids": list(self.omitted_mass_ids),
            "validation": self.validation,
        }


def _decode_runs(runs: Any, *, width: int, height: int) -> np.ndarray:
    if not isinstance(runs, list):
        raise ValueError("Phase 7 mass pixel_runs must be a list")
    mask = np.zeros((height, width), dtype=bool)
    for raw in runs:
        if not isinstance(raw, (list, tuple)) or len(raw) != 3:
            raise ValueError("Phase 7 mass pixel_runs must contain [y, x0, x1]")
        y, x0, x1 = (int(raw[0]), int(raw[1]), int(raw[2]))
        if not (0 <= y < height and 0 <= x0 < x1 <= width):
            raise ValueError("Phase 7 mass pixel run is outside the canvas")
        if np.any(mask[y, x0:x1]):
            raise ValueError("Phase 7 mass pixel_runs overlap")
        mask[y, x0:x1] = True
    return mask


def _contours(mask: np.ndarray) -> list[np.ndarray]:
    found, _ = cv2.findContours(
        mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
    )
    return sorted(
        found,
        key=lambda contour: (
            -float(cv2.contourArea(contour)),
            int(cv2.boundingRect(contour)[1]),
            int(cv2.boundingRect(contour)[0]),
        ),
    )


def _approx_contour(contour: np.ndarray, budget: int) -> np.ndarray:
    if len(contour) <= 2:
        x, y, w, h = cv2.boundingRect(contour)
        return np.asarray(
            [[x, y], [x + max(0, w - 1), y], [x + max(0, w - 1), y + max(0, h - 1)], [x, y + max(0, h - 1)]],
            dtype=np.float32,
        )
    perimeter = float(cv2.arcLength(contour, True))
    chosen = contour.reshape(-1, 2)
    for ratio in (0.005, 0.008, 0.012, 0.018, 0.026, 0.038, 0.055, 0.08, 0.12):
        candidate = cv2.approxPolyDP(contour, ratio * perimeter, True).reshape(-1, 2)
        chosen = candidate
        if len(candidate) <= budget:
            break
    return chosen.astype(np.float32)


def _fill_polygons(shape: tuple[int, int], polygons: list[np.ndarray]) -> np.ndarray:
    canvas = np.zeros(shape, dtype=np.uint8)
    for points in polygons:
        rounded = np.rint(points).astype(np.int32).reshape(-1, 1, 2)
        if len(rounded) >= 3:
            cv2.fillPoly(canvas, [rounded], 255, lineType=cv2.LINE_8)
        elif len(rounded) == 2:
            cv2.line(canvas, tuple(rounded[0, 0]), tuple(rounded[1, 0]), 255, 1, cv2.LINE_8)
        elif len(rounded) == 1:
            x, y = rounded[0, 0]
            if 0 <= y < shape[0] and 0 <= x < shape[1]:
                canvas[y, x] = 255
    return canvas > 0


def _principal_axes(mask: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    ys, xs = np.where(mask)
    points = np.column_stack((xs, ys)).astype(np.float64)
    center = points.mean(axis=0)
    if len(points) == 1:
        major = np.asarray((0.0, 1.0))
    else:
        covariance = np.cov(points - center, rowvar=False, bias=True)
        values, vectors = np.linalg.eigh(covariance)
        major = vectors[:, int(np.argmax(values))]
        if major[1] < 0 or (abs(major[1]) < 1e-12 and major[0] < 0):
            major = -major
    minor = np.asarray((-major[1], major[0]))
    relative = points - center
    return center, major, minor, np.column_stack((relative @ major, relative @ minor))


def _mass_elongation(mask: np.ndarray) -> float:
    _, _, _, projections = _principal_axes(mask)
    if len(projections) <= 1:
        return 1.0
    major_span = float(np.ptp(projections[:, 0])) + 1.0
    minor_span = float(np.ptp(projections[:, 1])) + 1.0
    return max(major_span, minor_span) / max(1.0, min(major_span, minor_span))


def _polygon_candidate(mask: np.ndarray, budget: int, *, rounded: bool) -> tuple[np.ndarray, dict[str, Any], int]:
    contours = _contours(mask)
    component_budget = max(3, budget // max(1, len(contours)))
    polygons = [_approx_contour(contour, component_budget) for contour in contours]
    candidate = _fill_polygons(mask.shape, polygons)
    radius = 0
    if rounded:
        ys, xs = np.where(mask)
        radius = max(1, int(round(min(xs.max() - xs.min() + 1, ys.max() - ys.min() + 1) * 0.04)))
        kernel_size = radius * 2 + 1
        blurred = cv2.GaussianBlur(candidate.astype(np.uint8) * 255, (kernel_size, kernel_size), 0)
        rounded_candidate = blurred >= 128
        if np.any(rounded_candidate):
            candidate = rounded_candidate
    parameters = {
        "components": [_points_payload(points) for points in polygons],
        "corner_radius_px": radius,
    }
    return candidate, parameters, sum(len(points) for points in polygons)


def _ellipse_candidate(mask: np.ndarray) -> tuple[np.ndarray, dict[str, Any], int]:
    contours = _contours(mask)
    points = np.concatenate([contour.reshape(-1, 2) for contour in contours]).astype(np.float32)
    if len(points) >= 5:
        (cx, cy), (diameter_x, diameter_y), angle = cv2.fitEllipse(points.reshape(-1, 1, 2))
    else:
        x, y, w, h = cv2.boundingRect(points.reshape(-1, 1, 2).astype(np.int32))
        cx, cy = x + (w - 1) / 2.0, y + (h - 1) / 2.0
        diameter_x, diameter_y, angle = max(1, w), max(1, h), 0.0
    canvas = np.zeros(mask.shape, dtype=np.uint8)
    axes = (max(1, int(round(diameter_x / 2.0))), max(1, int(round(diameter_y / 2.0))))
    cv2.ellipse(canvas, (int(round(cx)), int(round(cy))), axes, float(angle), 0, 360, 255, -1, cv2.LINE_8)
    parameters = {
        "center_xy": [_rounded(cx), _rounded(cy)],
        "radii_xy": [_rounded(diameter_x / 2.0), _rounded(diameter_y / 2.0)],
        "angle_degrees": _rounded(angle),
    }
    return canvas > 0, parameters, 4


def _oriented_box_candidate(mask: np.ndarray) -> tuple[np.ndarray, dict[str, Any], int]:
    ys, xs = np.where(mask)
    points = np.column_stack((xs, ys)).astype(np.float32)
    rect = cv2.minAreaRect(points.reshape(-1, 1, 2))
    box = cv2.boxPoints(rect)
    candidate = _fill_polygons(mask.shape, [box])
    parameters = {
        "center_xy": [_rounded(rect[0][0]), _rounded(rect[0][1])],
        "size_wh": [_rounded(rect[1][0]), _rounded(rect[1][1])],
        "angle_degrees": _rounded(rect[2]),
        "points": _points_payload(box),
    }
    return candidate, parameters, 4


def _capsule_candidate(mask: np.ndarray) -> tuple[np.ndarray, dict[str, Any], int]:
    center, major, _, projections = _principal_axes(mask)
    along = projections[:, 0]
    span = float(along.max() - along.min()) if len(along) else 0.0
    radius = max(0.5, min(sqrt(float(np.count_nonzero(mask)) / np.pi), max(0.5, span / 2.0)))
    start = center + major * (float(along.min()) + radius)
    end = center + major * (float(along.max()) - radius)
    if float(along.max()) - float(along.min()) < 2.0 * radius:
        start = end = center
    canvas = np.zeros(mask.shape, dtype=np.uint8)
    cv2.line(
        canvas,
        tuple(np.rint(start).astype(int)),
        tuple(np.rint(end).astype(int)),
        255,
        max(1, int(round(radius * 2.0))),
        cv2.LINE_8,
    )
    cv2.circle(canvas, tuple(np.rint(start).astype(int)), max(1, int(round(radius))), 255, -1, cv2.LINE_8)
    cv2.circle(canvas, tuple(np.rint(end).astype(int)), max(1, int(round(radius))), 255, -1, cv2.LINE_8)
    parameters = {
        "start_xy": [_rounded(value) for value in start],
        "end_xy": [_rounded(value) for value in end],
        "radius_px": _rounded(radius),
    }
    return canvas > 0, parameters, 4


def _strip_profile(mask: np.ndarray, samples: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    center, major, minor, projections = _principal_axes(mask)
    along = projections[:, 0]
    across = projections[:, 1]
    edges = np.linspace(float(along.min()), float(along.max()) + 1e-9, samples + 1)
    centers: list[np.ndarray] = []
    widths: list[float] = []
    for index in range(samples):
        selected = (along >= edges[index]) & (along <= edges[index + 1] if index == samples - 1 else along < edges[index + 1])
        if not np.any(selected):
            axis_value = (edges[index] + edges[index + 1]) / 2.0
            across_value = 0.0
            width = 1.0
        else:
            axis_value = float(np.mean(along[selected]))
            across_value = float(np.mean(across[selected]))
            width = max(1.0, float(np.max(across[selected]) - np.min(across[selected]) + 1.0))
        centers.append(center + major * axis_value + minor * across_value)
        widths.append(width)
    return np.asarray(centers), np.asarray(widths), major, minor


def _tapered_strip_candidate(mask: np.ndarray) -> tuple[np.ndarray, dict[str, Any], int]:
    centers, widths, _, minor = _strip_profile(mask, 3)
    first_width = max(1.0, float((widths[0] + widths[1]) / 2.0))
    last_width = max(1.0, float((widths[1] + widths[2]) / 2.0))
    points = np.asarray(
        [
            centers[0] - minor * first_width / 2.0,
            centers[0] + minor * first_width / 2.0,
            centers[-1] + minor * last_width / 2.0,
            centers[-1] - minor * last_width / 2.0,
        ]
    )
    candidate = _fill_polygons(mask.shape, [points])
    parameters = {
        "points": _points_payload(points),
        "endpoint_widths_px": [_rounded(first_width), _rounded(last_width)],
    }
    return candidate, parameters, 4


def _polyline_ribbon_candidate(mask: np.ndarray) -> tuple[np.ndarray, dict[str, Any], int]:
    centers, widths, _, minor = _strip_profile(mask, 5)
    left = centers - minor[None, :] * widths[:, None] / 2.0
    right = centers + minor[None, :] * widths[:, None] / 2.0
    polygon = np.concatenate((left, right[::-1]), axis=0)
    candidate = _fill_polygons(mask.shape, [polygon])
    parameters = {
        "centerline": _points_payload(centers),
        "widths_px": [_rounded(value) for value in widths],
        "outline": _points_payload(polygon),
    }
    return candidate, parameters, len(polygon)


def _make_geometry(mask: np.ndarray, family: str, budget: int) -> tuple[np.ndarray, dict[str, Any], int]:
    if family == "polygon":
        return _polygon_candidate(mask, budget, rounded=False)
    if family == "rounded_polygon":
        return _polygon_candidate(mask, budget, rounded=True)
    if family == "ellipse":
        return _ellipse_candidate(mask)
    if family == "capsule":
        return _capsule_candidate(mask)
    if family == "oriented_rectangle":
        return _oriented_box_candidate(mask)
    if family == "tapered_strip":
        return _tapered_strip_candidate(mask)
    if family == "polyline_ribbon":
        return _polyline_ribbon_candidate(mask)
    raise ValueError(f"unsupported Phase 10 primitive family: {family}")


def _candidate_cost(
    source_mask: np.ndarray,
    candidate_mask: np.ndarray,
    *,
    complexity_units: int,
    complexity_budget: int,
    family_prior: float,
    policy: PartAwareGeometrizationPolicy,
) -> tuple[dict[str, float], float]:
    source_pixels = int(np.count_nonzero(source_mask))
    candidate_pixels = int(np.count_nonzero(candidate_mask))
    intersection = int(np.count_nonzero(source_mask & candidate_mask))
    union = int(np.count_nonzero(source_mask | candidate_mask))
    coverage_loss = 1.0 - intersection / float(source_pixels)
    spill_loss = max(0, candidate_pixels - intersection) / float(source_pixels)
    silhouette_loss = 1.0 - intersection / float(union) if union else 1.0
    complexity = min(2.0, complexity_units / float(max(1, complexity_budget)))
    total = (
        policy.coverage_weight * coverage_loss
        + policy.spill_weight * spill_loss
        + policy.silhouette_weight * silhouette_loss
        + policy.complexity_weight * complexity
        + family_prior
    )
    breakdown = {
        "coverage_loss": _rounded(coverage_loss),
        "spill_loss": _rounded(spill_loss),
        "silhouette_loss": _rounded(silhouette_loss),
        "complexity": _rounded(complexity),
        "family_prior": _rounded(family_prior),
    }
    return breakdown, _rounded(total)


def geometrize_parts(
    phase7_payload: Mapping[str, Any],
    phase8_payload: Mapping[str, Any],
    phase9_payload: Mapping[str, Any],
    mass_labels: np.ndarray,
    *,
    policy: PartAwareGeometrizationPolicy | None = None,
) -> PartAwareGeometrizationResult:
    policy = policy or PartAwareGeometrizationPolicy()
    coordinate = phase7_payload.get("coordinate_space")
    if not isinstance(coordinate, Mapping):
        raise ValueError("Phase 10 requires Phase 7 coordinate_space")
    width = int(coordinate.get("pixel_width", 0))
    height = int(coordinate.get("pixel_height", 0))
    if width <= 0 or height <= 0:
        raise ValueError("Phase 10 coordinate space must be positive")
    for phase, payload in ((7, phase7_payload), (8, phase8_payload), (9, phase9_payload)):
        if payload.get("validation", {}).get("pass") is not True:
            raise ValueError(f"Phase 10 requires a passing Phase {phase} result")
        other = payload.get("coordinate_space")
        if not isinstance(other, Mapping) or int(other.get("pixel_width", 0)) != width or int(other.get("pixel_height", 0)) != height:
            raise ValueError(f"Phase {phase} coordinate space drift")

    labels = np.asarray(mass_labels).astype(np.int64, copy=True)
    if labels.shape != (height, width):
        raise ValueError("Phase 7 mass labels do not match coordinate space")
    labels[labels == 65535] = -1
    raw_masses = phase7_payload.get("masses")
    raw_decisions = phase8_payload.get("decisions")
    raw_assignments = phase9_payload.get("assignments")
    raw_palette = phase9_payload.get("palette")
    if not isinstance(raw_masses, list) or not raw_masses:
        raise ValueError("Phase 10 requires non-empty Phase 7 masses")
    if not isinstance(raw_decisions, list) or not isinstance(raw_assignments, list):
        raise ValueError("Phase 10 requires Phase 8 decisions and Phase 9 assignments")
    if not isinstance(raw_palette, list):
        raise ValueError("Phase 10 requires a Phase 9 palette")
    if np.any(labels >= len(raw_masses)):
        raise ValueError("Phase 7 labels reference a missing mass")

    decisions = {str(item.get("mass_id", "")): item for item in raw_decisions if isinstance(item, Mapping)}
    assignments = {str(item.get("mass_id", "")): item for item in raw_assignments if isinstance(item, Mapping)}
    palette = {str(item.get("palette_id", "")): item for item in raw_palette if isinstance(item, Mapping)}
    if len(decisions) != len(raw_decisions) or len(assignments) != len(raw_assignments) or len(palette) != len(raw_palette):
        raise ValueError("Phase 10 upstream IDs must be present and unique")

    candidates: list[PrimitiveCandidate] = []
    selected: list[SelectedPrimitive] = []
    omitted: list[str] = []
    candidate_masks: dict[str, np.ndarray] = {}
    seen_mass_ids: set[str] = set()
    active_source_pixels = 0
    selected_pixels = 0
    subject_pixels = int(
        phase7_payload.get("validation", {}).get(
            "subject_pixel_count", int(np.count_nonzero(labels >= 0))
        )
    )

    for index, raw in enumerate(raw_masses):
        if not isinstance(raw, Mapping):
            raise ValueError("Phase 7 masses must be objects")
        mass_id = str(raw.get("mass_id", ""))
        if not mass_id or mass_id in seen_mass_ids:
            raise ValueError("Phase 7 mass_id must be present and unique")
        seen_mass_ids.add(mass_id)
        decision = decisions.get(mass_id)
        assignment = assignments.get(mass_id)
        if decision is None or assignment is None:
            raise ValueError(f"Phase 10 upstream record missing for {mass_id}")
        part_id = raw.get("semantic_part_id")
        status = str(raw.get("binding_status", ""))
        action = str(decision.get("action", ""))
        if status not in {"bound", "unbound"}:
            raise ValueError("unsupported Phase 7 binding_status")
        if status == "bound" and not isinstance(part_id, str):
            raise ValueError("bound Phase 7 mass requires semantic_part_id")
        if status == "unbound" and part_id is not None:
            raise ValueError("unbound Phase 7 mass must not claim semantic_part_id")
        if action not in {"protect", "keep", "prune"}:
            raise ValueError("unsupported Phase 8 action")
        for label, upstream in (("Phase 8", decision), ("Phase 9", assignment)):
            if upstream.get("semantic_part_id") != part_id:
                raise ValueError(f"{label} semantic owner drift for {mass_id}")
            if upstream.get("binding_status") != status:
                raise ValueError(f"{label} binding status drift for {mass_id}")
            if int(upstream.get("pixel_count", -1)) != int(raw.get("pixel_count", -2)):
                raise ValueError(f"{label} pixel_count drift for {mass_id}")
        if assignment.get("action") != action:
            raise ValueError(f"Phase 9 action drift for {mass_id}")

        mask = labels == index
        pixel_count = int(np.count_nonzero(mask))
        if pixel_count <= 0 or pixel_count != int(raw.get("pixel_count", -1)):
            raise ValueError(f"Phase 7 pixel_count mismatch for {mass_id}")
        if not np.array_equal(_decode_runs(raw.get("pixel_runs"), width=width, height=height), mask):
            raise ValueError(f"Phase 7 labels and pixel_runs disagree for {mass_id}")

        palette_id_raw = assignment.get("palette_id")
        if action == "prune":
            if palette_id_raw is not None:
                raise ValueError(f"Phase 10 refuses Phase 9 prune resurrection for {mass_id}")
            omitted.append(mass_id)
            continue
        if not isinstance(palette_id_raw, str) or palette_id_raw not in palette:
            raise ValueError(f"Phase 10 requires an active Phase 9 palette assignment for {mass_id}")
        palette_entry = palette[palette_id_raw]
        assigned_ids = palette_entry.get("assigned_mass_ids")
        if not isinstance(assigned_ids, list) or mass_id not in assigned_ids:
            raise ValueError(f"Phase 9 palette membership drift for {mass_id}")
        color_raw = palette_entry.get("color_rgb")
        if not isinstance(color_raw, list) or len(color_raw) != 3:
            raise ValueError("Phase 9 palette color must be RGB")
        color = tuple(int(value) for value in color_raw)
        if any(value < 0 or value > 255 for value in color):
            raise ValueError("Phase 9 palette color is outside RGB range")

        normalized_part_id = part_id if isinstance(part_id, str) else None
        elongation = _mass_elongation(mask)
        mass_subject_ratio = pixel_count / float(max(1, subject_pixels))
        families = policy.families_for_mass(
            normalized_part_id,
            elongation=elongation,
        )
        if len(families) < policy.minimum_candidates_per_active_mass:
            raise ValueError(f"Phase 10 requires multiple candidates for {mass_id}")
        budget = policy.vertex_budget_for(part_id if isinstance(part_id, str) else None)
        mass_candidates: list[PrimitiveCandidate] = []
        for family in families:
            candidate_mask, parameters, complexity_units = _make_geometry(mask, family, budget)
            if not np.any(candidate_mask):
                raise ValueError(f"Phase 10 generated an empty candidate for {mass_id}")
            candidate_id = f"{mass_id}:{family}"
            prior = FAMILY_PRIORS.get(str(part_id), {}).get(family, 0.0)
            breakdown, total = _candidate_cost(
                mask,
                candidate_mask,
                complexity_units=complexity_units,
                complexity_budget=budget,
                family_prior=prior,
                policy=policy,
            )
            item = PrimitiveCandidate(
                candidate_id=candidate_id,
                mass_id=mass_id,
                semantic_part_id=part_id if isinstance(part_id, str) else None,
                binding_status=status,
                action=action,
                primitive_type=family,
                parameters={
                    **parameters,
                    "source_mass_shape": {
                        "elongation": _rounded(elongation),
                        "subject_area_ratio": _rounded(mass_subject_ratio),
                    },
                },
                source_pixel_count=pixel_count,
                candidate_pixel_count=int(np.count_nonzero(candidate_mask)),
                complexity_units=complexity_units,
                complexity_budget=budget,
                cost_breakdown=breakdown,
                total_cost=total,
                palette_id=palette_id_raw,
                evidence_refs=(
                    f"phase07:{mass_id}",
                    f"phase08:{mass_id}:{action}",
                    f"phase09:{palette_id_raw}",
                ),
            )
            mass_candidates.append(item)
            candidates.append(item)
            candidate_masks[candidate_id] = candidate_mask

        non_giant_candidates = [
            item
            for item in mass_candidates
            if item.primitive_type not in {"oriented_rectangle", "capsule"}
            or item.candidate_pixel_count <= 0.18 * max(1, subject_pixels)
        ]
        if (
            normalized_part_id in ARM_PARTS
            and elongation <= ARM_LOW_ELONGATION_MAX
            and mass_subject_ratio >= ARM_LARGE_MASS_MIN_SUBJECT_RATIO
        ):
            non_giant_candidates = [
                item
                for item in non_giant_candidates
                if item.primitive_type not in {"capsule", "oriented_rectangle"}
            ]
        winner = min(
            non_giant_candidates or mass_candidates,
            key=lambda item: (
                item.total_cost,
                FAMILY_ORDER.index(item.primitive_type),
                item.candidate_id,
            ),
        )
        selected.append(
            SelectedPrimitive(
                primitive_id=f"primitive-{mass_id.removeprefix('mass-')}",
                candidate_id=winner.candidate_id,
                mass_id=mass_id,
                semantic_part_id=winner.semantic_part_id,
                binding_status=status,
                primitive_type=winner.primitive_type,
                palette_id=palette_id_raw,
                palette_color_rgb=color,
                total_cost=winner.total_cost,
                selection_rationale=(
                    "minimum-aspect-aware-arm-cost-with-broad-mass-guard"
                    if normalized_part_id in ARM_PARTS
                    and elongation <= ARM_LOW_ELONGATION_MAX
                    and mass_subject_ratio >= ARM_LARGE_MASS_MIN_SUBJECT_RATIO
                    else "minimum-part-aware-cost-with-stable-family-tie-break"
                ),
            )
        )
        active_source_pixels += pixel_count
        selected_pixels += int(np.count_nonzero(candidate_masks[winner.candidate_id]))

    if set(decisions) != seen_mass_ids or set(assignments) != seen_mass_ids:
        raise ValueError("Phase 8/9 records contain unknown masses")

    by_mass: dict[str, list[PrimitiveCandidate]] = {}
    for candidate in candidates:
        by_mass.setdefault(candidate.mass_id, []).append(candidate)
    multiple_candidate_violations = sorted(
        mass_id
        for mass_id, items in by_mass.items()
        if len(items) < policy.minimum_candidates_per_active_mass
    )
    family_violations = sorted(
        candidate.candidate_id
        for candidate in candidates
        if candidate.primitive_type not in PART_FAMILIES.get(
            candidate.semantic_part_id,
            policy.unbound_families,
        )
    )
    complexity_violations = sorted(
        candidate.candidate_id
        for candidate in candidates
        if candidate.complexity_units > candidate.complexity_budget
        and candidate.primitive_type in {"polygon", "rounded_polygon", "polyline_ribbon"}
    )
    selected_ids = {item.candidate_id for item in selected}
    orphan_selections = sorted(selected_ids - set(candidate_masks))
    selected_by_mass = {item.mass_id for item in selected}
    missing_selections = sorted(set(by_mass) - selected_by_mass)
    prune_resurrections = sorted(set(omitted) & selected_by_mass)
    giant_box_or_capsule = sorted(
        item.candidate_id
        for item in selected
        if item.primitive_type in {"oriented_rectangle", "capsule"}
        and int(np.count_nonzero(candidate_masks[item.candidate_id])) > 0.18 * max(1, subject_pixels)
    )
    selected_family_counts = {
        family: sum(item.primitive_type == family for item in selected)
        for family in FAMILY_ORDER
        if any(item.primitive_type == family for item in selected)
    }
    mean_selected_iou = (
        sum(
            1.0 - next(candidate for candidate in candidates if candidate.candidate_id == item.candidate_id).cost_breakdown["silhouette_loss"]
            for item in selected
        )
        / len(selected)
        if selected
        else 0.0
    )
    validation = {
        "mass_count": len(raw_masses),
        "active_mass_count": len(selected),
        "pruned_mass_count": len(omitted),
        "candidate_count": len(candidates),
        "selected_primitive_count": len(selected),
        "candidate_family_count": len({item.primitive_type for item in candidates}),
        "part_family_policy_count": len(set(PART_FAMILIES.values())),
        "selected_family_counts": selected_family_counts,
        "mean_candidates_per_active_mass": _rounded(len(candidates) / float(len(selected)) if selected else 0.0),
        "mean_selected_iou": _rounded(mean_selected_iou),
        "selected_to_source_pixel_ratio": _rounded(selected_pixels / float(active_source_pixels) if active_source_pixels else 0.0),
        "multiple_candidate_violations": multiple_candidate_violations,
        "part_family_violations": family_violations,
        "complexity_budget_violations": complexity_violations,
        "missing_selections": missing_selections,
        "orphan_selections": orphan_selections,
        "prune_resurrections": prune_resurrections,
        "giant_box_or_capsule_chain_candidates": giant_box_or_capsule,
        "cross_mass_candidate_count": 0,
        "semantic_owner_change_count": 0,
        "phase8_action_change_count": 0,
        "phase9_palette_change_count": 0,
        "axis_aligned_rectangle_candidate_count": 0,
        "observed_geometry_only": True,
        "generated_or_inpainted_pixel_count": 0,
        "pass": not any(
            (
                multiple_candidate_violations,
                family_violations,
                complexity_violations,
                missing_selections,
                orphan_selections,
                prune_resurrections,
                giant_box_or_capsule,
            )
        )
        and len(selected) + len(omitted) == len(raw_masses),
    }
    return PartAwareGeometrizationResult(
        width=width,
        height=height,
        candidates=tuple(candidates),
        selected=tuple(selected),
        omitted_mass_ids=tuple(omitted),
        validation=validation,
        policy=policy,
        candidate_masks=candidate_masks,
    )
