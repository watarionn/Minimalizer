from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class StructureForegroundResult:
    enabled: bool
    reason: str
    mask: np.ndarray | None = None
    foreground_area_ratio: float = 0.0
    background_cluster_count: int = 0
    method: str = "none"
    border_leak_ratio: float = 0.0

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "reason": self.reason,
            "foreground_area_ratio": round(float(self.foreground_area_ratio), 6),
            "background_cluster_count": int(self.background_cluster_count),
            "method": self.method,
            "border_leak_ratio": round(float(self.border_leak_ratio), 6),
        }


def _fill_holes(mask: np.ndarray) -> np.ndarray:
    h, w = mask.shape
    inv = (1 - mask.astype(np.uint8)).copy()
    flood = inv.copy()
    pad = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(flood, pad, (0, 0), 2)
    holes = (flood == 1).astype(np.uint8)
    return np.clip(mask.astype(np.uint8) + holes, 0, 1)


def _border_pixels(rgb: np.ndarray) -> np.ndarray:
    h, w = rgb.shape[:2]
    thick = max(6, int(round(min(h, w) * 0.06)))
    return np.concatenate(
        [
            rgb[:thick].reshape(-1, 3),
            rgb[-thick:].reshape(-1, 3),
            rgb[thick:-thick, :thick].reshape(-1, 3),
            rgb[thick:-thick, -thick:].reshape(-1, 3),
        ],
        axis=0,
    )


def _background_centers(rgb: np.ndarray) -> np.ndarray:
    border = _border_pixels(rgb)
    lab = cv2.cvtColor(border.reshape(-1, 1, 3), cv2.COLOR_RGB2LAB).reshape(-1, 3).astype(np.float32)
    cluster_count = min(4, max(1, len(lab) // 256))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 0.6)
    cv2.setRNGSeed(1701)
    _score, labels, centers = cv2.kmeans(lab, cluster_count, None, criteria, 4, cv2.KMEANS_PP_CENTERS)
    counts = np.bincount(labels.ravel(), minlength=cluster_count)
    order = np.argsort(-counts)
    selected: list[np.ndarray] = []
    covered = 0.0
    total = max(int(counts.sum()), 1)
    for index in order:
        fraction = float(counts[index]) / total
        if selected and fraction < 0.035 and covered > 0.82:
            break
        selected.append(centers[index])
        covered += fraction
        if covered >= 0.94:
            break
    return np.asarray(selected, dtype=np.float32)


def _merge_subject_components(mask: np.ndarray) -> np.ndarray:
    h, w = mask.shape
    count, labels, stats, centers = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    if count <= 1:
        return mask.astype(np.uint8)

    cx, cy = w * 0.5, h * 0.5
    ranked: list[tuple[float, int]] = []
    for index in range(1, count):
        area = int(stats[index, cv2.CC_STAT_AREA])
        if area < h * w * 0.002:
            continue
        ccx, ccy = centers[index]
        centrality = np.exp(-((ccx - cx) / max(w * 0.40, 1.0)) ** 2 - ((ccy - cy) / max(h * 0.45, 1.0)) ** 2)
        ranked.append((area / float(h * w) + 0.50 * float(centrality), index))
    if not ranked:
        return np.zeros_like(mask, dtype=np.uint8)

    ranked.sort(reverse=True)
    merged = (labels == ranked[0][1]).astype(np.uint8)
    link_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))
    for _ in range(3):
        dilated = cv2.dilate(merged, link_kernel)
        changed = False
        for _score, index in ranked[1:]:
            component = (labels == index).astype(np.uint8)
            if np.any(component & dilated):
                old_area = int(merged.sum())
                merged |= component
                changed = changed or int(merged.sum()) > old_area
        if not changed:
            break
    return merged


def _border_leak(mask: np.ndarray) -> float:
    h, w = mask.shape
    thick = max(2, int(round(min(h, w) * 0.03)))
    border = np.concatenate(
        [
            mask[:thick].ravel(),
            mask[-thick:].ravel(),
            mask[thick:-thick, :thick].ravel(),
            mask[thick:-thick, -thick:].ravel(),
        ]
    )
    return float(border.mean()) if len(border) else 0.0


def _grabcut_subject(rgb: np.ndarray) -> np.ndarray:
    h, w = rgb.shape[:2]
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    grab = np.full((h, w), cv2.GC_PR_BGD, dtype=np.uint8)
    edge = max(2, int(round(min(h, w) * 0.02)))
    grab[:edge, :] = cv2.GC_BGD
    grab[-edge:, :] = cv2.GC_BGD
    grab[:, :edge] = cv2.GC_BGD
    grab[:, -edge:] = cv2.GC_BGD
    grab[int(h * 0.05) : int(h * 0.98), int(w * 0.08) : int(w * 0.92)] = cv2.GC_PR_FGD
    bg_model = np.zeros((1, 65), dtype=np.float64)
    fg_model = np.zeros((1, 65), dtype=np.float64)
    cv2.setRNGSeed(1701)
    cv2.grabCut(bgr, grab, None, bg_model, fg_model, 5, cv2.GC_INIT_WITH_MASK)
    mask = np.isin(grab, (cv2.GC_FGD, cv2.GC_PR_FGD)).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    mask = _merge_subject_components(mask)
    return _fill_holes(mask)


def build_structure_foreground(rgb: np.ndarray) -> StructureForegroundResult:
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        return StructureForegroundResult(False, "rgb_required")
    h, w = rgb.shape[:2]
    if min(h, w) < 64:
        return StructureForegroundResult(False, "image_too_small")

    centers = _background_centers(rgb)
    if centers.size == 0:
        return StructureForegroundResult(False, "background_cluster_missing")

    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    distance = np.linalg.norm(lab[:, :, None, :] - centers[None, None, :, :], axis=3).min(axis=2)
    mask = (distance > 20.0).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17)))
    mask = _merge_subject_components(mask)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    mask = _fill_holes(mask)

    area_ratio = float(mask.mean())
    leak_ratio = _border_leak(mask)
    method = "border_color"
    if not (0.08 <= area_ratio <= 0.72 and leak_ratio <= 0.18):
        mask = _grabcut_subject(rgb)
        area_ratio = float(mask.mean())
        leak_ratio = _border_leak(mask)
        method = "grabcut"

    if not 0.08 <= area_ratio <= 0.82:
        return StructureForegroundResult(
            False,
            "foreground_area_gate",
            mask=mask,
            foreground_area_ratio=area_ratio,
            background_cluster_count=len(centers),
            method=method,
            border_leak_ratio=leak_ratio,
        )
    return StructureForegroundResult(
        True,
        "ok",
        mask=mask,
        foreground_area_ratio=area_ratio,
        background_cluster_count=len(centers),
        method=method,
        border_leak_ratio=leak_ratio,
    )
