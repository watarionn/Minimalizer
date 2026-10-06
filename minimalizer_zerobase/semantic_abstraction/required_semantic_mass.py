from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping

import cv2
import numpy as np

REQUIRED_SEMANTIC_MASS_VERSION = "sa7.37-v1"
ROLE_CLUSTER_COUNTS = {
    "torso": 4,
    "left_arm": 2,
    "right_arm": 2,
}
MIN_ROLE_COMPONENT_RATIO = .005
MIN_CONTRAST = 38.0
MIN_SOURCE_COVERAGE = .65
MAX_EXPANSION_RATIO = 1.12
_EPSILON_SCHEDULE = (.01, .0075, .005, .003, .002, .001, 0.0)


@dataclass(frozen=True)
class RequiredSemanticMass:
    version: str
    role: str
    cluster_index: int
    polygon: tuple[tuple[float, float], ...]
    rgb: tuple[int, int, int]
    source_area: int
    role_area_ratio: float
    contrast_from_role_median: float
    source_coverage: float
    expansion_ratio: float
    outside_role_pixels: int

    def to_dict(self) -> dict:
        return asdict(self)


def _coarsest_safe_polygon(
    component: np.ndarray,
    role_mask: np.ndarray,
) -> tuple[np.ndarray, float, float, int] | None:
    cs, _ = cv2.findContours(
        component.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    if not cs:
        return None
    contour = max(cs, key=cv2.contourArea)
    source_area = max(1, int(component.sum()))
    perimeter = cv2.arcLength(contour, True)

    for frac in _EPSILON_SCHEDULE:
        poly = (
            contour.reshape(-1, 2)
            if frac == 0.0
            else cv2.approxPolyDP(
                contour, max(.25, frac * perimeter), True
            ).reshape(-1, 2)
        )
        if len(poly) < 3:
            continue
        raster = np.zeros_like(role_mask, dtype=np.uint8)
        cv2.fillPoly(raster, [poly.astype(np.int32)], 1)
        raster = raster.astype(bool)
        retained = int((raster & component).sum())
        render_area = int(raster.sum())
        coverage = retained / source_area
        expansion = render_area / source_area
        outside = int((raster & ~role_mask).sum())
        if (
            coverage >= MIN_SOURCE_COVERAGE
            and expansion <= MAX_EXPANSION_RATIO
            and outside == 0
        ):
            return poly.astype(np.float32), float(coverage), float(expansion), outside
    return None


def reserve_required_semantic_masses(
    source_rgb: np.ndarray,
    semantic_masks: Mapping[str, np.ndarray],
    *,
    role_cluster_counts: Mapping[str, int] | None = None,
) -> tuple[RequiredSemanticMass, ...]:
    """Reserve a bounded set of source-supported internal masses for critical roles.

    Production inputs are source RGB and semantic masks only. No Golden, adopted
    baseline, missing-signature RGB, or case-specific coordinates are accepted.
    Face/head are intentionally absent from the default role policy.
    """
    image = np.asarray(source_rgb, dtype=np.uint8)
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("source_rgb must be HxWx3")

    h, w = image.shape[:2]
    masks = {
        role: np.asarray(mask, dtype=bool)
        for role, mask in semantic_masks.items()
    }
    if any(mask.shape != (h, w) for mask in masks.values()):
        raise ValueError("semantic mask shape mismatch")

    policy = dict(ROLE_CLUSTER_COUNTS if role_cluster_counts is None else role_cluster_counts)
    if any(role in {"face", "head"} for role in policy):
        raise ValueError("face/head semantic mass reservation is forbidden")
    if any(int(count) <= 0 for count in policy.values()):
        raise ValueError("role cluster counts must be positive")

    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
    rows: list[RequiredSemanticMass] = []

    for role in sorted(policy):
        role_mask = masks.get(role)
        if role_mask is None or not np.any(role_mask):
            continue
        role_area = int(role_mask.sum())
        if role_area < 16:
            continue

        role_rgb = image[role_mask]
        role_median = np.median(role_rgb, axis=0).astype(float)
        values = lab[role_mask].astype(np.float32)
        k = min(int(policy[role]), max(1, role_area // 64))

        cv2.setRNGSeed(737)
        _, labels, centers = cv2.kmeans(
            values,
            k,
            None,
            (
                cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
                40,
                .5,
            ),
            1,
            cv2.KMEANS_PP_CENTERS,
        )
        labels = labels.reshape(-1)
        yy, xx = np.where(role_mask)

        for cluster in range(k):
            raw = np.zeros((h, w), dtype=bool)
            selected = labels == cluster
            raw[yy[selected], xx[selected]] = True
            count, comp_labels, stats, _ = cv2.connectedComponentsWithStats(
                raw.astype(np.uint8), 8
            )
            if count <= 1:
                continue
            largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
            component = comp_labels == largest
            source_area = int(component.sum())
            ratio = source_area / role_area
            if ratio < MIN_ROLE_COMPONENT_RATIO:
                continue

            color = np.median(image[component], axis=0).astype(int)
            contrast = float(
                np.linalg.norm(color.astype(float) - role_median)
            )
            if contrast < MIN_CONTRAST:
                continue

            fitted = _coarsest_safe_polygon(component, role_mask)
            if fitted is None:
                continue
            polygon, coverage, expansion, outside = fitted
            rows.append(
                RequiredSemanticMass(
                    version=REQUIRED_SEMANTIC_MASS_VERSION,
                    role=role,
                    cluster_index=int(cluster),
                    polygon=tuple(
                        (float(x), float(y)) for x, y in polygon
                    ),
                    rgb=tuple(int(v) for v in color),
                    source_area=source_area,
                    role_area_ratio=float(ratio),
                    contrast_from_role_median=contrast,
                    source_coverage=coverage,
                    expansion_ratio=expansion,
                    outside_role_pixels=outside,
                )
            )

    rows.sort(
        key=lambda row: (
            row.role,
            -row.source_area,
            row.rgb,
            row.cluster_index,
        )
    )
    return tuple(rows)
