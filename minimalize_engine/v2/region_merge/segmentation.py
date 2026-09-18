from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from numpy.typing import NDArray

from minimalize_engine.v2.types import ImageBundle, LabelMap

DEFAULT_TARGET_AREA = 900.0
DEFAULT_TARGET_MIN = 400
DEFAULT_TARGET_MAX = 1200
DEFAULT_MIN_SUPERPIXEL_AREA = 64.0
DEFAULT_SLIC_ITERATIONS = 10
DEFAULT_EDGE_COVERAGE_THRESHOLD = 0.75
DEFAULT_RETRY_SCALE = 0.80
DEFAULT_MAX_RETRY_TARGET_FACTOR = 2.5
DEFAULT_SLICO_COLOR_SCALE_FLOOR = 5000.0


@dataclass(frozen=True, slots=True)
class OversegmentationResult:
    labels: LabelMap
    region_size: int
    region_count: int
    edge_coverage: float
    retried: bool = False
    initial_edge_coverage: float | None = None


def target_superpixel_count(
    height: int,
    width: int,
    *,
    target_area: float = DEFAULT_TARGET_AREA,
    minimum: int = DEFAULT_TARGET_MIN,
    maximum: int = DEFAULT_TARGET_MAX,
    min_average_area: float = DEFAULT_MIN_SUPERPIXEL_AREA,
) -> int:
    if height <= 0 or width <= 0:
        raise ValueError("image dimensions must be positive")
    if target_area <= 0.0 or min_average_area <= 0.0:
        raise ValueError("target areas must be positive")
    if minimum <= 0 or maximum < minimum:
        raise ValueError("invalid target-count bounds")

    area = height * width
    requested = int(round(area / target_area))
    requested = int(np.clip(requested, minimum, maximum))
    area_limited = max(1, int(np.floor(area / min_average_area)))
    return max(1, min(requested, area_limited))


def region_size_for_target(height: int, width: int, target_count: int) -> int:
    if target_count <= 0:
        raise ValueError("target_count must be positive")
    area = height * width
    return max(1, int(round(np.sqrt(area / float(target_count)))))


def _move_center_to_low_edge(
    y: int,
    x: int,
    edge: NDArray[np.float32],
) -> tuple[int, int]:
    height, width = edge.shape
    y0, y1 = max(0, y - 1), min(height, y + 2)
    x0, x1 = max(0, x - 1), min(width, x + 2)
    patch = edge[y0:y1, x0:x1]
    index = int(np.argmin(patch))
    py, px = np.unravel_index(index, patch.shape)
    return y0 + int(py), x0 + int(px)


def _initial_centers(
    lab: NDArray[np.float32],
    edge: NDArray[np.float32],
    region_size: int,
) -> NDArray[np.float64]:
    height, width = lab.shape[:2]
    offset = max(0, region_size // 2)
    ys = np.arange(offset, height, region_size, dtype=np.int64)
    xs = np.arange(offset, width, region_size, dtype=np.int64)
    if ys.size == 0:
        ys = np.array([height // 2], dtype=np.int64)
    if xs.size == 0:
        xs = np.array([width // 2], dtype=np.int64)

    centers: list[list[float]] = []
    for y in ys:
        for x in xs:
            cy, cx = _move_center_to_low_edge(int(y), int(x), edge)
            l, a, b = lab[cy, cx]
            centers.append([float(l), float(a), float(b), float(cy), float(cx)])
    return np.asarray(centers, dtype=np.float64)


def _run_numpy_slico(
    lab: NDArray[np.float32],
    edge_structural: NDArray[np.float32],
    *,
    region_size: int,
    iterations: int,
) -> LabelMap:
    if region_size <= 0 or iterations <= 0:
        raise ValueError("region_size and iterations must be positive")
    height, width = lab.shape[:2]
    centers = _initial_centers(lab, edge_structural, region_size)
    cluster_count = centers.shape[0]
    color_scales = np.full(cluster_count, DEFAULT_SLICO_COLOR_SCALE_FLOOR, dtype=np.float64)
    labels = np.full((height, width), -1, dtype=np.int32)
    distances = np.full((height, width), np.inf, dtype=np.float64)

    yy, xx = np.indices((height, width), dtype=np.float64)
    yy_flat = yy.ravel()
    xx_flat = xx.ravel()
    spatial_scale = max(float(region_size * region_size), 1.0)
    lab64 = lab.astype(np.float64, copy=False)
    lab_flat = lab64.reshape(-1, 3)

    for _ in range(iterations):
        labels.fill(-1)
        distances.fill(np.inf)
        for cluster_id, center in enumerate(centers):
            cl, ca, cb, cy, cx = center
            y0 = max(0, int(np.floor(cy - region_size)))
            y1 = min(height, int(np.ceil(cy + region_size)) + 1)
            x0 = max(0, int(np.floor(cx - region_size)))
            x1 = min(width, int(np.ceil(cx + region_size)) + 1)
            patch_lab = lab64[y0:y1, x0:x1]
            dc2 = np.sum(
                (patch_lab - np.array([cl, ca, cb])) ** 2,
                axis=2,
            )
            ds2 = (
                (yy[y0:y1, x0:x1] - cy) ** 2
                + (xx[y0:y1, x0:x1] - cx) ** 2
            )
            distance = dc2 / max(color_scales[cluster_id], 1.0) + ds2 / spatial_scale
            current = distances[y0:y1, x0:x1]
            take = distance < current
            current[take] = distance[take]
            labels[y0:y1, x0:x1][take] = cluster_id

        if np.any(labels < 0):
            raise RuntimeError("SLICO assignment left unlabeled pixels")

        flat = labels.ravel()
        counts = np.bincount(flat, minlength=cluster_count).astype(np.float64)
        # Group pixel positions once per iteration. Stable ordering preserves the
        # exact C-order previously produced by boolean masks for every cluster.
        order = np.argsort(flat, kind="stable")
        ends = np.cumsum(counts.astype(np.int64))
        start = 0
        for cluster_id in range(cluster_count):
            end = int(ends[cluster_id])
            if counts[cluster_id] > 0.0:
                positions = order[start:end]
                pixels = lab_flat[positions]
                centers[cluster_id, :3] = pixels.mean(axis=0)
                centers[cluster_id, 3] = yy_flat[positions].mean()
                centers[cluster_id, 4] = xx_flat[positions].mean()
                color_delta = pixels - centers[cluster_id, :3]
                color_scales[cluster_id] = max(
                    DEFAULT_SLICO_COLOR_SCALE_FLOOR,
                    float(np.max(np.sum(color_delta * color_delta, axis=1))),
                )
            start = end

    return labels.astype(np.int32, copy=False)


def split_disconnected_labels(labels: NDArray[np.integer]) -> LabelMap:
    source = np.asarray(labels, dtype=np.int32)
    if source.ndim != 2 or source.size == 0:
        raise ValueError("labels must be a non-empty 2D array")
    if np.any(source < 0):
        raise ValueError("labels must be non-negative")

    output = np.full(source.shape, -1, dtype=np.int32)
    next_id = 0
    for label in np.unique(source):
        ys, xs = np.where(source == label)
        y0, y1 = int(ys.min()), int(ys.max()) + 1
        x0, x1 = int(xs.min()), int(xs.max()) + 1
        mask = (source[y0:y1, x0:x1] == label).astype(np.uint8)
        count, components = cv2.connectedComponents(mask, connectivity=4)
        target = output[y0:y1, x0:x1]
        for component_id in range(1, count):
            target[components == component_id] = next_id
            next_id += 1

    if np.any(output < 0):
        raise RuntimeError("connectivity split left unlabeled pixels")
    return output


def label_boundary_mask(labels: NDArray[np.integer]) -> NDArray[np.bool_]:
    array = np.asarray(labels)
    if array.ndim != 2:
        raise ValueError("labels must be 2D")
    boundary = np.zeros(array.shape, dtype=bool)
    horizontal = array[:, :-1] != array[:, 1:]
    boundary[:, :-1] |= horizontal
    boundary[:, 1:] |= horizontal
    vertical = array[:-1, :] != array[1:, :]
    boundary[:-1, :] |= vertical
    boundary[1:, :] |= vertical
    return boundary


def structural_edge_coverage(
    labels: NDArray[np.integer],
    edge_structural: NDArray[np.floating],
) -> float:
    edge = np.asarray(edge_structural, dtype=np.float32)
    if edge.shape != np.asarray(labels).shape:
        raise ValueError("edge_structural must match labels shape")
    weights = np.clip(edge, 0.0, 1.0)
    total = float(weights.sum())
    if total <= 1.0e-12:
        return 1.0
    boundary = label_boundary_mask(labels).astype(np.uint8)
    near_boundary = cv2.dilate(boundary, np.ones((3, 3), np.uint8)) > 0
    covered = float(weights[near_boundary].sum())
    return float(np.clip(covered / total, 0.0, 1.0))


def _segment_once(
    bundle: ImageBundle,
    *,
    region_size: int,
    iterations: int,
    provider: str,
) -> LabelMap:
    if provider != "numpy_slico":
        raise ValueError("unsupported SLICO provider; use 'numpy_slico'")
    raw_labels = _run_numpy_slico(
        bundle.structural_lab,
        bundle.edge_structural,
        region_size=region_size,
        iterations=iterations,
    )
    return split_disconnected_labels(raw_labels)


def oversegment(
    bundle: ImageBundle,
    *,
    iterations: int = DEFAULT_SLIC_ITERATIONS,
    edge_coverage_threshold: float = DEFAULT_EDGE_COVERAGE_THRESHOLD,
    retry_scale: float = DEFAULT_RETRY_SCALE,
    max_retry_target_factor: float = DEFAULT_MAX_RETRY_TARGET_FACTOR,
    provider: str = "numpy_slico",
) -> OversegmentationResult:
    height, width = bundle.analysis_rgb.shape[:2]
    if bundle.structural_lab.shape != (height, width, 3):
        raise ValueError("structural_lab shape must match analysis_rgb")
    if bundle.edge_structural.shape != (height, width):
        raise ValueError("edge_structural shape must match analysis_rgb")
    if not 0.0 <= edge_coverage_threshold <= 1.0:
        raise ValueError("edge_coverage_threshold must be in [0, 1]")
    if not 0.0 < retry_scale < 1.0:
        raise ValueError("retry_scale must be in (0, 1)")
    if max_retry_target_factor < 1.0:
        raise ValueError("max_retry_target_factor must be at least 1")

    target_count = target_superpixel_count(height, width)
    region_size = region_size_for_target(height, width, target_count)
    labels = _segment_once(
        bundle,
        region_size=region_size,
        iterations=iterations,
        provider=provider,
    )
    region_count = int(labels.max()) + 1
    coverage = structural_edge_coverage(labels, bundle.edge_structural)

    if coverage >= edge_coverage_threshold or region_size <= 1:
        return OversegmentationResult(
            labels=labels,
            region_size=region_size,
            region_count=region_count,
            edge_coverage=coverage,
        )

    retry_size = max(1, int(round(region_size * retry_scale)))
    if retry_size >= region_size:
        retry_size = region_size - 1
    retry_labels = _segment_once(
        bundle,
        region_size=retry_size,
        iterations=iterations,
        provider=provider,
    )
    retry_count = int(retry_labels.max()) + 1
    retry_coverage = structural_edge_coverage(
        retry_labels,
        bundle.edge_structural,
    )
    count_limit = max(
        region_count,
        int(np.ceil(target_count * max_retry_target_factor)),
    )
    keep_retry = retry_coverage > coverage and retry_count <= count_limit
    if keep_retry:
        return OversegmentationResult(
            labels=retry_labels,
            region_size=retry_size,
            region_count=retry_count,
            edge_coverage=retry_coverage,
            retried=True,
            initial_edge_coverage=coverage,
        )
    return OversegmentationResult(
        labels=labels,
        region_size=region_size,
        region_count=region_count,
        edge_coverage=coverage,
        initial_edge_coverage=coverage,
    )
