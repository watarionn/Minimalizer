from __future__ import annotations

from dataclasses import asdict, dataclass
from time import perf_counter
from typing import Mapping
import statistics

import numpy as np

from .pipeline import PipelineConfig, _minimalize_v2_impl
from .regression.compare import algorithm_digest

PERFORMANCE_SCHEMA_VERSION = "minimalizer-v2-performance-v1"

@dataclass(frozen=True, slots=True)
class V2PerformanceSample:
    wall_seconds: float
    phase_timings: Mapping[str, float]
    algorithm_digest: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

@dataclass(frozen=True, slots=True)
class V2PerformanceSummary:
    mean_wall_seconds: float
    mean_phase_seconds: Mapping[str, float]
    phase_share: Mapping[str, float]
    samples: tuple[V2PerformanceSample, ...]


def profile_v2_rgb(source_rgb: np.ndarray, *, preset: str = "minimal", repeats: int = 1, config: PipelineConfig | None = None) -> V2PerformanceSummary:
    if repeats <= 0:
        raise ValueError("repeats must be positive")
    active = config or PipelineConfig()
    samples: list[V2PerformanceSample] = []
    for _ in range(repeats):
        timings: dict[str, float] = {}
        def observer(name: str, seconds: float) -> None:
            timings[name] = timings.get(name, 0.0) + seconds
        started = perf_counter()
        result = _minimalize_v2_impl(source_rgb, presets=(preset,), config=active, characteristic=None, observer=observer)
        wall = perf_counter() - started
        samples.append(V2PerformanceSample(wall, dict(timings), algorithm_digest(result, preset)))
    digests = {sample.algorithm_digest for sample in samples}
    if len(digests) != 1:
        raise RuntimeError("profiling repeats changed the algorithm digest")
    names = sorted(set().union(*(sample.phase_timings for sample in samples)))
    mean_wall = statistics.mean(sample.wall_seconds for sample in samples)
    means = {name: statistics.mean(sample.phase_timings.get(name, 0.0) for sample in samples) for name in names}
    shares = {name: value / mean_wall for name, value in means.items()}
    return V2PerformanceSummary(mean_wall, means, shares, tuple(samples))
