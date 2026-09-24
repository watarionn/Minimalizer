from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from minimalize_engine.v2.analysis_guidance import AnalysisGuidance


@dataclass(frozen=True, slots=True)
class RembgGuidanceConfig:
    model: str = "isnet-anime"
    confidence_power: float = 2.0

    def __post_init__(self) -> None:
        if not self.model:
            raise ValueError("rembg model must be non-empty")
        if not np.isfinite(self.confidence_power) or self.confidence_power < 1.0:
            raise ValueError("rembg confidence_power must be finite and at least 1.0")


def subject_confidence_from_probability(
    probability: NDArray[np.float32],
    *,
    power: float = 2.0,
) -> NDArray[np.float32]:
    """Calibrate rembg certainty so only very strong evidence becomes a hard barrier."""
    if not np.isfinite(power) or power < 1.0:
        raise ValueError("confidence power must be finite and at least 1.0")
    linear = np.clip(2.0 * np.abs(probability - 0.5), 0.0, 1.0)
    return np.power(linear, power).astype(np.float32)


def _mask_to_probability(mask: Any, source_shape: tuple[int, int]) -> NDArray[np.float32]:
    if isinstance(mask, Image.Image):
        array = np.asarray(mask.convert("L"), dtype=np.float32)
    else:
        array = np.asarray(mask)
        if array.ndim == 3 and array.shape[2] == 4:
            array = array[..., 3]
        elif array.ndim == 3 and array.shape[2] == 1:
            array = array[..., 0]
        array = array.astype(np.float32, copy=False)
    if array.shape != source_shape:
        raise ValueError(f"rembg mask must have source shape {source_shape}")
    if array.size == 0 or not np.all(np.isfinite(array)):
        raise ValueError("rembg mask must be non-empty and finite")
    maximum = float(array.max())
    if maximum > 1.0:
        array = array / 255.0
    probability = np.clip(array, 0.0, 1.0).astype(np.float32)
    return probability


def _load_rembg():
    try:
        module = import_module("rembg")
    except ImportError as exc:
        raise RuntimeError(
            "rembg is optional; install the isolated rembg evaluation/runtime dependency"
        ) from exc
    return module


def create_rembg_session(
    config: RembgGuidanceConfig | None = None,
    *,
    sess_opts=None,
):
    active = config or RembgGuidanceConfig()
    rembg = _load_rembg()
    return rembg.new_session(active.model, sess_opts=sess_opts)


def build_rembg_guidance_from_mask(
    mask: Any,
    source_shape: tuple[int, int],
    *,
    config: RembgGuidanceConfig | None = None,
) -> AnalysisGuidance:
    active = config or RembgGuidanceConfig()
    probability = _mask_to_probability(mask, source_shape)
    confidence = subject_confidence_from_probability(probability, power=active.confidence_power)
    return AnalysisGuidance(
        subject_prob=probability,
        subject_confidence=confidence,
        subject_provider="rembg",
        subject_model=active.model,
    )


def build_rembg_guidance(
    source_rgb: NDArray[np.uint8],
    *,
    config: RembgGuidanceConfig | None = None,
    session=None,
) -> AnalysisGuidance:
    active = config or RembgGuidanceConfig()
    source = np.asarray(source_rgb)
    if source.dtype != np.uint8 or source.ndim != 3 or source.shape[2] != 3:
        raise ValueError("source_rgb must be uint8 with shape (H, W, 3)")
    rembg = _load_rembg()
    active_session = session if session is not None else rembg.new_session(active.model)
    mask = rembg.remove(Image.fromarray(source, mode="RGB"), session=active_session, only_mask=True)
    return build_rembg_guidance_from_mask(
        mask,
        source.shape[:2],
        config=active,
    )
