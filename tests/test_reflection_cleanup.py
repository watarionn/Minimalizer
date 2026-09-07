from pathlib import Path

from minimalize_engine import MinimalizeConfig, minimalize


def test_reflection_noise_is_limited():
    path = Path(__file__).parents[1] / "examples" / "input.webp"
    if not path.exists():
        return

    scene = minimalize(path, MinimalizeConfig.from_level(4, line_mode="none", enable_auto_retry=False))
    scene_area = scene.width * scene.height

    low_half_smallish = 0
    for shape in scene.shapes:
        if shape.shape_type == "line":
            continue

        if shape.shape_type == "rectangle":
            cy = (shape.y + shape.height / 2)
            area = shape.width * shape.height
        elif shape.shape_type == "circle":
            cy = shape.cy
            area = 3.14159 * shape.rx * shape.rx
        elif shape.shape_type == "ellipse":
            cy = shape.cy
            area = 3.14159 * shape.rx * shape.ry
        else:
            pts = shape.points
            cy = sum(y for _, y in pts) / len(pts)
            area = 0.0
            for i, (x1, y1) in enumerate(pts):
                x2, y2 = pts[(i + 1) % len(pts)]
                area += x1 * y2 - x2 * y1
            area = abs(area) / 2.0

        if cy > scene.height * 0.58 and area / scene_area < 0.004:
            low_half_smallish += 1

    assert low_half_smallish <= 28
