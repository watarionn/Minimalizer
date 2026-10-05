from __future__ import annotations

import html
import json
from typing import Iterable

from .ir import AbstractionPlan, SemanticPart


_POLICY_STYLE = {
    "preserve": ("#1f7a4d", "PRESERVE"),
    "simplify": ("#2f67b1", "SIMPLIFY"),
    "suppress": ("#a23b3b", "SUPPRESS"),
    "conditional": ("#7a6a1f", "CONDITIONAL"),
}


def canonical_debug_json(plan: AbstractionPlan) -> str:
    return json.dumps(plan.to_dict(), ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _rect(part: SemanticPart, width: int, height: int) -> str:
    if part.bbox is None:
        return ""
    x0, y0, x1, y1 = part.bbox
    x = x0 * width
    y = y0 * height
    w = max((x1 - x0) * width, 0.0)
    h = max((y1 - y0) * height, 0.0)
    color, label = _POLICY_STYLE[part.abstraction_policy.value]
    title = html.escape(
        f"{part.id} | {label} | importance={part.importance:.3f} | confidence={part.confidence:.3f}"
    )
    return (
        f'<g data-part="{html.escape(part.id)}" data-policy="{part.abstraction_policy.value}">'
        f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" '
        f'fill="none" stroke="{color}" stroke-width="2"/>'
        f'<rect x="{x:.3f}" y="{y:.3f}" width="{max(len(title) * 6.2, 90):.3f}" height="18" '
        f'fill="#ffffff" fill-opacity="0.88"/>'
        f'<text x="{x + 3:.3f}" y="{y + 13:.3f}" font-size="11" '
        f'font-family="monospace" fill="{color}">{title}</text></g>'
    )


def render_semantic_debug_svg(
    plan: AbstractionPlan,
    *,
    width: int,
    height: int,
    source_href: str | None = None,
) -> str:
    if width <= 0 or height <= 0:
        raise ValueError("debug board dimensions must be positive")
    image = (
        f'<image href="{html.escape(source_href)}" x="0" y="0" width="{width}" height="{height}"/>'
        if source_href
        else f'<rect x="0" y="0" width="{width}" height="{height}" fill="#f4f4f4"/>'
    )
    overlays = "".join(_rect(part, width, height) for part in sorted(plan.parts, key=lambda p: p.id))
    rows = []
    for part in sorted(plan.parts, key=lambda p: p.id):
        topology = ",".join(
            f"{item.relation}:{item.target_part_id}" for item in part.topology_constraints
        ) or "-"
        rows.append(
            f"{html.escape(part.id)} | {part.abstraction_policy.value.upper()} | "
            f"{part.importance:.3f} | {html.escape(topology)}"
        )
    panel_x = width + 16
    panel_width = 430
    panel = [
        f'<rect x="{width}" y="0" width="{panel_width + 16}" height="{height}" fill="#ffffff"/>',
        f'<text x="{panel_x}" y="24" font-size="16" font-family="sans-serif" font-weight="bold">Semantic Debug Board</text>',
    ]
    for index, row in enumerate(rows):
        panel.append(
            f'<text x="{panel_x}" y="{48 + index * 18}" font-size="11" font-family="monospace">'
            f'{html.escape(row)}</text>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width + panel_width + 16}" height="{height}" '
        f'viewBox="0 0 {width + panel_width + 16} {height}">{image}{overlays}{"".join(panel)}</svg>\n'
    )
