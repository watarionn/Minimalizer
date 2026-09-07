from pathlib import Path

from minimalize_engine import MinimalizeConfig, minimalize


def _poly_area(points):
    if len(points) < 3:
        return 0.0
    total = 0.0
    for i, (x1, y1) in enumerate(points):
        x2, y2 = points[(i + 1) % len(points)]
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0


def test_major_polygons_do_not_collapse_to_triangles():
    path = Path(__file__).parents[1] / "examples" / "input.webp"
    if not path.exists():
        return

    scene = minimalize(path, MinimalizeConfig.from_level(4, line_mode="none", enable_auto_retry=False))
    scene_area = scene.width * scene.height

    for shape in scene.shapes:
        if shape.shape_type != "polygon":
            continue
        area = _poly_area(shape.points)
        if area / scene_area >= 0.03:
            assert len(shape.points) >= 4
