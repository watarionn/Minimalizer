from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module

import cv2
import numpy as np
from numpy.typing import NDArray

from minimalize_engine.v2.analysis_guidance import AnalysisGuidance, StructuralGuide


RTMLIB_STRUCTURAL_LABELS = (
    "torso",
    "left_upper_arm",
    "left_forearm",
    "right_upper_arm",
    "right_forearm",
    "left_thigh",
    "left_shin",
    "right_thigh",
    "right_shin",
)

_BODY17_ANCHORS = tuple(range(5, 17))
_CHANNEL_SEGMENTS: dict[str, tuple[tuple[int, int], ...]] = {
    "torso": ((5, 6), (11, 12), (5, 11), (6, 12)),
    "left_upper_arm": ((5, 7),),
    "left_forearm": ((7, 9),),
    "right_upper_arm": ((6, 8),),
    "right_forearm": ((8, 10),),
    "left_thigh": ((11, 13),),
    "left_shin": ((13, 15),),
    "right_thigh": ((12, 14),),
    "right_shin": ((14, 16),),
}


@dataclass(frozen=True, slots=True)
class RtmlibStructuralConfig:
    model_name: str = "wholebody-balanced"
    provider: str = "rtmlib"
    mode: str = "balanced"
    backend: str = "onnxruntime"
    device: str = "cpu"
    visibility_threshold: float = 0.30
    duplicate_distance_ratio: float = 0.025
    duplicate_min_common_joints: int = 6
    subject_threshold: float = 0.50
    corridor_radius_ratio: float = 0.02
    min_corridor_radius_px: float = 2.0
    max_corridor_radius_px: float = 16.0
    subject_weight: float = 0.50
    confidence_weight: float = 0.40
    bbox_area_weight: float = 0.10

    def __post_init__(self) -> None:
        if not self.model_name or not self.provider or not self.mode or not self.backend or not self.device:
            raise ValueError("rtmlib model/provider/runtime metadata must be non-empty")
        for name in ("visibility_threshold", "duplicate_distance_ratio", "subject_threshold", "corridor_radius_ratio"):
            value = float(getattr(self, name))
            if not np.isfinite(value) or not 0.0 < value <= 1.0:
                raise ValueError(f"{name} must be finite and within (0, 1]")
        if self.duplicate_min_common_joints < 2 or self.duplicate_min_common_joints > 17:
            raise ValueError("duplicate_min_common_joints must be within [2, 17]")
        if (
            not np.isfinite(self.min_corridor_radius_px)
            or not np.isfinite(self.max_corridor_radius_px)
            or self.min_corridor_radius_px <= 0.0
            or self.max_corridor_radius_px < self.min_corridor_radius_px
        ):
            raise ValueError("corridor radius bounds must be finite, positive, and ordered")
        weights = (self.subject_weight, self.confidence_weight, self.bbox_area_weight)
        if any(not np.isfinite(value) or value < 0.0 for value in weights) or sum(weights) <= 0.0:
            raise ValueError("selection weights must be finite, non-negative, and not all zero")


@dataclass(frozen=True, slots=True)
class SkeletonSelection:
    person_index: int
    keypoints: NDArray[np.float32]
    scores: NDArray[np.float32]
    quality: float
    duplicate_indices: tuple[int, ...]


def _load_rtmlib():
    try:
        return import_module("rtmlib")
    except ImportError as exc:
        raise RuntimeError(
            "rtmlib is optional; install it in the isolated pose evaluation/runtime environment"
        ) from exc


def create_rtmlib_wholebody(config: RtmlibStructuralConfig | None = None):
    cfg = config or RtmlibStructuralConfig()
    wholebody = getattr(_load_rtmlib(), "Wholebody")
    return wholebody(
        to_openpose=False,
        mode=cfg.mode,
        backend=cfg.backend,
        device=cfg.device,
    )


def _validate_source_rgb(source_rgb: NDArray[np.uint8]) -> NDArray[np.uint8]:
    source = np.asarray(source_rgb)
    if source.dtype != np.uint8 or source.ndim != 3 or source.shape[2] != 3:
        raise ValueError("source_rgb must be uint8 with shape (H, W, 3)")
    return source


def _validate_subject_prob(
    subject_prob: NDArray[np.float32] | None,
    source_shape: tuple[int, int],
) -> NDArray[np.float32] | None:
    if subject_prob is None:
        return None
    value = np.asarray(subject_prob)
    if value.dtype != np.float32 or value.shape != source_shape:
        raise ValueError("subject_prob must be float32 and match source resolution")
    if not np.all(np.isfinite(value)) or np.any((value < 0.0) | (value > 1.0)):
        raise ValueError("subject_prob must be finite and within [0, 1]")
    return value


def _normalize_people(
    keypoints,
    scores,
) -> tuple[NDArray[np.float32], NDArray[np.float32]]:
    k = np.asarray(keypoints, dtype=np.float32)
    s = np.asarray(scores, dtype=np.float32)
    if k.ndim == 2:
        k = k[None, ...]
    if s.ndim == 1:
        s = s[None, ...]
    if s.ndim == 3 and s.shape[-1] == 1:
        s = s[..., 0]
    if k.ndim != 3 or k.shape[2] < 2 or s.ndim != 2:
        raise ValueError("rtmlib pose arrays must have shapes (P, K, 2+) and (P, K)")
    if k.shape[:2] != s.shape or k.shape[1] < 17:
        raise ValueError("rtmlib pose arrays must align and contain at least BODY17 keypoints")
    body_k = np.array(k[:, :17, :2], dtype=np.float32, copy=True)
    body_s = np.array(s[:, :17], dtype=np.float32, copy=True)
    invalid_xy = ~np.all(np.isfinite(body_k), axis=2)
    body_s[~np.isfinite(body_s) | invalid_xy] = 0.0
    np.clip(body_s, 0.0, 1.0, out=body_s)
    body_k[~np.isfinite(body_k)] = 0.0
    return body_k, body_s


def _bbox_area_ratio(
    keypoints: NDArray[np.float32],
    scores: NDArray[np.float32],
    *,
    source_shape: tuple[int, int],
    threshold: float,
) -> float:
    visible = scores >= threshold
    if int(visible.sum()) < 2:
        return 0.0
    points = keypoints[visible]
    width = max(float(points[:, 0].max() - points[:, 0].min()), 0.0)
    height = max(float(points[:, 1].max() - points[:, 1].min()), 0.0)
    image_area = float(source_shape[0] * source_shape[1])
    return float(np.clip((width * height) / max(image_area, 1.0), 0.0, 1.0))


def _subject_support(
    keypoints: NDArray[np.float32],
    scores: NDArray[np.float32],
    subject_prob: NDArray[np.float32] | None,
    *,
    threshold: float,
) -> float:
    if subject_prob is None:
        return 0.0
    visible = scores >= threshold
    if not np.any(visible):
        return 0.0
    height, width = subject_prob.shape
    points = keypoints[visible]
    xs = np.clip(np.rint(points[:, 0]).astype(np.int64), 0, width - 1)
    ys = np.clip(np.rint(points[:, 1]).astype(np.int64), 0, height - 1)
    return float(np.mean(subject_prob[ys, xs]))


def _person_quality(
    keypoints: NDArray[np.float32],
    scores: NDArray[np.float32],
    *,
    source_shape: tuple[int, int],
    subject_prob: NDArray[np.float32] | None,
    config: RtmlibStructuralConfig,
) -> tuple[float, float, float]:
    anchor_scores = scores[list(_BODY17_ANCHORS)]
    confidence = float(np.mean(anchor_scores))
    area = _bbox_area_ratio(
        keypoints[list(_BODY17_ANCHORS)],
        anchor_scores,
        source_shape=source_shape,
        threshold=config.visibility_threshold,
    )
    subject = _subject_support(
        keypoints[list(_BODY17_ANCHORS)],
        anchor_scores,
        subject_prob,
        threshold=config.visibility_threshold,
    )
    weights = [config.confidence_weight, config.bbox_area_weight]
    values = [confidence, area]
    if subject_prob is not None:
        weights.insert(0, config.subject_weight)
        values.insert(0, subject)
    total_weight = float(sum(weights))
    quality = float(sum(w * v for w, v in zip(weights, values, strict=True)) / total_weight)
    return quality, confidence, area


def _are_near_duplicate_skeletons(
    left_k: NDArray[np.float32],
    left_s: NDArray[np.float32],
    right_k: NDArray[np.float32],
    right_s: NDArray[np.float32],
    *,
    source_shape: tuple[int, int],
    config: RtmlibStructuralConfig,
) -> bool:
    common = (left_s >= config.visibility_threshold) & (right_s >= config.visibility_threshold)
    if int(common.sum()) < config.duplicate_min_common_joints:
        return False
    distances = np.linalg.norm(left_k[common] - right_k[common], axis=1)
    diagonal = float(np.hypot(source_shape[1], source_shape[0]))
    normalized_median = float(np.median(distances) / max(diagonal, 1.0))
    return normalized_median <= config.duplicate_distance_ratio


def select_primary_skeleton(
    keypoints,
    scores,
    *,
    source_shape: tuple[int, int],
    config: RtmlibStructuralConfig | None = None,
    subject_prob: NDArray[np.float32] | None = None,
) -> SkeletonSelection | None:
    cfg = config or RtmlibStructuralConfig()
    if source_shape[0] <= 0 or source_shape[1] <= 0:
        raise ValueError("source_shape must be positive")
    subject = _validate_subject_prob(subject_prob, source_shape)
    people_k, people_s = _normalize_people(keypoints, scores)
    if people_k.shape[0] == 0:
        return None

    ranked: list[tuple[float, float, float, int]] = []
    for index in range(people_k.shape[0]):
        quality, confidence, area = _person_quality(
            people_k[index],
            people_s[index],
            source_shape=source_shape,
            subject_prob=subject,
            config=cfg,
        )
        ranked.append((quality, confidence, area, index))
    ranked.sort(key=lambda item: (item[0], item[1], item[2], -item[3]), reverse=True)

    kept: list[int] = []
    suppressed: list[int] = []
    for _, _, _, index in ranked:
        if any(
            _are_near_duplicate_skeletons(
                people_k[index],
                people_s[index],
                people_k[other],
                people_s[other],
                source_shape=source_shape,
                config=cfg,
            )
            for other in kept
        ):
            suppressed.append(index)
        else:
            kept.append(index)

    if not kept:
        return None
    primary = kept[0]
    quality = next(item[0] for item in ranked if item[3] == primary)
    return SkeletonSelection(
        person_index=primary,
        keypoints=people_k[primary],
        scores=people_s[primary],
        quality=float(quality),
        duplicate_indices=tuple(sorted(suppressed)),
    )


def _subject_bbox_diagonal(
    subject_prob: NDArray[np.float32] | None,
    source_shape: tuple[int, int],
    *,
    threshold: float,
) -> float:
    if subject_prob is not None:
        ys, xs = np.where(subject_prob >= threshold)
        if xs.size:
            return float(np.hypot(xs.max() - xs.min() + 1, ys.max() - ys.min() + 1))
    return float(np.hypot(source_shape[1], source_shape[0]))


def _soft_segment(
    source_shape: tuple[int, int],
    start: NDArray[np.float32],
    end: NDArray[np.float32],
    *,
    confidence: float,
    radius: float,
) -> NDArray[np.float32]:
    height, width = source_shape
    seed = np.ones((height, width), dtype=np.uint8)
    x0 = int(np.clip(round(float(start[0])), 0, width - 1))
    y0 = int(np.clip(round(float(start[1])), 0, height - 1))
    x1 = int(np.clip(round(float(end[0])), 0, width - 1))
    y1 = int(np.clip(round(float(end[1])), 0, height - 1))
    cv2.line(seed, (x0, y0), (x1, y1), 0, 1, cv2.LINE_8)
    distance = cv2.distanceTransform(seed, cv2.DIST_L2, 3)
    support = np.exp(-0.5 * np.square(distance / max(radius, 1e-6)))
    support[distance > radius * 3.0] = 0.0
    return (support * float(confidence)).astype(np.float32)


def build_structural_guide_from_pose(
    keypoints,
    scores,
    *,
    source_shape: tuple[int, int],
    config: RtmlibStructuralConfig | None = None,
    subject_prob: NDArray[np.float32] | None = None,
) -> tuple[StructuralGuide, SkeletonSelection | None]:
    cfg = config or RtmlibStructuralConfig()
    subject = _validate_subject_prob(subject_prob, source_shape)
    selection = select_primary_skeleton(
        keypoints,
        scores,
        source_shape=source_shape,
        config=cfg,
        subject_prob=subject,
    )
    maps = np.zeros((len(RTMLIB_STRUCTURAL_LABELS), *source_shape), dtype=np.float32)
    if selection is not None:
        subject_diagonal = _subject_bbox_diagonal(
            subject,
            source_shape,
            threshold=cfg.subject_threshold,
        )
        radius = float(
            np.clip(
                subject_diagonal * cfg.corridor_radius_ratio,
                cfg.min_corridor_radius_px,
                cfg.max_corridor_radius_px,
            )
        )
        for channel_index, label in enumerate(RTMLIB_STRUCTURAL_LABELS):
            channel = maps[channel_index]
            for start_index, end_index in _CHANNEL_SEGMENTS[label]:
                endpoint_confidence = min(
                    float(selection.scores[start_index]),
                    float(selection.scores[end_index]),
                )
                if endpoint_confidence < cfg.visibility_threshold:
                    continue
                support = _soft_segment(
                    source_shape,
                    selection.keypoints[start_index],
                    selection.keypoints[end_index],
                    confidence=endpoint_confidence,
                    radius=radius,
                )
                np.maximum(channel, support, out=channel)
        if subject is not None:
            maps *= subject[None, ...]
    return (
        StructuralGuide(
            labels=RTMLIB_STRUCTURAL_LABELS,
            confidence_maps=maps,
            provider=cfg.provider,
            model=cfg.model_name,
        ),
        selection,
    )


def build_rtmlib_structural_guide(
    source_rgb: NDArray[np.uint8],
    *,
    config: RtmlibStructuralConfig | None = None,
    model=None,
    subject_prob: NDArray[np.float32] | None = None,
) -> tuple[StructuralGuide, SkeletonSelection | None]:
    cfg = config or RtmlibStructuralConfig()
    source = _validate_source_rgb(source_rgb)
    subject = _validate_subject_prob(subject_prob, source.shape[:2])
    active_model = model if model is not None else create_rtmlib_wholebody(cfg)
    source_bgr = np.ascontiguousarray(source[..., ::-1])
    output = active_model(source_bgr)
    if not isinstance(output, tuple) or len(output) != 2:
        raise ValueError("rtmlib Wholebody must return (keypoints, scores)")
    return build_structural_guide_from_pose(
        output[0],
        output[1],
        source_shape=source.shape[:2],
        config=cfg,
        subject_prob=subject,
    )


def attach_rtmlib_structure(
    source_rgb: NDArray[np.uint8],
    *,
    config: RtmlibStructuralConfig | None = None,
    base_guidance: AnalysisGuidance | None = None,
    model=None,
) -> tuple[AnalysisGuidance, SkeletonSelection | None]:
    base = base_guidance or AnalysisGuidance()
    structural, selection = build_rtmlib_structural_guide(
        source_rgb,
        config=config,
        model=model,
        subject_prob=base.subject_prob,
    )
    return (
        AnalysisGuidance(
            subject_prob=base.subject_prob,
            subject_confidence=base.subject_confidence,
            alpha=base.alpha,
            semantic=base.semantic,
            structural=structural,
            line=base.line,
            subject_provider=base.subject_provider,
            subject_model=base.subject_model,
        ),
        selection,
    )
