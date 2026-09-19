from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from numpy.typing import NDArray

from minimalize_engine.v2.analysis_guidance import AnalysisGuidance, LineGuide


DEEPLSD_INFERENCE_CONFIG = {
    "detect_lines": True,
    "line_detection_params": {
        "merge": False,
        "filtering": True,
        "grad_thresh": 3,
        "grad_nfa": True,
    },
}


@dataclass(frozen=True, slots=True)
class DeepLsdLineConfig:
    weights_path: str | None = None
    model_name: str = "deeplsd_md"
    provider: str = "deeplsd"
    device: str = "auto"
    min_length_diagonal_ratio: float = 0.13
    support_radius_diagonal_ratio: float = 0.003
    min_support_radius_px: float = 1.0
    max_support_radius_px: float = 4.0

    def __post_init__(self) -> None:
        if not self.model_name or not self.provider or not self.device:
            raise ValueError("DeepLSD model/provider/device metadata must be non-empty")
        for name in ("min_length_diagonal_ratio", "support_radius_diagonal_ratio"):
            value = float(getattr(self, name))
            if not np.isfinite(value) or not 0.0 < value <= 1.0:
                raise ValueError(f"{name} must be finite and within (0, 1]")
        if (
            not np.isfinite(self.min_support_radius_px)
            or not np.isfinite(self.max_support_radius_px)
            or self.min_support_radius_px <= 0.0
            or self.max_support_radius_px < self.min_support_radius_px
        ):
            raise ValueError("support radius bounds must be finite, positive, and ordered")


@dataclass(frozen=True, slots=True)
class LineDetectionSummary:
    source_shape: tuple[int, int]
    raw_line_count: int
    clipped_line_count: int
    accepted_line_count: int
    outside_endpoint_line_count: int
    accepted_lines: NDArray[np.float32]

    def __post_init__(self) -> None:
        if self.source_shape[0] <= 0 or self.source_shape[1] <= 0:
            raise ValueError("source_shape must be positive")
        counts = (
            self.raw_line_count,
            self.clipped_line_count,
            self.accepted_line_count,
            self.outside_endpoint_line_count,
        )
        if any(value < 0 for value in counts):
            raise ValueError("line counts must be non-negative")
        if self.accepted_line_count > self.clipped_line_count:
            raise ValueError("accepted lines cannot exceed clipped lines")
        lines = np.array(self.accepted_lines, dtype=np.float32, copy=True)
        if lines.shape != (self.accepted_line_count, 2, 2):
            raise ValueError("accepted_lines must have shape (accepted_line_count, 2, 2)")
        if not np.all(np.isfinite(lines)):
            raise ValueError("accepted_lines must be finite")
        lines.flags.writeable = False
        object.__setattr__(self, "accepted_lines", lines)


@dataclass(slots=True)
class DeepLsdRuntime:
    model: Any
    torch_module: Any
    device: Any

    def infer(self, gray: NDArray[np.uint8]) -> NDArray[np.float64]:
        torch = self.torch_module
        tensor = torch.tensor(
            gray,
            dtype=torch.float32,
            device=self.device,
        )[None, None] / 255.0
        if getattr(self.device, "type", str(self.device)) == "cuda":
            torch.cuda.synchronize(self.device)
        with torch.no_grad():
            output = self.model({"image": tensor})
        if getattr(self.device, "type", str(self.device)) == "cuda":
            torch.cuda.synchronize(self.device)
        if "lines" not in output:
            raise ValueError("DeepLSD output must contain lines")
        return _normalize_segments(output["lines"][0])


def _load_torch():
    try:
        return import_module("torch")
    except ImportError as exc:
        raise RuntimeError(
            "torch is optional; install it in the isolated DeepLSD runtime environment"
        ) from exc


def _load_deeplsd_class():
    try:
        module = import_module("deeplsd.models.deeplsd_inference")
    except ImportError as exc:
        raise RuntimeError(
            "DeepLSD is optional; install it in the isolated line evaluation/runtime environment"
        ) from exc
    return getattr(module, "DeepLSD")


def create_deeplsd_runtime(
    config: DeepLsdLineConfig,
) -> DeepLsdRuntime:
    if not config.weights_path:
        raise ValueError("DeepLSD weights_path is required to create the runtime")
    weights = Path(config.weights_path)
    if not weights.is_file():
        raise ValueError(f"DeepLSD weights file does not exist: {weights}")
    torch = _load_torch()
    device_name = config.device
    if device_name == "auto":
        device_name = "cuda" if torch.cuda.is_available() else "cpu"
    device = torch.device(device_name)
    checkpoint = torch.load(weights, map_location="cpu", weights_only=False)
    model = _load_deeplsd_class()(DEEPLSD_INFERENCE_CONFIG)
    if "model" not in checkpoint:
        raise ValueError("DeepLSD checkpoint must contain a model state")
    model.load_state_dict(checkpoint["model"])
    model = model.to(device).eval()
    return DeepLsdRuntime(model=model, torch_module=torch, device=device)


def _validate_source_rgb(source_rgb: NDArray[np.uint8]) -> NDArray[np.uint8]:
    source = np.asarray(source_rgb)
    if source.dtype != np.uint8 or source.ndim != 3 or source.shape[2] != 3:
        raise ValueError("source_rgb must be uint8 with shape (H, W, 3)")
    return source


def _normalize_segments(lines) -> NDArray[np.float64]:
    value = np.asarray(lines, dtype=np.float64)
    if value.size == 0:
        return np.empty((0, 2, 2), dtype=np.float64)
    if value.ndim != 3 or value.shape[1:] != (2, 2):
        raise ValueError("line segments must have shape (N, 2, 2)")
    if not np.all(np.isfinite(value)):
        raise ValueError("line segments must be finite")
    return value


def _clip_segments(
    lines: NDArray[np.float64],
    *,
    source_shape: tuple[int, int],
) -> tuple[NDArray[np.float64], int]:
    height, width = source_shape
    clipped: list[list[list[float]]] = []
    outside_count = 0
    for line in lines:
        p0f, p1f = line
        outside = (
            p0f[0] < 0.0
            or p0f[0] > width - 1
            or p0f[1] < 0.0
            or p0f[1] > height - 1
            or p1f[0] < 0.0
            or p1f[0] > width - 1
            or p1f[1] < 0.0
            or p1f[1] > height - 1
        )
        outside_count += int(outside)
        p0 = tuple(np.rint(p0f).astype(int))
        p1 = tuple(np.rint(p1f).astype(int))
        ok, q0, q1 = cv2.clipLine((0, 0, width, height), p0, p1)
        if ok:
            clipped.append(
                [
                    [float(q0[0]), float(q0[1])],
                    [float(q1[0]), float(q1[1])],
                ]
            )
    if not clipped:
        return np.empty((0, 2, 2), dtype=np.float64), outside_count
    return np.asarray(clipped, dtype=np.float64), outside_count


def _segment_lengths(lines: NDArray[np.float64]) -> NDArray[np.float64]:
    if len(lines) == 0:
        return np.empty((0,), dtype=np.float64)
    return np.linalg.norm(lines[:, 1] - lines[:, 0], axis=1)


def _soft_line_support(
    source_shape: tuple[int, int],
    lines: NDArray[np.float64],
    *,
    radius: float,
) -> NDArray[np.float32]:
    height, width = source_shape
    if len(lines) == 0:
        return np.zeros((height, width), dtype=np.float32)
    seed = np.ones((height, width), dtype=np.uint8)
    for line in lines:
        p0 = tuple(np.rint(line[0]).astype(int))
        p1 = tuple(np.rint(line[1]).astype(int))
        cv2.line(seed, p0, p1, 0, 1, cv2.LINE_8)
    distance = cv2.distanceTransform(seed, cv2.DIST_L2, 3)
    support = np.exp(-0.5 * np.square(distance / max(radius, 1e-6)))
    support[distance > radius * 3.0] = 0.0
    return np.clip(support, 0.0, 1.0).astype(np.float32)


def build_line_guide_from_segments(
    lines,
    *,
    source_shape: tuple[int, int],
    config: DeepLsdLineConfig | None = None,
) -> tuple[LineGuide, LineDetectionSummary]:
    cfg = config or DeepLsdLineConfig()
    height, width = source_shape
    if height <= 0 or width <= 0:
        raise ValueError("source_shape must be positive")
    raw = _normalize_segments(lines)
    clipped, outside_count = _clip_segments(raw, source_shape=source_shape)
    diagonal = float(np.hypot(width, height))
    min_length = diagonal * cfg.min_length_diagonal_ratio
    lengths = _segment_lengths(clipped)
    accepted = clipped[lengths >= min_length] if len(clipped) else clipped
    radius = float(
        np.clip(
            diagonal * cfg.support_radius_diagonal_ratio,
            cfg.min_support_radius_px,
            cfg.max_support_radius_px,
        )
    )
    support = _soft_line_support(source_shape, accepted, radius=radius)
    guide = LineGuide(
        support_map=support,
        provider=cfg.provider,
        model=cfg.model_name,
        min_length_diagonal_ratio=cfg.min_length_diagonal_ratio,
    )
    summary = LineDetectionSummary(
        source_shape=source_shape,
        raw_line_count=len(raw),
        clipped_line_count=len(clipped),
        accepted_line_count=len(accepted),
        outside_endpoint_line_count=outside_count,
        accepted_lines=accepted.astype(np.float32, copy=False),
    )
    return guide, summary


def build_deeplsd_line_guide(
    source_rgb: NDArray[np.uint8],
    *,
    config: DeepLsdLineConfig,
    runtime: Any | None = None,
) -> tuple[LineGuide, LineDetectionSummary]:
    source = _validate_source_rgb(source_rgb)
    gray = cv2.cvtColor(source, cv2.COLOR_RGB2GRAY)
    active_runtime = runtime if runtime is not None else create_deeplsd_runtime(config)
    if not hasattr(active_runtime, "infer"):
        raise ValueError("DeepLSD runtime must provide infer(gray)")
    lines = active_runtime.infer(gray)
    return build_line_guide_from_segments(
        lines,
        source_shape=source.shape[:2],
        config=config,
    )


def attach_deeplsd_lines(
    source_rgb: NDArray[np.uint8],
    *,
    config: DeepLsdLineConfig,
    base_guidance: AnalysisGuidance | None = None,
    runtime: Any | None = None,
) -> tuple[AnalysisGuidance, LineDetectionSummary]:
    base = base_guidance or AnalysisGuidance()
    line, summary = build_deeplsd_line_guide(
        source_rgb,
        config=config,
        runtime=runtime,
    )
    return (
        AnalysisGuidance(
            subject_prob=base.subject_prob,
            subject_confidence=base.subject_confidence,
            semantic=base.semantic,
            structural=base.structural,
            line=line,
            subject_provider=base.subject_provider,
            subject_model=base.subject_model,
        ),
        summary,
    )
