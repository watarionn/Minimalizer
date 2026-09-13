from __future__ import annotations

from dataclasses import dataclass
from math import exp

import numpy as np

from .structure_face_locator import locate_structure_face


@dataclass
class StructureMaskSelection:
    enabled: bool
    reason: str
    source: str = "none"
    mask: np.ndarray | None = None
    score: float = 0.0
    candidates: tuple[dict, ...] = ()

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "reason": self.reason,
            "source": self.source,
            "score": round(float(self.score), 6),
            "candidates": list(self.candidates),
        }


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


def _centrality(mask: np.ndarray) -> float:
    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        return 0.0
    h, w = mask.shape
    cx = float(np.mean(xs))
    cy = float(np.mean(ys))
    return exp(
        -((cx - w * 0.5) / max(w * 0.38, 1.0)) ** 2
        -((cy - h * 0.52) / max(h * 0.42, 1.0)) ** 2
    )


def _candidate_stats(
    rgb: np.ndarray,
    source: str,
    mask: np.ndarray,
) -> tuple[float, dict]:
    binary = (mask > 0).astype(np.uint8)
    area_ratio = float(binary.mean())
    leak_ratio = _border_leak(binary)
    centrality = _centrality(binary)
    face = locate_structure_face(rgb, binary)

    area_prior = exp(-((area_ratio - 0.42) / 0.30) ** 2)
    leak_prior = max(0.0, 1.0 - leak_ratio / 0.35)
    face_bonus = 1.0 if face.enabled else 0.0
    face_score = min(max(float(face.score) / 5.0, 0.0), 1.0)
    score = (
        0.80 * area_prior
        + 1.00 * leak_prior
        + 0.55 * centrality
        + 1.50 * face_bonus
        + 0.45 * face_score
    )
    if not 0.06 <= area_ratio <= 0.88:
        score -= 2.0
    if leak_ratio > 0.40:
        score -= 1.5
    if not face.enabled:
        score -= 2.0

    return score, {
        "source": source,
        "score": round(float(score), 6),
        "area_ratio": round(area_ratio, 6),
        "border_leak_ratio": round(leak_ratio, 6),
        "centrality": round(float(centrality), 6),
        "face_enabled": bool(face.enabled),
        "face_reason": face.reason,
        "face_score": round(float(face.score), 6),
    }


def select_structure_mask(
    rgb: np.ndarray,
    candidates: dict[str, np.ndarray | None],
) -> StructureMaskSelection:
    ranked: list[tuple[float, str, np.ndarray, dict]] = []
    for source, mask in candidates.items():
        if mask is None:
            continue
        binary = (np.asarray(mask) > 0).astype(np.uint8)
        if binary.shape != rgb.shape[:2]:
            continue
        score, stats = _candidate_stats(rgb, source, binary)
        ranked.append((score, source, binary, stats))

    if not ranked:
        return StructureMaskSelection(False, "candidate_missing")

    ranked.sort(key=lambda item: item[0], reverse=True)
    score, source, mask, _stats = ranked[0]
    summaries = tuple(item[3] for item in ranked)
    if score < 1.55:
        return StructureMaskSelection(
            False,
            "quality_gate",
            source=source,
            mask=mask,
            score=score,
            candidates=summaries,
        )
    return StructureMaskSelection(
        True,
        "ok",
        source=source,
        mask=mask,
        score=score,
        candidates=summaries,
    )
