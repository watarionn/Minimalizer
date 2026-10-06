from __future__ import annotations
from html import escape
from minimalizer_zerobase.compose import VectorScene

class SvgRenderer:
    producer = "SvgRenderer"
    producer_version = "1.1"

    def render(self, scene: VectorScene) -> str:
        lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{scene.width}" height="{scene.height}" '
            f'viewBox="0 0 {scene.width} {scene.height}">'
        ]
        for primitive in sorted(scene.primitives, key=lambda x: (x.z_order, x.primitive_id)):
            lines.append(self._primitive(primitive))
        lines.append("</svg>")
        return "\n".join(lines) + "\n"

    def _primitive(self, primitive) -> str:
        p = primitive.parameters
        fill = escape(primitive.fill_ref or "none", quote=True)
        common = f'id="{escape(primitive.primitive_id, quote=True)}" fill="{fill}"'
        shape_rendering = p.get("shape_rendering")
        if shape_rendering is not None:
            if shape_rendering not in {
                "auto",
                "optimizeSpeed",
                "crispEdges",
                "geometricPrecision",
            }:
                raise ValueError("unsupported shape_rendering hint")
            common += f' shape-rendering="{escape(shape_rendering, quote=True)}"'

        kind = primitive.primitive_type
        if kind == "ellipse":
            return (
                f'  <ellipse {common} cx="{self._n(p["cx"])}" cy="{self._n(p["cy"])}" '
                f'rx="{self._n(p["rx"])}" ry="{self._n(p["ry"])}"/>'
            )
        if kind in {"triangle", "trapezoid", "convex_polygon"}:
            points = " ".join(
                f'{self._n(x)},{self._n(y)}' for x, y in p["points"]
            )
            return f'  <polygon {common} points="{points}"/>'
        x, y, w, h = (float(v) for v in p["bbox"])
        if kind == "capsule":
            radius = float(p["radius"])
            return (
                f'  <rect {common} x="{self._n(x)}" y="{self._n(y)}" '
                f'width="{self._n(w)}" height="{self._n(h)}" '
                f'rx="{self._n(radius)}" ry="{self._n(radius)}"/>'
            )
        if kind == "rectangle":
            return (
                f'  <rect {common} x="{self._n(x)}" y="{self._n(y)}" '
                f'width="{self._n(w)}" height="{self._n(h)}"/>'
            )
        raise ValueError(f"unsupported primitive type: {kind}")

    @staticmethod
    def _n(value: float) -> str:
        value = float(value)
        if value == int(value):
            return str(int(value))
        return format(value, ".6f").rstrip("0").rstrip(".")
