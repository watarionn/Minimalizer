"""Non-rendering SVG evidence exporter for SA10 source-grounded contours.

The SVG is for inspection only. Never insert it into the production scene.
"""
from __future__ import annotations

from html import escape

from .source_svg_contour_proposals import ContourProposal


def proposal_svg_evidence(
    proposal: ContourProposal,
    *,
    width: int,
    height: int,
) -> str:
    """Serialize an existing-owner contour without paint or facial features."""
    if width <= 0 or height <= 0:
        raise ValueError("invalid canvas dimensions")
    if proposal.owner not in {"face", "hair"}:
        raise ValueError("unsupported owner")
    if len(proposal.points_xy) < 3 or len(proposal.points_xy) != proposal.vertices:
        raise ValueError("invalid polygon")
    for x, y in proposal.points_xy:
        if not (0 <= x < width and 0 <= y < height):
            raise ValueError("point outside canvas")
    path = "M " + " L ".join(f"{x} {y}" for x, y in proposal.points_xy) + " Z"
    owner = escape(proposal.owner, quote=True)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<title>Diagnostic contour: {owner}</title>'
        f'<path data-owner="{owner}" d="{path}" fill="none" '
        f'stroke="#000" stroke-width="1"/></svg>'
    )
