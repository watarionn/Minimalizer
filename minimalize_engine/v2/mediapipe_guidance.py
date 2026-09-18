from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from minimalize_engine.v2.analysis_guidance import AnalysisGuidance, SemanticGuide


MEDIAPIPE_MULTICLASS_LABELS = (
    "background",
    "hair",
    "body-skin",
    "face-skin",
    "clothes",
    "others",
)


@dataclass(frozen=True, slots=True)
class MediaPipeSemanticConfig:
    model_path: str
    model_name: str = "selfie_multiclass_256x256"
    provider: str = "mediapipe"
    foreground_only: bool = True
    def __post_init__(self) -> None:
        if not self.model_path:
            raise ValueError("MediaPipe model_path must be non-empty")
        if not self.model_name or not self.provider:
            raise ValueError("MediaPipe model_name/provider must be non-empty")


def _load_mediapipe():
    try:
        return import_module("mediapipe")
    except ImportError as exc:
        raise RuntimeError(
            "mediapipe is optional; install it in the isolated semantic evaluation/runtime environment"
        ) from exc


def create_mediapipe_segmenter(config: MediaPipeSemanticConfig):
    model_path = Path(config.model_path)
    if not model_path.is_file():
        raise ValueError(f"MediaPipe model file does not exist: {model_path}")
    mp = _load_mediapipe()
    tasks_python = import_module("mediapipe.tasks.python")
    vision = import_module("mediapipe.tasks.python.vision")
    options = vision.ImageSegmenterOptions(
        base_options=tasks_python.BaseOptions(model_asset_path=str(model_path)),
        running_mode=vision.RunningMode.IMAGE,
        output_confidence_masks=True,
        output_category_mask=False,
    )
    return vision.ImageSegmenter.create_from_options(options)


def _extract_confidence_maps(result: Any, source_shape: tuple[int, int]) -> NDArray[np.float32]:
    masks = getattr(result, "confidence_masks", None)
    if masks is None or len(masks) != len(MEDIAPIPE_MULTICLASS_LABELS):
        raise ValueError("MediaPipe result must contain six confidence masks")
    channels: list[NDArray[np.float32]] = []
    for mask in masks:
        array = np.asarray(mask.numpy_view(), dtype=np.float32)
        if array.ndim == 3 and array.shape[2] == 1:
            array = array[..., 0]
        if array.shape != source_shape:
            raise ValueError(f"MediaPipe confidence mask must have source shape {source_shape}")
        channels.append(np.clip(array, 0.0, 1.0).astype(np.float32))
    return np.stack(channels, axis=0)


def _foreground_semantic_maps(
    confidence_maps: NDArray[np.float32],
    *,
    subject_prob: NDArray[np.float32] | None,
) -> tuple[tuple[str, ...], NDArray[np.float32]]:
    maps = confidence_maps[1:].copy()
    if subject_prob is not None:
        if subject_prob.dtype != np.float32 or subject_prob.shape != maps.shape[1:]:
            raise ValueError("subject_prob must be float32 and match the source shape")
        maps *= np.clip(subject_prob, 0.0, 1.0)[None, ...]
    return MEDIAPIPE_MULTICLASS_LABELS[1:], maps.astype(np.float32)


def build_mediapipe_semantic_guide(
    source_rgb: NDArray[np.uint8],
    *,
    config: MediaPipeSemanticConfig,
    segmenter=None,
    subject_prob: NDArray[np.float32] | None = None,
) -> SemanticGuide:
    source = np.asarray(source_rgb)
    if source.dtype != np.uint8 or source.ndim != 3 or source.shape[2] != 3:
        raise ValueError("source_rgb must be uint8 with shape (H, W, 3)")
    mp = _load_mediapipe()
    active_segmenter = segmenter if segmenter is not None else create_mediapipe_segmenter(config)
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(source))
    result = active_segmenter.segment(image)
    maps = _extract_confidence_maps(result, source.shape[:2])
    if config.foreground_only:
        labels, maps = _foreground_semantic_maps(maps, subject_prob=subject_prob)
    else:
        labels = MEDIAPIPE_MULTICLASS_LABELS
    return SemanticGuide(
        labels=tuple(labels),
        confidence_maps=maps.astype(np.float32),
        provider=config.provider,
        model=config.model_name,
    )


def attach_mediapipe_semantics(
    source_rgb: NDArray[np.uint8],
    *,
    config: MediaPipeSemanticConfig,
    base_guidance: AnalysisGuidance | None = None,
    segmenter=None,
) -> AnalysisGuidance:
    base = base_guidance or AnalysisGuidance()
    semantic = build_mediapipe_semantic_guide(
        source_rgb,
        config=config,
        segmenter=segmenter,
        subject_prob=base.subject_prob,
    )
    return AnalysisGuidance(
        subject_prob=base.subject_prob,
        subject_confidence=base.subject_confidence,
        semantic=semantic,
        subject_provider=base.subject_provider,
        subject_model=base.subject_model,
    )
