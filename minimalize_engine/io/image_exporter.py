from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw
from ..models import Scene


def render_scene(scene: Scene, scale: int = 1) -> Image.Image:
    mode = "RGBA" if scene.background is None else "RGB"
    bg = (0, 0, 0, 0) if scene.background is None else scene.background
    img = Image.new(mode, (scene.width * scale, scene.height * scale), bg)
    draw = ImageDraw.Draw(img, "RGBA")

    def sc(v): return int(round(v * scale))
    def color(c, alpha=255):
        if c is None:
            return None
        return (*c, alpha) if mode == "RGBA" else c

    for s in sorted(scene.shapes, key=lambda x: x.z_index):
        fill = color(s.fill_color)
        stroke = color(s.stroke_color)
        sw = max(1, sc(s.stroke_width)) if s.stroke_width > 0 else 0

        if s.shape_type == "rectangle":
            box = [sc(s.x), sc(s.y), sc(s.x + s.width), sc(s.y + s.height)]
            draw.rectangle(box, fill=fill, outline=stroke, width=sw)
        elif s.shape_type == "circle":
            box = [sc(s.cx - s.rx), sc(s.cy - s.rx), sc(s.cx + s.rx), sc(s.cy + s.rx)]
            draw.ellipse(box, fill=fill, outline=stroke, width=sw)
        elif s.shape_type == "ellipse":
            box = [sc(s.cx - s.rx), sc(s.cy - s.ry), sc(s.cx + s.rx), sc(s.cy + s.ry)]
            draw.ellipse(box, fill=fill, outline=stroke, width=sw)
        elif s.shape_type == "line":
            pts = [(sc(x), sc(y)) for x, y in s.points]
            draw.line(pts, fill=stroke, width=sw)
        else:
            pts = [(sc(x), sc(y)) for x, y in s.points]
            if len(pts) >= 3:
                draw.polygon(pts, fill=fill)
                if stroke and sw:
                    draw.line(pts + [pts[0]], fill=stroke, width=sw)

    return img


def export_png(scene: Scene, path: str | Path, scale: int = 1) -> None:
    render_scene(scene, scale=scale).save(path)


def export_webp(scene: Scene, path: str | Path, scale: int = 1, quality: int = 95) -> None:
    render_scene(scene, scale=scale).save(path, "WEBP", quality=quality)
