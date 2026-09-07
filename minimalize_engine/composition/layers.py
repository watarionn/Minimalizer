from __future__ import annotations

from ..models import Shape
from .layer_plan import LAYER_ORDER


def _approx_area(s: Shape):
    if s.shape_type == "rectangle":
        return (s.width or 0) * (s.height or 0)
    if s.shape_type == "circle":
        return 3.14159 * (s.rx or 0) ** 2
    if s.shape_type == "ellipse":
        return 3.14159 * (s.rx or 0) * (s.ry or 0)
    if s.shape_type == "polygon" and len(s.points) >= 3:
        area = 0.0
        pts = s.points
        for i in range(len(pts)):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % len(pts)]
            area += x1 * y2 - x2 * y1
        return abs(area) / 2
    return 0.0


def assign_layers(shapes: list[Shape]) -> list[Shape]:
    """
    Compose by semantic layer first, size second.

    Macro underlays sit behind detail shapes; accents and structural lines sit
    on top. Within a layer, larger shapes are drawn first so smaller detail can
    remain visible.
    """
    ordered = sorted(
        shapes,
        key=lambda s: (
            LAYER_ORDER.get(s.layer_name, 30),
            -_approx_area(s),
            s.importance,
        ),
    )

    layer_offsets = {name: rank * 1000 for name, rank in LAYER_ORDER.items()}
    counters: dict[str, int] = {}
    for s in ordered:
        layer = s.layer_name or "midground"
        counters[layer] = counters.get(layer, 0) + 1
        s.z_index = layer_offsets.get(layer, 30000) + counters[layer]
    return ordered
