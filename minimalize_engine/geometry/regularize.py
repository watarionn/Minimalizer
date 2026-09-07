from __future__ import annotations
import math


def _distance_point_to_line(p, a, b):
    px, py = p
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    num = abs(dy * px - dx * py + bx * ay - by * ax)
    den = math.hypot(dx, dy)
    return num / max(den, 1e-6)


def simplify_collinear(points, tolerance=2.0):
    if len(points) <= 3:
        return points

    pts = points[:]
    changed = True
    while changed and len(pts) > 3:
        changed = False
        new_pts = []
        n = len(pts)
        for i in range(n):
            prev = pts[(i - 1) % n]
            cur = pts[i]
            nxt = pts[(i + 1) % n]
            d = _distance_point_to_line(cur, prev, nxt)
            if d <= tolerance:
                changed = True
                continue
            new_pts.append(cur)
        if len(new_pts) >= 3 and len(new_pts) < len(pts):
            pts = new_pts
        else:
            break
    return pts


def snap_axis_aligned(points, angle_threshold_deg=16.0, merge_tol=1.5):
    if len(points) < 3:
        return points

    pts = [list(p) for p in points]
    n = len(pts)
    thr = math.radians(angle_threshold_deg)

    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        ang = abs(math.atan2(y2 - y1, x2 - x1))
        ang = min(ang, abs(math.pi - ang))

        # Near-horizontal edge -> align y.
        if ang <= thr:
            target_y = (y1 + y2) / 2.0
            pts[i][1] = target_y
            pts[(i + 1) % n][1] = target_y

        # Near-vertical edge -> align x.
        if abs(ang - math.pi / 2) <= thr:
            target_x = (x1 + x2) / 2.0
            pts[i][0] = target_x
            pts[(i + 1) % n][0] = target_x

    out = [(float(x), float(y)) for x, y in pts]
    out = simplify_collinear(out, tolerance=merge_tol)
    return out


def flatten_lower_edge(points, bbox_bottom, y_blend=0.72):
    """
    For water / boat-like lower masses, keep the lower silhouette calmer by
    gently aligning the lowest vertices.
    """
    if len(points) < 3:
        return points
    ys = [p[1] for p in points]
    cutoff = min(max(ys), bbox_bottom) - (max(ys) - min(ys)) * (1 - y_blend)
    out = []
    lower = [y for y in ys if y >= cutoff]
    if not lower:
        return points
    target = sum(lower) / len(lower)
    for x, y in points:
        if y >= cutoff:
            out.append((x, target))
        else:
            out.append((x, y))
    return simplify_collinear(out, tolerance=2.0)


def fit_boat_polygon(bbox):
    x, y, w, h = bbox
    bottom = y + h - 1
    top = y + h * 0.34
    bow_inset = w * 0.10
    roof_inset = w * 0.22

    pts = [
        (x + bow_inset, bottom),
        (x + w - bow_inset, bottom),
        (x + w - roof_inset, top),
        (x + roof_inset, top),
    ]
    return [(float(px), float(py)) for px, py in pts]
