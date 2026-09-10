from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from .io.image_loader import load_image_data


SUBJECT_SEGMENTATION_MIN_CONFIDENCE = 0.58


@dataclass
class SubjectSegmentation:
    enabled: bool
    reason: str
    rgba: np.ndarray | None = None
    mask: np.ndarray | None = None
    background_rgb: tuple[int, int, int] | None = None
    border_dominant_fraction: float = 0.0
    foreground_area_ratio: float = 0.0
    center_fill_ratio: float = 0.0
    border_leak_ratio: float = 0.0
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "reason": self.reason,
            "background_rgb": list(self.background_rgb) if self.background_rgb is not None else None,
            "border_dominant_fraction": round(float(self.border_dominant_fraction), 6),
            "foreground_area_ratio": round(float(self.foreground_area_ratio), 6),
            "center_fill_ratio": round(float(self.center_fill_ratio), 6),
            "border_leak_ratio": round(float(self.border_leak_ratio), 6),
            "confidence": round(float(self.confidence), 6),
        }


def _source_rgba(image_or_path) -> tuple[np.ndarray, np.ndarray | None]:
    if isinstance(image_or_path, (str, Path)):
        data = load_image_data(image_or_path)
        return data.rgb, data.alpha
    arr = np.asarray(image_or_path)
    if arr.ndim != 3 or arr.shape[2] not in {3, 4}:
        raise ValueError("image array must be HxWx3 or HxWx4")
    return arr[:, :, :3], arr[:, :, 3] if arr.shape[2] == 4 else None


def _border_pixels(rgb: np.ndarray, ratio: float = 0.04) -> np.ndarray:
    h, w = rgb.shape[:2]
    b = max(2, int(round(min(h, w) * ratio)))
    return np.concatenate([
        rgb[:b].reshape(-1, 3), rgb[h-b:].reshape(-1, 3),
        rgb[b:h-b, :b].reshape(-1, 3), rgb[b:h-b, w-b:].reshape(-1, 3),
    ])


def _background_prototypes(border: np.ndarray) -> tuple[list[np.ndarray], list[tuple[int, int, int]], float]:
    bins = (border // 24).astype(np.int16)
    keys = bins[:, 0] * 121 + bins[:, 1] * 11 + bins[:, 2]
    values, counts = np.unique(keys, return_counts=True)
    order = np.argsort(counts)[::-1]
    prototypes: list[np.ndarray] = []
    colors: list[tuple[int, int, int]] = []
    dominant = 0.0
    total = max(len(border), 1)
    for rank, idx in enumerate(order[:8]):
        selected = keys == values[idx]
        fraction = float(counts[idx]) / float(total)
        if rank == 0:
            dominant = fraction
        if prototypes and fraction < 0.06:
            break
        color = np.median(border[selected], axis=0).astype(np.uint8)
        lab = cv2.cvtColor(color.reshape(1, 1, 3), cv2.COLOR_RGB2LAB).astype(np.float32)[0, 0]
        if prototypes and float(np.linalg.norm(lab - prototypes[0])) > 42.0:
            continue
        prototypes.append(lab)
        colors.append(tuple(int(x) for x in color))
    return prototypes, colors, dominant


def _edge_connected_background(candidate: np.ndarray) -> np.ndarray:
    n, labels, _, _ = cv2.connectedComponentsWithStats(candidate.astype(np.uint8), 8)
    if n <= 1:
        return np.zeros_like(candidate, dtype=np.uint8)
    edge_labels = np.unique(np.concatenate([
        labels[0, :], labels[-1, :], labels[:, 0], labels[:, -1]
    ]))
    edge_labels = edge_labels[edge_labels != 0]
    if edge_labels.size == 0:
        return np.zeros_like(candidate, dtype=np.uint8)
    return np.isin(labels, edge_labels).astype(np.uint8)


def _cleanup_subject_mask(mask: np.ndarray, min_side: int) -> np.ndarray:
    close_k = max(3, int(round(min_side * 0.010)))
    if close_k % 2 == 0:
        close_k += 1
    open_k = max(3, int(round(min_side * 0.004)))
    if open_k % 2 == 0:
        open_k += 1
    out = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((close_k, close_k), np.uint8))
    out = cv2.morphologyEx(out, cv2.MORPH_OPEN, np.ones((open_k, open_k), np.uint8))
    return (out > 0).astype(np.uint8)


def segment_subject_without_ai(image_or_path) -> SubjectSegmentation:
    rgb, alpha = _source_rgba(image_or_path)
    if alpha is not None and bool(np.any(alpha < 250)):
        occupancy = float((alpha >= 16).mean())
        if 0.025 <= occupancy <= 0.96:
            return SubjectSegmentation(False, "alpha_subject")

    h, w = rgb.shape[:2]
    aspect = min(h, w) / max(float(max(h, w)), 1.0)
    if aspect < 0.82:
        return SubjectSegmentation(False, "aspect_gate")
    border = _border_pixels(rgb)
    prototypes, colors, dominant = _background_prototypes(border)
    if not prototypes or dominant < 0.30:
        return SubjectSegmentation(False, "border_gate", border_dominant_fraction=dominant)

    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    centers = np.stack(prototypes)
    distance = np.linalg.norm(lab[:, :, None, :] - centers[None, None, :, :], axis=3).min(axis=2)
    background_candidate = (distance <= 28.0).astype(np.uint8)
    if alpha is not None:
        background_candidate[alpha < 128] = 1
    background = _edge_connected_background(background_candidate)
    subject = (1 - background).astype(np.uint8)
    if alpha is not None:
        subject[alpha < 16] = 0
    subject = _cleanup_subject_mask(subject, min(h, w))

    area_ratio = float(subject.mean())
    center = subject[int(h * 0.20):int(h * 0.80), int(w * 0.20):int(w * 0.80)]
    center_fill = float(center.mean()) if center.size else 0.0
    edge = np.concatenate([subject[0, :], subject[-1, :], subject[:, 0], subject[:, -1]])
    border_leak = float(edge.mean()) if edge.size else 1.0

    if not 0.18 <= area_ratio <= 0.80:
        return SubjectSegmentation(False, "area_gate", background_rgb=colors[0], border_dominant_fraction=dominant, foreground_area_ratio=area_ratio, center_fill_ratio=center_fill, border_leak_ratio=border_leak)
    if center_fill < 0.30:
        return SubjectSegmentation(False, "center_gate", background_rgb=colors[0], border_dominant_fraction=dominant, foreground_area_ratio=area_ratio, center_fill_ratio=center_fill, border_leak_ratio=border_leak)

    confidence = float(np.clip(
        0.42 * dominant
        + 0.36 * min(center_fill / 0.80, 1.0)
        + 0.22 * (1.0 - min(border_leak / 0.35, 1.0)),
        0.0, 1.0,
    ))
    if confidence < SUBJECT_SEGMENTATION_MIN_CONFIDENCE:
        return SubjectSegmentation(False, "confidence_gate", background_rgb=colors[0], border_dominant_fraction=dominant, foreground_area_ratio=area_ratio, center_fill_ratio=center_fill, border_leak_ratio=border_leak, confidence=confidence)

    rgba = np.dstack([rgb, subject.astype(np.uint8) * 255])
    return SubjectSegmentation(
        True, "accepted", rgba=rgba, mask=subject,
        background_rgb=colors[0], border_dominant_fraction=dominant,
        foreground_area_ratio=area_ratio, center_fill_ratio=center_fill,
        border_leak_ratio=border_leak, confidence=confidence,
    )
