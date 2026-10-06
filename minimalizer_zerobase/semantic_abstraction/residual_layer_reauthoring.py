from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import cv2
import numpy as np

from .macro_geometry_reauthoring import MacroGeometryPrimitive


RESIDUAL_LAYER_VERSION = "sa7.44-v1"
DEFAULT_RESIDUAL_GLOBAL_CAP = 3
DEFAULT_MIN_RESIDUAL_RATIO = 0.015
DEFAULT_MIN_RESIDUAL_PIXELS = 24
DEFAULT_MAX_RESIDUAL_VERTICES = 32
_EPSILON_SCHEDULE = (0.02, 0.015, 0.01, 0.0075, 0.005, 0.003, 0.001, 0.0)


@dataclass(frozen=True)
class ResidualLayerCandidate:
    role: str
    component_index: int
    polygon: np.ndarray
    role_source_area: int
    residual_area: int
    retained_area: int
    render_area: int
    residual_coverage: float
    role_coverage_gain: float
    expansion_ratio: float
    authority_spill: int
    vertex_count: int
    marginal_value: float

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "component_index": self.component_index,
            "role_source_area": self.role_source_area,
            "residual_area": self.residual_area,
            "retained_area": self.retained_area,
            "render_area": self.render_area,
            "residual_coverage": round(float(self.residual_coverage), 6),
            "role_coverage_gain": round(float(self.role_coverage_gain), 6),
            "expansion_ratio": round(float(self.expansion_ratio), 6),
            "authority_spill": self.authority_spill,
            "vertex_count": self.vertex_count,
            "marginal_value": round(float(self.marginal_value), 8),
        }


@dataclass(frozen=True)
class ResidualLayerReport:
    global_cap: int
    selected_count: int
    candidate_count: int
    selected: tuple[ResidualLayerCandidate, ...]
    version: str = RESIDUAL_LAYER_VERSION

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "global_cap": self.global_cap,
            "candidate_count": self.candidate_count,
            "selected_count": self.selected_count,
            "selected": [row.to_dict() for row in self.selected],
        }


def _rasterize_role_geometry(
    shape: tuple[int, int],
    primitives: Sequence[MacroGeometryPrimitive],
    role: str,
) -> np.ndarray:
    raster = np.zeros(shape, np.uint8)
    for primitive in primitives:
        if primitive.semantic_part != role:
            continue
        polygon = np.asarray(primitive.polygon)
        if polygon.ndim != 2 or polygon.shape[1] != 2 or len(polygon) < 3:
            continue
        cv2.fillPoly(raster, [polygon.astype(np.int32)], 1)
    return raster.astype(bool)


def _component_rows(mask: np.ndarray) -> tuple[tuple[int, int, int, np.ndarray], ...]:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(
        np.asarray(mask).astype(np.uint8),
        8,
    )
    rows: list[tuple[int, int, int, np.ndarray]] = []
    for label in range(1, count):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area <= 0:
            continue
        x = int(stats[label, cv2.CC_STAT_LEFT])
        y = int(stats[label, cv2.CC_STAT_TOP])
        rows.append((area, y, x, labels == label))
    rows.sort(key=lambda row: (-row[0], row[1], row[2]))
    return tuple(rows)


def _fit_safe_polygon(
    component: np.ndarray,
    authority: np.ndarray,
    *,
    max_vertices: int,
) -> tuple[np.ndarray, int, int, float, float, int] | None:
    contours, _ = cv2.findContours(
        component.astype(np.uint8),
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    if not contours:
        return None

    contour = max(contours, key=cv2.contourArea)
    perimeter = cv2.arcLength(contour, True)
    component_area = int(component.sum())

    for frac in _EPSILON_SCHEDULE:
        polygon = (
            contour.reshape(-1, 2)
            if frac == 0.0
            else cv2.approxPolyDP(
                contour,
                max(0.5, frac * perimeter),
                True,
            ).reshape(-1, 2)
        )
        if len(polygon) < 3 or len(polygon) > max_vertices:
            continue

        rendered = np.zeros(component.shape, np.uint8)
        cv2.fillPoly(rendered, [polygon.astype(np.int32)], 1)
        rendered = rendered.astype(bool)

        spill = int((rendered & ~authority).sum())
        if spill:
            continue

        retained = int((rendered & component).sum())
        render_area = int(rendered.sum())
        residual_coverage = retained / max(1, component_area)
        expansion = render_area / max(1, component_area)

        if residual_coverage < 0.60 or expansion > 1.12:
            continue

        return (
            polygon.astype(np.float32),
            retained,
            render_area,
            residual_coverage,
            expansion,
            spill,
        )

    return None


def _candidate_sort_key(candidate: ResidualLayerCandidate) -> tuple:
    return (
        -candidate.marginal_value,
        -candidate.retained_area,
        candidate.vertex_count,
        candidate.role,
        candidate.component_index,
    )


def reauthor_residual_layers(
    role_masks: Mapping[str, np.ndarray],
    base_primitives: Sequence[MacroGeometryPrimitive],
    *,
    global_cap: int = DEFAULT_RESIDUAL_GLOBAL_CAP,
    min_residual_ratio: float = DEFAULT_MIN_RESIDUAL_RATIO,
    min_residual_pixels: int = DEFAULT_MIN_RESIDUAL_PIXELS,
    max_vertices: int = DEFAULT_MAX_RESIDUAL_VERTICES,
) -> tuple[tuple[MacroGeometryPrimitive, ...], ResidualLayerReport]:
    """Add bounded source-supported residual layers above accepted coarse geometry.

    Residuals are computed only inside each role's semantic authority. The base
    geometry is never removed or re-fit in this stage.
    """
    if global_cap < 0:
        raise ValueError("global_cap must be non-negative")
    if not 0.0 <= min_residual_ratio <= 1.0:
        raise ValueError("min_residual_ratio must be within [0, 1]")
    if min_residual_pixels < 1 or max_vertices < 3:
        raise ValueError("invalid residual thresholds")

    normalized = {
        role: np.asarray(mask).astype(bool)
        for role, mask in sorted(role_masks.items())
    }
    shapes = {mask.shape for mask in normalized.values()}
    if len(shapes) > 1:
        raise ValueError("role mask shape mismatch")

    candidates: list[ResidualLayerCandidate] = []
    for role, source in normalized.items():
        role_source_area = int(source.sum())
        if role_source_area <= 0:
            continue

        others = np.zeros(source.shape, bool)
        for other_role, other_mask in normalized.items():
            if other_role != role:
                others |= other_mask

        authority = source & ~others
        base = _rasterize_role_geometry(
            source.shape,
            base_primitives,
            role,
        )
        residual = authority & ~base

        minimum = max(
            int(min_residual_pixels),
            int(role_source_area * float(min_residual_ratio)),
        )
        component_rows = _component_rows(residual)
        for component_index, (area, _, _, component) in enumerate(component_rows):
            if area < minimum:
                continue

            fit = _fit_safe_polygon(
                component,
                authority,
                max_vertices=max_vertices,
            )
            if fit is None:
                continue

            (
                polygon,
                retained,
                render_area,
                residual_coverage,
                expansion,
                spill,
            ) = fit
            role_gain = retained / max(1, role_source_area)
            vertex_count = int(len(polygon))
            # Primitive / Geometrize-inspired marginal value: source-support
            # gain is rewarded while geometric complexity is explicitly taxed.
            marginal = role_gain / max(1.0, vertex_count ** 0.5)

            candidates.append(
                ResidualLayerCandidate(
                    role=role,
                    component_index=component_index,
                    polygon=polygon,
                    role_source_area=role_source_area,
                    residual_area=area,
                    retained_area=retained,
                    render_area=render_area,
                    residual_coverage=residual_coverage,
                    role_coverage_gain=role_gain,
                    expansion_ratio=expansion,
                    authority_spill=spill,
                    vertex_count=vertex_count,
                    marginal_value=marginal,
                )
            )

    selected = tuple(
        sorted(candidates, key=_candidate_sort_key)[:global_cap]
    )

    layers = tuple(
        MacroGeometryPrimitive(
            semantic_part=row.role,
            polygon=row.polygon,
            source_area=row.residual_area,
            retained_area=row.render_area,
            layer_kind="residual",
            component_index=row.component_index,
        )
        for row in selected
    )

    return layers, ResidualLayerReport(
        global_cap=global_cap,
        selected_count=len(selected),
        candidate_count=len(candidates),
        selected=selected,
    )
