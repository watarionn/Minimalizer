from __future__ import annotations
from ..models import Shape


def apply_padding(shapes: list[Shape], width: int, height: int, ratio: float):
    ratio = max(0.0, min(0.40, ratio))
    if ratio == 0:
        return shapes

    sx = sy = 1.0 - 2.0 * ratio
    ox, oy = width * ratio, height * ratio

    for s in shapes:
        if s.shape_type == "rectangle":
            s.x = ox + s.x * sx
            s.y = oy + s.y * sy
            s.width *= sx
            s.height *= sy
        elif s.shape_type in {"circle", "ellipse"}:
            s.cx = ox + s.cx * sx
            s.cy = oy + s.cy * sy
            s.rx *= sx
            s.ry *= sy
        else:
            s.points = [(ox + x * sx, oy + y * sy) for x, y in s.points]
        s.stroke_width *= (sx + sy) / 2
    return shapes
