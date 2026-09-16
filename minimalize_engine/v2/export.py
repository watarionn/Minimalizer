from __future__ import annotations

import hashlib
import struct
import zlib
from dataclasses import asdict, dataclass

import numpy as np

from minimalize_engine.v2.pipeline import MinimalizerV2Result
from minimalize_engine.v2.render import render_scene

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


def export_png(
    result: MinimalizerV2Result,
    *,
    preset: str = "minimal",
    include_facets: bool = True,
    filename: str | None = None,
) -> V2PngExport:
    if preset not in result.presets:
        raise ValueError(f"preset is not present in result: {preset}")
    pipeline = result.presets[preset]
    rgb = render_scene(pipeline.scene, include_facets=include_facets)
    content = encode_rgb_png(rgb)
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
        pixel_sha256=hashlib.sha256(rgb.tobytes()).hexdigest(),
        png_sha256=hashlib.sha256(content).hexdigest(),
    )
    return V2PngExport(
        content=content,
        media_type="image/png",
        filename=filename or f"minimalized-v2-{preset}.png",
        metadata=metadata,
    )
