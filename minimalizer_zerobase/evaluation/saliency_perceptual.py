from __future__ import annotations

from typing import Any, Mapping

import cv2
import numpy as np


REGION_ORDER = ("face", "head", "left_arm", "right_arm", "outer_boundary")


def _ssim(a: np.ndarray, b: np.ndarray) -> float:
    x = a.astype(np.float32) / 255.0
    y = b.astype(np.float32) / 255.0
    mu_x, mu_y = float(x.mean()), float(y.mean())
    var_x, var_y = float(x.var()), float(y.var())
    cov = float(((x - mu_x) * (y - mu_y)).mean())
    c1, c2 = 0.01**2, 0.03**2
    return float(((2 * mu_x * mu_y + c1) * (2 * cov + c2)) /
                 ((mu_x**2 + mu_y**2 + c1) * (var_x + var_y + c2)))


def _region_masks(source_masks: Mapping[str, np.ndarray]) -> dict[str, np.ndarray]:
    if not source_masks:
        raise ValueError("source semantic masks are required")
    shape = next(iter(source_masks.values())).shape
    out = {name: np.asarray(source_masks.get(name, np.zeros(shape, bool))).astype(bool)
           for name in REGION_ORDER[:-1]}
    outer = np.logical_or.reduce([np.asarray(v).astype(bool) for v in source_masks.values()])
    edge = cv2.morphologyEx(outer.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0
    out["outer_boundary"] = edge
    return out


def evaluate_saliency_perceptual(
    source_rgb: np.ndarray,
    candidate_rgb: np.ndarray,
    source_masks: Mapping[str, np.ndarray],
    *,
    dino_observer: Any | None = None,
    lpips_observer: Any | None = None,
) -> dict[str, Any]:
    """Emit observer-only, source-derived region perceptual evidence.

    No result here is a gate or rendering authority. Optional observers are
    deliberately injected so heavyweight packages are never imported here.
    """
    source = np.asarray(source_rgb)
    candidate = np.asarray(candidate_rgb)
    if source.shape != candidate.shape or source.ndim != 3 or source.shape[2] != 3:
        raise ValueError("source and candidate RGB frames must have equal HxWx3 shape")
    rows: dict[str, dict[str, Any]] = {}
    weights: list[float] = []
    scores: list[float] = []
    for name, mask in _region_masks(source_masks).items():
        pixels = int(np.count_nonzero(mask))
        if not pixels:
            rows[name] = {"available": False, "pixels": 0}
            continue
        diff = np.abs(source.astype(np.float32) - candidate.astype(np.float32)).mean(axis=2)
        mae = float(diff[mask].mean())
        score = float(np.clip(1.0 - mae / 255.0, 0.0, 1.0))
        ssim = _ssim(cv2.cvtColor(source, cv2.COLOR_RGB2GRAY)[mask],
                     cv2.cvtColor(candidate, cv2.COLOR_RGB2GRAY)[mask])
        rows[name] = {"available": True, "pixels": pixels, "weight": float(pixels),
                      "mae": mae, "ssim": ssim, "score": score,
                      "provenance": "source-semantic-mask"}
        weights.append(float(pixels)); scores.append(score)
    backend = {
        "dinov3": "available" if dino_observer is not None else "unavailable",
        "lpips": "available" if lpips_observer is not None else "unavailable",
        "ssim": "built-in-deterministic",
    }
    aggregate = float(np.average(scores, weights=weights)) if scores else None
    return {"schema_version": "sa10.21-saliency-perceptual-v1", "regions": rows,
            "aggregate_score": aggregate, "backend": backend,
            "authority": False, "fail_open": True,
            "note": "observer-only evidence; SA10.18 anatomy/silhouette and SA10.20 topology remain hard gates"}
