from __future__ import annotations
from pathlib import Path
from html import escape
from ..models import Scene, Shape


def _rgb(c):
    return f"rgb({c[0]},{c[1]},{c[2]})"


def scene_to_svg(scene: Scene) -> str:
    bg = ""
    if scene.background is not None:
        bg = f'<rect x="0" y="0" width="{scene.width}" height="{scene.height}" fill="{_rgb(scene.background)}"/>'

    body = []
    for s in sorted(scene.shapes, key=lambda x: x.z_index):
        fill = "none" if s.fill_color is None else _rgb(s.fill_color)
        stroke = "none" if s.stroke_color is None else _rgb(s.stroke_color)
        sw = s.stroke_width

        if s.shape_type == "rectangle":
            body.append(
                f'<rect x="{s.x:.2f}" y="{s.y:.2f}" width="{s.width:.2f}" height="{s.height:.2f}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="{sw:.2f}"/>'
            )
        elif s.shape_type == "circle":
            body.append(
                f'<circle cx="{s.cx:.2f}" cy="{s.cy:.2f}" r="{s.rx:.2f}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="{sw:.2f}"/>'
            )
        elif s.shape_type == "ellipse":
            body.append(
                f'<ellipse cx="{s.cx:.2f}" cy="{s.cy:.2f}" rx="{s.rx:.2f}" ry="{s.ry:.2f}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="{sw:.2f}"/>'
            )
        elif s.shape_type == "line":
            (x1, y1), (x2, y2) = s.points
            body.append(
                f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
                f'stroke="{stroke}" stroke-width="{sw:.2f}" stroke-linecap="round"/>'
            )
        else:
            pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in s.points)
            body.append(
                f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{sw:.2f}"/>'
            )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{scene.width}" height="{scene.height}" '
        f'viewBox="0 0 {scene.width} {scene.height}">\n'
        + bg + "\n" + "\n".join(body) + "\n</svg>\n"
    )


def export_svg(scene: Scene, path: str | Path) -> None:
    Path(path).write_text(scene_to_svg(scene), encoding="utf-8")
