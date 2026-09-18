from __future__ import annotations

import hashlib
import json
from dataclasses import fields

import numpy as np

from minimalize_engine.v2.pipeline import MinimalizerV2Result
from minimalize_engine.v2.regression.types import MetricDelta, RegressionMetrics


def _update_array(digest, value: np.ndarray | None) -> None:
    if value is None:
        digest.update(b"<none>")
        return
    array = np.ascontiguousarray(value)
    digest.update(str(array.dtype).encode("ascii"))
    digest.update(str(array.shape).encode("ascii"))
    digest.update(array.tobytes())


def algorithm_digest(result: MinimalizerV2Result, preset: str) -> str:
    pipeline = result.presets[preset]
    digest = hashlib.sha256()
    digest.update(preset.encode("utf-8"))
    digest.update(np.asarray(pipeline.selection.labels, dtype=np.int32).tobytes())
    for chain_id in sorted(pipeline.contour.boundary_graph.chains):
        chain = pipeline.contour.boundary_graph.chains[chain_id]
        digest.update(f"chain:{chain_id}:{chain.regions}".encode("utf-8"))
        _update_array(digest, chain.points)
    for region_id in sorted(pipeline.primitives.primitives):
        selected = pipeline.primitives.primitives[region_id].selected
        geometry = selected.geometry
        digest.update(f"primitive:{region_id}:{geometry.kind}".encode("utf-8"))
        for loop in geometry.loops:
            _update_array(digest, loop)
        _update_array(digest, geometry.points)
        digest.update(repr((geometry.center, geometry.axes, geometry.angle_deg)).encode("ascii"))
        digest.update(repr((geometry.segment_start, geometry.segment_end, geometry.radius)).encode("ascii"))
    for palette_id in sorted(pipeline.palette.entries):
        entry = pipeline.palette.entries[palette_id]
        digest.update(
            repr((palette_id, entry.member_regions, entry.rgb, entry.anchor_ids)).encode("utf-8")
        )
        _update_array(digest, entry.lab)
    for region_id in sorted(pipeline.detail_budget.actions):
        digest.update(
            repr(
                (
                    region_id,
                    pipeline.detail_budget.actions[region_id],
                    pipeline.detail_budget.effective_palette_by_region[region_id],
                    pipeline.detail_budget.fallback_region_by_region[region_id],
                )
            ).encode("utf-8")
        )
    for shape in pipeline.scene.shapes:
        digest.update(
            repr((shape.region_id, shape.palette_id, shape.visible)).encode("utf-8")
        )
    for overlay in sorted(pipeline.scene.facet_overlays, key=lambda item: item.region_id):
        digest.update(
            repr((
                overlay.region_id, overlay.rgb, overlay.line_a, overlay.line_b,
                overlay.line_c, overlay.variant_side,
            )).encode("utf-8")
        )
    return digest.hexdigest()


def metrics_as_scalars(metrics: RegressionMetrics) -> dict[str, float]:
    result: dict[str, float] = {}
    for item in fields(metrics):
        if item.name == "phase_timings":
            continue
        value = getattr(metrics, item.name)
        if value is None:
            continue
        if isinstance(value, (int, float, np.integer, np.floating)):
            result[item.name] = float(value)
    return result


def compare_metrics(
    current: RegressionMetrics,
    baseline: RegressionMetrics,
    *,
    performance_warning_factor: float = 1.5,
) -> tuple[MetricDelta, ...]:
    current_values = metrics_as_scalars(current)
    baseline_values = metrics_as_scalars(baseline)
    deltas: list[MetricDelta] = []
    for name in sorted(current_values.keys() & baseline_values.keys()):
        now = current_values[name]
        old = baseline_values[name]
        delta = now - old
        relative = None if abs(old) <= 1.0e-12 else delta / abs(old)
        severity = "ok"
        if name == "runtime_seconds" and old > 0.0 and now > old * performance_warning_factor:
            severity = "warning"
        deltas.append(MetricDelta(name, now, old, delta, relative, severity))
    return tuple(deltas)
