from __future__ import annotations

import numpy as np

from minimalize_engine.v2.facet.types import PlanarFacetOverlay
from minimalize_engine.v2.primitive.scoring import rasterize_geometry
from minimalize_engine.v2.primitive.types import PrimitiveGeometry


def facet_overlay_mask(
    shape: tuple[int, int],
    geometry: PrimitiveGeometry,
    overlay: PlanarFacetOverlay,
) -> np.ndarray:
    height, width = shape
    yy, xx = np.indices((height, width), dtype=np.float64)
    xn = xx / max(width - 1, 1) - 0.5
    yn = yy / max(height - 1, 1) - 0.5
    plane = overlay.line_a * xn + overlay.line_b * yn + overlay.line_c
    half = plane >= 0.0 if overlay.variant_side > 0 else plane < 0.0
    primitive = rasterize_geometry(
        geometry, shape, origin=(0, 0), scale=2
    )
    return primitive & half


def apply_planar_facet_overlay(
    image: np.ndarray,
    geometry: PrimitiveGeometry,
    overlay: PlanarFacetOverlay,
) -> np.ndarray:
    canvas = np.asarray(image, dtype=np.uint8).copy()
    mask = facet_overlay_mask(canvas.shape[:2], geometry, overlay)
    canvas[mask] = np.asarray(overlay.rgb, dtype=np.uint8)
    return canvas
