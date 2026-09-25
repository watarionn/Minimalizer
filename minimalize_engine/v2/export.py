from __future__ import annotations

import hashlib
import struct
import zlib
from dataclasses import asdict, dataclass

import numpy as np

from minimalize_engine.v2.pipeline import MinimalizerV2Result
from minimalize_engine.v2.render import render_scene, render_scene_coverage
from minimalize_engine.v2.layered_composition import render_partitioned_scene

PNG_CONTRACT_VERSION = "minimalizer-v2-png-v1"


@dataclass(frozen=True, slots=True)
class V2PngMetadata:
    contract_version: str
    preset: str
    source_width: int
    source_height: int
    width: int
    height: int
    visible_shape_count: int
    palette_count: int
    scene_facet_count: int
    rendered_facet_count: int
    include_facets: bool
    pixel_sha256: str
    png_sha256: str
    preserves_source_alpha: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class V2PngExport:
    content: bytes
    media_type: str
    filename: str
    metadata: V2PngMetadata


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    crc = zlib.crc32(kind)
    crc = zlib.crc32(payload, crc) & 0xFFFFFFFF
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", crc)
    )


def encode_rgb_png(rgb: np.ndarray) -> bytes:
    array = np.asarray(rgb, dtype=np.uint8)
    if array.ndim != 3 or array.shape[2] != 3:
        raise ValueError("rgb must have shape (H, W, 3)")
    array = np.ascontiguousarray(array)
    height, width = array.shape[:2]
    if height <= 0 or width <= 0:
        raise ValueError("rgb dimensions must be positive")
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(
        ">IIBBBBB", width, height, 8, 2, 0, 0, 0
    )
    scanlines = b"".join(
        b"\x00" + array[row].tobytes() for row in range(height)
    )
    compressed = zlib.compress(scanlines, level=9)
    return (
        signature
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", compressed)
        + _png_chunk(b"IEND", b"")
    )


def encode_rgba_png(rgba: np.ndarray) -> bytes:
    array = np.asarray(rgba, dtype=np.uint8)
    if array.ndim != 3 or array.shape[2] != 4:
        raise ValueError("rgba must have shape (H, W, 4)")
    array = np.ascontiguousarray(array)
    height, width = array.shape[:2]
    if height <= 0 or width <= 0:
        raise ValueError("rgba dimensions must be positive")
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(
        ">IIBBBBB", width, height, 8, 6, 0, 0, 0
    )
    scanlines = b"".join(
        b"\x00" + array[row].tobytes() for row in range(height)
    )
    compressed = zlib.compress(scanlines, level=9)
    return (
        signature
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", compressed)
        + _png_chunk(b"IEND", b"")
    )


def export_png(
    result: MinimalizerV2Result,
    *,
    preset: str = "minimal",
    include_facets: bool = True,
    filename: str | None = None,
    preserve_source_alpha: bool = False,
) -> V2PngExport:
    if preset not in result.presets:
        raise ValueError(f"preset is not present in result: {preset}")
    pipeline = result.presets[preset]
    rgb = render_scene(pipeline.scene, include_facets=include_facets)
    if result.person_parts is not None:
        part_renders = {
            name: render_scene(presets[preset].scene, include_facets=include_facets)
            for name, presets in result.person_part_presets.items()
            if preset in presets
        }
        part_coverage_masks = {
            name: render_scene_coverage(presets[preset].scene)
            for name, presets in result.person_part_presets.items()
            if preset in presets
        }
        rgb = render_partitioned_scene(
            rgb,
            result.bundle.analysis_rgb,
            result.person_parts,
            part_renders=part_renders or None,
            part_coverage_masks=part_coverage_masks or None,
            scene_coverage_mask=render_scene_coverage(pipeline.scene),
            source_alpha=result.bundle.alpha,
        )
    preserves_alpha = preserve_source_alpha and result.bundle.alpha is not None
    if preserves_alpha:
        alpha = np.clip(
            np.rint(result.bundle.alpha * 255.0),
            0,
            255,
        ).astype(np.uint8)
        rgba = np.dstack((rgb, alpha))
        content = encode_rgba_png(rgba)
        pixel_bytes = rgba.tobytes()
    else:
        content = encode_rgb_png(rgb)
        pixel_bytes = rgb.tobytes()
    source_height, source_width = result.bundle.source_rgb.shape[:2]
    metadata = V2PngMetadata(
        contract_version=PNG_CONTRACT_VERSION,
        preset=preset,
        source_width=source_width,
        source_height=source_height,
        width=pipeline.scene.width,
        height=pipeline.scene.height,
        visible_shape_count=sum(shape.visible for shape in pipeline.scene.shapes),
        palette_count=len(pipeline.scene.palette),
        scene_facet_count=len(pipeline.scene.facet_overlays),
        rendered_facet_count=(
            len(pipeline.scene.facet_overlays) if include_facets else 0
        ),
        include_facets=include_facets,
        pixel_sha256=hashlib.sha256(pixel_bytes).hexdigest(),
        png_sha256=hashlib.sha256(content).hexdigest(),
        preserves_source_alpha=preserves_alpha,
    )
    return V2PngExport(
        content=content,
        media_type="image/png",
        filename=filename or f"minimalized-v2-{preset}.png",
        metadata=metadata,
    )
