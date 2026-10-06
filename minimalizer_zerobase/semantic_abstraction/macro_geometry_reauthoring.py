from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .adaptive_primitive_budget import (
    AdaptivePrimitiveBudget,
    allocate_adaptive_primitive_budget,
)


MACRO_GEOMETRY_VERSION = "sa7.43-v1"
MAX_EXPANSION_RATIO = 1.12
MIN_SOURCE_COVERAGE = 0.65
DEFAULT_MACRO_GLOBAL_CAP = 5

_MACRO_MINIMUMS = {
    "hair": 1,
    "major_clothing": 1,
}
_MACRO_MAXIMUMS = {
    "hair": 3,
    "major_clothing": 3,
}
_MACRO_IMPORTANCE = {
    "hair": 1.0,
    "major_clothing": 1.0,
}


@dataclass(frozen=True)
class MacroGeometryPrimitive:
    semantic_part: str
    polygon: np.ndarray
    source_area: int
    retained_area: int


def _masses(mask: np.ndarray, limit: int) -> tuple[np.ndarray, ...]:
    if limit <= 0:
        return ()
    m = np.asarray(mask).astype(np.uint8)
    k = max(3, int(round(min(m.shape) * 0.008)) | 1)
    clean = cv2.morphologyEx(
        m,
        cv2.MORPH_CLOSE,
        np.ones((k, k), np.uint8),
    )
    n, lab, stats, _ = cv2.connectedComponentsWithStats(clean, 8)
    minimum = max(12, int(m.sum() * 0.02))
    rows = [
        (int(stats[i, cv2.CC_STAT_AREA]), i)
        for i in range(1, n)
        if int(stats[i, cv2.CC_STAT_AREA]) >= minimum
    ]
    rows.sort(key=lambda x: (-x[0], x[1]))
    return tuple(lab == i for _, i in rows[:limit])


def _coarse_polygon(mask: np.ndarray) -> np.ndarray | None:
    ys, xs = np.where(mask)
    if not xs.size:
        return None
    contours, _ = cv2.findContours(
        np.asarray(mask).astype(np.uint8),
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    perimeter = cv2.arcLength(contour, True)
    polygon = cv2.approxPolyDP(
        contour,
        max(1.5, 0.01 * perimeter),
        True,
    ).reshape(-1, 2)
    return polygon if len(polygon) >= 3 else contour.reshape(-1, 2)


def _primitive_for_mass(
    name: str,
    source_mask: np.ndarray,
    mass: np.ndarray,
) -> MacroGeometryPrimitive | None:
    polygon = _coarse_polygon(mass)
    if polygon is None:
        return None

    canvas = np.zeros(source_mask.shape, np.uint8)
    cv2.fillPoly(canvas, [polygon.astype(np.int32)], 1)

    # Geometry may bridge tiny source gaps but must remain near source support.
    dilated = (
        cv2.dilate(
            source_mask.astype(np.uint8),
            np.ones((5, 5), np.uint8),
        )
        > 0
    )
    clipped = (canvas > 0) & dilated
    polygon2 = _coarse_polygon(clipped)
    if polygon2 is None:
        return None

    final = np.zeros(source_mask.shape, np.uint8)
    cv2.fillPoly(final, [polygon2.astype(np.int32)], 1)
    source_n = max(1, int(mass.sum()))
    final_n = int(final.sum())
    covered = int(((final > 0) & mass).sum())
    expansion = final_n / source_n
    coverage = covered / source_n

    if expansion > MAX_EXPANSION_RATIO or coverage < MIN_SOURCE_COVERAGE:
        contours, _ = cv2.findContours(
            mass.astype(np.uint8),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        if not contours:
            return None
        contour = max(contours, key=cv2.contourArea)
        perimeter = cv2.arcLength(contour, True)
        polygon2 = cv2.approxPolyDP(
            contour,
            max(1.5, 0.01 * perimeter),
            True,
        ).reshape(-1, 2)
        if len(polygon2) < 3:
            return None
        final = np.zeros(source_mask.shape, np.uint8)
        cv2.fillPoly(final, [polygon2.astype(np.int32)], 1)
        final_n = int(final.sum())
        covered = int(((final > 0) & mass).sum())
        if (
            final_n / source_n > MAX_EXPANSION_RATIO
            or covered / source_n < MIN_SOURCE_COVERAGE
        ):
            return None

    return MacroGeometryPrimitive(
        semantic_part=name,
        polygon=polygon2,
        source_area=source_n,
        retained_area=final_n,
    )


def reauthor_macro_geometry_with_budget(
    *,
    hair_mask: np.ndarray,
    clothing_mask: np.ndarray,
    global_primitive_budget: int = DEFAULT_MACRO_GLOBAL_CAP,
) -> tuple[tuple[MacroGeometryPrimitive, ...], AdaptivePrimitiveBudget]:
    role_masks = {
        "hair": np.asarray(hair_mask).astype(bool),
        "major_clothing": np.asarray(clothing_mask).astype(bool),
    }
    budget = allocate_adaptive_primitive_budget(
        role_masks,
        global_cap=global_primitive_budget,
        minimums=_MACRO_MINIMUMS,
        maximums=_MACRO_MAXIMUMS,
        importance=_MACRO_IMPORTANCE,
    )

    output: list[MacroGeometryPrimitive] = []
    for name in ("hair", "major_clothing"):
        source = role_masks[name]
        for mass in _masses(source, budget.for_role(name)):
            primitive = _primitive_for_mass(name, source, mass)
            if primitive is not None:
                output.append(primitive)

    return tuple(output), budget


def reauthor_macro_geometry(
    *,
    hair_mask: np.ndarray,
    clothing_mask: np.ndarray,
    global_primitive_budget: int = DEFAULT_MACRO_GLOBAL_CAP,
) -> tuple[MacroGeometryPrimitive, ...]:
    primitives, _ = reauthor_macro_geometry_with_budget(
        hair_mask=hair_mask,
        clothing_mask=clothing_mask,
        global_primitive_budget=global_primitive_budget,
    )
    return primitives
