from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from minimalize_engine.v2.contour.types import ContourSimplificationResult
from minimalize_engine.v2.palette.types import PaletteConfig, RegionColorSample
from minimalize_engine.v2.region_merge.types import RegionSelection
from minimalize_engine.v2.types import CharacteristicContext, ImageBundle, RegionId


def ciede2000(
    first: NDArray[np.floating],
    second: NDArray[np.floating],
) -> NDArray[np.float64] | np.float64:
    a = np.asarray(first, dtype=np.float64)
    b = np.asarray(second, dtype=np.float64)
    if a.shape[-1:] != (3,) or b.shape[-1:] != (3,):
        raise ValueError("CIEDE2000 inputs must end with three Lab channels")
    l1, aa1, bb1 = np.moveaxis(a, -1, 0)
    l2, aa2, bb2 = np.moveaxis(b, -1, 0)
    c1 = np.hypot(aa1, bb1)
    c2 = np.hypot(aa2, bb2)
    cbar = (c1 + c2) * 0.5
    cbar7 = np.power(cbar, 7)
    g = 0.5 * (1.0 - np.sqrt(cbar7 / (cbar7 + 25.0 ** 7)))
    a1p = (1.0 + g) * aa1
    a2p = (1.0 + g) * aa2
    c1p = np.hypot(a1p, bb1)
    c2p = np.hypot(a2p, bb2)
    h1p = np.mod(np.degrees(np.arctan2(bb1, a1p)), 360.0)
    h2p = np.mod(np.degrees(np.arctan2(bb2, a2p)), 360.0)

    delta_lp = l2 - l1
    delta_cp = c2p - c1p
    hue_delta = h2p - h1p
    product = c1p * c2p
    delta_hp = np.where(
        product == 0.0,
        0.0,
        np.where(
            np.abs(hue_delta) <= 180.0,
            hue_delta,
            np.where(hue_delta > 180.0, hue_delta - 360.0, hue_delta + 360.0),
        ),
    )
    delta_hp_term = 2.0 * np.sqrt(product) * np.sin(np.radians(delta_hp * 0.5))

    lbarp = (l1 + l2) * 0.5
    cbarp = (c1p + c2p) * 0.5
    hue_sum = h1p + h2p
    hue_abs = np.abs(h1p - h2p)
    hbarp = np.where(
        product == 0.0,
        hue_sum,
        np.where(
            hue_abs <= 180.0,
            hue_sum * 0.5,
            np.where(hue_sum < 360.0, (hue_sum + 360.0) * 0.5, (hue_sum - 360.0) * 0.5),
        ),
    )
    t = (
        1.0
        - 0.17 * np.cos(np.radians(hbarp - 30.0))
        + 0.24 * np.cos(np.radians(2.0 * hbarp))
        + 0.32 * np.cos(np.radians(3.0 * hbarp + 6.0))
        - 0.20 * np.cos(np.radians(4.0 * hbarp - 63.0))
    )
    delta_theta = 30.0 * np.exp(-np.square((hbarp - 275.0) / 25.0))
    cbarp7 = np.power(cbarp, 7)
    rc = 2.0 * np.sqrt(cbarp7 / (cbarp7 + 25.0 ** 7))
    sl = 1.0 + 0.015 * np.square(lbarp - 50.0) / np.sqrt(20.0 + np.square(lbarp - 50.0))
    sc = 1.0 + 0.045 * cbarp
    sh = 1.0 + 0.015 * cbarp * t
    rt = -np.sin(np.radians(2.0 * delta_theta)) * rc
    l_term = delta_lp / sl
    c_term = delta_cp / sc
    h_term = delta_hp_term / sh
    value = np.sqrt(
        np.maximum(
            0.0,
            np.square(l_term) + np.square(c_term) + np.square(h_term) + rt * c_term * h_term,
        )
    )
    if np.ndim(value) == 0:
        return np.float64(value)
    return np.asarray(value, dtype=np.float64)


def deterministic_region_indices(
    labels: NDArray[np.int32], region_id: RegionId, maximum: int
) -> NDArray[np.int64]:
    flat = np.flatnonzero(labels.reshape(-1) == region_id)
    if flat.size == 0:
        raise ValueError(f"region {region_id} has no pixels")
    if flat.size <= maximum:
        return flat.astype(np.int64, copy=False)
    positions = np.linspace(0, flat.size - 1, num=maximum, dtype=np.int64)
    return flat[positions].astype(np.int64, copy=False)


def robust_region_medoid(
    bundle: ImageBundle,
    labels: NDArray[np.int32],
    region_id: RegionId,
    config: PaletteConfig,
) -> tuple[np.ndarray, tuple[int, int], tuple[int, int, int], int]:
    indices = deterministic_region_indices(labels, region_id, config.max_samples_per_region)
    height, width = labels.shape
    ys = indices // width
    xs = indices % width
    samples = bundle.analysis_lab[ys, xs].astype(np.float64, copy=False)
    median = np.median(samples, axis=0)
    euclidean = np.linalg.norm(samples - median[None, :], axis=1)
    candidate_count = min(config.medoid_candidate_count, samples.shape[0])
    candidate_order = np.argsort(euclidean, kind="stable")[:candidate_count]
    candidates = samples[candidate_order]
    distances = ciede2000(candidates[:, None, :], samples[None, :, :])
    totals = np.sum(distances, axis=1)
    best_local = int(np.argmin(totals))
    best_index = int(candidate_order[best_local])
    y, x = int(ys[best_index]), int(xs[best_index])
    rgb_array = bundle.analysis_rgb[y, x]
    rgb = tuple(int(value) for value in rgb_array)
    pixel_count = int(np.count_nonzero(labels == region_id))
    return samples[best_index].copy(), (x, y), rgb, pixel_count


def _region_anchor_ids(
    selection: RegionSelection,
    region_id: RegionId,
    characteristic: CharacteristicContext | None,
    config: PaletteConfig,
) -> tuple[int, ...]:
    if characteristic is None or characteristic.anchor_map is None:
        return ()
    anchor_map = characteristic.anchor_map
    if anchor_map.shape != selection.labels.shape:
        raise ValueError("characteristic anchor_map must match selection labels")
    confidence_map = characteristic.confidence_map
    if confidence_map is not None and confidence_map.shape != selection.labels.shape:
        raise ValueError("characteristic confidence_map must match selection labels")
    anchors = {anchor.id: anchor for anchor in characteristic.anchors}
    region_mask = selection.labels == region_id
    result: list[int] = []
    for anchor_id in sorted(int(value) for value in np.unique(anchor_map[region_mask]) if value >= 0):
        if anchor_id not in anchors:
            raise ValueError(f"anchor_map references unknown anchor {anchor_id}")
        local = region_mask & (anchor_map == anchor_id)
        confidence = anchors[anchor_id].confidence
        if confidence_map is not None:
            confidence *= float(np.mean(confidence_map[local], dtype=np.float64))
        if confidence >= config.anchor_confidence_threshold:
            result.append(anchor_id)
    return tuple(result)


def sample_region_colors(
    bundle: ImageBundle,
    selection: RegionSelection,
    contour_result: ContourSimplificationResult,
    *,
    characteristic: CharacteristicContext | None,
    config: PaletteConfig,
) -> dict[RegionId, RegionColorSample]:
    if selection.labels.shape != bundle.analysis_lab.shape[:2]:
        raise ValueError("selection labels must match analysis Lab resolution")
    if set(contour_result.contours) != set(selection.region_ids):
        raise ValueError("contour result must match selected regions")
    samples: dict[RegionId, RegionColorSample] = {}
    for region_id in sorted(selection.region_ids):
        lab, xy, rgb, count = robust_region_medoid(
            bundle, selection.labels, region_id, config
        )
        contour = contour_result.contours[region_id]
        samples[region_id] = RegionColorSample(
            region_id=region_id,
            lab=lab,
            rgb=rgb,
            source_xy=xy,
            pixel_count=count,
            anchor_ids=_region_anchor_ids(selection, region_id, characteristic, config),
            semantic_tag=contour.semantic_tag,
            semantic_confidence=contour.semantic_confidence,
        )
    return samples
