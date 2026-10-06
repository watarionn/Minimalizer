from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


BACKGROUND_FIELD_GEOMETRY_VERSION = "sa7.42-v1"
MAX_PALETTE_CLUSTERS = 3
MAX_FIELDS = 6
MIN_FIELD_RATIO = 0.03
MIN_SOURCE_COVERAGE = 0.60
MAX_EXPANSION_RATIO = 1.12
_EPSILON_SCHEDULE = (0.01, 0.0075, 0.005, 0.003, 0.002, 0.001, 0.0)


@dataclass(frozen=True)
class BackgroundFieldPrimitive:
    role_index: int
    cluster_index: int
    component_index: int
    polygon: np.ndarray
    rgb: tuple[int, int, int]
    source_area: int
    retained_area: int
    render_area: int
    source_coverage: float
    expansion_ratio: float
    subject_overlap: int


@dataclass(frozen=True)
class _BackgroundFieldCandidate:
    cluster_index: int
    component_index: int
    polygon: np.ndarray
    rgb: tuple[int, int, int]
    source_area: int
    retained_area: int
    render_area: int
    source_coverage: float
    expansion_ratio: float
    subject_overlap: int


def _border_connected_background(subject: np.ndarray) -> np.ndarray:
    bg = (~subject).astype(np.uint8)
    _, labels, stats, _ = cv2.connectedComponentsWithStats(bg, 8)
    border_labels = np.unique(
        np.concatenate((labels[0], labels[-1], labels[:, 0], labels[:, -1]))
    )
    valid = [
        int(i)
        for i in border_labels
        if i and stats[int(i), cv2.CC_STAT_AREA] >= 16
    ]
    return np.isin(labels, valid)


def _connected_components(mask: np.ndarray) -> tuple[np.ndarray, ...]:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(
        mask.astype(np.uint8), 8
    )
    rows: list[tuple[int, int, int, int, int, np.ndarray]] = []
    for label in range(1, count):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area <= 0:
            continue
        x = int(stats[label, cv2.CC_STAT_LEFT])
        y = int(stats[label, cv2.CC_STAT_TOP])
        w = int(stats[label, cv2.CC_STAT_WIDTH])
        h = int(stats[label, cv2.CC_STAT_HEIGHT])
        rows.append((area, y, x, h, w, labels == label))
    rows.sort(key=lambda row: (-row[0], row[1], row[2], row[3], row[4]))
    return tuple(row[-1] for row in rows)


def _coarsest_safe_polygon(
    contour: np.ndarray,
    component: np.ndarray,
    subject: np.ndarray,
):
    source_area = int(component.sum())
    perimeter = cv2.arcLength(contour, True)
    for frac in _EPSILON_SCHEDULE:
        poly = (
            contour.reshape(-1, 2)
            if frac == 0
            else cv2.approxPolyDP(
                contour, max(0.25, frac * perimeter), True
            ).reshape(-1, 2)
        )
        if len(poly) < 3:
            continue
        raster = np.zeros_like(subject, dtype=np.uint8)
        cv2.fillPoly(raster, [poly.astype(np.int32)], 1)
        raster = raster.astype(bool)
        retained = int((raster & component).sum())
        render_area = int(raster.sum())
        coverage = retained / max(1, source_area)
        expansion = render_area / max(1, source_area)
        overlap = int((raster & subject).sum())
        if (
            coverage >= MIN_SOURCE_COVERAGE
            and expansion <= MAX_EXPANSION_RATIO
            and overlap == 0
        ):
            return (
                poly.astype(np.float32),
                retained,
                render_area,
                coverage,
                expansion,
                overlap,
            )
    return None


def _candidate_sort_key(candidate: _BackgroundFieldCandidate) -> tuple:
    # Primitive/Geometrize-inspired bounded selection: the strongest
    # source-supported components consume the global field budget first.
    # Cluster/component indices remain deterministic tie-breakers.
    return (
        -candidate.source_area,
        candidate.cluster_index,
        candidate.component_index,
        candidate.rgb,
    )


def reauthor_background_fields(
    rgb: np.ndarray,
    subject_mask: np.ndarray,
    *,
    max_fields: int = MAX_FIELDS,
    max_palette_clusters: int = MAX_PALETTE_CLUSTERS,
) -> tuple[BackgroundFieldPrimitive, ...]:
    im = np.asarray(rgb).astype(np.uint8)
    subject = np.asarray(subject_mask).astype(bool)
    if (
        im.ndim != 3
        or im.shape[2] != 3
        or subject.shape != im.shape[:2]
    ):
        raise ValueError("shape mismatch")
    if max_fields < 1 or max_palette_clusters < 1:
        return ()

    field = _border_connected_background(subject)
    field_area = int(field.sum())
    if field_area < 64:
        return ()

    safe = field & (
        cv2.dilate(
            subject.astype(np.uint8),
            np.ones((7, 7), np.uint8),
        )
        == 0
    )
    yy, xx = np.where(safe)
    data = im[safe].astype(np.float32)
    if len(data) < 64:
        return ()

    # AdaVec-inspired separation: palette complexity and geometry budget
    # are independent. K-means determines palette roles only.
    cluster_count = min(
        max_palette_clusters,
        max(1, len(data) // 64),
    )
    cv2.setRNGSeed(733)
    _, idx, centers = cv2.kmeans(
        data,
        cluster_count,
        None,
        (
            cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
            30,
            0.5,
        ),
        1,
        cv2.KMEANS_PP_CENTERS,
    )
    labels = idx.reshape(-1)
    counts = np.bincount(labels, minlength=cluster_count)
    cluster_order = sorted(
        range(cluster_count),
        key=lambda i: (
            -int(counts[i]),
            tuple(float(x) for x in centers[i]),
        ),
    )

    candidates: list[_BackgroundFieldCandidate] = []
    for cluster_index, cluster in enumerate(cluster_order):
        raw = np.zeros_like(subject, dtype=bool)
        selected = labels == cluster
        raw[yy[selected], xx[selected]] = True

        # LIVE-inspired layer handling: a palette role may own multiple
        # disconnected source-supported components.
        for component_index, component in enumerate(
            _connected_components(raw)
        ):
            source_area = int(component.sum())
            if source_area / max(1, field_area) < MIN_FIELD_RATIO:
                continue

            contours, _ = cv2.findContours(
                component.astype(np.uint8),
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE,
            )
            if not contours:
                continue
            chosen = _coarsest_safe_polygon(
                max(contours, key=cv2.contourArea),
                component,
                subject,
            )
            if chosen is None:
                continue

            (
                polygon,
                retained,
                render_area,
                coverage,
                expansion,
                overlap,
            ) = chosen
            color = tuple(
                int(x)
                for x in np.median(im[component], axis=0)
            )
            candidates.append(
                _BackgroundFieldCandidate(
                    cluster_index=cluster_index,
                    component_index=component_index,
                    polygon=polygon,
                    rgb=color,
                    source_area=source_area,
                    retained_area=retained,
                    render_area=render_area,
                    source_coverage=coverage,
                    expansion_ratio=expansion,
                    subject_overlap=overlap,
                )
            )

    selected_candidates = sorted(
        candidates,
        key=_candidate_sort_key,
    )[:max_fields]

    return tuple(
        BackgroundFieldPrimitive(
            role_index=role_index,
            cluster_index=candidate.cluster_index,
            component_index=candidate.component_index,
            polygon=candidate.polygon,
            rgb=candidate.rgb,
            source_area=candidate.source_area,
            retained_area=candidate.retained_area,
            render_area=candidate.render_area,
            source_coverage=candidate.source_coverage,
            expansion_ratio=candidate.expansion_ratio,
            subject_overlap=candidate.subject_overlap,
        )
        for role_index, candidate in enumerate(selected_candidates)
    )
