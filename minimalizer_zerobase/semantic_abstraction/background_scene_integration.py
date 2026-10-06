from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from minimalizer_zerobase.compose.composer import ComposedPrimitive, VectorScene
from minimalizer_zerobase.render import SvgRenderer

from .background_field_geometry import BackgroundFieldPrimitive, reauthor_background_fields

BACKGROUND_SCENE_STAGE_VERSION = "sa7.34-v1"
BackgroundMode = Literal["field_polygons", "bbox_frame", "preserve_existing"]


@dataclass(frozen=True)
class BackgroundSceneResult:
    scene: VectorScene
    svg: str
    mode: BackgroundMode
    generated_background_count: int


def _hex(rgb: tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % tuple(int(np.clip(x, 0, 255)) for x in rgb)


def _median_rgb(rgb: np.ndarray, y0: int, y1: int, x0: int, x1: int) -> tuple[int, int, int]:
    patch = rgb[y0:y1, x0:x1]
    if patch.size == 0:
        raise ValueError("empty background frame patch")
    return tuple(int(x) for x in np.median(patch.reshape(-1, 3), axis=0))


def _bbox_frame_primitives(
    rgb: np.ndarray,
    subject_mask: np.ndarray,
) -> tuple[ComposedPrimitive, ...]:
    h, w = subject_mask.shape
    ys, xs = np.where(subject_mask)
    if len(xs) == 0:
        return ()
    x0, x1 = int(xs.min()), int(xs.max() + 1)
    y0, y1 = int(ys.min()), int(ys.max() + 1)

    strips = (
        ("top", 0, y0, 0, w),
        ("bottom", y1, h, 0, w),
        ("left", y0, y1, 0, x0),
        ("right", y0, y1, x1, w),
    )
    out: list[ComposedPrimitive] = []
    for name, sy0, sy1, sx0, sx1 in strips:
        ph = sy1 - sy0
        pw = sx1 - sx0
        if ph <= 0 or pw <= 0 or ph * pw < 32:
            continue
        # Because every strip lies strictly outside the subject bounding box,
        # it cannot overlap subject pixels. This is the hole-safe fallback.
        color = _median_rgb(rgb, sy0, sy1, sx0, sx1)
        out.append(
            ComposedPrimitive(
                primitive_id=f"semantic-background-frame:{name}",
                source_region_id="background",
                selected_candidate_id=f"semantic-background:{BACKGROUND_SCENE_STAGE_VERSION}:frame:{name}",
                primitive_type="rectangle",
                parameters={"bbox": [float(sx0), float(sy0), float(pw), float(ph)]},
                fill_ref=_hex(color),
                z_order=0,
            )
        )
    return tuple(out)


def _field_primitives(fields: tuple[BackgroundFieldPrimitive, ...]) -> tuple[ComposedPrimitive, ...]:
    out = []
    for field in fields:
        if field.subject_overlap != 0:
            raise ValueError("unsafe background field overlaps subject")
        out.append(
            ComposedPrimitive(
                primitive_id=f"semantic-background-field:{field.role_index}",
                source_region_id="background",
                selected_candidate_id=f"semantic-background:{BACKGROUND_SCENE_STAGE_VERSION}:field:{field.role_index}",
                primitive_type="convex_polygon",
                parameters={"points": [[float(x), float(y)] for x, y in field.polygon]},
                fill_ref=_hex(field.rgb),
                z_order=0,
            )
        )
    return tuple(out)


def apply_background_scene_stage(
    scene: VectorScene,
    source_rgb: np.ndarray,
    subject_mask: np.ndarray,
) -> BackgroundSceneResult:
    rgb = np.asarray(source_rgb).astype(np.uint8)
    subject = np.asarray(subject_mask).astype(bool)
    if rgb.ndim != 3 or rgb.shape[2] != 3 or subject.shape != rgb.shape[:2]:
        raise ValueError("shape mismatch")
    if rgb.shape[1] != scene.width or rgb.shape[0] != scene.height:
        raise ValueError("scene/source size mismatch")
    if int(subject.sum()) < 16:
        raise ValueError("invalid subject mask")

    fields = reauthor_background_fields(rgb, subject)
    generated = _field_primitives(fields)
    mode: BackgroundMode = "field_polygons"

    if not generated:
        generated = _bbox_frame_primitives(rgb, subject)
        mode = "bbox_frame" if generated else "preserve_existing"

    if not generated:
        out = VectorScene(
            scene.width,
            scene.height,
            scene.primitives,
            {
                **scene.provenance,
                "background_scene_stage": BACKGROUND_SCENE_STAGE_VERSION,
                "background_scene_mode": mode,
                "golden_raster_used": False,
            },
        )
        return BackgroundSceneResult(out, SvgRenderer().render(out), mode, 0)

    subject_primitives = [p for p in scene.primitives if p.source_region_id != "background"]
    min_z = min((p.z_order for p in subject_primitives), default=0)
    start_z = min_z - len(generated) - 1
    placed = []
    for index, primitive in enumerate(generated):
        placed.append(
            ComposedPrimitive(
                primitive_id=primitive.primitive_id,
                source_region_id=primitive.source_region_id,
                selected_candidate_id=primitive.selected_candidate_id,
                primitive_type=primitive.primitive_type,
                parameters=dict(primitive.parameters),
                fill_ref=primitive.fill_ref,
                z_order=start_z + index,
                occluded_by=primitive.occluded_by,
            )
        )

    merged = tuple(
        sorted(
            subject_primitives + placed,
            key=lambda p: (p.z_order, p.primitive_id),
        )
    )
    out = VectorScene(
        scene.width,
        scene.height,
        merged,
        {
            **scene.provenance,
            "background_scene_stage": BACKGROUND_SCENE_STAGE_VERSION,
            "background_scene_mode": mode,
            "background_generated_count": len(placed),
            "background_replaced_existing": sum(
                1 for p in scene.primitives if p.source_region_id == "background"
            ),
            "golden_raster_used": False,
        },
    )
    return BackgroundSceneResult(out, SvgRenderer().render(out), mode, len(placed))
