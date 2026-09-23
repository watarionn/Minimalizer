from __future__ import annotations

from typing import Mapping

import numpy as np

from minimalize_engine.v2.facet.render import apply_planar_facet_overlay
from minimalize_engine.v2.pipeline import SceneModel
from minimalize_engine.v2.primitive.scoring import rasterize_geometry


def render_geometry_scene(
    shape: tuple[int, int],
    geometries,
    palette_ids: Mapping[int, int],
    entries,
    visible: Mapping[int, bool] | None = None,
) -> np.ndarray:
    height, width = shape
    canvas = np.full((height, width, 3), 255, dtype=np.uint8)
    for region_id in sorted(geometries):
        if visible is not None and not visible.get(region_id, True):
            continue
        geometry = geometries[region_id]
        mask = rasterize_geometry(
            geometry, (height, width), origin=(0, 0), scale=2
        )
        canvas[mask] = entries[palette_ids[region_id]].rgb
    return canvas



def render_scene_coverage(scene: SceneModel) -> np.ndarray:
    """Return the union of visible primitive geometry in a scene."""
    coverage = np.zeros((scene.height, scene.width), dtype=np.bool_)
    for shape in scene.shapes:
        if not shape.visible:
            continue
        coverage |= np.asarray(
            rasterize_geometry(
                shape.geometry,
                (scene.height, scene.width),
                origin=(0, 0),
                scale=2,
            ),
            dtype=np.bool_,
        )
    return coverage


def render_scene(
    scene: SceneModel, *, include_facets: bool = True
) -> np.ndarray:
    entries = {entry.palette_id: entry for entry in scene.palette}
    geometries = {shape.region_id: shape.geometry for shape in scene.shapes}
    palette_ids = {shape.region_id: shape.palette_id for shape in scene.shapes}
    visible = {shape.region_id: shape.visible for shape in scene.shapes}
    canvas = render_geometry_scene(
        (scene.height, scene.width), geometries, palette_ids, entries, visible
    )
    if include_facets:
        for overlay in sorted(scene.facet_overlays, key=lambda item: item.region_id):
            if not visible.get(overlay.region_id, True):
                continue
            canvas = apply_planar_facet_overlay(
                canvas, geometries[overlay.region_id], overlay
            )
    return canvas
