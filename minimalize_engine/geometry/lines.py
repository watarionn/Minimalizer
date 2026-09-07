from __future__ import annotations
import cv2
import numpy as np
from ..models import Shape


def detect_structural_lines(image_rgb: np.ndarray, mode: str, starting_id: int = 100000) -> list[Shape]:
    if mode == "none":
        return []

    h, w = image_rgb.shape[:2]
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 80, 170)

    if mode == "standard":
        min_len_ratio, max_gap_ratio, threshold = 0.04, 0.015, 45
    else:
        min_len_ratio, max_gap_ratio, threshold = 0.07, 0.010, 60

    min_len = max(10, int(min(h, w) * min_len_ratio))
    max_gap = max(3, int(min(h, w) * max_gap_ratio))

    lines = cv2.HoughLinesP(
        edges, 1, np.pi / 180, threshold=threshold,
        minLineLength=min_len, maxLineGap=max_gap
    )
    if lines is None:
        return []

    candidates = []
    for raw in lines[:120]:
        x1, y1, x2, y2 = map(int, raw[0])
        length = float(np.hypot(x2 - x1, y2 - y1))
        angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1))) % 180
        # Minimal aesthetic: favor near-horizontal/vertical structural lines.
        axial = min(abs(angle), abs(angle - 90), abs(angle - 180))
        if axial > 12:
            continue

        # Ignore likely source-photo frame edges. They are long, nearly axial,
        # and sit very close to the image boundary.
        xmid = (x1 + x2) / 2.0
        ymid = (y1 + y2) / 2.0
        near_top_or_bottom = ymid < h * 0.04 or ymid > h * 0.96
        near_left_or_right = xmid < w * 0.04 or xmid > w * 0.96
        mostly_horizontal = min(abs(angle), abs(angle - 180)) <= 8
        mostly_vertical = abs(angle - 90) <= 8

        if mostly_horizontal and near_top_or_bottom and length > w * 0.25:
            continue
        if mostly_vertical and near_left_or_right and length > h * 0.25:
            continue

        candidates.append((length, x1, y1, x2, y2))

    candidates.sort(reverse=True)
    limit = 14 if mode == "standard" else 8
    shapes = []
    for i, (_, x1, y1, x2, y2) in enumerate(candidates[:limit]):
        shapes.append(
            Shape(
                id=starting_id + i,
                shape_type="line",
                fill_color=None,
                stroke_color=(35, 35, 30),
                stroke_width=max(1.0, min(h, w) * 0.0022),
                points=[(x1, y1), (x2, y2)],
                z_index=1000 + i,
                importance=0.5,
                source_role="line",
                layer_name="lines",
            )
        )
    return shapes
